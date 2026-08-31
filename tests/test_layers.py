"""Enforce the import table in CONVENTIONS section 2 through tools/layer_check.py (ADR-033).

Three claims, and only the first is obvious. The real tree is clean; the tool actually
reports something when the rule is broken; and the table in the document and the table in
the tool still name the same rows (ADR-037.1).

The middle one is the reason this file is long. A checker that silently sees nothing -
wrong import form, import hidden in a function body, relative import never resolved -
passes "the tree is clean" forever and proves nothing.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = REPO_ROOT / "tools" / "layer_check.py"
CONVENTIONS_PATH = REPO_ROOT / "docs" / "CONVENTIONS.md"

# tools/ is a folder of scripts, not a package: it has no __init__.py on purpose, because
# layer_check.py is run as a script and never imported (faza-0.md, task 0.1, question 2).
# So the module is loaded by path - computed from __file__, never from the working
# directory (CONVENTIONS 7). sys.path is left alone; nothing here leaks into other tests.
_spec = importlib.util.spec_from_file_location("layer_check", TOOL_PATH)
layer_check = importlib.util.module_from_spec(_spec)
# Registering before exec_module is the documented importlib recipe, and here it is not
# optional: @dataclass resolves the annotations of a module that uses
# `from __future__ import annotations` through sys.modules[cls.__module__], which is None
# for a module that is not registered. Without this line the tool fails to load.
sys.modules[_spec.name] = layer_check
_spec.loader.exec_module(layer_check)


# Every case is (table row this file falls under, source). The source is text, never a
# file on disk - a test does not touch the disk outside tempfile (CONVENTIONS 5).
ALLOWED = (
    ("core/board.py", "import math"),
    ("core/board.py", "from dataclasses import dataclass"),
    ("core/board.py", "from .types import Piece"),
    ("core/board.py", "from . import types"),
    ("core/board.py", "from chess.core.types import Piece"),
    ("protocol/codec.py", "from chess.core.types import Move"),
    ("protocol/codec.py", "from .messages import Move"),
    ("server/session.py", "from chess.protocol.codec import decode"),
    ("server/session.py", "from chess.core.game import Game"),
    ("server/transport/tcp.py", "import selectors"),
    ("client/net.py", "from chess.protocol.codec import encode"),
    ("client/state.py", "from chess.core.fen import parse_fen"),
    ("client/state.py", "from ..core import fen"),
    ("client/i18n.py", "import json"),
    ("client/render.py", "import pygame"),
    ("client/render.py", "from chess.client.state import ClientState"),
    ("client/scenes/game.py", "import pygame"),
    ("client/scenes/game.py", "from chess.client.render import draw_board"),
    ("tools/perft.py", "import pygame"),
    ("tests/core/test_board.py", "from chess.core.movegen import legal_moves"),
    ("core/__init__.py", '"""Docstring only."""'),
)

FORBIDDEN = (
    # core is the whole point: standard library and nothing else (ADR-002).
    ("core/board.py", "from chess.protocol import codec"),
    ("core/movegen.py", "import pygame"),
    ("core/movegen.py", "import numpy"),  # any PyPI package, not just pygame
    ("core/movegen.py", "from chess.server.lobby import Lobby"),
    # The arrow never turns around.
    ("protocol/codec.py", "from chess.server import lobby"),
    ("protocol/codec.py", "from chess.client import net"),
    ("server/session.py", "from chess.client import net"),
    ("server/session.py", "import pygame"),
    # The boundary that is easiest to cross by accident (ADR-024).
    ("client/state.py", "from chess.core.movegen import legal_moves"),
    ("client/state.py", "from ..core import movegen"),
    ("client/state.py", "from chess.core.rules import is_draw"),
    ("client/state.py", "import pygame"),
    ("client/net.py", "import pygame"),
    ("client/net.py", "from chess.core.fen import parse_fen"),
    ("client/i18n.py", "import pygame"),
    ("client/i18n.py", "from chess.core.types import Piece"),
    ("client/render.py", "from chess.core import rules"),
    ("client/scenes/game.py", "from chess.core.game import Game"),
    # state.py must stay translatable to JavaScript 1:1 (ADR-004), so it may not reach
    # pygame through render.py either.
    ("client/state.py", "from chess.client.render import draw_board"),
    # ADR-037.3
    ("core/__init__.py", "from .types import Piece"),
    ("client/__init__.py", "from chess.protocol import codec"),
)


class RealTreeTest(unittest.TestCase):
    def test_project_tree_has_no_forbidden_imports(self) -> None:
        violations = layer_check.check_tree()
        self.assertEqual([], violations, "\n" + "\n".join(str(v) for v in violations))

    def test_every_source_file_is_covered_by_a_row(self) -> None:
        """A file the table does not describe is not checked - and must not pass quietly."""
        for key, _path in layer_check.iter_source_files():
            with self.subTest(file=key):
                self.assertIsNotNone(layer_check.rule_for(key))

    def test_tree_walk_finds_the_client_files_too(self) -> None:
        """tests/ has no client/ subpackage; the tool walks src/chess, not tests/."""
        keys = {key for key, _ in layer_check.iter_source_files()}
        self.assertIn("client/__init__.py", keys)
        self.assertIn("client/scenes/__init__.py", keys)


class RuleEnforcementTest(unittest.TestCase):
    def test_allowed_imports_are_not_reported(self) -> None:
        for key, source in ALLOWED:
            with self.subTest(file=key, source=source):
                self.assertEqual([], layer_check.check_source(key, source))

    def test_forbidden_imports_are_reported(self) -> None:
        for key, source in FORBIDDEN:
            with self.subTest(file=key, source=source):
                violations = layer_check.check_source(key, source)
                self.assertEqual(1, len(violations), f"expected exactly one finding: {violations}")
                self.assertEqual(1, violations[0].line)

    def test_violation_names_the_import_it_rejected(self) -> None:
        (violation,) = layer_check.check_source(
            "client/state.py", "from chess.core.movegen import legal_moves"
        )
        self.assertEqual("chess.core.movegen.legal_moves", violation.imported)
        self.assertIn("client/state.py:1", str(violation))


class ImportFormTest(unittest.TestCase):
    """Every spelling of the same forbidden import has to be seen."""

    FORMS = (
        "import pygame",
        "import pygame.display",
        "import pygame as pg",
        "import pygame.display as display",
        "from pygame import Surface",
        "from pygame.display import flip",
        "def draw():\n    import pygame\n",  # hidden in a function body
        "if True:\n    import pygame\n",
        "try:\n    import pygame\nexcept ImportError:\n    pygame = None\n",
    )

    def test_every_import_form_is_seen(self) -> None:
        for source in self.FORMS:
            with self.subTest(source=source):
                self.assertEqual(1, len(layer_check.check_source("core/movegen.py", source)))

    def test_relative_imports_are_resolved_before_they_are_judged(self) -> None:
        cases = (
            # (file, source, expected absolute name)
            ("core/board.py", "from . import types", "chess.core.types"),
            ("core/board.py", "from .types import Piece", "chess.core.types.Piece"),
            ("client/state.py", "from ..core import movegen", "chess.core.movegen"),
            ("client/scenes/game.py", "from ...core import game", "chess.core.game"),
        )
        for key, source, expected in cases:
            with self.subTest(file=key, source=source):
                self.assertEqual([(1, expected)], layer_check.imported_names(key, source))

    def test_relative_import_that_escapes_the_package_is_reported(self) -> None:
        violations = layer_check.check_source("core/board.py", "from ... import something")
        self.assertEqual(1, len(violations))
        self.assertIn("escapes", violations[0].message)


class UncoveredFileTest(unittest.TestCase):
    """A file no row describes is a finding, not silence and not a traceback (ADR-037.2)."""

    def test_file_outside_the_table_is_reported(self) -> None:
        violations = layer_check.check_source("ai/engine.py", "import os")
        self.assertEqual(1, len(violations))
        self.assertIn(layer_check.UNCOVERED, violations[0].message)

    def test_unparsable_file_is_reported_instead_of_raising(self) -> None:
        violations = layer_check.check_source("core/board.py", "def broken(:\n")
        self.assertEqual(1, len(violations))
        self.assertIn("parse", violations[0].message)


class TableBindingTest(unittest.TestCase):
    """The document is the source of truth; RULES is a transcription (ADR-037.1)."""

    @staticmethod
    def rows_from_conventions() -> set[str]:
        text = CONVENTIONS_PATH.read_text(encoding="utf-8")
        start = text.index("### Tabela dozvoljenih uvoza")
        block = text[start : text.index("###", start + 3)]
        rows = set()
        for raw in block.splitlines():
            line = raw.strip()
            if not line.startswith("|"):
                continue
            cell = line.split("|")[1].strip().strip("*").strip().strip("`")
            if cell == "Modul" or set(cell) <= set("-: "):  # header and separator rows
                continue
            rows.add(cell)
        return rows

    def test_parser_finds_the_table(self) -> None:
        """A parser that quietly matches nothing would make the test below always pass."""
        self.assertGreater(len(self.rows_from_conventions()), 5)

    def test_every_row_in_conventions_has_a_rule(self) -> None:
        self.assertEqual(self.rows_from_conventions(), set(layer_check.RULES))


if __name__ == "__main__":
    unittest.main()
