"""Standard Algebraic Notation: a legal move to its SAN, and SAN text back to the move.

Both functions take the move from `legal_moves(board)` and return or work with the
generated instance, because only it carries the right `kind` (ADR-022). Both leave
`board` as they found it: the check suffix is found by make and unmake.

`to_san` writes
  - a piece as its uppercase letter, a pawn without one; `x` before a captured square, a
    pawn capture with the pawn's file first (`exd5`), en passant the same, no suffix
  - a promotion as `e8=Q`, castling as `O-O` / `O-O-O` with the letter O
  - disambiguation for a piece other than a pawn or king, among the LEGAL moves of the
    same piece type to the same square: the origin file if it tells them apart, else the
    origin rank, else both (`Nbd2`, `N1f3`, `Qb4d2`); a pinned piece is no rival
  - `#` when the side to move after the move is in check and has no legal move, else `+`
    when it is in check

`parse_san` takes off one trailing `+` or `#` without checking it is right, reads `O-O` /
`O-O-O` as castling and anything else as piece [KQRBN]? · origin file [a-h]? · origin rank
[1-8]? · `x`? · target · (=[QRBN])?. It keeps the legal moves that agree with everything
given, so surplus disambiguation passes. A given `x` demands a capture; a pawn capture
demands the `x`; a promotion demands `=X` and `=X` demands a promotion; castling is written
only as `O-O` / `O-O-O`. A piece capture without `x` passes. Exactly one match is returned;
none, several, or text of any other shape (`0-0`, `e.p.`, a lowercase piece, empty) raise
InvalidSanError. A move that is not legal handed to `to_san` is a wrong call: ValueError.
"""

from __future__ import annotations

import re

from chess.core.attacks import is_in_check
from chess.core.board import Board
from chess.core.movegen import legal_moves
from chess.core.types import (
    FILE_NAMES,
    RANK_NAMES,
    InvalidSanError,
    Move,
    MoveKind,
    PieceType,
    file_of,
    from_algebraic,
    rank_of,
    to_algebraic,
)

_SAN = re.compile(r"([KQRBN])?([a-h])?([1-8])?(x)?([a-h][1-8])(?:=([QRBN]))?")

# Castling SAN -> file of the king's destination.
_CASTLING_FILES = {"O-O": 6, "O-O-O": 2}


def to_san(board: Board, move: Move) -> str:
    """Return the SAN of `move` on `board`, check or mate suffix included.

    `move` is looked up in `legal_moves(board)` and the generated instance is used, so a
    move from `Move.from_uci` will do. A move that is not legal raises ValueError.
    `board` is left as it was.
    """
    moves = legal_moves(board)
    try:
        move = moves[moves.index(move)]
    except ValueError:
        raise ValueError(f"{move.to_uci()} is not a legal move in {board.to_fen()}") from None
    return _body(board, move, moves) + _suffix(board, move)


def parse_san(board: Board, text: str) -> Move:
    """Return the legal move on `board` that SAN `text` names, as generated.

    The tolerances and the shapes accepted are those of the module docstring. Text that
    names no legal move or more than one raises InvalidSanError. `board` is left as it was.
    """
    body = text[:-1] if text[-1:] in ("+", "#") else text
    moves = legal_moves(board)
    if body in _CASTLING_FILES:
        file = _CASTLING_FILES[body]
        candidates = [m for m in moves if m.kind is MoveKind.CASTLE and file_of(m.to_sq) == file]
    else:
        match = _SAN.fullmatch(body)
        if match is None:
            raise InvalidSanError(f"{text!r} is not SAN")
        candidates = _matching(board, moves, match)
    if not candidates:
        raise InvalidSanError(f"{text!r} names no legal move in {board.to_fen()}")
    if len(candidates) > 1:
        ucis = ", ".join(m.to_uci() for m in candidates)
        raise InvalidSanError(f"{text!r} is ambiguous in {board.to_fen()}: {ucis}")
    return candidates[0]


def _is_capture(board: Board, move: Move) -> bool:
    """Return True when `move`, not yet made on `board`, takes a piece."""
    kind = move.kind
    if kind is MoveKind.CAPTURE or kind is MoveKind.EN_PASSANT:
        return True
    return kind is MoveKind.PROMOTION and board.piece_at(move.to_sq) is not None


def _body(board: Board, move: Move, moves: list[Move]) -> str:
    """Return the SAN of legal `move` without the check suffix; `moves` is the legal list."""
    if move.kind is MoveKind.CASTLE:
        return "O-O" if file_of(move.to_sq) == 6 else "O-O-O"
    kind = board.piece_at(move.from_sq).kind
    target = to_algebraic(move.to_sq)
    capture = "x" if _is_capture(board, move) else ""
    if kind is PieceType.PAWN:
        origin = FILE_NAMES[file_of(move.from_sq)] if capture else ""
        promotion = "" if move.promotion is None else "=" + move.promotion.letter.upper()
        return origin + capture + target + promotion
    letter = kind.letter.upper()
    if kind is PieceType.KING:
        return letter + capture + target
    return letter + _disambiguation(board, move, moves) + capture + target


def _disambiguation(board: Board, move: Move, moves: list[Move]) -> str:
    """Return what tells `move` apart from legal moves of the same piece type to its square.

    The file if no rival shares it, else the rank if no rival shares that, else both.
    """
    kind = board.piece_at(move.from_sq).kind
    rivals = [
        m.from_sq
        for m in moves
        if m.to_sq == move.to_sq
        and m.from_sq != move.from_sq
        and board.piece_at(m.from_sq).kind is kind
    ]
    if not rivals:
        return ""
    file = file_of(move.from_sq)
    rank = rank_of(move.from_sq)
    if all(file_of(sq) != file for sq in rivals):
        return FILE_NAMES[file]
    if all(rank_of(sq) != rank for sq in rivals):
        return RANK_NAMES[rank]
    return to_algebraic(move.from_sq)


def _suffix(board: Board, move: Move) -> str:
    """Return "#", "+" or "" for legal `move` on `board`; make and unmake find it."""
    undo = board.make(move)
    try:
        if not is_in_check(board, board.turn):
            return ""
        return "+" if legal_moves(board) else "#"
    finally:
        board.unmake(move, undo)


def _matching(board: Board, moves: list[Move], match: re.Match[str]) -> list[Move]:
    """Return the legal `moves` that agree with every part of the SAN `match`."""
    letter, file, rank, capture, target, promotion = match.groups()
    kind = PieceType.PAWN if letter is None else PieceType.from_letter(letter.lower())
    to_sq = from_algebraic(target)
    promoted = None if promotion is None else PieceType.from_letter(promotion.lower())
    found = []
    for m in moves:
        if m.to_sq != to_sq or m.kind is MoveKind.CASTLE or m.promotion is not promoted:
            continue
        if board.piece_at(m.from_sq).kind is not kind:
            continue
        if file is not None and FILE_NAMES[file_of(m.from_sq)] != file:
            continue
        if rank is not None and RANK_NAMES[rank_of(m.from_sq)] != rank:
            continue
        takes = _is_capture(board, m)
        if capture is not None and not takes:
            continue
        if kind is PieceType.PAWN and takes and capture is None:
            continue
        found.append(m)
    return found
