"""core/san.py: SAN generation with disambiguation, SAN parsing and the round trip."""

from __future__ import annotations

import unittest

from chess.core.board import Board
from chess.core.fen import STARTING_FEN
from chess.core.movegen import legal_moves
from chess.core.san import parse_san, to_san
from chess.core.types import InvalidSanError, Move

# Same FENs as tests/core/test_perft.py, source https://www.chessprogramming.org/Perft_Results.
# (name, FEN, number of legal moves at depth 1)
PERFT_POSITIONS = (
    ("start", STARTING_FEN, 20),
    ("kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq -", 48),
    ("position 3", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 14),
    ("position 4", "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", 6),
    ("position 5", "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", 44),
)

ROOK_FEN = "4k3/8/8/8/8/8/8/R3K3 w - - 0 1"
EN_PASSANT_FEN = "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1"
CASTLING_FEN = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
PROMOTION_FEN = "1n5k/P7/8/8/8/8/8/4K3 w - - 0 1"
FOOLS_MATE_FEN = "rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq g3 0 2"

TWO_KNIGHTS_FILES_FEN = "r3k3/8/8/8/8/5N2/8/RN2K3 w - - 0 1"
TWO_KNIGHTS_RANKS_FEN = "4k3/8/8/6N1/8/8/8/4K1N1 w - - 0 1"
THREE_QUEENS_FEN = "k7/8/8/8/1Q1Q4/8/1Q6/4K3 w - - 0 1"
PINNED_KNIGHT_FEN = "5r1k/8/8/8/8/5N2/8/1N3K2 w - - 0 1"

DISAMBIGUATION_POSITIONS = (
    TWO_KNIGHTS_FILES_FEN,
    TWO_KNIGHTS_RANKS_FEN,
    THREE_QUEENS_FEN,
    PINNED_KNIGHT_FEN,
)


def _legal(board: Board, uci: str) -> Move:
    """Return the generated legal move `uci` on `board` (ADR-022)."""
    moves = legal_moves(board)
    return moves[moves.index(Move.from_uci(uci))]


class ToSanTest(unittest.TestCase):
    def test_single_moves_match_expected_san(self) -> None:
        cases = (
            (STARTING_FEN, "e2e4", "e4"),
            (STARTING_FEN, "g1f3", "Nf3"),
            ("rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2", "e4d5", "exd5"),
            ("4k3/8/8/4p3/8/5N2/8/4K3 w - - 0 1", "f3e5", "Nxe5"),
            (ROOK_FEN, "e1f1", "Kf1"),
            (ROOK_FEN, "a1a8", "Ra8+"),
            (EN_PASSANT_FEN, "e5d6", "exd6"),
            (CASTLING_FEN, "e1g1", "O-O"),
            (CASTLING_FEN, "e1c1", "O-O-O"),
            (PROMOTION_FEN, "a7a8q", "a8=Q"),
            (PROMOTION_FEN, "a7a8n", "a8=N"),
            (PROMOTION_FEN, "a7b8q", "axb8=Q+"),
            (FOOLS_MATE_FEN, "d8h4", "Qh4#"),
        )  # fmt: skip
        for fen, uci, san in cases:
            with self.subTest(fen=fen, move=uci):
                board = Board.from_fen(fen)
                self.assertEqual(to_san(board, _legal(board, uci)), san)

    def test_disambiguation_file_then_rank_then_both(self) -> None:
        cases = (
            (TWO_KNIGHTS_FILES_FEN, "b1d2", "Nbd2"),
            (TWO_KNIGHTS_FILES_FEN, "f3d2", "Nfd2"),
            (TWO_KNIGHTS_RANKS_FEN, "g1f3", "N1f3"),
            (TWO_KNIGHTS_RANKS_FEN, "g5f3", "N5f3"),
            (THREE_QUEENS_FEN, "b4d2", "Qb4d2"),
            (THREE_QUEENS_FEN, "b2d2", "Q2d2"),
            (THREE_QUEENS_FEN, "d4d2", "Qdd2"),
            # The f3 knight is pinned by the f8 rook, so it is not a legal rival.
            (PINNED_KNIGHT_FEN, "b1d2", "Nd2"),
        )
        for fen, uci, san in cases:
            with self.subTest(fen=fen, move=uci):
                board = Board.from_fen(fen)
                self.assertEqual(to_san(board, _legal(board, uci)), san)

    def test_move_from_uci_without_kind_uses_generated_move(self) -> None:
        cases = ((CASTLING_FEN, "e1g1", "O-O"), (EN_PASSANT_FEN, "e5d6", "exd6"))
        for fen, uci, san in cases:
            with self.subTest(fen=fen, move=uci):
                self.assertEqual(to_san(Board.from_fen(fen), Move.from_uci(uci)), san)

    def test_move_not_legal_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            to_san(Board.from_fen(STARTING_FEN), Move.from_uci("e2e5"))


