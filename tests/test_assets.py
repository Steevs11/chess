"""Check that the third-party pieces on disk are the ones LICENSE.txt claims (ADR-039).

assets/pieces/LICENSE.txt records a sha1 per SVG original. That is a verifiable
claim, and it holds only as long as nothing rewrites the bytes between the commit
and the working tree - which is exactly what core.autocrlf=true does on Windows,
turning LF into CRLF on checkout. .gitattributes switches that off for these paths.

The failure happens on someone else's machine, right after `git clone`. That is why
this is a test and not a tool in tools/: at that moment the test suite runs and no
generator does. The mirror-image case is ADR-038, where the failure can only happen
while rasterizing, so the rasterizer checks its own output instead.

The claim about .gitattributes is what turns a symptom into a diagnosis. "sha1
mismatch" tells a fresh cloner nothing; naming the cause tells them what to do.

The font checks are second-order and rest on a weaker argument. *.ttf is declared
binary, so end-of-line conversion cannot reach the font files at all - the failure
mode above does not exist for them. What is being guarded is slower and human: a
recorded hash that nothing verifies goes stale the day someone bumps DejaVu to 2.38
and forgets the record. The cost is a few lines and no new import.

Nothing here imports pygame. Reading files from the repository is what this test is
about; it writes nothing (CONVENTIONS 5).
"""

from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SVG_DIR = REPO_ROOT / "assets" / "pieces" / "svg"
PIECES_LICENSE = REPO_ROOT / "assets" / "pieces" / "LICENSE.txt"
FONTS_DIR = REPO_ROOT / "assets" / "fonts"
FONTS_PROVENANCE = FONTS_DIR / "PROVENANCE.txt"
GITATTRIBUTES = REPO_ROOT / ".gitattributes"

EXPECTED_PIECE_COUNT = 12
EXPECTED_FONT_COUNT = 3

# One entry: a line that starts with our name and ends with the Commons file name,
# then any number of indented lines, then the indented sha1 line. What the middle
# says is not this test's business - only that the name and the sha1 belong to the
# same entry. The repetition is lazy and every middle line must be indented and
# non-empty, so an entry can never swallow the blank line and reach the next one.
_ENTRY = re.compile(
    r"^(?P<name>[wb][pnbrqk])[ \t]+[^\n]*?(?P<commons>\S+\.svg)[ \t]*$\n"
    r"(?:^[ \t]+\S[^\n]*$\n)*?"
    r"^[ \t]+sha1[ \t]+(?P<sha1>[0-9a-f]{40})[ \t]*$",
    re.MULTILINE,
)

# One entry in PROVENANCE.txt: the arrow line names the file we keep, then its size
# and its sha256. The archive's own sha256 has no arrow line, so it is not matched.
_FONT_ENTRY = re.compile(
    r"^[ \t]+\S+[ \t]+->[ \t]+(?P<name>\S+)[ \t]*$\n"
    r"^[ \t]+\d+ bytes[ \t]*$\n"
    r"^[ \t]+sha256[ \t]+(?P<sha256>[0-9a-f]{64})[ \t]*$",
    re.MULTILINE,
)

# The .gitattributes lines those claims depend on, whatever the spacing.
_ATTR_LINES = {
    "assets/pieces/svg/*.svg -text": re.compile(
        r"^assets/pieces/svg/\*\.svg[ \t]+-text[ \t]*$", re.MULTILINE
    ),
    "assets/fonts/LICENSE.txt -text": re.compile(
        r"^assets/fonts/LICENSE\.txt[ \t]+-text[ \t]*$", re.MULTILINE
    ),
    "*.ttf binary": re.compile(r"^\*\.ttf[ \t]+binary[ \t]*$", re.MULTILINE),
}

CAUSE = (
    "The recorded sha1 values hold only while .gitattributes keeps git from "
    "rewriting line endings in assets/pieces/svg/ (ADR-039). Check that first: "
    "with core.autocrlf=true a checkout turns LF into CRLF and every sha1 differs."
)


def documented_pieces() -> dict[str, str]:
    """Return {our name: sha1} as recorded in assets/pieces/LICENSE.txt."""
    text = PIECES_LICENSE.read_text(encoding="utf-8")
    return {m.group("name"): m.group("sha1") for m in _ENTRY.finditer(text)}


