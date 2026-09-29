"""Attack geometry: which squares a piece on a square can reach on an empty board.

The tables live here, not in movegen, because both the generator and castling (1.5) need
them; castling also needs is_square_attacked, and a table in movegen would make an
import cycle movegen <-> attacks. is_square_attacked and is_in_check arrive in 1.4.

Every table is built once at import from (file, rank) steps with a bounds check, never
from index arithmetic, so no target wraps around the edge of the board. Tables are
tuples, never lists: fixed order keeps the generator deterministic.
"""

from __future__ import annotations

from chess.core.types import Color, Square, file_of, rank_of, square

# Direction indices into RAYS[sq]: straight lines first, then diagonals, each clockwise
# from north. The generator walks them in this order.
NORTH, EAST, SOUTH, WEST, NORTH_EAST, SOUTH_EAST, SOUTH_WEST, NORTH_WEST = range(8)
ORTHOGONAL = (NORTH, EAST, SOUTH, WEST)
DIAGONAL = (NORTH_EAST, SOUTH_EAST, SOUTH_WEST, NORTH_WEST)

# (file step, rank step) per direction, in index order.
_DIRECTION_STEPS = ((0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, -1), (-1, 1))

# Clockwise from north-north-east.
_KNIGHT_STEPS = ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2))


def _targets(sq: Square, steps: tuple[tuple[int, int], ...]) -> tuple[Square, ...]:
    """Squares one step away from Square `sq` for each step that stays on the board."""
    file, rank = file_of(sq), rank_of(sq)
    return tuple(
        square(file + df, rank + dr)
        for df, dr in steps
        if 0 <= file + df < 8 and 0 <= rank + dr < 8
    )


def _ray(sq: Square, df: int, dr: int) -> tuple[Square, ...]:
    """Squares from Square `sq` (excluded) to the edge of the board in one direction."""
    file, rank = file_of(sq) + df, rank_of(sq) + dr
    ray = []
    while 0 <= file < 8 and 0 <= rank < 8:
        ray.append(square(file, rank))
        file += df
        rank += dr
    return tuple(ray)


def _build_pawn_attacks(color: Color) -> tuple[tuple[Square, ...], ...]:
    """Squares a pawn of `color` captures on, from each square; towards the a-file first."""
    forward = 1 if color is Color.WHITE else -1
    return tuple(_targets(sq, ((-1, forward), (1, forward))) for sq in range(64))


KNIGHT_TARGETS: tuple[tuple[Square, ...], ...] = tuple(
    _targets(sq, _KNIGHT_STEPS) for sq in range(64)
)
KING_TARGETS: tuple[tuple[Square, ...], ...] = tuple(
    _targets(sq, _DIRECTION_STEPS) for sq in range(64)
)
RAYS: tuple[tuple[tuple[Square, ...], ...], ...] = tuple(
    tuple(_ray(sq, df, dr) for df, dr in _DIRECTION_STEPS) for sq in range(64)
)
# Indexed by color.value. Captures only: a pawn pushes where it cannot capture.
PAWN_ATTACKS: tuple[tuple[tuple[Square, ...], ...], ...] = tuple(
    _build_pawn_attacks(color) for color in Color
)
