"""Move generation: pseudo-legal moves, the legality filter over them, and perft.

Pseudo-legal means by the rules of movement only: a move that leaves the own king in
check is still generated. Legal moves are the pseudo-legal ones that survive make, a
check test and unmake (ADR-006); perft counts legal moves.

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
    is_in_check,
    is_square_attacked,
)
from chess.core.board import Board
from chess.core.types import (
    B1,
    B8,
    C1,
    C8,
    D1,
    D8,
    F1,
    F8,
    G1,
    G8,
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
_EN_PASSANT = MoveKind.EN_PASSANT
_CASTLE = MoveKind.CASTLE
_PROMOTION = MoveKind.PROMOTION

_SLIDER_DIRECTIONS = {
    PieceType.BISHOP: DIAGONAL,
    PieceType.ROOK: ORTHOGONAL,
    PieceType.QUEEN: ORTHOGONAL + DIAGONAL,
}

# Indexed by color.value, kingside first: (right, king destination, squares that must be
# empty, squares the king crosses or lands on). b1/b8 must be empty but may be attacked:
# the king does not cross it.
_CASTLINGS = (
    (
        ("white_kingside", G1, (F1, G1), (F1, G1)),
        ("white_queenside", C1, (D1, C1, B1), (D1, C1)),
    ),
    (
        ("black_kingside", G8, (F8, G8), (F8, G8)),
        ("black_queenside", C8, (D8, C8, B8), (D8, C8)),
    ),
)


def pseudo_legal_moves(board: Board) -> list[Move]:
    """Return every pseudo-legal move of the side to move; `board` is left as it was.

    The order is part of the contract, because perft_divide reports by root move:
    origin squares 0-63 in turn, and for each piece
      - pawn: one step, two steps, then captures towards the a-file before the h-file,
        en passant among them in the same order; a move to the last rank is four
        PROMOTION moves in PROMOTION_PIECES order
      - knight, king: targets in KNIGHT_TARGETS / KING_TARGETS order; after the king's
        steps castling, kingside before queenside
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
            _pawn_moves(squares, us, from_sq, board.ep_square, moves)
        elif kind is PieceType.KNIGHT:
            _step_moves(squares, us, from_sq, KNIGHT_TARGETS[from_sq], moves)
        elif kind is PieceType.KING:
            _step_moves(squares, us, from_sq, KING_TARGETS[from_sq], moves)
            _castling_moves(board, us, from_sq, moves)
        else:
            _slider_moves(squares, us, from_sq, _SLIDER_DIRECTIONS[kind], moves)
    return moves


def legal_moves(board: Board) -> list[Move]:
    """Return every legal move of the side to move; `board` is left as it was.

    Each pseudo-legal move is played with make, kept when the own king is not in check,
    and taken back with unmake (ADR-006). The order is that of pseudo_legal_moves with
    the illegal moves dropped; it is part of the contract, for perft_divide and for
    finding a move from the wire by legal_moves(board).index(move) (ADR-022).
    """
    # Remembered before make: afterwards the opponent is to move.
    us = board.turn
    moves: list[Move] = []
    for move in pseudo_legal_moves(board):
        undo = board.make(move)
        if not is_in_check(board, us):
            moves.append(move)
        board.unmake(move, undo)
    return moves


def _pawn_moves(
    squares: list[Piece | None],
    us: Color,
    from_sq: Square,
    ep_square: Square | None,
    moves: list[Move],
) -> None:
    """Append the pushes and captures of the pawn of `us` on Square `from_sq`.

    `ep_square` is the en passant Square of the position, or None.
    """
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
        if to_sq == ep_square:
            # Nothing else is checked. The ep square stands only on rank 3 or 6, so the
            # capturer is on its fifth rank; parse_fen and make guarantee that the square
            # is empty and the pushed pawn stands behind it.
            moves.append(Move(from_sq, to_sq, _EN_PASSANT))
            continue
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


def _castling_moves(board: Board, us: Color, from_sq: Square, moves: list[Move]) -> None:
    """Append the castling moves of the king of `us` on Square `from_sq`, kingside first.

    The move is the king's, to g1/c1 or g8/c8; make moves the rook.
    """
    # The right alone says that the king and that rook have not moved: parse_fen rejects a
    # right without both at home, and make drops it when the king moves, the rook moves or
    # the rook is captured at home. Their presence is not checked again.
    squares = board.squares
    rights = board.castling
    sides = [
        (king_to, path)
        for right, king_to, empty, path in _CASTLINGS[us.value]
        if getattr(rights, right) and all(squares[sq] is None for sq in empty)
    ]
    if not sides:
        return
    # The attacks are checked here, not left to the legality filter (1.6): that one sees
    # only the final position, so it cannot tell that the king was in check or crossed an
    # attacked square. The rook may be attacked, and may cross an attacked square.
    them = us.opposite
    if is_square_attacked(board, from_sq, them):
        return
    for king_to, path in sides:
        if not any(is_square_attacked(board, sq, them) for sq in path):
            moves.append(Move(from_sq, king_to, _CASTLE))


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

    Legal moves are counted. They are played with make/unmake, never on a copy (ADR-006);
    `board` is left as it was. At depth 1 the moves are counted, not played.
    """
    if depth <= 0:
        return 1
    moves = legal_moves(board)
    if depth == 1:
        return len(moves)
    nodes = 0
    for move in moves:
        undo = board.make(move)
        nodes += perft(board, depth - 1)
        board.unmake(move, undo)
    return nodes


def perft_divide(board: Board, depth: int) -> dict[Move, int]:
    """Return perft of `depth` split by legal root move, keys in legal_moves order.

    A mismatch against the reference is traced by comparing root moves, then descending
    into the one that differs (ADR-007). A depth below 1 has no root moves: ValueError.
    """
    if depth < 1:
        raise ValueError(f"perft_divide depth must be at least 1, got {depth}")
    divide: dict[Move, int] = {}
    for move in legal_moves(board):
        undo = board.make(move)
        divide[move] = perft(board, depth - 1)
        board.unmake(move, undo)
    return divide
