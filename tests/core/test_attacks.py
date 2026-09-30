"""core/attacks.py: the geometry tables, is_square_attacked and is_in_check.

Every expectation is worked out by hand from the board; none is read back from the tables.
Every FEN has both kings, placed away from the squares under test.
"""

from __future__ import annotations

import unittest

from chess.core.attacks import (
    DIAGONAL,
    EAST,
    KING_TARGETS,
    KNIGHT_TARGETS,
    NORTH,
    NORTH_EAST,
    ORTHOGONAL,
    PAWN_ATTACKS,
    RAYS,
    SOUTH,
    SOUTH_WEST,
    WEST,
    is_in_check,
    is_square_attacked,
)
from chess.core.board import Board
from chess.core.fen import STARTING_FEN
from chess.core.movegen import pseudo_legal_moves
from chess.core.types import (
    A1,
    A2,
    A3,
    A4,
    A5,
    A6,
    A7,
    A8,
    B1,
    B2,
    B3,
    B7,
    B8,
    C1,
    C2,
    C3,
    C5,
    D1,
    D2,
    D3,
    D4,
    D5,
    D6,
    D8,
    E1,
    E2,
    E3,
    E4,
    E5,
    E6,
    F1,
    F2,
    F3,
    F4,
    F5,
    F6,
    G1,
    G3,
    G5,
    G6,
    G7,
    H1,
    H4,
    H6,
    H7,
    H8,
    Color,
)

WHITE = Color.WHITE.value
BLACK = Color.BLACK.value

KIWIPETE_FEN = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"

# Source: https://www.chessprogramming.org/Perft_Results, starting position, columns
# Checks and Captures, transcribed 2026-09-26. {depth: (checks, captures)}
START_CHECKS_AND_CAPTURES = {1: (0, 0), 2: (0, 0), 3: (12, 34)}


class TableShapeTest(unittest.TestCase):
    TABLES = (
        ("knight", KNIGHT_TARGETS),
        ("king", KING_TARGETS),
        ("white pawn", PAWN_ATTACKS[WHITE]),
        ("black pawn", PAWN_ATTACKS[BLACK]),
    )

    def test_every_table_has_64_tuple_entries_of_valid_squares(self) -> None:
        for name, table in self.TABLES:
            with self.subTest(table=name):
                self.assertIsInstance(table, tuple)
                self.assertEqual(len(table), 64)
                for targets in table:
                    self.assertIsInstance(targets, tuple)
                    self.assertTrue(all(0 <= sq < 64 for sq in targets))

    def test_every_square_has_eight_tuple_rays_of_valid_squares(self) -> None:
        self.assertIsInstance(RAYS, tuple)
        self.assertEqual(len(RAYS), 64)
        for sq in range(64):
            with self.subTest(sq=sq):
                self.assertIsInstance(RAYS[sq], tuple)
                self.assertEqual(len(RAYS[sq]), 8)
                for ray in RAYS[sq]:
                    self.assertIsInstance(ray, tuple)
                    self.assertTrue(all(0 <= target < 64 for target in ray))

    def test_orthogonal_and_diagonal_split_the_eight_directions(self) -> None:
        self.assertEqual(sorted(ORTHOGONAL + DIAGONAL), list(range(8)))


class KnightTest(unittest.TestCase):
    def test_knight_targets_by_square(self) -> None:
        cases = (
            ("a1 corner", A1, {B3, C2}),
            ("h1 corner, no wrap to the a-file", H1, {F2, G3}),
            ("e4 open", E4, {D6, F6, G5, G3, F2, D2, C3, C5}),
        )
        for what, sq, expected in cases:
            with self.subTest(what=what):
                self.assertEqual(len(KNIGHT_TARGETS[sq]), len(expected))
                self.assertEqual(set(KNIGHT_TARGETS[sq]), expected)


class KingTest(unittest.TestCase):
    def test_king_targets_by_square(self) -> None:
        cases = (
            ("a8 corner", A8, {A7, B7, B8}),
            ("e4 open", E4, {D3, E3, F3, D4, F4, D5, E5, F5}),
        )
        for what, sq, expected in cases:
            with self.subTest(what=what):
                self.assertEqual(len(KING_TARGETS[sq]), len(expected))
                self.assertEqual(set(KING_TARGETS[sq]), expected)


