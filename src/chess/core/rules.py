"""End of the game for the side to move.

For now this module holds checkmate and stalemate, both over legal_moves and is_in_check.
Task 1.9 adds the draws (insufficient material, the fifty-move rule, repetition) and the
RuleSet (ADR-008).
"""

from __future__ import annotations

from chess.core.attacks import is_in_check
from chess.core.board import Board
from chess.core.movegen import legal_moves

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
