"""core/rules.py: checkmate, stalemate, draws and the RuleSet profiles.

The mate table expectations were checked with an independent generator on 2026-10-17; the
leaf counts are the CPW Checkmates column. The repetition counts were checked against the
Board key on 2026-10-19.
"""

from __future__ import annotations

import dataclasses
import unittest
from collections.abc import Iterator

from chess.core.board import Board
from chess.core.fen import STARTING_FEN
from chess.core.movegen import legal_moves
from chess.core.rules import (
    FIDE_RULES,
    ONLINE_RULES,
    RuleSet,
    draw_reason,
    has_insufficient_material,
    is_checkmate,
    is_stalemate,
)
from chess.core.types import Move, Termination

FOOLS_MATE_FEN = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
QUEEN_STALEMATE_FEN = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
CASTLING_FEN = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"

KIWIPETE_FEN = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
POSITION_3_FEN = "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"
POSITION_4_FEN = "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1"

# Source: https://www.chessprogramming.org/Perft_Results, column Checkmates,
# transcribed 2026-10-17. {name: (fen, depth, checkmates)}
CHECKMATE_LEAVES = {
    "Kiwipete": (KIWIPETE_FEN, 3, 1),
    "Position 3": (POSITION_3_FEN, 4, 17),
    "Position 4": (POSITION_4_FEN, 3, 22),
}


class MateAndStalemateTest(unittest.TestCase):
    def test_mate_and_stalemate_by_position_match_expected(self) -> None:
        cases = (
            ("start", STARTING_FEN, False, False),
            ("fool's mate", FOOLS_MATE_FEN, True, False),
            ("back rank mate", "4R1k1/5ppp/8/8/8/8/8/6K1 b - - 0 1", True, False),
            ("smothered mate", "6rk/5Npp/8/8/8/8/8/K7 b - - 0 1", True, False),
            ("scholar's mate, queen f7 covered by bishop c4",
             "r1bqkb1r/pppp1Qpp/2n2n2/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4", True, False),
            ("stalemate, queen and king", QUEEN_STALEMATE_FEN, False, True),
            ("stalemate by a pawn", "k7/P7/K7/8/8/8/8/8 b - - 0 1", False, True),
            ("check with a way out", "4k3/8/8/8/8/8/8/4K2r w - - 0 1", False, False),
            ("castling base", CASTLING_FEN, False, False),
        )  # fmt: skip
        for what, fen, mate, stalemate in cases:
            with self.subTest(what=what):
                board = Board.from_fen(fen)
                self.assertIs(is_checkmate(board), mate)
                self.assertIs(is_stalemate(board), stalemate)

    def test_queries_leave_fen_key_and_squares_unchanged(self) -> None:
        for fen in (FOOLS_MATE_FEN, QUEEN_STALEMATE_FEN, CASTLING_FEN):
            with self.subTest(fen=fen):
                board = Board.from_fen(fen)
                squares = list(board.squares)
                key = board.key
                is_checkmate(board)
                is_stalemate(board)
                has_insufficient_material(board)
                draw_reason(board, (board.key,))
                self.assertEqual(board.to_fen(), fen)
                self.assertEqual(board.key, key)
                self.assertEqual(board.squares, squares)


def _count_checkmate_leaves(board: Board, depth: int) -> int:
    """Return the number of leaves at `depth` where the side to move is checkmated."""
    if depth == 0:
        return int(is_checkmate(board))
    count = 0
    for move in legal_moves(board):
        undo = board.make(move)
        count += _count_checkmate_leaves(board, depth - 1)
        board.unmake(move, undo)
    return count


class CheckmateLeavesTest(unittest.TestCase):
    def test_checkmate_leaves_match_cpw(self) -> None:
        for name, (fen, depth, expected) in CHECKMATE_LEAVES.items():
            with self.subTest(position=name, depth=depth):
                board = Board.from_fen(fen)
                self.assertEqual(_count_checkmate_leaves(board, depth), expected)


