"""Pseudo-legal move generation in core/movegen.py.

Every FEN is built by hand with both kings, and every expectation is worked out on the
board. Move equality ignores `kind` (ADR-022), so moves are compared as (uci, kind) pairs.
Most tests look only at the moves of one square, so the kings do not get in the way.
"""

from __future__ import annotations

import unittest

from chess.core.board import Board
from chess.core.fen import STARTING_FEN
from chess.core.movegen import pseudo_legal_moves
from chess.core.types import (
    PROMOTION_PIECES,
    MoveKind,
    PieceType,
    from_algebraic,
    rank_of,
)

NORMAL = MoveKind.NORMAL
CAPTURE = MoveKind.CAPTURE
DOUBLE = MoveKind.DOUBLE_PAWN_PUSH
PROMOTION = MoveKind.PROMOTION
EN_PASSANT = MoveKind.EN_PASSANT
CASTLE = MoveKind.CASTLE

# PROTOCOL.md section 5, the STATE example: the position after 1.e4.
AFTER_E4_FEN = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
KIWIPETE_FEN = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
# Kings and rooks at home, nothing else: both sides may castle both ways.
CASTLING_FEN = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
# After 1.e4 a6 2.e5 d5: the e5 pawn may take the d5 pawn en passant.
AFTER_D5_EP_FEN = "rnbqkbnr/1pp1pppp/p7/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3"


def all_moves(fen: str) -> list[tuple[str, MoveKind]]:
    """Every generated move of `fen` as (uci, kind), in generator order."""
    return [(move.to_uci(), move.kind) for move in pseudo_legal_moves(Board.from_fen(fen))]


def moves_from(fen: str, name: str) -> list[tuple[str, MoveKind]]:
    """The generated moves of `fen` that start on the square called `name`, in order."""
    return [pair for pair in all_moves(fen) if pair[0][:2] == name]


def promotions(from_to: str) -> list[tuple[str, MoveKind]]:
    """The four promotions of `from_to`, e.g. "e7e8", in PROMOTION_PIECES order."""
    return [(from_to + kind.letter, PROMOTION) for kind in PROMOTION_PIECES]


def castles(fen: str) -> list[tuple[str, MoveKind]]:
    """The generated CASTLE moves of `fen`, in generator order."""
    return [pair for pair in all_moves(fen) if pair[1] is CASTLE]


class StartingPositionTest(unittest.TestCase):
    def test_start_has_twenty_moves_split_by_kind_and_no_capture(self) -> None:
        board = Board.from_fen(STARTING_FEN)
        moves = pseudo_legal_moves(board)
        self.assertEqual(len(moves), 20)
        pawn = [m for m in moves if board.piece_at(m.from_sq).kind is PieceType.PAWN]
        knight = [m for m in moves if board.piece_at(m.from_sq).kind is PieceType.KNIGHT]
        self.assertEqual(sum(m.kind is NORMAL for m in pawn), 8)
        self.assertEqual(sum(m.kind is DOUBLE for m in pawn), 8)
        self.assertEqual(len(knight), 4)
        self.assertTrue(all(m.kind is NORMAL for m in knight))
        self.assertFalse(any(m.kind is CAPTURE for m in moves))

    def test_black_after_e4_has_twenty_moves_and_pawns_go_down(self) -> None:
        board = Board.from_fen(AFTER_E4_FEN)
        moves = pseudo_legal_moves(board)
        self.assertEqual(len(moves), 20)
        pairs = [(m.to_uci(), m.kind) for m in moves]
        self.assertIn(("e7e6", NORMAL), pairs)
        self.assertIn(("e7e5", DOUBLE), pairs)
        for move in moves:
            if board.piece_at(move.from_sq).kind is PieceType.PAWN:
                with self.subTest(move=move.to_uci()):
                    self.assertLess(move.to_sq, move.from_sq)


