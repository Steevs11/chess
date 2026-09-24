"""Value types every other core module is built on: squares, pieces, moves, castling rights.

A square is a plain int (ADR-013): perft visits millions of nodes and an object per
square is too expensive. Functions that take one say so in their signature and docstring.

Bad text or an out-of-range argument raises ValueError: that is a wrong call, not a chess
error. The boundary (protocol codec, CLI client) checks input before it calls into core,
so the check is not written twice (CONVENTIONS 6).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

Square = int  # 0-63, a1 = 0, h8 = 63, sq = rank * 8 + file

FILE_NAMES = "abcdefgh"
RANK_NAMES = "12345678"

A1, B1, C1, D1, E1, F1, G1, H1 = range(0, 8)
A2, B2, C2, D2, E2, F2, G2, H2 = range(8, 16)
A3, B3, C3, D3, E3, F3, G3, H3 = range(16, 24)
A4, B4, C4, D4, E4, F4, G4, H4 = range(24, 32)
A5, B5, C5, D5, E5, F5, G5, H5 = range(32, 40)
A6, B6, C6, D6, E6, F6, G6, H6 = range(40, 48)
A7, B7, C7, D7, E7, F7, G7, H7 = range(48, 56)
A8, B8, C8, D8, E8, F8, G8, H8 = range(56, 64)


def file_of(sq: Square) -> int:
    """Return the file (0 = a, 7 = h) of Square `sq`. The range is not checked."""
    return sq & 7


def rank_of(sq: Square) -> int:
    """Return the rank (0 = first, 7 = eighth) of Square `sq`. The range is not checked."""
    return sq >> 3


def square(file: int, rank: int) -> Square:
    """Return the Square at `file` and `rank`, both 0-7. The range is not checked."""
    return rank * 8 + file


def to_algebraic(sq: Square) -> str:
    """Return the name of Square `sq`, e.g. 28 -> "e4"; ValueError outside 0-63."""
    if not 0 <= sq < 64:
        raise ValueError(f"square index must be 0-63, got {sq}")
    return FILE_NAMES[sq & 7] + RANK_NAMES[sq >> 3]


def from_algebraic(text: str) -> Square:
    """Return the Square named by `text`: exactly a lowercase file a-h and a rank 1-8.

    Anything else, "E4" and "e44" included, raises ValueError.
    """
    # The length comes first: "" is a substring of every string.
    if len(text) != 2 or text[0] not in FILE_NAMES or text[1] not in RANK_NAMES:
        raise ValueError(f"square must be a file a-h and a rank 1-8, got {text!r}")
    return FILE_NAMES.index(text[0]) + 8 * RANK_NAMES.index(text[1])


class Color(Enum):
    """Side to move. Values index per-color tables (Zobrist keys, piece lists)."""

    WHITE = 0
    BLACK = 1

    @property
    def opposite(self) -> Color:
        """The other color."""
        return Color.BLACK if self is Color.WHITE else Color.WHITE


_PIECE_LETTERS = "pnbrqk"


class PieceType(Enum):
    """Kind of piece, colorless. Values index per-piece tables."""

    PAWN = 0
    KNIGHT = 1
    BISHOP = 2
    ROOK = 3
    QUEEN = 4
    KING = 5

    @property
    def letter(self) -> str:
        """Lowercase letter of this piece type, as UCI, FEN and SAN spell it: p n b r q k."""
        return _PIECE_LETTERS[self.value]

    @classmethod
    def from_letter(cls, letter: str) -> PieceType:
        """Return the piece type for a single lowercase `letter`; ValueError otherwise."""
        if len(letter) != 1 or letter not in _PIECE_LETTERS:
            raise ValueError(f"piece letter must be one of {_PIECE_LETTERS!r}, got {letter!r}")
        return cls(_PIECE_LETTERS.index(letter))


@dataclass(frozen=True, slots=True)
class Piece:
    """A piece of one color. Data only; how it moves is the generator's business."""

    color: Color
    kind: PieceType


