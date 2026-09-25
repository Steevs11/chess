"""Board, make/unmake and the Zobrist key in core/board.py.

Positions come from literal FEN strings and moves are built by hand with their kind, the
way the generator will hand them over: make does not validate (ADR-006, ADR-022).
"""

from __future__ import annotations

import unittest

from chess.core.board import Board, compute_key
from chess.core.fen import STARTING_FEN
from chess.core.types import (
    A1,
    A5,
    A7,
    A8,
    B6,
    B7,
    C1,
    C4,
    C5,
    C7,
    C8,
    D1,
    D2,
    D4,
    D5,
    D6,
    D7,
    D8,
    E1,
    E2,
    E3,
    E4,
    E5,
    E7,
    E8,
    F1,
    F3,
    F6,
    F8,
    G1,
    G8,
    H1,
    H2,
    H7,
    H8,
    CastlingRights,
    Color,
    Move,
    MoveKind,
    Piece,
    PieceType,
)

# PROTOCOL.md section 5, the STATE example: the position after 1.e4.
AFTER_E4_FEN = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
CASTLING_FEN = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"

WHITE_PAWN = Piece(Color.WHITE, PieceType.PAWN)
BLACK_PAWN = Piece(Color.BLACK, PieceType.PAWN)
WHITE_KNIGHT = Piece(Color.WHITE, PieceType.KNIGHT)
WHITE_KING = Piece(Color.WHITE, PieceType.KING)
BLACK_KING = Piece(Color.BLACK, PieceType.KING)
WHITE_ROOK = Piece(Color.WHITE, PieceType.ROOK)
BLACK_ROOK = Piece(Color.BLACK, PieceType.ROOK)


class FenBridgeTest(unittest.TestCase):
    def test_starting_fen_round_trips_through_board(self) -> None:
        self.assertEqual(Board.from_fen(STARTING_FEN).to_fen(), STARTING_FEN)

    def test_piece_at_reads_the_square(self) -> None:
        board = Board.from_fen(STARTING_FEN)
        self.assertEqual(board.piece_at(E1), WHITE_KING)
        self.assertEqual(board.piece_at(D7), BLACK_PAWN)
        self.assertIsNone(board.piece_at(E4))


class QuietAndDoublePushTest(unittest.TestCase):
    def test_knight_move_updates_squares_turn_and_counters(self) -> None:
        board = Board.from_fen(STARTING_FEN)
        board.make(Move(G1, F3))
        self.assertIsNone(board.piece_at(G1))
        self.assertEqual(board.piece_at(F3), WHITE_KNIGHT)
        self.assertIs(board.turn, Color.BLACK)
        self.assertEqual(board.halfmove_clock, 1)
        self.assertEqual(board.fullmove_number, 1)
        self.assertIsNone(board.ep_square)

    def test_double_push_gives_protocol_example_fen(self) -> None:
        board = Board.from_fen(STARTING_FEN)
        board.make(Move(E2, E4, MoveKind.DOUBLE_PAWN_PUSH))
        self.assertEqual(board.to_fen(), AFTER_E4_FEN)
        self.assertEqual(board.ep_square, E3)
        self.assertEqual(board.halfmove_clock, 0)


class CaptureTest(unittest.TestCase):
    def test_capture_records_piece_and_square_and_resets_halfmove(self) -> None:
        board = Board.from_fen("4k3/8/8/3p4/4P3/8/8/4K3 w - - 5 10")
        undo = board.make(Move(E4, D5, MoveKind.CAPTURE))
        self.assertEqual(undo.captured, BLACK_PAWN)
        self.assertEqual(undo.captured_sq, D5)
        self.assertEqual(board.piece_at(D5), WHITE_PAWN)
        self.assertEqual(board.halfmove_clock, 0)

    def test_en_passant_removes_pawn_behind_target_square(self) -> None:
        board = Board.from_fen("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2")
        undo = board.make(Move(E5, D6, MoveKind.EN_PASSANT))
        self.assertIsNone(board.piece_at(D5))
        self.assertIsNone(board.piece_at(E5))
        self.assertEqual(board.piece_at(D6), WHITE_PAWN)
        self.assertEqual(undo.captured, BLACK_PAWN)
        self.assertEqual(undo.captured_sq, D5)


class CastleTest(unittest.TestCase):
    # (turn, king to, rook from, rook to, rights left)
    CASES = (
        ("w", G1, H1, F1, CastlingRights(False, False, True, True)),
        ("w", C1, A1, D1, CastlingRights(False, False, True, True)),
        ("b", G8, H8, F8, CastlingRights(True, True, False, False)),
        ("b", C8, A8, D8, CastlingRights(True, True, False, False)),
    )

    def test_castle_moves_king_and_rook_and_drops_both_rights_of_that_color(self) -> None:
        for turn, king_to, rook_from, rook_to, rights in self.CASES:
            with self.subTest(turn=turn, king_to=king_to):
                board = Board.from_fen(f"r3k2r/8/8/8/8/8/8/R3K2R {turn} KQkq - 0 1")
                king_from = E1 if turn == "w" else E8
                king = board.piece_at(king_from)
                rook = board.piece_at(rook_from)
                board.make(Move(king_from, king_to, MoveKind.CASTLE))
                self.assertEqual(board.piece_at(king_to), king)
                self.assertEqual(board.piece_at(rook_to), rook)
                self.assertIsNone(board.piece_at(king_from))
                self.assertIsNone(board.piece_at(rook_from))
                self.assertEqual(board.castling, rights)


