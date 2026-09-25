"""FEN text to a Position and back.

A Position is the six FEN fields as values, nothing more. This module does not know that
Board exists (CONVENTIONS 2): the client reads positions through it without importing
anything that could decide legality (ADR-024).

`parse_fen` rejects text that is malformed or describes a position no board can hold -
not exactly one king per color, a pawn on the first or last rank, a castling right
without its king and rook at home. Whether the position is reachable, or whether the side
not to move is in check, is not checked here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from chess.core.types import (
    A1,
    A8,
    CASTLING_NONE,
    E1,
    E8,
    H1,
    H8,
    CastlingRights,
    Color,
    InvalidFenError,
    Piece,
    PieceType,
    Square,
    from_algebraic,
    rank_of,
    square,
    to_algebraic,
)

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

_PIECE_CHARS = "pnbrqkPNBRQK"
_CASTLING_ORDER = "KQkq"
_COUNTER = re.compile(r"-?[0-9]+")

# (right, king square, rook square, color) - what each castling right needs at home.
_CASTLING_HOMES = (
    ("white_kingside", E1, H1, Color.WHITE),
    ("white_queenside", E1, A1, Color.WHITE),
    ("black_kingside", E8, H8, Color.BLACK),
    ("black_queenside", E8, A8, Color.BLACK),
)


@dataclass(frozen=True, slots=True)
class Position:
    """The six FEN fields as values. `placement` is indexed by Square, a1 = 0, h8 = 63."""

    placement: tuple[Piece | None, ...]
    turn: Color
    castling: CastlingRights
    ep_square: Square | None
    halfmove_clock: int
    fullmove_number: int


def parse_fen(text: str) -> Position:
    """Parse a FEN string of six fields, or of four with the counters defaulting to 0 and 1.

    Raises InvalidFenError naming the bad field and its value.
    """
    fields = text.split()
    if len(fields) not in (4, 6):
        raise InvalidFenError(f"FEN must have 4 or 6 fields, got {len(fields)}: {text!r}")
    if len(fields) == 4:
        # CPW writes some test positions, Kiwipete among them, without the counters.
        fields += ["0", "1"]
    placement_text, turn_text, castling_text, ep_text, halfmove_text, fullmove_text = fields

    placement = _parse_placement(placement_text)
    turn = _parse_turn(turn_text)
    castling = _parse_castling(castling_text)
    ep_square = _parse_ep(ep_text, turn)
    halfmove_clock = _parse_counter("halfmove clock", halfmove_text, 0)
    fullmove_number = _parse_counter("fullmove number", fullmove_text, 1)
    _check_structure(placement, castling)
    return Position(placement, turn, castling, ep_square, halfmove_clock, fullmove_number)


def format_fen(position: Position) -> str:
    """Return the FEN of `position`, always six fields, empty squares as canonical digits."""
    ranks = []
    for rank in range(7, -1, -1):
        row = ""
        empty = 0
        for file in range(8):
            piece = position.placement[square(file, rank)]
            if piece is None:
                empty += 1
                continue
            if empty:
                row += str(empty)
                empty = 0
            row += _letter(piece)
        if empty:
            row += str(empty)
        ranks.append(row)

    castling = position.castling
    flags = (
        castling.white_kingside,
        castling.white_queenside,
        castling.black_kingside,
        castling.black_queenside,
    )
    castling_text = "".join(c for c, allowed in zip(_CASTLING_ORDER, flags, strict=True) if allowed)
    ep_text = "-" if position.ep_square is None else to_algebraic(position.ep_square)
    return " ".join(
        (
            "/".join(ranks),
            "w" if position.turn is Color.WHITE else "b",
            castling_text or "-",
            ep_text,
            str(position.halfmove_clock),
            str(position.fullmove_number),
        )
    )


def _piece_from_letter(char: str) -> Piece:
    """Uppercase is white. The explicit set check matters: KELVIN SIGN lowercases to "k"."""
    if char not in _PIECE_CHARS:
        raise InvalidFenError(f"FEN placement has unknown piece letter {char!r}")
    color = Color.WHITE if char.isupper() else Color.BLACK
    return Piece(color, PieceType.from_letter(char.lower()))


def _letter(piece: Piece) -> str:
    letter = piece.kind.letter
    return letter.upper() if piece.color is Color.WHITE else letter


def _parse_placement(text: str) -> tuple[Piece | None, ...]:
    rows = text.split("/")
    if len(rows) != 8:
        raise InvalidFenError(f"FEN placement must have 8 ranks, got {len(rows)}: {text!r}")
    placement: list[Piece | None] = [None] * 64
    for index, row in enumerate(rows):
        rank = 7 - index  # FEN lists the eighth rank first
        file = 0
        for char in row:
            if char in "12345678":
                file += int(char)
                continue
            piece = _piece_from_letter(char)
            if file < 8:
                placement[square(file, rank)] = piece
            file += 1
        if file != 8:
            raise InvalidFenError(f"FEN rank {rank + 1} must cover 8 squares, got {file}: {row!r}")
    return tuple(placement)


def _parse_turn(text: str) -> Color:
    if text == "w":
        return Color.WHITE
    if text == "b":
        return Color.BLACK
    raise InvalidFenError(f"FEN side to move must be 'w' or 'b', got {text!r}")


def _parse_castling(text: str) -> CastlingRights:
    if text == "-":
        return CASTLING_NONE
    last = -1
    for char in text:
        index = _CASTLING_ORDER.find(char)
        # Strictly increasing order rejects unknown letters, repeats and "qK" at once.
        if index <= last:
            raise InvalidFenError(
                f"FEN castling must be '-' or letters of 'KQkq' in that order, got {text!r}"
            )
        last = index
    return CastlingRights("K" in text, "Q" in text, "k" in text, "q" in text)


def _parse_ep(text: str, turn: Color) -> Square | None:
    if text == "-":
        return None
    try:
        ep_square = from_algebraic(text)
    except ValueError:
        raise InvalidFenError(f"FEN en passant must be '-' or a square, got {text!r}") from None
    # The target is behind the pawn that just moved: rank 6 when white is to move, rank 3
    # when black is.
    expected_rank = 5 if turn is Color.WHITE else 2
    if rank_of(ep_square) != expected_rank:
        raise InvalidFenError(
            f"FEN en passant with {'white' if turn is Color.WHITE else 'black'} to move "
            f"must be on rank {expected_rank + 1}, got {text!r}"
        )
    return ep_square


def _parse_counter(name: str, text: str, minimum: int) -> int:
    # int() alone would also take "+1", "1_0" and non-ASCII digits.
    if not _COUNTER.fullmatch(text):
        raise InvalidFenError(f"FEN {name} must be an integer, got {text!r}")
    value = int(text)
    if value < minimum:
        raise InvalidFenError(f"FEN {name} must be at least {minimum}, got {text!r}")
    return value


def _check_structure(placement: tuple[Piece | None, ...], castling: CastlingRights) -> None:
    for color in Color:
        king = Piece(color, PieceType.KING)
        count = placement.count(king)
        if count != 1:
            name = color.name.lower()
            raise InvalidFenError(f"FEN must have exactly one {name} king, got {count}")
    for sq in (*range(0, 8), *range(56, 64)):
        piece = placement[sq]
        if piece is not None and piece.kind is PieceType.PAWN:
            raise InvalidFenError(f"FEN has a pawn on {to_algebraic(sq)}")
    for right, king_sq, rook_sq, color in _CASTLING_HOMES:
        if not getattr(castling, right):
            continue
        if placement[king_sq] != Piece(color, PieceType.KING):
            raise InvalidFenError(f"FEN castling {right} needs the king on {to_algebraic(king_sq)}")
        if placement[rook_sq] != Piece(color, PieceType.ROOK):
            raise InvalidFenError(f"FEN castling {right} needs a rook on {to_algebraic(rook_sq)}")
