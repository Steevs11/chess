"""User-facing text, looked up by key (ADR-010, CONVENTIONS 7).

This module is translated 1:1 into JavaScript in task 4.7, so every choice here is
made twice: once for Python and once for a language that will not have **kwargs,
str.format or Python's str(). Hence a dict of string parameters, and the {{name}}
placeholder syntax - deliberately one that no language implements on its own, so
neither side can quietly grow features the other lacks (ADR-040).

The contract is split in two on purpose. load() is where bad data is refused, and it
is refused loudly: a BOM, broken JSON or a duplicated key all raise ValueError with an
English message aimed at whoever is holding the file. t() runs after that, works only
with what load() let through, and never raises on catalog content - a missing key or a
missing parameter shows up on the screen instead, because a game that loses its whole
screen over one translation is worse than a game showing a key. What t() does raise on
is a wrong call: t() before load(), or a parameter that is not a string. That is a bug
at the call site, not bad data (ADR-040).

Exceptions carry English text for a programmer; user-facing text only ever comes out of
the catalog (CONVENTIONS 6, ADR-010). Log messages stay ASCII - the Windows console is
not UTF-8 and dies on the Serbian diacritics (CONVENTIONS 7). So does this file: nothing
in it, comments included, is written outside ASCII.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# i18n.py -> client -> chess -> src -> repository root. Four .parent, one per level;
# the example in CONVENTIONS 7 has three because it is written for src/chess/<module>.py.
DEFAULT_PATH = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "i18n" / "sr.json"

# A literal character class, not \w: \w is Unicode in Python and ASCII in JavaScript,
# so the same pattern would accept different names on the two sides (ADR-040).
_PLACEHOLDER = re.compile(r"\{\{([a-z][a-z0-9_]*)\}\}")

# The BOM as a code point. Written as chr() and not as an escape sequence because an
# escape can be silently rewritten into the character itself by an editor or a tool,
# and a literal BOM is invisible in both the file and the diff.
_BOM = chr(0xFEFF)

# None means load() has not run yet - a state that exists only before the first call.
_catalog: dict[str, str] | None = None

# Keys already reported as missing. Cleared by load(), so it belongs to the catalog and
# not to the module: a reloaded catalog that still lacks the key has to say so again.
_reported: set[str] = set()


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Build the dict json.load would build, but refuse a repeated key.

    Plain JSON parsing keeps the last of two identical keys and says nothing, so a
    translation could be overwritten by a merge and never be seen again.
    """
    catalog: dict[str, object] = {}
    for key, value in pairs:
        if key in catalog:
            raise ValueError(
                f"duplicate key {key!r} in the catalog. JSON keeps the last one and says "
                f"nothing, so the entry above it would be lost without a trace."
            )
        catalog[key] = value
    return catalog


def load(path: Path = DEFAULT_PATH) -> None:
    """Read the catalog at `path` and make it the one t() serves.

    No language is named here on purpose: choosing between sr.json and en.json is a
    phase 4 decision and this signature does not close it.

    Raises ValueError if the file has a BOM, is not valid JSON, or repeats a key.
    """
    text = path.read_text(encoding="utf-8")
    if text.startswith(_BOM):
        raise ValueError(
            f"{path} starts with a UTF-8 BOM (U+FEFF). The catalog has to be UTF-8 "
            f"without a BOM - re-save it as 'UTF-8', not 'UTF-8 with BOM'. Reading it with "
            f"utf-8-sig would hide the BOM here and leave it in the repository for the web "
            f"client to trip over (ADR-040)."
        )

    catalog = json.loads(text, object_pairs_hook=_reject_duplicate_keys)

    # Rebound only after parsing succeeds: a broken file leaves the old catalog in place.
    global _catalog
    _catalog = catalog
    _reported.clear()


def t(key: str, params: dict[str, str] | None = None) -> str:
    """Return the text for `key`, with every {{name}} replaced from `params`.

    Parameters are strings and are used verbatim - t() never calls str(). Python and
    JavaScript disagree about what that would produce (str(1.0) is "1.0",
    String(1.0) is "1"), so formatting stays at the call site, in each language by its
    own rules (ADR-040).

    Never raises on catalog content: an unknown key comes back as the key itself and a
    parameter that was not supplied stays visible as {{name}}. Both also log a WARNING -
    a second channel next to the symptom on screen, never the only one.

    Raises RuntimeError if load() has not run, and TypeError if a parameter is not a
    string. Both are wrong calls from our own code, not bad data.
    """
    if params is not None:
        for name, value in params.items():
            if not isinstance(value, str):
                raise TypeError(
                    f"parameter {name!r} for key {key!r} is {type(value).__name__}, not str. "
                    f"t() does not call str() - format the value at the call site (ADR-040)."
                )

    if _catalog is None:
        raise RuntimeError("i18n.load() has to be called before t()")

    if key not in _catalog:
        if key not in _reported:
            _reported.add(key)
            logger.warning("i18n: no such key in the catalog: %s", key)
        return key

    supplied = params or {}
    wanted: set[str] = set()
    missing: set[str] = set()

    def _substitute(match: re.Match[str]) -> str:
        name = match.group(1)
        wanted.add(name)
        if name in supplied:
            return supplied[name]
        missing.add(name)
        return match.group(0)

    text = _PLACEHOLDER.sub(_substitute, _catalog[key])

    for name in sorted(missing):
        logger.warning("i18n: key %s has no value for placeholder %s", key, name)
    for name in sorted(set(supplied) - wanted):
        logger.warning("i18n: key %s was given an unused parameter %s", key, name)

    return text
