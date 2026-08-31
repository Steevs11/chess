"""Enforce the import table in CONVENTIONS section 2 (ADR-033).

Parses every .py file under src/chess, tools and tests with `ast` and reports each import
the table does not allow. Runs as a script - exit code 1 on any finding - and as a test
(tests/test_layers.py), so the phase checkpoint fails when the rule is broken.

The table in docs/CONVENTIONS.md section 2 is the source of truth (CONVENTIONS 1). RULES
below is a transcription of it, and tests/test_layers.py binds the two by asserting that
the row names match (ADR-037.1). When the two disagree, the document is right and this
file is wrong.

Transcribed table, row for row:

    | Module            | May import                                |
    |-------------------|-------------------------------------------|
    | */__init__.py     | stdlib only                               |
    | core/*            | stdlib only                               |
    | protocol/*        | stdlib, core                              |
    | server/*          | stdlib, core, protocol                    |
    | client/net.py     | stdlib, protocol                          |
    | client/state.py   | stdlib, protocol, core.types, core.fen    |
    | client/i18n.py    | stdlib                                    |
    | client/render.py  | everything above + pygame                 |
    | client/scenes/*   | everything above + pygame                 |
    | tools/*           | everything                                |
    | tests/*           | everything                                |

Every row allows the standard library, so "stdlib" is not a field of Rule - it is the
floor. "Everything above" is read as: what the client rows above may import, plus those
modules themselves, which keeps the import direction inside client/ pointing one way
(i18n <- state <- render <- scenes). Written down in CONVENTIONS 2.

Known limit, and no ast tool can do better: only static imports are visible.
`importlib.import_module("pygame")` is not seen.
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_ROOT = REPO_ROOT / "src" / "chess"
EXTRA_ROOTS = (REPO_ROOT / "tools", REPO_ROOT / "tests")

UNCOVERED = "not covered by the import table"
ESCAPES = "<relative import escapes the package>"


@dataclass(frozen=True, slots=True)
class Rule:
    """One row of the table.

    `project` and `third_party` list what the row allows on top of the standard library.
    Entries in `project` are module prefixes without the `chess.` part: "core" allows all
    of core, "core.types" allows that module alone.
    """

    project: tuple[str, ...] = ()
    third_party: tuple[str, ...] = ()
    unrestricted: bool = False


# What the pygame-free client modules may reach into (CONVENTIONS 3, ADR-024): the client
# reads the position, it never decides legality.
_CLIENT_CORE = ("protocol", "core.types", "core.fen")

RULES: dict[str, Rule] = {
    "*/__init__.py": Rule(),  # a package marker imports nothing from the project (ADR-037.3)
    "core/*": Rule(project=("core",)),
    "protocol/*": Rule(project=("core", "protocol")),
    "server/*": Rule(project=("core", "protocol", "server")),
    "client/net.py": Rule(project=("protocol",)),
    "client/state.py": Rule(project=_CLIENT_CORE),
    "client/i18n.py": Rule(),
    "client/render.py": Rule(
        project=(*_CLIENT_CORE, "client.i18n", "client.net", "client.state"),
        third_party=("pygame",),
    ),
    "client/scenes/*": Rule(
        project=(*_CLIENT_CORE, "client.i18n", "client.net", "client.state", "client.render"),
        third_party=("pygame",),
    ),
    "tools/*": Rule(unrestricted=True),
    "tests/*": Rule(unrestricted=True),
}


@dataclass(frozen=True, slots=True)
class Violation:
    """One rejected import, or one file the table does not describe."""

    path: str
    line: int
    imported: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


def rule_for(key: str) -> Rule | None:
    """Return the row that governs `key`, or None when the table does not cover it.

    `key` is the path a row names: relative to src/chess for package files
    ("client/scenes/game.py"), relative to the repository root for the rest
    ("tools/perft.py"). Precedence is exact row, then */__init__.py, then the longest
    prefix row - the same order CONVENTIONS 2 states.
    """
    if key in RULES:
        return RULES[key]
    if key.rsplit("/", 1)[-1] == "__init__.py":
        return RULES["*/__init__.py"]
    best: Rule | None = None
    best_length = -1
    for pattern, rule in RULES.items():
        prefix = pattern[:-1]
        if pattern.endswith("/*") and key.startswith(prefix) and len(prefix) > best_length:
            best, best_length = rule, len(prefix)
    return best


def _package_of(key: str) -> tuple[str, ...]:
    """Return the dotted package a file lives in, as parts, for relative imports.

    Package files are inside `chess`; tools/ and tests/ are their own top level.
    """
    parts = tuple(key.split("/")[:-1])
    if key.startswith(("tools/", "tests/")):
        return parts
    return ("chess", *parts)


def _resolve(package: tuple[str, ...], level: int, module: str | None) -> str | None:
    """Return what `from ... import` points at, or None when it escapes the package.

    Turns `from ..core import fen` written in client/state.py into `chess.core`. Level 0
    is an absolute import and passes through unchanged.
    """
    if level == 0:
        return module
    if level > len(package):
        return None
    base = package[: len(package) - (level - 1)]
    return ".".join((*base, module) if module else base)


def _names_from_tree(tree: ast.AST, package: tuple[str, ...]) -> list[tuple[int, str]]:
    """Collect (line, absolute dotted name) for every import in the file.

    `ast.walk`, not `tree.body`: an import inside a function body is the same dependency
    and must not slip through. `from x import y` yields "x.y" - whether y is a submodule
    or a name in x does not matter, because rules match on prefixes either way.
    """
    names: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = _resolve(package, node.level, node.module)
            if base is None:
                names.append((node.lineno, ESCAPES))
                continue
            names.extend((node.lineno, f"{base}.{alias.name}") for alias in node.names)
    return names


def imported_names(key: str, source: str) -> list[tuple[int, str]]:
    """Every import in `source`, as (line, absolute dotted name). Relative imports resolved."""
    return _names_from_tree(ast.parse(source, filename=key), _package_of(key))


def _rejection_reason(rule: Rule, name: str) -> str | None:
    """Return why `name` is not allowed under `rule`, or None when it is allowed."""
    if rule.unrestricted:
        return None
    if name == ESCAPES:
        return "relative import escapes the package"
    top, _, rest = name.partition(".")
    if top == "chess":
        if any(rest == p or rest.startswith(f"{p}.") for p in rule.project):
            return None
        return f"may not import {name} (CONVENTIONS 2)"
    if top in sys.stdlib_module_names:
        return None
    if top in rule.third_party:
        return None
    return f"may not import third-party {name} (CONVENTIONS 2)"


def check_source(key: str, source: str) -> list[Violation]:
    """Check one file's text against the row that governs `key`.

    Takes text rather than a path so the rules can be tested on sources that never exist
    on disk (CONVENTIONS 5, isolation).
    """
    rule = rule_for(key)
    if rule is None:
        # Silence here would mean a whole new package is checked by nobody, and nobody
        # would notice (ADR-037.2). Adding a module forces adding a row.
        return [Violation(key, 0, "", f"{UNCOVERED} (CONVENTIONS 2) - add a row for it")]
    try:
        tree = ast.parse(source, filename=key)
    except SyntaxError as exc:
        return [Violation(key, exc.lineno or 0, "", f"cannot parse: {exc.msg}")]

    violations = []
    for line, name in _names_from_tree(tree, _package_of(key)):
        reason = _rejection_reason(rule, name)
        if reason is not None:
            violations.append(Violation(key, line, name, reason))
    return violations


def iter_source_files() -> list[tuple[str, Path]]:
    """Every .py file the table has to account for, as (table key, path).

    The key is the path a row names: relative to src/chess for package files, relative to
    the repository root for tools/ and tests/.
    """
    found: list[tuple[str, Path]] = []
    for root in (PACKAGE_ROOT, *EXTRA_ROOTS):
        base = PACKAGE_ROOT if root == PACKAGE_ROOT else REPO_ROOT
        for path in root.rglob("*.py"):
            if "__pycache__" not in path.parts:
                found.append((path.relative_to(base).as_posix(), path))
    return sorted(found)


def check_tree() -> list[Violation]:
    """Check the whole project. Paths in the result are relative to the repository root."""
    violations: list[Violation] = []
    for key, path in iter_source_files():
        source = path.read_text(encoding="utf-8")
        display = path.relative_to(REPO_ROOT).as_posix()
        violations.extend(replace(v, path=display) for v in check_source(key, source))
    return violations


def main() -> int:
    violations = check_tree()
    for violation in violations:
        print(violation)
    if violations:
        print(f"{len(violations)} violation(s) of the import table in CONVENTIONS 2")
        return 1
    print(f"layer check clean: {len(iter_source_files())} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
