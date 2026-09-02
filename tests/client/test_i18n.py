"""The catalog, the module that serves it, and the seam that ties both to PROTOCOL 5.

Three groups, three different subjects:

A. The seam. The code column of the ERROR table in PROTOCOL.md is read by machine, and
   every code has to have its key in sr.json (ADR-041). Both directions are asserted: a
   code without a key, and a key without a code. One direction alone would leave the
   scope of this task a promise rather than a rule.
B. The file itself - encoding, keys, and which characters a value may contain.
C. The behaviour of t() under the contract in ADR-040.

Group C reloads the module in setUp. The state "no catalog loaded" exists only before
the first load() and never comes back, so without the reload C12 would pass alone and
fail inside the suite - a test whose result depends on order (CONVENTIONS 5). That is
also why the module is imported as a module and never as `from ... import t`: after a
reload, a name imported that way still points at the old function object, silently.

Groups A and B read files from the repository. That is allowed exactly because the
content of the repository is what they are about (CONVENTIONS 5, ADR-039); group C
writes its own catalogs into tempfile.

Nothing in this file is written outside ASCII, letters with diacritics included: they
are built from code points below. Failure messages name a character by its code point
(U+00C4) and never print it - the Windows console is not UTF-8, so printing would raise
while reporting the failure, and a broken character is unreadable anyway (CONVENTIONS 7).
"""

from __future__ import annotations

import importlib
import json
import re
import string
import tempfile
import unittest
from pathlib import Path

import chess.client.i18n as i18n

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG = REPO_ROOT / "assets" / "i18n" / "sr.json"
PROTOCOL = REPO_ROOT / "docs" / "PROTOCOL.md"

EXPECTED_CODE_COUNT = 9

# The header row of the ERROR code table in PROTOCOL 5, and the first cell of a row.
_TABLE_HEADER = re.compile(r"^\|\s*Kod\s*\|.*$", re.MULTILINE)
_CODE_CELL = re.compile(r"^\|\s*`([A-Z][A-Z0-9_]*)`\s*\|")

# The ### `ERROR` section only: up to the next ###, or to the end of the file if ERROR
# ever becomes the last section. Without the second boundary A5 would fail with "section
# not found", which would be the wrong cause. Over the whole file the claim would already
# be green, because section 3 mentions sr.json.
_ERROR_SECTION = re.compile(r"^### `ERROR`\s*$\n(.*?)(?=^### |\Z)", re.MULTILINE | re.DOTALL)

_KEY = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")

# The Serbian Latin diacritics, by code point. They are built with chr() and not written
# as the letters themselves for the same reason the BOM in i18n.py is: if this file were
# ever saved in the wrong encoding, a literal whitelist would quietly deform and B11 would
# start accepting exactly what it exists to catch. A check must not share a failure mode
# with the failure it guards against.
_SMALL_DIACRITICS = "".join(
    chr(code_point)
    for code_point in (
        0x010D,  # c with caron
        0x0107,  # c with acute
        0x0161,  # s with caron
        0x017E,  # z with caron
        0x0111,  # d with stroke
    )
)
_CAPITAL_DIACRITICS = "".join(
    chr(code_point)
    for code_point in (
        0x010C,  # C with caron
        0x0106,  # C with acute
        0x0160,  # S with caron
        0x017D,  # Z with caron
        0x0110,  # D with stroke
    )
)

# Every character the current nine sentences use, and nothing else: ASCII letters in both
# cases, the ten diacritics, the space and the full stop. Digits, the comma, the braces
# and the underscore are deliberately absent - a new character gets added when a new text
# asks for it, consciously. That is what the whitelist is for.
#
# A whitelist and not a blacklist: a blacklist is walked around by any character we did
# not think to forbid, which is exactly what broken decoding produces.
ALLOWED_CHARACTERS = frozenset(
    string.ascii_letters + _SMALL_DIACRITICS + _CAPITAL_DIACRITICS + " ."
)

DIACRITICS = _SMALL_DIACRITICS


def _code_point(character: str) -> str:
    """Return U+XXXX for `character`. Never return the character itself - see the docstring."""
    return f"U+{ord(character):04X}"


def _catalog_json() -> dict[str, str]:
    """Return sr.json parsed the ordinary way.

    Duplicate keys are B7's business alone. If every test parsed through the hook, one
    duplicated key would take down half the suite and step 6 could not isolate anything.
    """
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def _error_codes(text: str) -> list[str] | None:
    """Return the codes from the ERROR table, or None if its header row is gone."""
    header = _TABLE_HEADER.search(text)
    if header is None:
        return None

    codes: list[str] = []
    # lstrip: the slice starts at the end of the header line, so the first element of
    # splitlines() would be the empty string left of that newline - and the loop below
    # would break on it before seeing a single row.
    for line in text[header.end() :].lstrip("\n").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            break
        cell = _CODE_CELL.match(stripped)
        if cell is not None:
            codes.append(cell.group(1))
    return codes