class KnightTest(unittest.TestCase):
    def test_knight_moves_by_position(self) -> None:
        cases = (
            ("corner", "4k3/8/8/8/8/8/8/N3K3 w - - 0 1", {("a1b3", NORMAL), ("a1c2", NORMAL)}),
            ("blocked by own pieces", "4k3/8/8/8/8/1P6/2P5/N3K3 w - - 0 1", set()),
            (
                "foreign piece",
                "4k3/8/8/8/8/1p6/8/N3K3 w - - 0 1",
                {("a1b3", CAPTURE), ("a1c2", NORMAL)},
            ),
        )
        for what, fen, expected in cases:
            with self.subTest(what=what):
                moves = moves_from(fen, "a1")
                self.assertEqual(len(moves), len(expected))
                self.assertEqual(set(moves), expected)


class SliderTest(unittest.TestCase):
    def test_slider_stops_before_own_and_on_foreign_piece(self) -> None:
        cases = (
            (
                # f4 black pawn, b2 white pawn: nothing past f4, nothing through b2.
                "bishop",
                "4k3/8/8/8/5p2/8/1P6/2B1K3 w - - 0 1",
                "c1",
                {("c1d2", NORMAL), ("c1e3", NORMAL), ("c1f4", CAPTURE)},
            ),
            (
                # a4 white pawn, d1 black knight: nothing past d1.
                "rook",
                "4k3/8/8/8/P7/8/8/R2n1K2 w - - 0 1",
                "a1",
                {
                    ("a1a2", NORMAL),
                    ("a1a3", NORMAL),
                    ("a1b1", NORMAL),
                    ("a1c1", NORMAL),
                    ("a1d1", CAPTURE),
                },
            ),
            (
                # a3 white pawn, c1 black knight, b2 black pawn: straight and diagonal.
                "queen",
                "4k3/8/8/8/8/P7/1p6/Q1n1K3 w - - 0 1",
                "a1",
                {("a1a2", NORMAL), ("a1b1", NORMAL), ("a1c1", CAPTURE), ("a1b2", CAPTURE)},
            ),
        )
        for what, fen, square, expected in cases:
            with self.subTest(what=what):
                moves = moves_from(fen, square)
                self.assertEqual(len(moves), len(expected))
                self.assertEqual(set(moves), expected)

    def test_lone_rook_on_empty_board_has_fourteen_quiet_moves(self) -> None:
        moves = moves_from("k7/8/8/8/3R4/8/8/7K w - - 0 1", "d4")
        self.assertEqual(len(moves), 14)
        self.assertTrue(all(kind is NORMAL for _, kind in moves))


class PawnTest(unittest.TestCase):
    def test_pawn_moves_by_position(self) -> None:
        cases = (
            ("push blocked by foreign piece", "4k3/8/8/8/8/4n3/4P3/4K3 w - - 0 1", "e2", set()),
            ("push blocked by own piece", "4k3/8/8/8/8/4N3/4P3/4K3 w - - 0 1", "e2", set()),
            (
                "second square blocked, one step only",
                "4k3/8/8/8/4n3/8/4P3/4K3 w - - 0 1",
                "e2",
                {("e2e3", NORMAL)},
            ),
            (
                "open start rank, both pushes",
                "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1",
                "e2",
                {("e2e3", NORMAL), ("e2e4", DOUBLE)},
            ),
            (
                "not on start rank, no double push",
                "4k3/8/8/8/8/4P3/8/4K3 w - - 0 1",
                "e3",
                {("e3e4", NORMAL)},
            ),
            (
                "captures diagonally only, never straight",
                "4k3/8/8/3ppp2/4P3/8/8/4K3 w - - 0 1",
                "e4",
                {("e4d5", CAPTURE), ("e4f5", CAPTURE)},
            ),
            (
                "never captures own piece",
                "4k3/8/8/3P1P2/4P3/8/8/4K3 w - - 0 1",
                "e4",
                {("e4e5", NORMAL)},
            ),
            (
                # h4 is a4 + 7 as an index; the pawn must not reach across the edge.
                "a-file captures one way",
                "4k3/8/8/1p6/P6p/8/8/4K3 w - - 0 1",
                "a4",
                {("a4a5", NORMAL), ("a4b5", CAPTURE)},
            ),
            (
                # a6 is h4 + 9 as an index.
                "h-file captures one way",
                "4k3/8/p7/6p1/7P/8/8/4K3 w - - 0 1",
                "h4",
                {("h4h5", NORMAL), ("h4g5", CAPTURE)},
            ),
            (
                "black push blocked on second square",
                "4k3/3p4/8/3N4/8/8/8/4K3 b - - 0 1",
                "d7",
                {("d7d6", NORMAL)},
            ),
        )
        for what, fen, square, expected in cases:
            with self.subTest(what=what):
                moves = moves_from(fen, square)
                self.assertEqual(len(moves), len(expected))
                self.assertEqual(set(moves), expected)


