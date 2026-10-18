"""core/rules.py: checkmate and stalemate for the side to move.

The table expectations were checked with an independent generator on 2026-10-17; the
leaf counts are the CPW Checkmates column.
"""

from __future__ import annotations

import unittest

from chess.core.board import Board
from chess.core.fen import STARTING_FEN
from chess.core.movegen import legal_moves
from chess.core.rules import is_checkmate, is_stalemate

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


if __name__ == "__main__":
    unittest.main()
