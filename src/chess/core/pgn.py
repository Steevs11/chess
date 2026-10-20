"""PGN export: a finished or running game as PGN text. PGN is written here, never read.

The input is the game's moves as SAN strings, already produced by `core.san`; they are
written as given, unchecked. The module knows nothing of the board or the generator.

The text is
  - the header: the seven tags always, in this order: Event, Site, Date, Round, White,
    Black, Result. A tag not given is `?`, Date is `????.??.??`. Result is always the
    `result` argument, and a "Result" key in `tags` is a wrong call (ValueError). Any
    other tags follow the seven in the order given. Each is one line `[Name "value"]`,
    the value escaped `\\` -> `\\\\` first, then `"` -> `\\"`
  - one empty line
  - the move text: tokens are the move number with a dot (`1.`) before each white move,
    the SAN strings, and the result as the last token. A token joins the current line
    when len(line) + 1 + len(token) <= 79, otherwise it starts a new line; the first token
    on a line has no space before it. With no moves only the result is left
  - exactly one "\\n" at the end

`result` is one of "1-0", "0-1", "1/2-1/2", "*"; anything else raises ValueError. There is
no FEN start position, no comments, no variations and no NAGs.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

_RESULTS = ("1-0", "0-1", "1/2-1/2", "*")

# The Seven Tag Roster before Result, which always comes from the `result` argument.
_ROSTER = ("Event", "Site", "Date", "Round", "White", "Black")
_UNKNOWN = {"Date": "????.??.??"}

_MAX_LINE = 79


def format_pgn(moves: Sequence[str], result: str, tags: Mapping[str, str] | None = None) -> str:
    """Return the PGN text of a game: the seven-tag header, an empty line, the move text.

    `moves` are SAN strings in play order, white first, written as given. `result` is one of
    "1-0", "0-1", "1/2-1/2", "*" and is both the Result tag and the last move-text token.
    `tags` fill the roster and add extra tags after it in their own order; a "Result" key
    or any other `result` raises ValueError.
    """
    if result not in _RESULTS:
        raise ValueError(f"result must be one of {', '.join(_RESULTS)}, got {result!r}")
    tags = tags or {}
    if "Result" in tags:
        raise ValueError("the Result tag comes from the result argument, not from tags")

    header = [_tag_line(name, tags.get(name, _UNKNOWN.get(name, "?"))) for name in _ROSTER]
    header.append(_tag_line("Result", result))
    header += [_tag_line(name, value) for name, value in tags.items() if name not in _ROSTER]

    tokens: list[str] = []
    for index, san in enumerate(moves):
        if index % 2 == 0:
            tokens.append(f"{index // 2 + 1}.")
        tokens.append(san)
    tokens.append(result)

    return "\n".join(header) + "\n\n" + "\n".join(_wrap(tokens)) + "\n"


def _tag_line(name: str, value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'[{name} "{escaped}"]'


def _wrap(tokens: list[str]) -> list[str]:
    lines: list[str] = []
    line = ""
    for token in tokens:
        if not line:
            line = token
        elif len(line) + 1 + len(token) <= _MAX_LINE:
            line += " " + token
        else:
            lines.append(line)
            line = token
    lines.append(line)
    return lines