class PromotionTest(unittest.TestCase):
    FENS = (
        "k7/4P3/8/8/8/8/8/4K3 w - - 0 1",
        "k2r4/4P3/8/8/8/8/8/4K3 w - - 0 1",
        "k3r3/4P3/8/8/8/8/8/4K3 w - - 0 1",
        "4k3/8/8/8/8/8/p7/4K3 b - - 0 1",
        "4k3/8/8/8/8/8/1p6/R3K3 b - - 0 1",
    )

    def test_push_to_last_rank_gives_four_promotions_in_order(self) -> None:
        moves = moves_from("k7/4P3/8/8/8/8/8/4K3 w - - 0 1", "e7")
        self.assertEqual(moves, promotions("e7e8"))

    def test_capture_to_last_rank_adds_four_capture_promotions(self) -> None:
        moves = moves_from("k2r4/4P3/8/8/8/8/8/4K3 w - - 0 1", "e7")
        self.assertEqual(moves, promotions("e7e8") + promotions("e7d8"))

    def test_piece_on_promotion_square_blocks_the_push(self) -> None:
        self.assertEqual(moves_from("k3r3/4P3/8/8/8/8/8/4K3 w - - 0 1", "e7"), [])

    def test_black_pawn_on_a2_promotes_on_a1(self) -> None:
        moves = moves_from("4k3/8/8/8/8/8/p7/4K3 b - - 0 1", "a2")
        self.assertEqual(moves, promotions("a2a1"))

    def test_promotion_carries_the_piece_in_promotion_pieces_order(self) -> None:
        board = Board.from_fen("k7/4P3/8/8/8/8/8/4K3 w - - 0 1")
        e7 = from_algebraic("e7")
        moves = [m for m in pseudo_legal_moves(board) if m.from_sq == e7]
        self.assertEqual(tuple(m.promotion for m in moves), PROMOTION_PIECES)

    def test_pawn_never_reaches_last_rank_without_promotion(self) -> None:
        for fen in self.FENS:
            board = Board.from_fen(fen)
            for move in pseudo_legal_moves(board):
                piece = board.piece_at(move.from_sq)
                if piece.kind is PieceType.PAWN and rank_of(move.to_sq) in (0, 7):
                    with self.subTest(fen=fen, move=move.to_uci()):
                        self.assertIs(move.kind, PROMOTION)


class KingTest(unittest.TestCase):
    def test_king_in_the_open_has_eight_quiet_moves(self) -> None:
        moves = moves_from("4k3/8/8/8/4K3/8/8/8 w - - 0 1", "e4")
        self.assertEqual(len(moves), 8)
        self.assertTrue(all(kind is NORMAL for _, kind in moves))

    def test_king_surrounded_by_own_pieces_has_no_move(self) -> None:
        self.assertEqual(moves_from("4k3/8/8/8/8/8/PPP5/NKN5 w - - 0 1", "b1"), [])