def _play(fen: str, ucis: list[str]) -> Iterator[tuple[int, Board, tuple[int, ...]]]:
    """Play `ucis` from `fen`; after each move yield (ply, board, keys of every position).

    A move is looked up in the legal moves and the generated instance is made (ADR-022).
    """
    board = Board.from_fen(fen)
    keys = [board.key]
    for ply, uci in enumerate(ucis, start=1):
        moves = legal_moves(board)
        board.make(moves[moves.index(Move.from_uci(uci))])
        keys.append(board.key)
        yield ply, board, tuple(keys)


class InsufficientMaterialTest(unittest.TestCase):
    def test_four_drawn_pairs_are_insufficient(self) -> None:
        cases = (
            ("K-K", "4k3/8/8/8/8/8/8/4K3 w - - 0 1"),
            ("KB-K", "4k3/8/8/8/8/8/8/2B1K3 w - - 0 1"),
            ("K-KB", "2b1k3/8/8/8/8/8/8/4K3 w - - 0 1"),
            ("KN-K", "4k3/8/8/8/8/8/8/1N2K3 w - - 0 1"),
            ("K-KN", "1n2k3/8/8/8/8/8/8/4K3 w - - 0 1"),
            ("KB-KB, c1 and f8 both dark", "4kb2/8/8/8/8/8/8/2B1K3 w - - 0 1"),
        )
        for what, fen in cases:
            with self.subTest(what=what):
                self.assertIs(has_insufficient_material(Board.from_fen(fen)), True)

    def test_anything_else_is_sufficient(self) -> None:
        cases = (
            ("KB-KB, c1 dark and c8 light", "2b1k3/8/8/8/8/8/8/2B1K3 w - - 0 1"),
            ("KBB-K, both bishops dark", "4k3/8/8/8/8/8/8/B1B1K3 w - - 0 1"),
            ("KBB-K, opposite colors", "4k3/8/8/8/8/8/8/2B1KB2 w - - 0 1"),
            ("KNN-K", "4k3/8/8/8/8/8/8/1N2K1N1 w - - 0 1"),
            ("KN-KN", "1n2k3/8/8/8/8/8/8/1N2K3 w - - 0 1"),
            ("KB-KN", "1n2k3/8/8/8/8/8/8/2B1K3 w - - 0 1"),
            ("KP-K", "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1"),
            ("KR-K", "4k3/8/8/8/8/8/8/R3K3 w - - 0 1"),
            ("KQ-KN", "1n2k3/8/8/8/8/8/8/3QK3 w - - 0 1"),
            ("start", STARTING_FEN),
        )
        for what, fen in cases:
            with self.subTest(what=what):
                self.assertIs(has_insufficient_material(Board.from_fen(fen)), False)


class HalfmoveClockTest(unittest.TestCase):
    def test_clock_threshold_follows_the_profile(self) -> None:
        cases = (
            ("online", ONLINE_RULES, 99, None),
            ("online", ONLINE_RULES, 100, Termination.FIFTY_MOVE),
            ("fide", FIDE_RULES, 100, None),
            ("fide", FIDE_RULES, 149, None),
            ("fide", FIDE_RULES, 150, Termination.SEVENTY_FIVE_MOVE),
        )
        for profile, rules, clock, expected in cases:
            with self.subTest(profile=profile, clock=clock):
                board = Board.from_fen(f"4k3/8/8/8/8/8/8/R3K3 w - - {clock} 60")
                self.assertIs(draw_reason(board, (board.key,), rules), expected)

    def test_quiet_move_at_99_reaches_fifty_move(self) -> None:
        for _, board, keys in _play("4k3/8/8/8/8/8/8/R3K3 w - - 99 60", ["a1a2"]):
            self.assertIs(draw_reason(board, keys), Termination.FIFTY_MOVE)

    def test_capture_at_99_resets_the_clock(self) -> None:
        for _, board, keys in _play("4k3/8/8/8/8/8/p7/R3K3 w - - 99 60", ["a1a2"]):
            self.assertIsNone(draw_reason(board, keys))


