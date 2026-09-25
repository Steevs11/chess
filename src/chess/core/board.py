"""The mutable board: piece placement, make/unmake and the incremental Zobrist key.

A move is played on the board and taken back (ADR-006); UndoRecord holds everything make
overwrites that unmake cannot derive (ADR-014). The key is kept up to date by XOR in make
and restored from the record in unmake (ADR-015).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace

from chess.core.fen import Position, format_fen, parse_fen
from chess.core.types import (
    A1,
    A8,
    C1,
    C8,
    D1,
    D8,
    E1,
    E8,
    F1,
    F8,
    G1,
    G8,
    H1,
    H8,
    CastlingRights,
    Color,
    Move,
    MoveKind,
    Piece,
    PieceType,
    Square,
    file_of,
)

# Any fixed value will do; it only has to be the same in every run (ADR-027).
_ZOBRIST_SEED = 0x5A0B_C0DE_2026

# Generation order is part of the key: changing it changes every key.
#   1. 2 x 6 x 64 piece keys, [color.value][kind.value][sq], innermost index fastest
#   2. 1 key for black to move
#   3. 16 castling keys, indexed by CastlingRights.to_index()
#   4. 8 en passant keys, one per file
_rng = random.Random(_ZOBRIST_SEED)
_PIECE_KEYS = tuple(
    tuple(tuple(_rng.getrandbits(64) for _sq in range(64)) for _kind in PieceType) for _c in Color
)
_BLACK_TO_MOVE_KEY = _rng.getrandbits(64)
_CASTLING_KEYS = tuple(_rng.getrandbits(64) for _ in range(16))
_EP_FILE_KEYS = tuple(_rng.getrandbits(64) for _ in range(8))
del _rng

_PAWNS = (Piece(Color.WHITE, PieceType.PAWN), Piece(Color.BLACK, PieceType.PAWN))

# King destination -> (rook from, rook to).
_CASTLE_ROOK = {G1: (H1, F1), C1: (A1, D1), G8: (H8, F8), C8: (A8, D8)}

# A move that starts or ends on one of these squares loses these rights. That covers the
# king moving, a rook moving and a rook captured at home in one rule.
_RIGHTS_LOST = {
    E1: ("white_kingside", "white_queenside"),
    H1: ("white_kingside",),
    A1: ("white_queenside",),
    E8: ("black_kingside", "black_queenside"),
    H8: ("black_kingside",),
    A8: ("black_queenside",),
}


@dataclass(frozen=True, slots=True)
class UndoRecord:
    """What `Board.make` overwrote (ADR-014). The fullmove number follows from the turn.

    `captured_sq` is where the captured piece stood, which is not `to_sq` for en passant.
    """

    captured: Piece | None
    captured_sq: Square | None
    castling: CastlingRights
    ep_square: Square | None
    halfmove_clock: int
    key: int


class Board:
    """A position that moves are played on. Mutable by design (ADR-006).

    `squares` is indexed by Square, a1 = 0, h8 = 63. `ep_square` follows FEN: set after
    every double pawn push, whether or not a capture is possible; the key is what is
    conditional (ADR-027).
    """

    __slots__ = (
        "squares",
        "turn",
        "castling",
        "ep_square",
        "halfmove_clock",
        "fullmove_number",
        "key",
    )

    def __init__(self, position: Position) -> None:
        self.squares: list[Piece | None] = list(position.placement)
        self.turn = position.turn
        self.castling = position.castling
        self.ep_square = position.ep_square
        self.halfmove_clock = position.halfmove_clock
        self.fullmove_number = position.fullmove_number
        self.key = compute_key(self)

    @classmethod
    def from_fen(cls, text: str) -> Board:
        """Return the board for FEN `text`; InvalidFenError if the text is not valid."""
        return cls(parse_fen(text))

    def to_position(self) -> Position:
        """Return an immutable snapshot of this board."""
        return Position(
            tuple(self.squares),
            self.turn,
            self.castling,
            self.ep_square,
            self.halfmove_clock,
            self.fullmove_number,
        )

    def to_fen(self) -> str:
        """Return the FEN of this board, always six fields."""
        return format_fen(self.to_position())

    def piece_at(self, sq: Square) -> Piece | None:
        """Return the piece on Square `sq`, or None when it is empty."""
        return self.squares[sq]

    def make(self, move: Move) -> UndoRecord:
        """Play `move` and return what `unmake` needs to take it back.

        The move is not validated: it comes from the generator, and a move from outside is
        looked up in the legal list first (ADR-022). Anything else corrupts the board.
        """
        squares = self.squares
        us = self.turn
        from_sq = move.from_sq
        to_sq = move.to_sq
        kind = move.kind
        piece = squares[from_sq]
        undo_castling = self.castling
        undo_ep = self.ep_square
        undo_halfmove = self.halfmove_clock
        undo_key = key = self.key

        if _has_ep_capture(squares, us, undo_ep):
            key ^= _EP_FILE_KEYS[file_of(undo_ep)]

        captured = None
        captured_sq = None
        if kind is MoveKind.EN_PASSANT:
            captured_sq = to_sq - 8 if us is Color.WHITE else to_sq + 8
            captured = squares[captured_sq]
            squares[captured_sq] = None
        elif kind is MoveKind.CAPTURE or kind is MoveKind.PROMOTION:
            captured = squares[to_sq]
            if captured is not None:
                captured_sq = to_sq
        if captured is not None:
            key ^= _PIECE_KEYS[captured.color.value][captured.kind.value][captured_sq]

        placed = piece if kind is not MoveKind.PROMOTION else Piece(us, move.promotion)
        squares[from_sq] = None
        squares[to_sq] = placed
        key ^= _PIECE_KEYS[us.value][piece.kind.value][from_sq]
        key ^= _PIECE_KEYS[us.value][placed.kind.value][to_sq]

        if kind is MoveKind.CASTLE:
            rook_from, rook_to = _CASTLE_ROOK[to_sq]
            rook = squares[rook_from]
            squares[rook_from] = None
            squares[rook_to] = rook
            rook_keys = _PIECE_KEYS[us.value][PieceType.ROOK.value]
            key ^= rook_keys[rook_from] ^ rook_keys[rook_to]

        castling = _update_castling(undo_castling, from_sq, to_sq)
        if castling is not undo_castling:
            key ^= _CASTLING_KEYS[undo_castling.to_index()] ^ _CASTLING_KEYS[castling.to_index()]
            self.castling = castling

        if piece.kind is PieceType.PAWN or captured is not None:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock = undo_halfmove + 1

        them = us.opposite
        self.turn = them
        key ^= _BLACK_TO_MOVE_KEY
        if us is Color.BLACK:
            self.fullmove_number += 1

        ep_square = (from_sq + to_sq) // 2 if kind is MoveKind.DOUBLE_PAWN_PUSH else None
        self.ep_square = ep_square
        if _has_ep_capture(squares, them, ep_square):
            key ^= _EP_FILE_KEYS[file_of(ep_square)]

        self.key = key
        return UndoRecord(captured, captured_sq, undo_castling, undo_ep, undo_halfmove, undo_key)

    def unmake(self, move: Move, undo: UndoRecord) -> None:
        """Take back `move`, which must be the last move made, using its `undo` record."""
        squares = self.squares
        us = self.turn.opposite  # the side that played `move`
        self.turn = us
        if us is Color.BLACK:
            self.fullmove_number -= 1

        from_sq = move.from_sq
        to_sq = move.to_sq
        kind = move.kind
        piece = squares[to_sq] if kind is not MoveKind.PROMOTION else _PAWNS[us.value]
        squares[to_sq] = None
        squares[from_sq] = piece

        if kind is MoveKind.CASTLE:
            rook_from, rook_to = _CASTLE_ROOK[to_sq]
            squares[rook_from] = squares[rook_to]
            squares[rook_to] = None

        if undo.captured is not None:
            squares[undo.captured_sq] = undo.captured

        self.castling = undo.castling
        self.ep_square = undo.ep_square
        self.halfmove_clock = undo.halfmove_clock
        self.key = undo.key


def compute_key(board: Board) -> int:
    """Return the Zobrist key of `board` computed from scratch.

    `Board.key` is kept incrementally; this is the reference it is tested against. The
    counters do not enter the key: repetition ignores them.
    """
    key = 0
    for sq, piece in enumerate(board.squares):
        if piece is not None:
            key ^= _PIECE_KEYS[piece.color.value][piece.kind.value][sq]
    if board.turn is Color.BLACK:
        key ^= _BLACK_TO_MOVE_KEY
    key ^= _CASTLING_KEYS[board.castling.to_index()]
    if _has_ep_capture(board.squares, board.turn, board.ep_square):
        key ^= _EP_FILE_KEYS[file_of(board.ep_square)]
    return key


def _has_ep_capture(squares: list[Piece | None], turn: Color, ep_square: Square | None) -> bool:
    """True when a pawn of `turn` stands beside the pawn that just pushed two squares.

    EP square enters the key only when a capture is possible (ADR-027) - pseudo-legally:
    a pinned capturer or a capture that leaves the king in check still counts.
    """
    if ep_square is None:
        return False
    # The pushed pawn stands one rank past the target, seen from the side that pushed it.
    pushed = ep_square - 8 if turn is Color.WHITE else ep_square + 8
    pawn = _PAWNS[turn.value]
    file = file_of(pushed)
    return (file > 0 and squares[pushed - 1] == pawn) or (file < 7 and squares[pushed + 1] == pawn)


def _update_castling(rights: CastlingRights, from_sq: Square, to_sq: Square) -> CastlingRights:
    """Return `rights` after a move between Squares `from_sq` and `to_sq`.

    The same object comes back when nothing is lost, so make can skip the key update with
    an identity check.
    """
    lost = _RIGHTS_LOST.get(from_sq, ()) + _RIGHTS_LOST.get(to_sq, ())
    changes = {name: False for name in lost if getattr(rights, name)}
    if not changes:
        return rights
    return replace(rights, **changes)
