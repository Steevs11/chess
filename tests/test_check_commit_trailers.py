"""The pure half of tools/check_commit_trailers.py: find_trailers (CONVENTIONS 8, ADR-047).

The tool itself calls git. This file does not: every input is a fixed message written below,
so tests/ keeps no dependency on an external program (CONVENTIONS 5, "Izolacija").
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = REPO_ROOT / "tools" / "check_commit_trailers.py"

# Loaded from its path, the same recipe as tests/test_layers.py: the tool is a script, not a
# package module, and sys.path is left alone.
_spec = importlib.util.spec_from_file_location("check_commit_trailers", TOOL_PATH)
check_commit_trailers = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = check_commit_trailers
_spec.loader.exec_module(check_commit_trailers)
find_trailers = check_commit_trailers.find_trailers

SHA_A = "a" * 40
SHA_B = "b" * 40


class FindTrailersTest(unittest.TestCase):
    def test_find_trailers_message_with_trailer_reports_sha_and_line(self):
        cases = [
            "Co-Authored-By: Someone <someone@example.invalid>",
            "Co-authored-by: Someone <someone@example.invalid>",
            "Claude-Session: 0000",
        ]
        for line in cases:
            with self.subTest(line=line):
                records = [
                    (SHA_A, "docs: clean message\n\nBody without trailers.\n"),
                    (SHA_B, f"feat: something\n\nBody.\n\n{line}\n"),
                ]
                self.assertEqual(find_trailers(records), [(SHA_B, line)])

    def test_find_trailers_message_without_trailer_returns_empty_list(self):
        records = [
            (SHA_A, "docs: clean message\n\nMentions Co-Authored-By: only mid-line.\n"),
            (SHA_B, "fix: another\n"),
        ]
        self.assertEqual(find_trailers(records), [])

    def test_find_trailers_no_records_raises_instead_of_passing(self):
        # An empty history is "the check had no input", never "clean". Returning [] here
        # would let a git call that silently read nothing look like a passing gate.
        with self.assertRaises(ValueError):
            find_trailers([])


if __name__ == "__main__":
    unittest.main()