def documented_fonts() -> dict[str, str]:
    """Return {file name: sha256} as recorded in assets/fonts/PROVENANCE.txt."""
    text = FONTS_PROVENANCE.read_text(encoding="utf-8")
    return {m.group("name"): m.group("sha256") for m in _FONT_ENTRY.finditer(text)}


class GitAttributesTest(unittest.TestCase):
    def test_gitattributes_still_carries_every_line_a_claim_depends_on(self):
        self.assertTrue(GITATTRIBUTES.is_file(), f".gitattributes is missing. {CAUSE}")
        text = GITATTRIBUTES.read_text(encoding="utf-8")
        for line, pattern in _ATTR_LINES.items():
            with self.subTest(line=line):
                self.assertRegex(
                    text,
                    pattern,
                    f"'{line}' is gone from .gitattributes. Removing it silently breaks "
                    f"a recorded hash in assets/pieces/LICENSE.txt or "
                    f"assets/fonts/PROVENANCE.txt (ADR-039).",
                )


class PieceLicenseTest(unittest.TestCase):
    def test_license_documents_exactly_twelve_pieces(self):
        documented = documented_pieces()
        self.assertEqual(
            len(documented),
            EXPECTED_PIECE_COUNT,
            f"assets/pieces/LICENSE.txt lists {len(documented)} pieces with a sha1, "
            f"expected {EXPECTED_PIECE_COUNT}",
        )

    def test_every_svg_on_disk_is_documented(self):
        on_disk = {path.stem for path in SVG_DIR.glob("*.svg")}
        documented = set(documented_pieces())
        self.assertEqual(
            on_disk,
            documented,
            "assets/pieces/svg/ and assets/pieces/LICENSE.txt disagree about which "
            "files are here. Third-party material without a recorded source and "
            "license is exactly what LICENSE.txt exists to prevent.",
        )

    def test_every_svg_matches_its_recorded_sha1(self):
        documented = documented_pieces()
        # Without this, a regex that stops matching leaves an empty loop, and a test
        # that asserts nothing passes. A checker that goes blind must fail at once
        # (faza-0.md, task 0.2b, question 2).
        self.assertEqual(
            len(documented),
            EXPECTED_PIECE_COUNT,
            f"parsed {len(documented)} sha1 entries out of {PIECES_LICENSE.name}, "
            f"expected {EXPECTED_PIECE_COUNT} - the file layout changed and this "
            f"test stopped reading it",
        )

        for name, expected in sorted(documented.items()):
            with self.subTest(piece=name):
                path = SVG_DIR / f"{name}.svg"
                self.assertTrue(path.is_file(), f"{path} is missing")
                actual = hashlib.sha1(path.read_bytes()).hexdigest()
                self.assertEqual(actual, expected, f"{path} has changed. {CAUSE}")


class FontProvenanceTest(unittest.TestCase):
    def test_provenance_documents_exactly_three_files(self):
        documented = documented_fonts()
        self.assertEqual(
            sorted(documented),
            ["DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "LICENSE.txt"],
            f"assets/fonts/PROVENANCE.txt records {sorted(documented)}, expected the "
            f"two fonts and the copied LICENSE",
        )

    def test_every_font_file_matches_its_recorded_sha256(self):
        documented = documented_fonts()
        # Same guard as for the pieces: an empty loop asserts nothing.
        self.assertEqual(
            len(documented),
            EXPECTED_FONT_COUNT,
            f"parsed {len(documented)} sha256 entries out of {FONTS_PROVENANCE.name}, "
            f"expected {EXPECTED_FONT_COUNT} - the file layout changed and this test "
            f"stopped reading it",
        )

        for name, expected in sorted(documented.items()):
            with self.subTest(file=name):
                path = FONTS_DIR / name
                self.assertTrue(path.is_file(), f"{path} is missing")
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(
                    actual,
                    expected,
                    f"{path} is not the file assets/fonts/PROVENANCE.txt describes. "
                    f"If DejaVu was upgraded, PROVENANCE.txt has to say so.",
                )


if __name__ == "__main__":
    unittest.main()
