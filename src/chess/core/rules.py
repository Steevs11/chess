"""End of the game for the side to move: checkmate, stalemate and the automatic draws.

`is_checkmate` and `is_stalemate` look at the board alone. `draw_reason` adds the draws -
insufficient material, the halfmove clock and repetition - and does not look at mate or
stalemate: the caller asks those first, because a mate on the move that also completes a
repetition is still a mate.

Repetition is counted over Zobrist keys (ADR-027). The history of keys is the caller's
(Game, 1.12) and comes in as an argument; this module keeps no state.

Which clock limit and which repetition count end the game is data in a `RuleSet`, never a
branch on the profile name (ADR-008). A wrong call raises ValueError, not a ChessError.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from chess.core.attacks import is_in_check
from chess.core.board import Board
from chess.core.movegen import legal_moves
from chess.core.types import Color, PieceType, Square, Termination, file_of, rank_of

# The cheap check test goes first and `and` short-circuits: a tree walk may ask
# is_checkmate at every leaf, so only a leaf in check pays for legal_moves.


def is_checkmate(board: Board) -> bool:
    """Return True when the side to move is in check and has no legal move.

    `board` is left as it was.
    """
    return is_in_check(board, board.turn) and not legal_moves(board)


def is_stalemate(board: Board) -> bool:
    """Return True when the side to move is not in check and has no legal move.

    `board` is left as it was.
    """
    return not is_in_check(board, board.turn) and not legal_moves(board)


@dataclass(frozen=True, slots=True)
class RuleSet:
    """Draw limits of one profile and the termination each one ends the game with.

    The game is drawn when the current position has occurred `repetitions` times, or when
    the halfmove clock reaches `halfmoves`.
    """

    repetitions: int
    repetition_termination: Termination
    halfmoves: int
    halfmove_termination: Termination


# ADR-008: online applies threefold and fifty moves automatically; fide applies only the
# automatic FIDE draws, fivefold and seventy-five moves (a claim needs a protocol message).
ONLINE_RULES = RuleSet(3, Termination.THREEFOLD_REPETITION, 100, Termination.FIFTY_MOVE)
FIDE_RULES = RuleSet(5, Termination.FIVEFOLD_REPETITION, 150, Termination.SEVENTY_FIVE_MOVE)

_MINOR_PIECES = (PieceType.KNIGHT, PieceType.BISHOP)


def _square_color(sq: Square) -> int:
    """Return 0 for a dark Square `sq` (a1 is dark), 1 for a light one."""
    return (file_of(sq) + rank_of(sq)) % 2


def has_insufficient_material(board: Board) -> bool:
    """Return True when the material on `board` is one of the four drawn pairs of PROJECT 7.

    The pairs are K-K, K+B-K, K+N-K and K+B-K+B with both bishops on squares of the same
    color, either side holding the minor piece. Nothing wider counts: two bishops of one
    side, two knights and K+N-K+N are not a draw here, even when mate cannot be forced.
    `board` is left as it was.
    """
    minors: list[tuple[Square, PieceType, Color]] = []
    for sq, piece in enumerate(board.squares):
        if piece is None or piece.kind is PieceType.KING:
            continue
        if piece.kind not in _MINOR_PIECES:
            return False
        minors.append((sq, piece.kind, piece.color))
    if len(minors) <= 1:
        return True
    if len(minors) > 2:
        return False
    (sq_a, kind_a, color_a), (sq_b, kind_b, color_b) = minors
    return (
        kind_a is PieceType.BISHOP
        and kind_b is PieceType.BISHOP
        and color_a is not color_b
        and _square_color(sq_a) == _square_color(sq_b)
    )


def draw_reason(
    board: Board, keys: Sequence[int], rules: RuleSet = ONLINE_RULES
) -> Termination | None:
    """Return the termination of an automatic draw on `board`, or None if the game goes on.

    `keys` are the Zobrist keys of every position of the game, from the first to the
    current one, which is last. The checks go in this order and the first one wins:
    insufficient material, then the halfmove clock reaching `rules.halfmoves`, then the
    current key occurring `rules.repetitions` times in `keys`. Checkmate and stalemate are
    not checked; the caller asks them first.

    An empty `keys`, or one whose last key is not `board.key`, is a wrong call and raises
    ValueError. `board` is left as it was.
    """
    if not keys:
        raise ValueError("keys must hold at least the current position's key")
    if keys[-1] != board.key:
        raise ValueError(f"last key {keys[-1]:#x} is not the board's key {board.key:#x}")
    if has_insufficient_material(board):
        return Termination.INSUFFICIENT_MATERIAL
    if board.halfmove_clock >= rules.halfmoves:
        return rules.halfmove_termination
    if keys.count(board.key) >= rules.repetitions:
        return rules.repetition_termination
    return None
