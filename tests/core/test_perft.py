"""perft and perft_divide in core/movegen.py, against the Chess Programming Wiki numbers.

The starting position is asserted at depth 1-3 since 1.3, Kiwipete and Position 5 at
depth 1 since 1.5: there pseudo-legal equals legal. From 1.6 on perft counts legal moves
and the default set of ADR-026 is asserted at every depth up to the listed one. The slow
set of ADR-026 runs only with CHESS_SLOW_TESTS: about 12 million nodes, minutes.
"""

from __future__ import annotations

import os
import unittest

from chess.core.board import Board
from chess.core.fen import STARTING_FEN
from chess.core.movegen import perft, perft_divide

# Source: https://www.chessprogramming.org/Perft_Results, transcribed 2026-09-26.
# (name, FEN, {depth: nodes})
PERFT_REFERENCE = (
    (
        "start",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        {1: 20, 2: 400, 3: 8902, 4: 197281, 5: 4865609, 6: 119060324},
    ),
    (
        "kiwipete",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq -",
        {1: 48, 2: 2039, 3: 97862, 4: 4085603, 5: 193690690},
    ),
    (
        "position 3",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        {1: 14, 2: 191, 3: 2812, 4: 43238, 5: 674624, 6: 11030083},
    ),
    (
        "position 4",
        "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
        {1: 6, 2: 264, 3: 9467, 4: 422333, 5: 15833292},
    ),
    (
        "position 5",
        "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
        {1: 44, 2: 1486, 3: 62379, 4: 2103487, 5: 89941194},
    ),
)

REFERENCE = {name: (fen, nodes) for name, fen, nodes in PERFT_REFERENCE}


class PerftTest(unittest.TestCase):
    def test_start_matches_reference_up_to_depth_three(self) -> None:
        fen, nodes = REFERENCE["start"]
        for depth in (1, 2, 3):
            with self.subTest(depth=depth):
                self.assertEqual(perft(Board.from_fen(fen), depth), nodes[depth])

    def test_kiwipete_and_position_5_match_reference_at_depth_one(self) -> None:
        for name in ("kiwipete", "position 5"):
            fen, nodes = REFERENCE[name]
            with self.subTest(position=name):
                self.assertEqual(perft(Board.from_fen(fen), 1), nodes[1])

    def test_default_set_matches_reference_at_every_depth_up_to_the_listed_one(self) -> None:
        # ADR-026.
        default_set = (
            ("start", 4),
            ("kiwipete", 3),
            ("position 3", 4),
            ("position 4", 3),
            ("position 5", 3),
        )
        for name, max_depth in default_set:
            fen, nodes = REFERENCE[name]
            for depth in range(1, max_depth + 1):
                with self.subTest(position=name, depth=depth):
                    self.assertEqual(perft(Board.from_fen(fen), depth), nodes[depth])

    def test_depth_zero_counts_the_position_itself(self) -> None:
        self.assertEqual(perft(Board.from_fen(STARTING_FEN), 0), 1)

    def test_perft_leaves_fen_and_key_unchanged(self) -> None:
        board = Board.from_fen(STARTING_FEN)
        key = board.key
        perft(board, 3)
        self.assertEqual(board.to_fen(), STARTING_FEN)
        self.assertEqual(board.key, key)


@unittest.skipUnless(os.environ.get("CHESS_SLOW_TESTS"), "slow")
class SlowPerftTest(unittest.TestCase):
    def test_slow_set_matches_reference_at_the_listed_depth(self) -> None:
        # ADR-026; the shallower depths are asserted by the default set.
        slow_set = (
            ("start", 5),
            ("kiwipete", 4),
            ("position 3", 5),
            ("position 4", 4),
            ("position 5", 4),
        )
        for name, depth in slow_set:
            fen, nodes = REFERENCE[name]
            with self.subTest(position=name):
                self.assertEqual(perft(Board.from_fen(fen), depth), nodes[depth])


class PerftDivideTest(unittest.TestCase):
    def test_divide_at_depth_two_from_start_gives_twenty_roots_of_twenty(self) -> None:
        divide = perft_divide(Board.from_fen(STARTING_FEN), 2)
        self.assertEqual(len(divide), 20)
        self.assertTrue(all(count == 20 for count in divide.values()))
        self.assertEqual(sum(divide.values()), 400)

    def test_divide_sums_to_perft_at_the_same_depth(self) -> None:
        for depth in (1, 2, 3):
            with self.subTest(depth=depth):
                board = Board.from_fen(STARTING_FEN)
                self.assertEqual(sum(perft_divide(board, depth).values()), perft(board, depth))

    def test_divide_below_depth_one_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            perft_divide(Board.from_fen(STARTING_FEN), 0)


if __name__ == "__main__":
    unittest.main()