class PromotionTest(unittest.TestCase):
    def test_each_promotion_piece_replaces_the_pawn(self) -> None:
        for kind in (PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT):
            with self.subTest(kind=kind):
                board = Board.from_fen("k7/4P3/8/8/8/8/8/4K3 w - - 0 1")
                undo = board.make(Move(E7, E8, MoveKind.PROMOTION, kind))
                self.assertIsNone(board.piece_at(E7))
                self.assertEqual(board.piece_at(E8), Piece(Color.WHITE, kind))
                self.assertIsNone(undo.captured)
                self.assertIsNone(undo.captured_sq)

    def test_promotion_capturing_rook_records_it_and_drops_black_long_right(self) -> None:
        board = Board.from_fen("r3k3/1P6/8/8/8/8/8/4K3 w q - 0 1")
        undo = board.make(Move(B7, A8, MoveKind.PROMOTION, PieceType.QUEEN))
        self.assertEqual(undo.captured, BLACK_ROOK)
        self.assertEqual(undo.captured_sq, A8)
        self.assertEqual(board.piece_at(A8), Piece(Color.WHITE, PieceType.QUEEN))
        self.assertFalse(board.castling.black_queenside)


class CastlingRightsUpdateTest(unittest.TestCase):
    def test_king_leaving_e1_drops_both_white_rights(self) -> None:
        board = Board.from_fen(CASTLING_FEN)
        board.make(Move(E1, E2))
        self.assertEqual(board.castling, CastlingRights(False, False, True, True))

    def test_rook_leaving_h1_drops_only_white_short_right(self) -> None:
        board = Board.from_fen(CASTLING_FEN)
        board.make(Move(H1, H2))
        self.assertEqual(board.castling, CastlingRights(False, True, True, True))

    def test_capture_of_rook_on_a8_drops_black_long_right(self) -> None:
        board = Board.from_fen("r3k2r/8/1N6/8/8/8/8/R3K2R w KQkq - 0 1")
        board.make(Move(B6, A8, MoveKind.CAPTURE))
        self.assertEqual(board.castling, CastlingRights(True, True, True, False))

    def test_move_away_from_the_six_squares_keeps_the_same_rights_object(self) -> None:
        board = Board.from_fen("r3k2r/8/1N6/8/8/8/8/R3K2R w KQkq - 0 1")
        before = board.castling
        board.make(Move(B6, C4))
        self.assertIs(board.castling, before)


class CounterTest(unittest.TestCase):
    FEN = "4k3/8/8/3p4/4P3/8/8/4K1N1 w - - 7 12"

    def test_halfmove_counts_up_on_quiet_piece_move(self) -> None:
        board = Board.from_fen(self.FEN)
        board.make(Move(G1, F3))
        self.assertEqual(board.halfmove_clock, 8)

    def test_halfmove_resets_on_pawn_move(self) -> None:
        board = Board.from_fen(self.FEN)
        board.make(Move(E4, E5))
        self.assertEqual(board.halfmove_clock, 0)

    def test_halfmove_resets_on_capture(self) -> None:
        board = Board.from_fen(self.FEN)
        board.make(Move(E4, D5, MoveKind.CAPTURE))
        self.assertEqual(board.halfmove_clock, 0)

    def test_fullmove_stays_after_white_and_grows_after_black(self) -> None:
        board = Board.from_fen(self.FEN)
        board.make(Move(G1, F3))
        self.assertEqual(board.fullmove_number, 12)
        board.make(Move(E8, E7))
        self.assertEqual(board.fullmove_number, 13)


class UnmakeTest(unittest.TestCase):
    # (what, FEN, move) - one move of every kind, and a black move for the fullmove count.
    CASES = (
        ("normal", STARTING_FEN, Move(G1, F3)),
        ("normal by black", "4k3/8/8/8/8/8/8/4K3 b - - 3 9", Move(E8, D7)),
        ("capture", "4k3/8/8/3p4/4P3/8/8/4K3 w - - 5 10", Move(E4, D5, MoveKind.CAPTURE)),
        ("double push", STARTING_FEN, Move(E2, E4, MoveKind.DOUBLE_PAWN_PUSH)),
        ("en passant", "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2", Move(E5, D6, MoveKind.EN_PASSANT)),
        ("white castle", CASTLING_FEN, Move(E1, G1, MoveKind.CASTLE)),
        ("black castle", "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1", Move(E8, C8, MoveKind.CASTLE)),
        (
            "promotion",
            "k7/4P3/8/8/8/8/8/4K3 w - - 0 1",
            Move(E7, E8, MoveKind.PROMOTION, PieceType.KNIGHT),
        ),
        (
            "promotion capture",
            "r3k3/1P6/8/8/8/8/8/4K3 w q - 0 1",
            Move(B7, A8, MoveKind.PROMOTION, PieceType.QUEEN),
        ),
    )

    def test_unmake_restores_fen_key_and_squares(self) -> None:
        for what, fen, move in self.CASES:
            with self.subTest(what=what):
                board = Board.from_fen(fen)
                squares = list(board.squares)
                key = board.key
                undo = board.make(move)
                board.unmake(move, undo)
                self.assertEqual(board.to_fen(), fen)
                self.assertEqual(board.key, key)
                self.assertEqual(board.squares, squares)


