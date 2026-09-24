"""Squares, pieces, moves, castling rights and the error hierarchy of core/types.py.

Expected square names are built here from literal strings, never from FILE_NAMES or
RANK_NAMES: a test that derives its expectations from the module under test agrees with
any mistake that module makes.
"""

from __future__ import annotations

import dataclasses
import itertools
import unittest

import chess.core.types as types
from chess.core.types import (
    A1,
    A8,
    CASTLING_ALL,
    CASTLING_NONE,
    D5,
    E1,
    E2,
    E4,
    E7,
    E8,
    G1,
    H1,
    H8,
    CastlingRights,
    ChessError,
    Color,
    IllegalMoveError,
    InvalidFenError,
    InvalidSanError,
    Move,
    MoveKind,
    Piece,
    PieceType,
    file_of,
    from_algebraic,
    rank_of,
    square,
    to_algebraic,
)

# Every square name in index order: a1, b1, ..., h1, a2, ..., h8.
ALL_NAMES = tuple(f + r for r in "12345678" for f in "abcdefgh")


class SquareTest(unittest.TestCase):
    def test_corner_and_center_constants_have_their_indices(self) -> None:
        for constant, expected in ((A1, 0), (H1, 7), (A8, 56), (H8, 63), (E4, 28)):
            with self.subTest(expected=expected):
                self.assertEqual(constant, expected)

    def test_every_constant_is_the_square_its_name_says(self) -> None:
        for name in ALL_NAMES:
            with self.subTest(name=name):
                self.assertEqual(getattr(types, name.upper()), from_algebraic(name))

    def test_file_rank_and_square_agree_on_the_same_table(self) -> None:
        # (square, file, rank)
        table = ((A1, 0, 0), (H1, 7, 0), (A8, 0, 7), (H8, 7, 7), (E4, 4, 3), (D5, 3, 4))
        for sq, file, rank in table:
            with self.subTest(sq=sq):
                self.assertEqual(file_of(sq), file)
                self.assertEqual(rank_of(sq), rank)
                self.assertEqual(square(file, rank), sq)

    def test_algebraic_round_trip_holds_for_all_64_squares(self) -> None:
        for index, name in enumerate(ALL_NAMES):
            with self.subTest(name=name):
                self.assertEqual(from_algebraic(name), index)
                self.assertEqual(to_algebraic(from_algebraic(name)), name)

    def test_from_algebraic_rejects_malformed_text(self) -> None:
        for text in ("", "e", "e9", "i1", "E4", "e44"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                from_algebraic(text)

    def test_to_algebraic_rejects_index_outside_the_board(self) -> None:
        for sq in (-1, 64):
            with self.subTest(sq=sq), self.assertRaises(ValueError):
                to_algebraic(sq)


class ColorTest(unittest.TestCase):
    def test_opposite_swaps_both_ways(self) -> None:
        self.assertIs(Color.WHITE.opposite, Color.BLACK)
        self.assertIs(Color.BLACK.opposite, Color.WHITE)

    def test_values_are_zero_and_one_for_indexing(self) -> None:
        self.assertEqual(Color.WHITE.value, 0)
        self.assertEqual(Color.BLACK.value, 1)


class PieceTypeTest(unittest.TestCase):
    LETTERS = (
        (PieceType.PAWN, "p"),
        (PieceType.KNIGHT, "n"),
        (PieceType.BISHOP, "b"),
        (PieceType.ROOK, "r"),
        (PieceType.QUEEN, "q"),
        (PieceType.KING, "k"),
    )

    def test_letter_round_trip_holds_for_all_six(self) -> None:
        for kind, letter in self.LETTERS:
            with self.subTest(kind=kind):
                self.assertEqual(kind.letter, letter)
                self.assertIs(PieceType.from_letter(letter), kind)

    def test_from_letter_rejects_unknown_and_uppercase_letters(self) -> None:
        for letter in ("x", "Q", "", "qq"):
            with self.subTest(letter=letter), self.assertRaises(ValueError):
                PieceType.from_letter(letter)


class PieceTest(unittest.TestCase):
    def test_equal_pieces_are_equal_and_frozen(self) -> None:
        piece = Piece(Color.WHITE, PieceType.QUEEN)
        self.assertEqual(piece, Piece(Color.WHITE, PieceType.QUEEN))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            piece.color = Color.BLACK  # type: ignore[misc]


class MoveUciTest(unittest.TestCase):
    def test_uci_round_trip_holds(self) -> None:
        for text in ("e2e4", "e7e8q", "a7a8n", "e1g1"):
            with self.subTest(text=text):
                self.assertEqual(Move.from_uci(text).to_uci(), text)

    def test_from_uci_reads_squares(self) -> None:
        move = Move.from_uci("e1g1")
        self.assertEqual((move.from_sq, move.to_sq), (E1, G1))

    def test_from_uci_with_letter_is_a_promotion(self) -> None:
        move = Move.from_uci("e7e8q")
        self.assertEqual((move.from_sq, move.to_sq), (E7, E8))
        self.assertIs(move.promotion, PieceType.QUEEN)
        self.assertIs(move.kind, MoveKind.PROMOTION)

    def test_from_uci_without_letter_is_normal(self) -> None:
        move = Move.from_uci("e2e4")
        self.assertIsNone(move.promotion)
        self.assertIs(move.kind, MoveKind.NORMAL)

    def test_from_uci_rejects_malformed_text(self) -> None:
        for text in ("", "e2", "e2e4e", "e9e4", "e7e8k", "e7e8p", "E2E4"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                Move.from_uci(text)


class MoveIdentityTest(unittest.TestCase):
    def test_equality_and_hash_ignore_kind(self) -> None:
        generated = Move(E4, D5, MoveKind.CAPTURE)
        wire = Move(E4, D5)
        self.assertEqual(generated, wire)
        self.assertEqual(hash(generated), hash(wire))

    def test_equality_and_hash_distinguish_promotion(self) -> None:
        queen = Move.from_uci("e7e8q")
        knight = Move.from_uci("e7e8n")
        self.assertNotEqual(queen, knight)
        self.assertEqual(len({queen, knight}), 2)

    def test_wire_move_found_in_legal_list_yields_generated_kind(self) -> None:
        legal = [Move(E2, E4, MoveKind.DOUBLE_PAWN_PUSH), Move(E4, D5, MoveKind.CAPTURE)]
        wire = Move.from_uci("e4d5")
        self.assertIs(legal[legal.index(wire)].kind, MoveKind.CAPTURE)

    def test_move_is_frozen(self) -> None:
        move = Move(E2, E4)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            move.to_sq = E1  # type: ignore[misc]


class MoveInvariantTest(unittest.TestCase):
    def test_promotion_without_promotion_kind_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Move(E7, E8, MoveKind.NORMAL, PieceType.QUEEN)

    def test_promotion_kind_without_promotion_piece_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Move(E7, E8, MoveKind.PROMOTION)

    def test_promotion_to_king_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Move(E7, E8, MoveKind.PROMOTION, PieceType.KING)

    def test_all_four_promotion_pieces_are_accepted(self) -> None:
        for kind in (PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT):
            with self.subTest(kind=kind):
                self.assertIs(Move(E7, E8, MoveKind.PROMOTION, kind).promotion, kind)


class CastlingRightsTest(unittest.TestCase):
    def test_all_16_combinations_give_distinct_indices_by_bit_formula(self) -> None:
        seen = set()
        for wk, wq, bk, bq in itertools.product((False, True), repeat=4):
            rights = CastlingRights(
                white_kingside=wk, white_queenside=wq, black_kingside=bk, black_queenside=bq
            )
            expected = wk * 1 + wq * 2 + bk * 4 + bq * 8
            with self.subTest(rights=rights):
                self.assertEqual(rights.to_index(), expected)
            seen.add(rights.to_index())
        self.assertEqual(seen, set(range(16)))

    def test_constants_are_all_and_none(self) -> None:
        self.assertEqual(CASTLING_ALL.to_index(), 15)
        self.assertEqual(CASTLING_NONE.to_index(), 0)

    def test_replace_drops_one_right(self) -> None:
        rights = dataclasses.replace(CASTLING_ALL, white_kingside=False)
        self.assertEqual(rights.to_index(), 14)
        self.assertEqual(CASTLING_ALL.to_index(), 15)

    def test_castling_rights_are_frozen(self) -> None:
        with self.assertRaises(dataclasses.FrozenInstanceError):
            CASTLING_ALL.white_kingside = False  # type: ignore[misc]


class ErrorHierarchyTest(unittest.TestCase):
    ERRORS = (IllegalMoveError, InvalidFenError, InvalidSanError)

    def test_every_core_error_is_a_chess_error(self) -> None:
        for error in self.ERRORS:
            with self.subTest(error=error.__name__):
                self.assertTrue(issubclass(error, ChessError))

    def test_except_chess_error_catches_every_core_error(self) -> None:
        for error in self.ERRORS:
            with self.subTest(error=error.__name__):
                try:
                    raise error("boom")
                except ChessError as caught:
                    self.assertIsInstance(caught, error)


if __name__ == "__main__":
    unittest.main()
