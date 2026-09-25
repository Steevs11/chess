"""FEN parsing and formatting in core/fen.py.

Expected pieces and squares are written out literally, never derived from the letter
helpers in fen.py: a test that borrows the mapping from the module under test agrees with
any mistake that module makes.
"""

from __future__ import annotations

import dataclasses
import unittest

from chess.core.fen import STARTING_FEN, Position, format_fen, parse_fen
from chess.core.types import (
    A8,
    CASTLING_ALL,
    CASTLING_NONE,
    D7,
    E1,
    E3,
    E4,
    F6,
    CastlingRights,
    Color,
    InvalidFenError,
    Piece,
    PieceType,
)

# PROTOCOL.md section 5, the STATE example: the position after 1.e4.
AFTER_E4_FEN = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"


class StartingPositionTest(unittest.TestCase):
    def test_starting_fen_parses_to_the_initial_position(self) -> None:
        position = parse_fen(STARTING_FEN)
        self.assertEqual(position.placement[E1], Piece(Color.WHITE, PieceType.KING))
        self.assertEqual(position.placement[A8], Piece(Color.BLACK, PieceType.ROOK))
        self.assertEqual(position.placement[D7], Piece(Color.BLACK, PieceType.PAWN))
        self.assertIsNone(position.placement[E4])
        self.assertEqual(len(position.placement), 64)
        self.assertIs(position.turn, Color.WHITE)
        self.assertEqual(position.castling, CASTLING_ALL)
        self.assertIsNone(position.ep_square)
        self.assertEqual(position.halfmove_clock, 0)
        self.assertEqual(position.fullmove_number, 1)

    def test_position_is_frozen(self) -> None:
        position = parse_fen(STARTING_FEN)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            position.turn = Color.BLACK  # type: ignore[misc]


class RoundTripTest(unittest.TestCase):
    FENS = (
        STARTING_FEN,
        AFTER_E4_FEN,
        # White to move, black has just played f7f5: ep target on the sixth rank.
        "rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3",
        # Partial rights: white short, black long.
        "r3k3/8/8/8/8/8/8/4K2R w Kq - 0 1",
        # No rights, empty ranks, counters away from their defaults.
        "4k3/8/8/8/8/8/8/4K3 b - - 17 42",
    )

    def test_format_fen_returns_the_parsed_text(self) -> None:
        for fen in self.FENS:
            with self.subTest(fen=fen):
                self.assertEqual(format_fen(parse_fen(fen)), fen)

    def test_protocol_example_has_ep_square_e3(self) -> None:
        self.assertEqual(parse_fen(AFTER_E4_FEN).ep_square, E3)

    def test_ep_square_on_sixth_rank_is_read_with_white_to_move(self) -> None:
        self.assertEqual(parse_fen(self.FENS[2]).ep_square, F6)

    def test_partial_rights_are_read_field_by_field(self) -> None:
        position = parse_fen(self.FENS[3])
        self.assertEqual(position.castling, CastlingRights(True, False, False, True))

    def test_no_rights_read_as_castling_none(self) -> None:
        self.assertEqual(parse_fen(self.FENS[4]).castling, CASTLING_NONE)


class FourFieldTest(unittest.TestCase):
    """CPW writes Kiwipete without counters; four fields mean 0 and 1."""

    FOUR_FIELDS = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -"

    def test_four_fields_parse_like_starting_fen(self) -> None:
        self.assertEqual(parse_fen(self.FOUR_FIELDS), parse_fen(STARTING_FEN))

    def test_four_fields_are_formatted_as_six(self) -> None:
        self.assertEqual(format_fen(parse_fen(self.FOUR_FIELDS)), STARTING_FEN)


class RejectionTest(unittest.TestCase):
    # (what is wrong, FEN)
    BAD = (
        ("3 fields", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq"),
        ("5 fields", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0"),
        ("7 ranks", "rnbqkbnr/pppppppp/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        ("9 ranks", "rnbqkbnr/pppppppp/8/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        ("rank sums to 7", "rnbqkbnr/pppppppp/8/8/7/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        ("rank sums to 9", "rnbqkbnr/pppppppp/8/8/4P4/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        ("letter x", "rnbqkbnr/pppppppp/8/8/4x3/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        ("turn x", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR x KQkq - 0 1"),
        ("turn W", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR W KQkq - 0 1"),
        ("castling qK", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w qK - 0 1"),
        ("castling KK", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KK - 0 1"),
        ("castling KQx", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQx - 0 1"),
        ("ep e4 with w", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq e4 0 1"),
        ("ep e6 with b", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq e6 0 1"),
        ("ep z9", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq z9 0 1"),
        ("halfmove -1", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - -1 1"),
        ("halfmove a", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - a 1"),
        ("fullmove 0", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 0"),
        ("two white kings", "4k3/8/8/8/8/8/8/3KK3 w - - 0 1"),
        ("no black king", "8/8/8/8/8/8/8/4K3 w - - 0 1"),
        ("white pawn on rank 8", "P3k3/8/8/8/8/8/8/4K3 w - - 0 1"),
        ("black pawn on rank 1", "4k3/8/8/8/8/8/8/p3K3 w - - 0 1"),
        ("K without king on e1", "4k3/8/8/8/8/8/8/3K3R w K - 0 1"),
        ("K without rook on h1", "4k3/8/8/8/8/8/8/4K3 w K - 0 1"),
        ("q without rook on a8", "4k3/8/8/8/8/8/8/4K3 w q - 0 1"),
    )

    def test_malformed_or_impossible_fen_raises_invalid_fen_error(self) -> None:
        for reason, fen in self.BAD:
            with self.subTest(reason=reason), self.assertRaises(InvalidFenError):
                parse_fen(fen)

    def test_error_message_names_the_bad_value(self) -> None:
        with self.assertRaises(InvalidFenError) as caught:
            parse_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR x KQkq - 0 1")
        self.assertIn("'x'", str(caught.exception))


class PositionShapeTest(unittest.TestCase):
    def test_placement_is_a_tuple(self) -> None:
        self.assertIsInstance(parse_fen(STARTING_FEN).placement, tuple)

    def test_equal_fens_give_equal_positions(self) -> None:
        self.assertEqual(parse_fen(STARTING_FEN), parse_fen(STARTING_FEN))
        self.assertIsInstance(parse_fen(STARTING_FEN), Position)


if __name__ == "__main__":
    unittest.main()