class RayTest(unittest.TestCase):
    def test_rays_run_from_the_source_to_the_edge(self) -> None:
        cases = (
            ("a1 north", A1, NORTH, (A2, A3, A4, A5, A6, A7, A8)),
            ("a1 east", A1, EAST, (B1, C1, D1, E1, F1, G1, H1)),
            ("a1 north-east", A1, NORTH_EAST, (B2, C3, D4, E5, F6, G7, H8)),
            ("a1 south", A1, SOUTH, ()),
            ("a1 west", A1, WEST, ()),
            ("a1 south-west", A1, SOUTH_WEST, ()),
            ("h1 west", H1, WEST, (G1, F1, E1, D1, C1, B1, A1)),
            ("h4 east, no wrap to a5", H4, EAST, ()),
        )
        for what, sq, direction, expected in cases:
            with self.subTest(what=what):
                self.assertEqual(RAYS[sq][direction], expected)


class PawnAttackTest(unittest.TestCase):
    def test_pawn_attacks_by_color_and_square(self) -> None:
        cases = (
            ("white a2, one side only", WHITE, A2, {B3}),
            ("white e4", WHITE, E4, {D5, F5}),
            ("black h7, one side only", BLACK, H7, {G6}),
            ("black e5", BLACK, E5, {D4, F4}),
        )
        for what, color, sq, expected in cases:
            with self.subTest(what=what):
                self.assertEqual(len(PAWN_ATTACKS[color][sq]), len(expected))
                self.assertEqual(set(PAWN_ATTACKS[color][sq]), expected)


class IsSquareAttackedTest(unittest.TestCase):
    def assert_attacked(self, fen: str, by: Color, expected: dict[int, bool]) -> None:
        board = Board.from_fen(fen)
        for sq, attacked in expected.items():
            with self.subTest(fen=fen, by=by.name, sq=sq):
                self.assertIs(is_square_attacked(board, sq, by), attacked)

    def test_square_attacked_by_piece_and_color_matches_hand_count(self) -> None:
        cases = (
            ("white pawn e4", "k7/8/8/8/4P3/8/8/7K w - - 0 1", Color.WHITE,
             {D5: True, F5: True, E5: False, D3: False}),
            ("black pawn e5 attacks downwards", "k7/8/8/4p3/8/8/8/7K w - - 0 1", Color.BLACK,
             {D4: True, F4: True, E4: False, D6: False}),
            ("knight b1", "k7/8/8/8/8/8/8/1N5K w - - 0 1", Color.WHITE,
             {A3: True, C3: True, D2: True, B3: False}),
            ("bishop c1, empty diagonal", "7k/8/8/8/8/7K/8/2B5 w - - 0 1", Color.WHITE,
             {D2: True, E3: True, F4: True, G5: True, H6: True}),
            ("rook a1, empty lines", "7k/8/8/8/8/7K/8/R7 w - - 0 1", Color.WHITE,
             dict.fromkeys((A2, A3, A4, A5, A6, A7, A8, B1, C1, D1, E1, F1, G1, H1), True)),
            ("queen d4, both kinds of line", "7k/8/8/8/3Q4/7K/8/8 w - - 0 1", Color.WHITE,
             {D8: True, A4: True, A7: True, G1: True, E6: False}),
            ("king e1, two squares away is not attacked", "7k/8/8/8/8/8/8/4K3 w - - 0 1",
             Color.WHITE, {D1: True, D2: True, E2: True, F1: True, F2: True, E3: False}),
        )  # fmt: skip
        for what, fen, by, expected in cases:
            with self.subTest(what=what):
                self.assert_attacked(fen, by, expected)

    def test_square_attacked_own_piece_blocks_ray_beyond_it(self) -> None:
        # f4 is not asserted: the pawn on e3 attacks it itself.
        self.assert_attacked(
            "7k/8/8/8/8/4P2K/8/2B5 w - - 0 1", Color.WHITE, {E3: True, G5: False, H6: False}
        )

    def test_square_attacked_enemy_piece_blocks_ray_beyond_it(self) -> None:
        self.assert_attacked("7k/8/8/8/8/n6K/8/R7 w - - 0 1", Color.WHITE, {A3: True, A4: False})

    def test_square_attacked_pinned_attacker_still_attacks(self) -> None:
        self.assert_attacked("4r2k/8/8/8/8/8/4B3/4K3 w - - 0 1", Color.WHITE, {D3: True})

    def test_square_attacked_own_piece_on_target_counts_as_attacked(self) -> None:
        fen = "7k/8/8/8/8/7K/P7/R7 w - - 0 1"
        self.assert_attacked(fen, Color.WHITE, {A2: True})
        self.assert_attacked(fen, Color.BLACK, {A2: False})

    def test_square_attacked_without_attacker_not_attacked(self) -> None:
        self.assert_attacked("7k/8/8/8/8/7K/8/8 w - - 0 1", Color.WHITE, {E4: False, F3: False})

    def test_square_attacked_leaves_fen_and_key_unchanged(self) -> None:
        board = Board.from_fen(KIWIPETE_FEN)
        key = board.key
        for by in Color:
            for sq in range(64):
                is_square_attacked(board, sq, by)
        self.assertEqual(board.to_fen(), KIWIPETE_FEN)
        self.assertEqual(board.key, key)