class RepetitionTest(unittest.TestCase):
    def test_knight_shuffle_from_start_repeats_by_profile(self) -> None:
        moves = ["g1f3", "g8f6", "f3g1", "f6g8"] * 4
        for ply, board, keys in _play(STARTING_FEN, moves):
            with self.subTest(ply=ply):
                online = Termination.THREEFOLD_REPETITION if ply >= 8 else None
                fide = Termination.FIVEFOLD_REPETITION if ply >= 16 else None
                self.assertIs(draw_reason(board, keys, ONLINE_RULES), online)
                self.assertIs(draw_reason(board, keys, FIDE_RULES), fide)

    def test_repetition_counts_castling_rights(self) -> None:
        # The placement is back for the third time after ply 8, but the start had KQkq
        # and every later copy has Kk, so the third equal position comes after ply 10.
        moves = ["a1b1", "a8b8", "b1a1", "b8a8"] * 3
        for ply, board, keys in _play("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", moves):
            with self.subTest(ply=ply):
                expected = Termination.THREEFOLD_REPETITION if ply >= 10 else None
                self.assertIs(draw_reason(board, keys), expected)

    def test_repetition_counts_en_passant_right(self) -> None:
        # After e2e4 the d4 pawn can take en passant, so that copy carries the EP square
        # in its key (ADR-027); the later copies do not and repeat among themselves.
        moves = ["e2e4"] + ["e8d8", "e1d1", "d8e8", "d1e1"] * 3
        for ply, board, keys in _play("4k3/8/8/8/3p4/8/4P3/4K3 w - - 0 1", moves):
            with self.subTest(ply=ply):
                expected = Termination.THREEFOLD_REPETITION if ply >= 10 else None
                self.assertIs(draw_reason(board, keys), expected)


class DrawPriorityTest(unittest.TestCase):
    def test_material_beats_clock_and_repetition(self) -> None:
        board = Board.from_fen("4k3/8/8/8/8/8/8/1N2K3 w - - 100 80")
        keys = (board.key,) * 3
        self.assertIs(draw_reason(board, keys), Termination.INSUFFICIENT_MATERIAL)

    def test_clock_beats_repetition(self) -> None:
        board = Board.from_fen("4k3/8/8/8/8/8/8/R3K3 w - - 100 80")
        keys = (board.key,) * 3
        self.assertIs(draw_reason(board, keys), Termination.FIFTY_MOVE)


class DrawReasonGuardTest(unittest.TestCase):
    def test_keys_empty_or_not_ending_with_board_key_raise_value_error(self) -> None:
        board = Board.from_fen(STARTING_FEN)
        for what, keys in (("empty", ()), ("other key last", (board.key ^ 1,))):
            with self.subTest(what=what), self.assertRaises(ValueError):
                draw_reason(board, keys)


class RuleSetTest(unittest.TestCase):
    def test_profiles_hold_their_thresholds_and_terminations(self) -> None:
        cases = (
            ("online", ONLINE_RULES, 3, Termination.THREEFOLD_REPETITION, 100,
             Termination.FIFTY_MOVE),
            ("fide", FIDE_RULES, 5, Termination.FIVEFOLD_REPETITION, 150,
             Termination.SEVENTY_FIVE_MOVE),
        )  # fmt: skip
        for name, rules, repetitions, repetition_end, halfmoves, halfmove_end in cases:
            with self.subTest(profile=name):
                self.assertEqual(rules.repetitions, repetitions)
                self.assertIs(rules.repetition_termination, repetition_end)
                self.assertEqual(rules.halfmoves, halfmoves)
                self.assertIs(rules.halfmove_termination, halfmove_end)

    def test_rule_set_is_frozen(self) -> None:
        self.assertIsInstance(ONLINE_RULES, RuleSet)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            ONLINE_RULES.repetitions = 2  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
