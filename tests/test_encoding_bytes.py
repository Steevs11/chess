"""No file matching assets/**/*.json, src/**/*.py or docs/**/*.md contains the bytes EF BB BF.

The check runs over Path.read_bytes(); decoded text is never used (CONVENTIONS 7, ADR-047).
The claim this test holds is recorded in docs/faze/faza-0.md, section 0.9.

The domain is path and extension, not the git index, so this test calls no external program.
Generated files (__pycache__, *.egg-info) and binary assets (PNG, TTF) fall outside it by
construction: binary content can carry these three bytes by chance, which has nothing to do
with the fault from task 0.5. docs/ is inside it because that fault also hit the file that
described it.
"""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Built from integers, never from an escape in a literal: the write tool decoded such an
# escape into the character itself in task 0.5, and a check spelled that way can be broken by
# the same fault it looks for.
BOM = bytes((0xEF, 0xBB, 0xBF))

PATTERNS = ("assets/**/*.json", "src/**/*.py", "docs/**/*.md")

# Each pattern proves on its own that it is not empty. A named file where one is known, and
# "at least one" otherwise - no file count as a threshold, because a count stays silent when
# it is passed.
REQUIRED = "assets/i18n/sr.json"


def collect(pattern: str) -> list[Path]:
    return sorted(path for path in REPO_ROOT.glob(pattern) if path.is_file())


class EncodingBytesTest(unittest.TestCase):
    def test_every_pattern_matches_files_and_catalog_is_among_them(self):
        for pattern in PATTERNS:
            with self.subTest(pattern=pattern):
                self.assertTrue(
                    collect(pattern),
                    f"{pattern} matches no file. The BOM check had no input for it, which "
                    f"is not the same as clean: either the tree moved or the scan stopped "
                    f"seeing it.",
                )
        self.assertIn(
            REPO_ROOT / REQUIRED,
            collect("assets/**/*.json"),
            f"{REQUIRED} is not among the files the BOM check reads. It is the file the "
            f"fault from task 0.5 hit; a scan that misses it checks nothing that matters.",
        )

    def test_no_matched_file_contains_a_byte_order_mark(self):
        files = [path for pattern in PATTERNS for path in collect(pattern)]
        self.assertTrue(files, "no file matched any pattern; the check had no input.")
        for path in files:
            offset = path.read_bytes().find(BOM)
            with self.subTest(path=path.relative_to(REPO_ROOT).as_posix()):
                self.assertEqual(
                    offset,
                    -1,
                    f"{path.relative_to(REPO_ROOT).as_posix()} contains the bytes "
                    f"{BOM.hex(' ').upper()} at byte offset {offset}. Read as bytes, not "
                    f"decoded, so the finding holds even where decoding would hide it "
                    f"(CONVENTIONS 7).",
                )


if __name__ == "__main__":
    unittest.main()