class IsInCheckTest(unittest.TestCase):
    def test_in_check_by_position_matches_hand_count(self) -> None:
        cases = (
            ("start, white", STARTING_FEN, Color.WHITE, False),
            ("start, black", STARTING_FEN, Color.BLACK, False),
            ("rook on the file, white", "4r2k/8/8/8/8/8/8/4K3 w - - 0 1", Color.WHITE, True),
            ("rook on the file, black", "4r2k/8/8/8/8/8/8/4K3 w - - 0 1", Color.BLACK, False),
            ("knight between rook and king", "4r2k/8/8/8/8/8/4N3/4K3 w - - 0 1", Color.WHITE,
             False),
            ("double check, rook and bishop", "4r2k/8/8/8/1b6/8/8/4K3 w - - 0 1", Color.WHITE,
             True),
            ("knight", "7k/8/8/8/8/3n4/8/4K3 w - - 0 1", Color.WHITE, True),
            ("black pawn d5, king e4", "7k/8/8/3p4/4K3/8/8/8 w - - 0 1", Color.WHITE, True),
            ("black pawn e5 in front of king e4", "7k/8/8/4p3/4K3/8/8/8 w - - 0 1", Color.WHITE,
             False),
            ("white pawn d4, king e5", "8/8/8/4k3/3P4/8/8/K7 b - - 0 1", Color.BLACK, True),
            ("white pawn d6 behind king e5", "8/8/3P4/4k3/8/8/8/K7 b - - 0 1", Color.BLACK,
             False),
            # The call from 1.6: the side that just moved, not the side to move.
            ("side not to move", "7k/8/8/8/8/8/8/r3K3 b - - 0 1", Color.WHITE, True),
        )  # fmt: skip
        for what, fen, color, expected in cases:
            with self.subTest(what=what):
                self.assertIs(is_in_check(Board.from_fen(fen), color), expected)

    def test_in_check_leaves_fen_and_key_unchanged(self) -> None:
        fen = "4r2k/8/8/8/1b6/8/8/4K3 w - - 0 1"
        board = Board.from_fen(fen)
        key = board.key
        for color in Color:
            is_in_check(board, color)
        self.assertEqual(board.to_fen(), fen)
        self.assertEqual(board.key, key)


def _count_check_and_capture_leaves(board: Board, depth: int) -> tuple[int, int]:
    """Return (leaves with the side to move in check, leaves reached by a capture).

    A capture is read from the undo record, not the move kind: the CPW column also counts
    en passant and capturing promotions.
    """
    checks = captures = 0
    for move in pseudo_legal_moves(board):
        undo = board.make(move)
        if depth == 1:
            checks += is_in_check(board, board.turn)
            captures += undo.captured is not None
        else:
            leaf_checks, leaf_captures = _count_check_and_capture_leaves(board, depth - 1)
            checks += leaf_checks
            captures += leaf_captures
        board.unmake(move, undo)
    return checks, captures


class CheckAndCaptureLeavesTest(unittest.TestCase):
    def test_start_check_and_capture_leaves_match_cpw(self) -> None:
        # Pseudo-legal equals legal up to depth 3 from the start, so the counts match CPW.
        for depth, expected in START_CHECKS_AND_CAPTURES.items():
            with self.subTest(depth=depth):
                board = Board.from_fen(STARTING_FEN)
                self.assertEqual(_count_check_and_capture_leaves(board, depth), expected)


if __name__ == "__main__":
    unittest.main()
