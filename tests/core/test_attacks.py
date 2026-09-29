"""Geometry tables in core/attacks.py: knight, king, ray and pawn-attack targets.

Every expectation is worked out by hand from the board; none is read back from the tables.
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
)
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
    E1,
    E3,
    E4,
    E5,
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
    H7,
    H8,
    Color,
)

WHITE = Color.WHITE.value
BLACK = Color.BLACK.value


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


if __name__ == "__main__":
    unittest.main()
