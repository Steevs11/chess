"""Attack geometry, and the queries over it: is_square_attacked and is_in_check.

The tables live here, not in movegen, because both the generator and castling (1.5) need
them; castling also needs is_square_attacked, and a table in movegen would make an
import cycle movegen <-> attacks.

Every table is built once at import from (file, rank) steps with a bounds check, never
from index arithmetic, so no target wraps around the edge of the board. Tables are
tuples, never lists: fixed order keeps the generator deterministic.

is_square_attacked works backwards from the target: it looks for an attacker on the
squares a piece of each kind on the target would reach, instead of generating moves.
"""

from __future__ import annotations

from chess.core.board import Board
from chess.core.types import Color, Piece, PieceType, Square, file_of, rank_of, square

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

# Indexed by color.value.
_PAWNS = tuple(Piece(color, PieceType.PAWN) for color in Color)
_KNIGHTS = tuple(Piece(color, PieceType.KNIGHT) for color in Color)
_KINGS = tuple(Piece(color, PieceType.KING) for color in Color)


def is_square_attacked(board: Board, sq: Square, by: Color) -> bool:
    """Return True when a piece of `by` attacks Square `sq` by the rules of movement.

    What stands on `sq` is not looked at: a square held by a piece of `by` is defended,
    which counts as attacked. Pieces of both colors block rays. Pins are ignored: a pinned
    piece still attacks (FIDE), which castling (1.5) relies on. `board` is left as it was.
    """
    squares = board.squares
    knight = _KNIGHTS[by.value]
    if any(squares[target] == knight for target in KNIGHT_TARGETS[sq]):
        return True
    king = _KINGS[by.value]
    if any(squares[target] == king for target in KING_TARGETS[sq]):
        return True
    # A pawn of `by` attacks `sq` from exactly the squares a pawn of the other color on
    # `sq` would capture on: the diagonal step is the same, only the direction is mirrored.
    pawn = _PAWNS[by.value]
    if any(squares[target] == pawn for target in PAWN_ATTACKS[by.opposite.value][sq]):
        return True
    rays = RAYS[sq]
    return _has_slider_on_rays(squares, rays, ORTHOGONAL, by, PieceType.ROOK) or (
        _has_slider_on_rays(squares, rays, DIAGONAL, by, PieceType.BISHOP)
    )


def is_in_check(board: Board, color: Color) -> bool:
    """Return True when the king of `color` is attacked by the other color.

    The color is explicit, not board.turn: the legality filter (1.6) asks about the side
    that has just moved, mate and stalemate (1.7) about the side to move. `board` is left
    as it was.
    """
    # Scanned, not cached: parse_fen guarantees exactly one king, and a king square in
    # Board waits until the measurement in 1.8 shows the need (as in ADR-013).
    king_sq = board.squares.index(_KINGS[color.value])
    return is_square_attacked(board, king_sq, color.opposite)


def _has_slider_on_rays(
    squares: list[Piece | None],
    rays: tuple[tuple[Square, ...], ...],
    directions: tuple[int, ...],
    by: Color,
    kind: PieceType,
) -> bool:
    """True when the first piece along one of `directions` is a `kind` or queen of `by`.

    Any other first piece, of either color, stops the ray.
    """
    for direction in directions:
        for target in rays[direction]:
            piece = squares[target]
            if piece is None:
                continue
            if piece.color is by and (piece.kind is kind or piece.kind is PieceType.QUEEN):
                return True
            break
    return False