class ProtocolSeamTest(unittest.TestCase):
    """A. PROTOCOL.md 5 <-> assets/i18n/sr.json."""

    def setUp(self):
        self.text = PROTOCOL.read_text(encoding="utf-8")

    def codes(self) -> list[str]:
        codes = _error_codes(self.text)
        # A1 first, and as its own sentence: if the header moved or was reformatted, the
        # honest failure is "the parser cannot find the table", not "zero codes".
        self.assertIsNotNone(
            codes,
            "the header row of the ERROR code table was not found in docs/PROTOCOL.md. "
            "The first column of that table is read by machine (ADR-041); reformatting "
            "it breaks this test on purpose.",
        )
        return codes

    def test_a1_the_error_code_table_header_is_found(self):
        self.codes()

    def test_a2_protocol_lists_exactly_nine_error_codes(self):
        codes = self.codes()
        self.assertEqual(
            len(codes),
            EXPECTED_CODE_COUNT,
            f"docs/PROTOCOL.md 5 lists {len(codes)} error codes, expected "
            f"{EXPECTED_CODE_COUNT}: {codes}. A code added or removed obliges a change to "
            f"assets/i18n/sr.json in the same commit (ADR-041).",
        )

    def test_a3_every_protocol_code_has_its_key_in_the_catalog(self):
        codes = self.codes()
        # Without this the loop below can be empty, and a test with an empty loop asserts
        # nothing while reporting success (faza-0.md, task 0.4).
        self.assertEqual(
            len(codes),
            EXPECTED_CODE_COUNT,
            f"parsed {len(codes)} codes out of the ERROR table, expected "
            f"{EXPECTED_CODE_COUNT} - the table layout changed and this test stopped "
            f"reading it. Fix the parser or the table before trusting this suite.",
        )
        keys = _catalog_json()
        for code in codes:
            with self.subTest(code=code):
                key = "error." + code.lower()
                self.assertIn(
                    key,
                    keys,
                    f"code {code} in docs/PROTOCOL.md 5 has no {key} in "
                    f"assets/i18n/sr.json. message_key is 'error.' + the code in lower "
                    f"case (ADR-041).",
                )

    def test_a4_every_error_key_in_the_catalog_belongs_to_a_code(self):
        codes = self.codes()
        expected = {"error." + code.lower() for code in codes}
        found = {key for key in _catalog_json() if key.startswith("error.")}
        self.assertEqual(
            found,
            expected,
            "assets/i18n/sr.json and the ERROR table in docs/PROTOCOL.md 5 disagree. "
            "This is the direction that keeps the catalog from growing error keys the "
            "protocol never sends (ADR-041).",
        )

    def test_a5_the_error_section_points_at_the_catalog(self):
        section = _ERROR_SECTION.search(self.text)
        self.assertIsNotNone(section, "the ### `ERROR` section was not found in docs/PROTOCOL.md")
        self.assertIn(
            "sr.json",
            section.group(1),
            "the ### `ERROR` section of docs/PROTOCOL.md does not mention "
            "assets/i18n/sr.json. Whoever edits the code table has to read there that a "
            "change obliges the catalog too (ADR-041). The claim is scoped to this "
            "section: over the whole file section 3 would already satisfy it.",
        )


class CatalogFileTest(unittest.TestCase):
    """B. assets/i18n/sr.json as a file."""

    def test_b6_the_catalog_has_no_byte_order_mark(self):
        # Over the bytes, not the text: the claim must not depend on decoding having
        # worked, and utf-8-sig would swallow the BOM before it could be seen.
        first = CATALOG.read_bytes()[:3]
        self.assertNotEqual(
            first,
            b"\xef\xbb\xbf",
            "assets/i18n/sr.json starts with a UTF-8 BOM (U+FEFF). Save it as UTF-8 "
            "without a BOM (ADR-040).",
        )

    def test_b7_the_catalog_has_no_duplicate_keys(self):
        def reject_duplicates(pairs):
            keys = [key for key, _ in pairs]
            duplicates = sorted({key for key in keys if keys.count(key) > 1})
            self.assertEqual(
                duplicates,
                [],
                f"duplicate keys in assets/i18n/sr.json: {duplicates}. JSON keeps the "
                f"last one and says nothing, so a translation would be lost silently.",
            )
            return dict(pairs)

        json.loads(CATALOG.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)

    def test_b8_every_key_follows_the_area_thing_convention(self):
        for key in _catalog_json():
            with self.subTest(key=key):
                self.assertRegex(
                    key,
                    _KEY,
                    f"key {key!r} is not of the form area.thing (CONVENTIONS 7)",
                )

    def test_b9_no_value_is_empty_or_equal_to_its_key(self):
        # This catches a placeholder left behind. Nothing checks the quality of a
        # translation, and nothing can.
        for key, value in _catalog_json().items():
            with self.subTest(key=key):
                self.assertNotEqual(value.strip(), "", f"{key} has an empty value")
                self.assertNotEqual(value, key, f"{key} still holds its own key as the translation")

    def test_b10_at_least_one_value_carries_a_diacritic(self):
        # Proof that decoding really was UTF-8. B10 catches missing diacritics, B11
        # catches broken ones - two different failures, and the first does not cover the
        # second.
        carriers = [
            key for key, value in _catalog_json().items() if any(c in DIACRITICS for c in value)
        ]
        self.assertTrue(
            carriers,
            "no value in assets/i18n/sr.json contains a Serbian diacritic. Either the "
            "text was written without them, or the file was not decoded as UTF-8.",
        )

    def test_b11_every_character_of_every_value_is_on_the_whitelist(self):
        for key, value in _catalog_json().items():
            for character in value:
                if character in ALLOWED_CHARACTERS:
                    continue
                with self.subTest(key=key, code_point=_code_point(character)):
                    self.fail(
                        f"value of {key} contains {_code_point(character)}, which is not "
                        f"on ALLOWED_CHARACTERS. If the text needs it, add it there "
                        f"deliberately; if it is a mojibake, the file was decoded with "
                        f"the wrong encoding."
                    )


