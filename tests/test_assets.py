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

Since 0.6 this file also guards the licensing chain of the repository itself
(ADR-042, ADR-043). LICENSE in the root states the terms for our code and names one
holder; THIRD-PARTY.txt next to it states the scope - which directories carry terms
of their own - and pyproject.toml states the same identifier a third time, for the
package metadata. Three places, one claim, and nothing but this file keeps them from
drifting apart one edit at a time.

THIRD-PARTY.txt is read exactly once, in third_party_lines(), and every reader works
over that list of lines. No pattern is ever applied to the whole text with
re.MULTILINE: that file deliberately has no .gitattributes row, so a fresh clone with
core.autocrlf=true puts CRLF on disk, an anchored $ then sits before the \\n with \\r
in the way, and the check would pass here and fail on someone else's machine - the
ADR-039 failure mode, one file over.

Nothing here imports pygame. Reading files from the repository is what this test is
about; it writes nothing (CONVENTIONS 5).
"""

from __future__ import annotations

import hashlib
import re
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SVG_DIR = REPO_ROOT / "assets" / "pieces" / "svg"
PIECES_LICENSE = REPO_ROOT / "assets" / "pieces" / "LICENSE.txt"
FONTS_DIR = REPO_ROOT / "assets" / "fonts"
FONTS_PROVENANCE = FONTS_DIR / "PROVENANCE.txt"
GITATTRIBUTES = REPO_ROOT / ".gitattributes"

ASSETS_DIR = REPO_ROOT / "assets"
ROOT_LICENSE = REPO_ROOT / "LICENSE"
THIRD_PARTY = REPO_ROOT / "THIRD-PARTY.txt"
PYPROJECT = REPO_ROOT / "pyproject.toml"

EXPECTED_PIECE_COUNT = 12
EXPECTED_FONT_COUNT = 3
EXPECTED_LICENSED_DIR_COUNT = 2

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

# The header of the machine-read block in THIRD-PARTY.txt. Compared as a whole line,
# not with a pattern: splitlines() has already removed the \r, and a plain equality
# cannot be defeated by an anchor that stops matching.
_BLOCK_HEADER = "DIRECTORIES WITH THEIR OWN LICENSE:"

# Applied to one line at a time - deliberately no re.MULTILINE. See the module
# docstring for why that distinction is load-bearing for this file.
_SPDX_LINE = re.compile(r"^SPDX-License-Identifier:[ \t]+(?P<id>\S+)[ \t]*$")

# chr(0x0107) is LATIN SMALL LETTER C WITH ACUTE, encoded in UTF-8 as C4 87. It is
# built from the code point and never written literally: whatever would corrupt it
# in LICENSE - a save through an editor in cp1252, a bad merge - would corrupt a
# literal here just as well, and the test would compare broken against broken. A
# check must not share the failure it guards against (faza-0.md, 0.5).
_COPYRIGHT_LINE = "Copyright (c) 2026 Stefan Obradovi" + chr(0x0107)

_BOM = b"\xef\xbb\xbf"

# Two different diagnoses, kept apart on purpose (ADR-041): the first says the
# formatting broke and nothing was read, the second says the content went empty.
HEADER_GONE = (
    f"header not found: the line '{_BLOCK_HEADER}' is gone from THIRD-PARTY.txt, so "
    f"the block was never located and nothing below it was read. This is a formatting "
    f"failure, not a content one (ADR-042)."
)
ZERO_PATHS = (
    "zero paths: the header is there but no path follows it. The block is empty, so "
    "every comparison against it would pass while claiming nothing (ADR-042)."
)

SCOPE_CAUSE = (
    "LICENSE in the root names one holder and one set of terms. The pieces are under "
    "the same terms but a different holder, and the font under different terms and a "
    "different holder, so THIRD-PARTY.txt has to name every directory that carries a "
    "LICENSE.txt of its own - and only those (ADR-042)."
)

# Shared by every class that reads one of these files, so that the same missing file
# gives the same sentence whichever reader hits it first. A reader without a claim in
# front of it raises FileNotFoundError instead - an ERROR with no sentence about the
# cause - while the reader next to it fails with one.
MANIFEST_MISSING = f"THIRD-PARTY.txt is missing from the repository root. {SCOPE_CAUSE}"
LICENSE_MISSING = (
    "LICENSE is missing from the repository root. A public repository without one is "
    "'all rights reserved' by default, which is not a decision anyone made (ADR-042)."
)


def documented_pieces() -> dict[str, str]:
    """Return {our name: sha1} as recorded in assets/pieces/LICENSE.txt."""
    text = PIECES_LICENSE.read_text(encoding="utf-8")
    return {m.group("name"): m.group("sha1") for m in _ENTRY.finditer(text)}


def documented_fonts() -> dict[str, str]:
    """Return {file name: sha256} as recorded in assets/fonts/PROVENANCE.txt."""
    text = FONTS_PROVENANCE.read_text(encoding="utf-8")
    return {m.group("name"): m.group("sha256") for m in _FONT_ENTRY.finditer(text)}


def third_party_lines() -> list[str]:
    """Return THIRD-PARTY.txt as decoded lines. Every reader of that file starts here.

    read_bytes() -> decode -> splitlines(), and nothing else. splitlines() ends a line
    on \\r\\n as readily as on \\n and keeps neither, so no reader downstream has to know
    which one is on disk - and on a fresh Windows clone it really is \\r\\n, because the
    file has no .gitattributes row (ADR-042). Splitting raw bytes on b"\\n" would leave
    the \\r attached, and so would any pattern anchored with re.MULTILINE.
    """
    return THIRD_PARTY.read_bytes().decode("utf-8").splitlines()


def documented_third_party_dirs(lines: list[str]) -> list[str] | None:
    """Return the paths listed in the block, or None when the header is not there.

    None and [] are different answers on purpose. None means the block could not be
    found at all, [] means it was found and holds nothing - a formatting failure and a
    content failure, which need different messages (ADR-041).
    """
    if _BLOCK_HEADER not in lines:
        return None
    paths = []
    for line in lines[lines.index(_BLOCK_HEADER) + 1 :]:
        if not line.strip():
            break
        paths.append(line.strip())
    return paths


def documented_spdx_id(lines: list[str]) -> str | None:
    """Return the SPDX identifier THIRD-PARTY.txt states for our own code, or None."""
    for line in lines:
        match = _SPDX_LINE.match(line)
        if match:
            return match.group("id")
    return None


def licensed_dirs_on_disk() -> list[str]:
    """Return the directories under assets/ that carry a LICENSE.txt of their own.

    The criterion is the file, not a list of names, which is why assets/i18n drops out
    by itself: sr.json is ours and has no separate terms, so there is no exception to
    write down and none to forget.
    """
    return sorted(f"assets/{path.parent.name}" for path in ASSETS_DIR.glob("*/LICENSE.txt"))


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


class RootLicenseTest(unittest.TestCase):
    # Every test below reads the bytes of LICENSE, so the claim that it exists belongs
    # here rather than inside one of them. Asserted in one test and not the other, a
    # missing file would fail with a sentence in the first and raise FileNotFoundError
    # in the second - the same file, two readers, two different fates.
    def setUp(self):
        self.assertTrue(ROOT_LICENSE.is_file(), LICENSE_MISSING)
        self.data = ROOT_LICENSE.read_bytes()

    def test_license_carries_the_copyright_line_it_must_retain(self):
        self.assertIn(
            _COPYRIGHT_LINE.encode("utf-8"),
            self.data,
            "the copyright line in LICENSE is not the one the first BSD-3 condition "
            "requires every redistribution to retain. Its last character is U+0107, "
            "encoded in UTF-8 as C4 87; it is named here and deliberately not printed, "
            "because a console that cannot encode it would break this message too "
            "(faza-0.md, 0.5). Searched as a substring of the bytes, so end-of-line "
            "conversion cannot reach it - which is the whole of what LICENSE needs "
            "from .gitattributes, and why it has no row there (ADR-042).",
        )

    def test_license_has_no_byte_order_mark(self):
        self.assertNotEqual(
            self.data[:3],
            _BOM,
            "LICENSE starts with a UTF-8 BOM (EF BB BF). Checked over the raw bytes "
            "rather than after decoding, so the claim holds even when decoding does "
            "not - the same reason B6 in tests/client/test_i18n.py reads bytes "
            "(ADR-040).",
        )


class LicensedDirectoriesTest(unittest.TestCase):
    def test_assets_holds_exactly_two_directories_with_their_own_license(self):
        on_disk = licensed_dirs_on_disk()
        # The count comes before any comparison. Without it a scan that goes blind
        # returns nothing, every set comparison below trivially agrees, and a test
        # that asserts nothing passes (faza-0.md, 0.2b and 0.4).
        self.assertTrue(
            on_disk,
            "no directory under assets/ carries a LICENSE.txt of its own. Either "
            "assets/ moved or this scan stopped seeing it; either way nothing else "
            "here compares anything, so it has to fail right at this line.",
        )
        self.assertEqual(
            len(on_disk),
            EXPECTED_LICENSED_DIR_COUNT,
            f"assets/ holds {len(on_disk)} directories with their own LICENSE.txt "
            f"({on_disk}), expected {EXPECTED_LICENSED_DIR_COUNT}. The number is "
            f"hardcoded on purpose: a third body of third-party material has to be a "
            f"deliberate event that touches this test and THIRD-PARTY.txt, never "
            f"something that slips in. {SCOPE_CAUSE}",
        )


class ThirdPartyManifestTest(unittest.TestCase):
    def setUp(self):
        self.assertTrue(THIRD_PARTY.is_file(), MANIFEST_MISSING)
        self.lines = third_party_lines()

    def test_block_header_is_still_there(self):
        self.assertIsNotNone(documented_third_party_dirs(self.lines), HEADER_GONE)

    def test_block_lists_at_least_one_directory(self):
        documented = documented_third_party_dirs(self.lines)
        self.assertIsNotNone(documented, HEADER_GONE)
        self.assertNotEqual(documented, [], ZERO_PATHS)

    def test_block_and_disk_agree_about_which_directories_carry_their_own_license(self):
        documented = documented_third_party_dirs(self.lines)
        self.assertIsNotNone(documented, HEADER_GONE)
        self.assertEqual(
            sorted(documented),
            licensed_dirs_on_disk(),
            f"THIRD-PARTY.txt and assets/ disagree about which directories carry their "
            f"own license. Both directions matter: a directory on disk that the file "
            f"does not name is third-party material the root LICENSE silently appears "
            f"to cover, and a name in the file with nothing behind it is a promise "
            f"about terms that are not there. {SCOPE_CAUSE}",
        )

    def test_every_documented_directory_really_carries_a_license(self):
        documented = documented_third_party_dirs(self.lines)
        self.assertIsNotNone(documented, HEADER_GONE)
        for path in documented:
            with self.subTest(path=path):
                self.assertTrue(
                    (REPO_ROOT / path / "LICENSE.txt").is_file(),
                    f"THIRD-PARTY.txt names {path}, but {path}/LICENSE.txt does not "
                    f"exist. A named directory without terms behind it is worse than "
                    f"an unnamed one, because it reads as covered.",
                )


class PackageMetadataTest(unittest.TestCase):
    # Same setUp as ThirdPartyManifestTest, and the same message. Without it this
    # class would read the same file with no claim in front of it: a missing
    # THIRD-PARTY.txt would surface as a FileNotFoundError - an ERROR with no sentence
    # about the cause - while the other reader of that same file fails with one.
    def setUp(self):
        self.assertTrue(THIRD_PARTY.is_file(), MANIFEST_MISSING)
        self.lines = third_party_lines()

    def test_pyproject_and_third_party_state_the_same_license(self):
        # Binary mode is not an oversight against CONVENTIONS 7: tomllib.load takes a
        # binary file and decodes UTF-8 itself, and passing it a text handle is an
        # error. Everything else in this file still opens with encoding="utf-8".
        with PYPROJECT.open("rb") as handle:
            declared = tomllib.load(handle)["project"].get("license")
        stated = documented_spdx_id(self.lines)
        self.assertIsNotNone(
            stated,
            "no 'SPDX-License-Identifier:' line in THIRD-PARTY.txt. That line is the "
            "only thing tying the prose to the package metadata; without it the two "
            "can drift apart and nothing notices (ADR-043).",
        )
        self.assertEqual(
            declared,
            stated,
            f"pyproject.toml declares project.license = {declared!r} while "
            f"THIRD-PARTY.txt states {stated!r}. The license is written down in two "
            f"places and they have to say the same thing (ADR-043).",
        )


class AsciiSourceTest(unittest.TestCase):
    # This holds for one file because there is one file. If the licensing claims are
    # ever split across several test modules, this check does NOT follow them on its
    # own: it reads Path(__file__) and nothing else, so the rule stops applying to the
    # new module the moment it is created, silently and without a failure anywhere.
    # Whoever splits them owes the new file its own copy of this check.
    def test_this_file_is_pure_ascii(self):
        offenders = [
            (index, hex(byte))
            for index, byte in enumerate(Path(__file__).resolve().read_bytes())
            if byte > 0x7F
        ]
        self.assertEqual(
            offenders,
            [],
            f"tests/test_assets.py is no longer pure ASCII: {offenders[:5]}. The "
            f"checks here are built out of code points, chr(0x0107) above, exactly so "
            f"that nothing which corrupts a character in LICENSE can corrupt it here "
            f"as well. A literal character pasted into this file would make the test "
            f"compare broken against broken (faza-0.md, 0.5).",
        )


if __name__ == "__main__":
    unittest.main()