class MoveKind(Enum):
    """What a move does on the board; make and unmake branch on it (ADR-022)."""

    NORMAL = 0
    CAPTURE = 1
    DOUBLE_PAWN_PUSH = 2
    EN_PASSANT = 3
    CASTLE = 4
    PROMOTION = 5


PROMOTION_PIECES = (PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT)


@dataclass(frozen=True, slots=True)
class Move:
    """A move from Square `from_sq` to Square `to_sq`, with an optional promotion piece.

    Identity is (from_sq, to_sq, promotion). `kind` is derived data the generator fills
    in from the position; it takes no part in equality or hashing because a move off the
    wire (`from_uci`) cannot know it. A move from outside is looked up in the list of
    legal moves and the generated instance is the one executed:
    `legal_moves[legal_moves.index(wire)]` (ADR-022).

    `promotion` is set exactly when `kind` is PROMOTION, and is one of PROMOTION_PIECES;
    anything else raises ValueError. A promotion that captures is PROMOTION: whether a
    move captures is known to the board, not to the move.
    """

    from_sq: Square
    to_sq: Square
    kind: MoveKind = field(default=MoveKind.NORMAL, compare=False)
    promotion: PieceType | None = None

    def __post_init__(self) -> None:
        if (self.promotion is not None) != (self.kind is MoveKind.PROMOTION):
            squares = to_algebraic(self.from_sq) + to_algebraic(self.to_sq)
            raise ValueError(
                f"promotion {self.promotion} does not match kind {self.kind} in move {squares}"
            )
        if self.promotion is not None and self.promotion not in PROMOTION_PIECES:
            squares = to_algebraic(self.from_sq) + to_algebraic(self.to_sq)
            raise ValueError(f"cannot promote to {self.promotion} in move {squares}")

    @classmethod
    def from_uci(cls, text: str) -> Move:
        """Parse a lowercase UCI move: "e2e4", or "e7e8q" with a promotion letter.

        With a letter the move is PROMOTION, without it NORMAL - the real kind comes from
        the legal move this one is looked up in. Bad text raises ValueError.
        """
        if len(text) not in (4, 5):
            raise ValueError(f"UCI move must be 4 or 5 characters, got {text!r}")
        from_sq = from_algebraic(text[0:2])
        to_sq = from_algebraic(text[2:4])
        if len(text) == 4:
            return cls(from_sq, to_sq)
        return cls(from_sq, to_sq, MoveKind.PROMOTION, PieceType.from_letter(text[4]))

    def to_uci(self) -> str:
        """Return the UCI spelling of this move; the inverse of `from_uci`."""
        text = to_algebraic(self.from_sq) + to_algebraic(self.to_sq)
        return text if self.promotion is None else text + self.promotion.letter


@dataclass(frozen=True, slots=True)
class CastlingRights:
    """Which castlings are still allowed. Losing a right is `dataclasses.replace`."""

    white_kingside: bool
    white_queenside: bool
    black_kingside: bool
    black_queenside: bool

    def to_index(self) -> int:
        """Return 0-15 in FEN order, K = 1, Q = 2, k = 4, q = 8; indexes Zobrist keys."""
        return (
            self.white_kingside
            | self.white_queenside << 1
            | self.black_kingside << 2
            | self.black_queenside << 3
        )


CASTLING_ALL = CastlingRights(True, True, True, True)
CASTLING_NONE = CastlingRights(False, False, False, False)


class ChessError(Exception):
    """Base of every error core raises about chess itself (CONVENTIONS 6)."""


class IllegalMoveError(ChessError):
    """A move that is not legal in the position."""


class InvalidFenError(ChessError):
    """A FEN string that does not describe a valid position."""


class InvalidSanError(ChessError):
    """A SAN string that names no legal move, or more than one."""