class CastlingTest(unittest.TestCase):
    def test_white_with_all_rights_castles_kingside_then_queenside_after_king_steps(self) -> None:
        self.assertEqual(len(all_moves(CASTLING_FEN)), 26)
        self.assertEqual(
            moves_from(CASTLING_FEN, "e1"),
            [
                ("e1e2", NORMAL),
                ("e1f1", NORMAL),
                ("e1d1", NORMAL),
                ("e1f2", NORMAL),
                ("e1d2", NORMAL),
                ("e1g1", CASTLE),
                ("e1c1", CASTLE),
            ],
        )

    def test_black_with_all_rights_castles_kingside_then_queenside_after_king_steps(self) -> None:
        fen = "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1"
        self.assertEqual(len(all_moves(fen)), 26)
        self.assertEqual(
            moves_from(fen, "e8"),
            [
                ("e8f8", NORMAL),
                ("e8e7", NORMAL),
                ("e8d8", NORMAL),
                ("e8f7", NORMAL),
                ("e8d7", NORMAL),
                ("e8g8", CASTLE),
                ("e8c8", CASTLE),
            ],
        )

    def test_castling_without_rights_is_not_generated(self) -> None:
        fen = "r3k2r/8/8/8/8/8/8/R3K2R w - - 0 1"
        self.assertEqual(len(all_moves(fen)), 24)
        self.assertEqual(castles(fen), [])

    def test_castling_generated_only_on_the_side_that_meets_the_conditions(self) -> None:
        kingside = [("e1g1", CASTLE)]
        queenside = [("e1c1", CASTLE)]
        black_queenside = [("e8c8", CASTLE)]
        cases = (
            ("kingside right only", "r3k2r/8/8/8/8/8/8/R3K2R w Kkq - 0 1", kingside),
            ("queenside right only", "r3k2r/8/8/8/8/8/8/R3K2R w Qkq - 0 1", queenside),
            ("own piece on f1", "r3k2r/8/8/8/8/8/8/R3KN1R w KQkq - 0 1", queenside),
            ("own piece on g1", "r3k2r/8/8/8/8/8/8/R3K1NR w KQkq - 0 1", queenside),
            ("own piece on b1", "r3k2r/8/8/8/8/8/8/RN2K2R w KQkq - 0 1", kingside),
            ("own piece on c1", "r3k2r/8/8/8/8/8/8/R1B1K2R w KQkq - 0 1", kingside),
            ("own piece on d1", "r3k2r/8/8/8/8/8/8/R2QK2R w KQkq - 0 1", kingside),
            # b5 bishop looks at f1.
            ("king passes attacked f1", "r3k2r/8/8/1b6/8/8/8/R3K2R w KQkq - 0 1", queenside),
            # h3 knight looks at g1.
            ("king lands on attacked g1", "r3k2r/8/8/8/8/7n/8/R3K2R w KQkq - 0 1", queenside),
            # a4 bishop looks at d1.
            ("king passes attacked d1", "r3k2r/8/8/8/b7/8/8/R3K2R w KQkq - 0 1", kingside),
            # h6 bishop looks at c1.
            ("king lands on attacked c1", "r3k2r/8/7b/8/8/8/8/R3K2R w KQkq - 0 1", kingside),
            # a3 knight looks at b1, which the king does not cross.
            (
                "b1 attacked but empty",
                "r3k2r/8/8/8/8/n7/8/R3K2R w KQkq - 0 1",
                kingside + queenside,
            ),
            # e4 bishop looks at h1 and b1: the rook may be attacked.
            (
                "rook on h1 and b1 attacked",
                "r3k2r/8/8/8/4b3/8/8/R3K2R w KQkq - 0 1",
                kingside + queenside,
            ),
            # b5 bishop is pinned to e8 by the a4 bishop and still attacks f1.
            ("pinned attacker of f1", "r3k2r/8/8/1b6/B7/8/8/R3K2R w KQkq - 0 1", queenside),
            # h6 knight looks at g8.
            (
                "black king lands on attacked g8",
                "r3k2r/8/7N/8/8/8/8/R3K2R b KQkq - 0 1",
                black_queenside,
            ),
            # a3 bishop looks at f8.
            (
                "black king passes attacked f8",
                "r3k2r/8/8/8/8/B7/8/R3K2R b KQkq - 0 1",
                black_queenside,
            ),
        )
        for what, fen, expected in cases:
            with self.subTest(what=what):
                self.assertEqual(castles(fen), expected)

    def test_castling_rejected_when_king_is_in_check(self) -> None:
        # d3 knight gives check; the king steps stay, they are pseudo-legal.
        fen = "r3k2r/8/8/8/8/3n4/8/R3K2R w KQkq - 0 1"
        self.assertEqual(castles(fen), [])
        self.assertEqual(
            moves_from(fen, "e1"),
            [
                ("e1e2", NORMAL),
                ("e1f1", NORMAL),
                ("e1d1", NORMAL),
                ("e1f2", NORMAL),
                ("e1d2", NORMAL),
            ],
        )