class TranslateTest(unittest.TestCase):
    """C. The contract of t() (ADR-040)."""

    def setUp(self):
        # Resets the whole module state, not just the attribute someone remembered, and
        # does not nail this test to the name of a private attribute.
        importlib.reload(i18n)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)

    def write_catalog(self, text: str) -> Path:
        path = self.directory / "catalog.json"
        path.write_text(text, encoding="utf-8")
        return path

    def load_catalog(self, mapping: dict[str, str]) -> Path:
        path = self.write_catalog(json.dumps(mapping, ensure_ascii=False))
        i18n.load(path)
        return path

    def test_c12_calling_t_before_load_raises(self):
        with self.assertRaises(RuntimeError):
            i18n.t("error.illegal_move")

    def test_c13_an_unknown_key_comes_back_as_itself(self):
        self.load_catalog({"error.illegal_move": "text"})
        # Inside assertLogs although the log is not the subject here: otherwise the suite
        # prints a pile of warnings on every run and stops being read.
        with self.assertLogs(i18n.__name__, "WARNING"):
            self.assertEqual(i18n.t("menu.play"), "menu.play")

    def test_c14_a_placeholder_is_replaced_from_params(self):
        self.load_catalog({"game.turn": "On turn: {{name}}"})
        self.assertEqual(i18n.t("game.turn", {"name": "Ana"}), "On turn: Ana")

    def test_c15_a_missing_parameter_stays_visible_on_screen(self):
        self.load_catalog({"game.turn": "On turn: {{name}}"})
        with self.assertLogs(i18n.__name__, "WARNING"):
            self.assertEqual(i18n.t("game.turn"), "On turn: {{name}}")

    def test_c16_an_unused_parameter_does_not_change_the_output(self):
        self.load_catalog({"game.turn": "On turn"})
        with self.assertLogs(i18n.__name__, "WARNING"):
            self.assertEqual(i18n.t("game.turn", {"name": "Ana"}), "On turn")

    def test_c17_a_parameter_that_is_not_a_string_raises(self):
        self.load_catalog({"clock.left": "{{seconds}}"})
        with self.assertRaises(TypeError):
            i18n.t("clock.left", {"seconds": 1.0})

    def test_c18_a_duplicate_key_in_the_file_raises(self):
        path = self.write_catalog('{"a.one": "first", "a.one": "second"}')
        with self.assertRaises(ValueError) as caught:
            i18n.load(path)
        self.assertIn("a.one", str(caught.exception))

    def test_c19_a_byte_order_mark_in_the_file_raises(self):
        path = self.write_catalog(chr(0xFEFF) + '{"a.one": "first"}')
        with self.assertRaises(ValueError):
            i18n.load(path)

    def test_c20_the_same_missing_key_is_reported_once(self):
        self.load_catalog({"error.illegal_move": "text"})
        # Both calls inside one test: setUp resets the state, so nothing may be counted
        # across tests.
        with self.assertLogs(i18n.__name__, "WARNING") as captured:
            i18n.t("menu.play")
            i18n.t("menu.play")
        self.assertEqual(
            len(captured.records),
            1,
            "a missing key has to warn once per key, not on every frame of the game",
        )

    def test_c21_a_reloaded_catalog_reports_the_same_missing_key_again(self):
        path = self.load_catalog({"error.illegal_move": "text"})
        with self.assertLogs(i18n.__name__, "WARNING"):
            i18n.t("menu.play")

        i18n.load(path)

        with self.assertLogs(i18n.__name__, "WARNING") as captured:
            i18n.t("menu.play")
        self.assertEqual(
            len(captured.records),
            1,
            "the set of reported keys belongs to the catalog, not to the module: a "
            "catalog loaded again while still lacking the key has to say so again "
            "(ADR-040)",
        )

    def test_c22_a_missing_parameter_is_logged(self):
        self.load_catalog({"game.turn": "On turn: {{name}}"})
        with self.assertLogs(i18n.__name__, "WARNING") as captured:
            i18n.t("game.turn")
        self.assertEqual(len(captured.records), 1)

    def test_c23_an_unused_parameter_is_logged(self):
        self.load_catalog({"game.turn": "On turn"})
        with self.assertLogs(i18n.__name__, "WARNING") as captured:
            i18n.t("game.turn", {"name": "Ana"})
        self.assertEqual(len(captured.records), 1)


if __name__ == "__main__":
    unittest.main()
