"""Pseudo-legal move generation, and perft over it.

Pseudo-legal means by the rules of movement only: a move that leaves the own king in
check is still generated; the legality filter is 1.6. En passant and castling are 1.5.

perft and perft_divide live here, not in tools/perft.py, so the tests import them as a
package; the tool is a CLI over them (ADR-007).
"""

from __future__ import annotations

from chess.core.attacks import (
    DIAGONAL,
    KING_TARGETS,
    KNIGHT_TARGETS,
    ORTHOGONAL,
    PAWN_ATTACKS,
    RAYS,
)
from chess.core.board import Board
from chess.core.types import (
    PROMOTION_PIECES,
    Color,
    Move,
    MoveKind,
    Piece,
    PieceType,
    Square,
    rank_of,
)

_NORMAL = MoveKind.NORMAL
_CAPTURE = MoveKind.CAPTURE
_DOUBLE_PAWN_PUSH = MoveKind.DOUBLE_PAWN_PUSH
_PROMOTION = MoveKind.PROMOTION

_SLIDER_DIRECTIONS = {
    PieceType.BISHOP: DIAGONAL,
    PieceType.ROOK: ORTHOGONAL,
    PieceType.QUEEN: ORTHOGONAL + DIAGONAL,
}


def pseudo_legal_moves(board: Board) -> list[Move]:
    """Return every pseudo-legal move of the side to move; `board` is left as it was.

    The order is part of the contract, because perft_divide reports by root move:
    origin squares 0-63 in turn, and for each piece
      - pawn: one step, two steps, then captures towards the a-file before the h-file;
        a move to the last rank is four PROMOTION moves in PROMOTION_PIECES order
      - knight, king: targets in KNIGHT_TARGETS / KING_TARGETS order
      - bishop, rook, queen: directions in RAYS index order (straight N E S W, then
        diagonal NE SE SW NW), nearest square first
    Every capture is CAPTURE or PROMOTION: make does not look at the target of a NORMAL
    move (ADR-022).
    """
    squares = board.squares
    us = board.turn
    moves: list[Move] = []
    for from_sq in range(64):
        piece = squares[from_sq]
        if piece is None or piece.color is not us:
            continue
        kind = piece.kind
        if kind is PieceType.PAWN:
            _pawn_moves(squares, us, from_sq, moves)
        elif kind is PieceType.KNIGHT:
            _step_moves(squares, us, from_sq, KNIGHT_TARGETS[from_sq], moves)
        elif kind is PieceType.KING:
            _step_moves(squares, us, from_sq, KING_TARGETS[from_sq], moves)
        else:
            _slider_moves(squares, us, from_sq, _SLIDER_DIRECTIONS[kind], moves)
    return moves


def _pawn_moves(squares: list[Piece | None], us: Color, from_sq: Square, moves: list[Move]) -> None:
    """Append the pushes and captures of the pawn of `us` on Square `from_sq`."""
    if us is Color.WHITE:
        step, start_rank, last_rank = 8, 1, 7
    else:
        step, start_rank, last_rank = -8, 6, 0
    promotes = rank_of(from_sq + step) == last_rank

    to_sq = from_sq + step
    if squares[to_sq] is None:
        if promotes:
            _append_promotions(from_sq, to_sq, moves)
        else:
            moves.append(Move(from_sq, to_sq, _NORMAL))
            two = to_sq + step
            if rank_of(from_sq) == start_rank and squares[two] is None:
                moves.append(Move(from_sq, two, _DOUBLE_PAWN_PUSH))

    for to_sq in PAWN_ATTACKS[us.value][from_sq]:
        target = squares[to_sq]
        if target is None or target.color is us:
            continue
        if promotes:
            _append_promotions(from_sq, to_sq, moves)
        else:
            moves.append(Move(from_sq, to_sq, _CAPTURE))


def _append_promotions(from_sq: Square, to_sq: Square, moves: list[Move]) -> None:
    """Append the four promotions from Square `from_sq` to Square `to_sq`.

    A promotion that captures is still PROMOTION; make reads the target square for it.
    """
    for promotion in PROMOTION_PIECES:
        moves.append(Move(from_sq, to_sq, _PROMOTION, promotion))


def _step_moves(
    squares: list[Piece | None],
    us: Color,
    from_sq: Square,
    targets: tuple[Square, ...],
    moves: list[Move],
) -> None:
    """Append the moves of a knight or king of `us` on Square `from_sq` to `targets`."""
    for to_sq in targets:
        target = squares[to_sq]
        if target is None:
            moves.append(Move(from_sq, to_sq, _NORMAL))
        elif target.color is not us:
            moves.append(Move(from_sq, to_sq, _CAPTURE))


def _slider_moves(
    squares: list[Piece | None],
    us: Color,
    from_sq: Square,
    directions: tuple[int, ...],
    moves: list[Move],
) -> None:
    """Append the moves of a slider of `us` on Square `from_sq` along `directions`.

    Each ray is walked to the first piece: a foreign one is captured, then the ray stops.
    """
    rays = RAYS[from_sq]
    for direction in directions:
        for to_sq in rays[direction]:
            target = squares[to_sq]
            if target is None:
                moves.append(Move(from_sq, to_sq, _NORMAL))
                continue
            if target.color is not us:
                moves.append(Move(from_sq, to_sq, _CAPTURE))
            break


def perft(board: Board, depth: int) -> int:
    """Return the number of leaf positions `depth` plies below `board`; 1 for depth <= 0.

    Moves are played with make/unmake, never on a copy (ADR-006); `board` is left as it
    was. At depth 1 the moves are counted, not played.
    """
    if depth <= 0:
        return 1
    moves = _perft_moves(board)
    if depth == 1:
        return len(moves)
    nodes = 0
    for move in moves:
        undo = board.make(move)
        nodes += perft(board, depth - 1)
        board.unmake(move, undo)
    return nodes


def perft_divide(board: Board, depth: int) -> dict[Move, int]:
    """Return perft of `depth` split by root move, keys in generator order.

    A mismatch against the reference is traced by comparing root moves, then descending
    into the one that differs (ADR-007). A depth below 1 has no root moves: ValueError.
    """
    if depth < 1:
        raise ValueError(f"perft_divide depth must be at least 1, got {depth}")
    divide: dict[Move, int] = {}
    for move in _perft_moves(board):
        undo = board.make(move)
        divide[move] = perft(board, depth - 1)
        board.unmake(move, undo)
    return divide


def _perft_moves(board: Board) -> list[Move]:
    """The moves perft and perft_divide count; the one line that turns legal in 1.6."""
    return pseudo_legal_moves(board)