class EnPassantTest(unittest.TestCase):
    def test_pawn_beside_the_pushed_pawn_takes_en_passant(self) -> None:
        self.assertEqual(
            moves_from(AFTER_D5_EP_FEN, "e5"), [("e5e6", NORMAL), ("e5d6", EN_PASSANT)]
        )
        self.assertEqual(len(all_moves(AFTER_D5_EP_FEN)), 31)

    def test_pawns_on_both_sides_each_take_en_passant(self) -> None:
        fen = "4k3/8/8/3PpP2/8/8/8/4K3 w - e6 0 1"
        self.assertEqual(moves_from(fen, "d5"), [("d5d6", NORMAL), ("d5e6", EN_PASSANT)])
        self.assertEqual(moves_from(fen, "f5"), [("f5f6", NORMAL), ("f5e6", EN_PASSANT)])
        self.assertEqual(len(all_moves(fen)), 9)

    def test_pawn_beside_a_pawn_without_ep_square_only_pushes(self) -> None:
        fen = "4k3/8/8/3Pp3/8/8/8/4K3 w - - 0 1"
        self.assertEqual(moves_from(fen, "d5"), [("d5d6", NORMAL)])

    def test_black_pawn_takes_en_passant_towards_the_third_rank(self) -> None:
        fen = "4k3/8/8/8/3pP3/8/8/4K3 b - e3 0 1"
        self.assertEqual(moves_from(fen, "d4"), [("d4d3", NORMAL), ("d4e3", EN_PASSANT)])

    def test_ep_square_without_a_capturer_gives_no_en_passant(self) -> None:
        moves = all_moves("4k3/8/8/4p3/8/8/8/4K3 w - e6 0 1")
        self.assertEqual(len(moves), 5)
        self.assertFalse(any(kind is EN_PASSANT for _, kind in moves))


class QueryTest(unittest.TestCase):
    FENS = (
        STARTING_FEN,
        AFTER_E4_FEN,
        KIWIPETE_FEN,
        "k2r4/4P3/8/8/8/8/8/4K3 w - - 0 1",
        CASTLING_FEN,
        AFTER_D5_EP_FEN,
    )

    def test_generation_leaves_fen_key_and_squares_unchanged(self) -> None:
        for fen in self.FENS:
            with self.subTest(fen=fen):
                board = Board.from_fen(fen)
                squares = list(board.squares)
                key = board.key
                pseudo_legal_moves(board)
                self.assertEqual(board.to_fen(), fen)
                self.assertEqual(board.key, key)
                self.assertEqual(board.squares, squares)


class OrderTest(unittest.TestCase):
    FENS = (STARTING_FEN, AFTER_E4_FEN, KIWIPETE_FEN, CASTLING_FEN, AFTER_D5_EP_FEN)

    def test_from_square_never_decreases_through_the_list(self) -> None:
        for fen in self.FENS:
            with self.subTest(fen=fen):
                origins = [m.from_sq for m in pseudo_legal_moves(Board.from_fen(fen))]
                self.assertEqual(origins, sorted(origins))

    def test_two_calls_give_identical_lists(self) -> None:
        for fen in self.FENS:
            with self.subTest(fen=fen):
                self.assertEqual(all_moves(fen), all_moves(fen))


if __name__ == "__main__":
    unittest.main()
