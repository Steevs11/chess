"""core/pgn.py: PGN export — the seven-tag header, escaping, move text and line wrapping."""

from __future__ import annotations

import unittest

from chess.core.pgn import format_pgn


def _header_lines(pgn: str) -> list[str]:
    return pgn.split("\n\n", 1)[0].split("\n")


def _move_lines(pgn: str) -> list[str]:
    return pgn.split("\n\n", 1)[1].removesuffix("\n").split("\n")


class FormatPgnTest(unittest.TestCase):
    def test_fools_mate_without_tags_matches_exact_text(self) -> None:
        expected = (
            '[Event "?"]\n[Site "?"]\n[Date "????.??.??"]\n[Round "?"]\n[White "?"]\n[Black "?"]\n'
            '[Result "0-1"]\n\n1. f3 e5 2. g4 Qh4# 0-1\n'
        )
        self.assertEqual(format_pgn(["f3", "e5", "g4", "Qh4#"], "0-1"), expected)

    def test_tags_fill_seven_in_order_then_extras(self) -> None:
        tags = {"Black": "Ana", "TimeControl": "300+3", "White": "Marko", "Date": "2026.10.21"}
        pgn = format_pgn(["e4"], "1-0", tags)
        self.assertEqual(
            _header_lines(pgn),
            [
                '[Event "?"]',
                '[Site "?"]',
                '[Date "2026.10.21"]',
                '[Round "?"]',
                '[White "Marko"]',
                '[Black "Ana"]',
                '[Result "1-0"]',
                '[TimeControl "300+3"]',
            ],
        )

    def test_result_key_in_tags_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            format_pgn(["e4"], "1-0", {"Result": "1-0"})

    def test_tag_value_escapes_backslash_then_quote(self) -> None:
        pgn = format_pgn([], "*", {"White": 'Marko "Mare" O\'Neil \\ x'})
        self.assertIn('[White "Marko \\"Mare\\" O\'Neil \\\\ x"]', _header_lines(pgn))

    def test_no_moves_leaves_only_result(self) -> None:
        pgn = format_pgn([], "*")
        self.assertTrue(pgn.endswith("\n\n*\n"))
        self.assertEqual(_move_lines(pgn), ["*"])
        self.assertIn('[Result "*"]', _header_lines(pgn))

    def test_single_white_move_has_move_number(self) -> None:
        self.assertEqual(_move_lines(format_pgn(["e4"], "*")), ["1. e4 *"])

    def test_long_game_wraps_at_79_without_losing_tokens(self) -> None:
        pgn = format_pgn(["Nf3", "Nf6", "Ng1", "Ng8"] * 30, "1/2-1/2")
        lines = _move_lines(pgn)
        expected_tokens: list[str] = []
        for number in range(1, 61, 2):
            expected_tokens += [f"{number}.", "Nf3", "Nf6", f"{number + 1}.", "Ng1", "Ng8"]
        expected_tokens.append("1/2-1/2")

        self.assertGreater(len(lines), 1)
        for line in lines:
            with self.subTest(line=line):
                self.assertLessEqual(len(line), 79)
                self.assertEqual(line, line.strip(" "))
        self.assertEqual(" ".join(lines), " ".join(expected_tokens))
        self.assertTrue(" ".join(lines).startswith("1. Nf3 Nf6 2. Ng1 Ng8 "))
        self.assertTrue(" ".join(lines).endswith(" 60. Ng1 Ng8 1/2-1/2"))
        self.assertEqual(lines[-1].split(" ")[-1], "1/2-1/2")

    def test_invalid_result_raises_value_error(self) -> None:
        for result in ("1–0", "", "1-0 "):
            with self.subTest(result=result), self.assertRaises(ValueError):
                format_pgn(["e4"], result)


if __name__ == "__main__":
    unittest.main()