class ZobristTest(unittest.TestCase):
    def test_key_matches_compute_key_after_from_fen(self) -> None:
        board = Board.from_fen(STARTING_FEN)
        self.assertEqual(board.key, compute_key(board))

    def test_incremental_key_matches_full_computation_through_make_and_unmake(self) -> None:
        board = Board.from_fen("r3k2r/1P1p4/8/4P3/8/8/8/R3K2R b KQkq - 0 1")
        moves = (
            Move(D7, D5, MoveKind.DOUBLE_PAWN_PUSH),  # ep d6 enters the key: pawn on e5
            Move(E5, D6, MoveKind.EN_PASSANT),
            Move(E8, G8, MoveKind.CASTLE),
            Move(B7, A8, MoveKind.PROMOTION, PieceType.QUEEN),
            Move(G8, H7),
            Move(E1, C1, MoveKind.CASTLE),
            Move(F8, A8, MoveKind.CAPTURE),
        )
        undos = []
        for move in moves:
            undos.append(board.make(move))
            with self.subTest(after_make=move.to_uci()):
                self.assertEqual(board.key, compute_key(board))
        for move, undo in zip(reversed(moves), reversed(undos), strict=True):
            board.unmake(move, undo)
            with self.subTest(after_unmake=move.to_uci()):
                self.assertEqual(board.key, compute_key(board))

    def test_counters_do_not_enter_the_key(self) -> None:
        board = Board.from_fen(STARTING_FEN)
        start = board.key
        for move in (Move(G1, F3), Move(G8, F6), Move(F3, G1), Move(F6, G8)):
            board.make(move)
        self.assertEqual(board.fullmove_number, 3)
        self.assertEqual(board.key, start)

    def test_starting_position_and_after_e4_have_different_keys(self) -> None:
        board = Board.from_fen(STARTING_FEN)
        start = board.key
        board.make(Move(E2, E4, MoveKind.DOUBLE_PAWN_PUSH))
        self.assertNotEqual(board.key, start)


class EnPassantKeyTest(unittest.TestCase):
    """ADR-027: the ep square counts only when a pawn of the side to move stands beside."""

    def assert_ep_in_key(self, fen: str, move: Move, fen_without_ep: str, expected: bool) -> None:
        board = Board.from_fen(fen)
        board.make(move)
        self.assertEqual(board.key, compute_key(board))
        without = Board.from_fen(fen_without_ep).key
        if expected:
            self.assertNotEqual(board.key, without)
        else:
            self.assertEqual(board.key, without)

    def test_e4_from_start_leaves_ep_out_of_key(self) -> None:
        self.assert_ep_in_key(
            STARTING_FEN,
            Move(E2, E4, MoveKind.DOUBLE_PAWN_PUSH),
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
            expected=False,
        )

    def test_black_double_push_beside_white_pawn_puts_ep_in_key(self) -> None:
        self.assert_ep_in_key(
            "4k3/2p5/8/3P4/8/8/8/4K3 b - - 0 1",
            Move(C7, C5, MoveKind.DOUBLE_PAWN_PUSH),
            "4k3/8/8/2pP4/8/8/8/4K3 w - - 0 2",
            expected=True,
        )

    def test_white_double_push_beside_black_pawn_puts_ep_in_key(self) -> None:
        self.assert_ep_in_key(
            "4k3/8/8/8/4p3/8/3P4/4K3 w - - 0 1",
            Move(D2, D4, MoveKind.DOUBLE_PAWN_PUSH),
            "4k3/8/8/8/3Pp3/8/8/4K3 b - - 0 1",
            expected=True,
        )

    def test_pawn_across_the_board_edge_does_not_count_as_neighbour(self) -> None:
        # a5 - 1 is h4 as an index; a pawn there is not beside a5.
        self.assert_ep_in_key(
            "4k3/p7/8/8/7P/8/8/4K3 b - - 0 1",
            Move(A7, A5, MoveKind.DOUBLE_PAWN_PUSH),
            "4k3/8/8/p7/7P/8/8/4K3 w - - 0 2",
            expected=False,
        )


if __name__ == "__main__":
    unittest.main()