class RoundTripTest(unittest.TestCase):
    def test_every_legal_move_round_trips_and_sans_are_distinct(self) -> None:
        positions = [(name, fen, count) for name, fen, count in PERFT_POSITIONS]
        positions += [(fen, fen, None) for fen in DISAMBIGUATION_POSITIONS]
        for name, fen, count in positions:
            with self.subTest(position=name):
                board = Board.from_fen(fen)
                moves = legal_moves(board)
                if count is not None:
                    self.assertEqual(len(moves), count)
                sans = []
                for move in moves:
                    san = to_san(board, move)
                    parsed = parse_san(board, san)
                    self.assertEqual(parsed, move, san)
                    self.assertIs(parsed.kind, move.kind, san)
                    sans.append(san)
                self.assertEqual(len(set(sans)), len(moves), sans)


class ParseSanTest(unittest.TestCase):
    def test_tolerated_forms_parse(self) -> None:
        board = Board.from_fen(STARTING_FEN)
        for text in ("Nf3+", "Ngf3"):
            with self.subTest(text=text):
                self.assertEqual(parse_san(board, text), Move.from_uci("g1f3"))

    def test_invalid_or_ambiguous_raise_invalid_san_error(self) -> None:
        cases = (
            (STARTING_FEN, "Nf6"),
            (STARTING_FEN, "nf3"),
            (STARTING_FEN, "xyz"),
            (STARTING_FEN, ""),
            (TWO_KNIGHTS_FILES_FEN, "Nd2"),
            (CASTLING_FEN, "0-0"),
            (PROMOTION_FEN, "a8"),
            (EN_PASSANT_FEN, "exd6 e.p."),
        )
        for fen, text in cases:
            with self.subTest(fen=fen, text=text), self.assertRaises(InvalidSanError):
                parse_san(Board.from_fen(fen), text)


class BoardUnchangedTest(unittest.TestCase):
    def test_to_san_and_parse_san_leave_fen_key_and_squares_unchanged(self) -> None:
        cases = (
            ("to_san Ra8+", ROOK_FEN, lambda board: to_san(board, _legal(board, "a1a8"))),
            ("to_san Qh4#", FOOLS_MATE_FEN, lambda board: to_san(board, _legal(board, "d8h4"))),
            ("parse_san Ra8+", ROOK_FEN, lambda board: parse_san(board, "Ra8+")),
            ("parse_san Qh4#", FOOLS_MATE_FEN, lambda board: parse_san(board, "Qh4#")),
        )  # fmt: skip
        for what, fen, call in cases:
            with self.subTest(what=what):
                board = Board.from_fen(fen)
                squares = list(board.squares)
                key = board.key
                call(board)
                self.assertEqual(board.to_fen(), fen)
                self.assertEqual(board.key, key)
                self.assertEqual(board.squares, squares)


if __name__ == "__main__":
    unittest.main()
