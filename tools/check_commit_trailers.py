"""Check that no commit message carries an authorship or session trailer (CONVENTIONS 8).

Claim: no commit message in the local history has a line that starts with
`Co-Authored-By:` or `Claude-Session:`. The prefix is compared without regard to case,
because GitHub writes `Co-authored-by:` - a wider domain than the claim, never a narrower
one (CONVENTIONS 5).

Two halves. find_trailers is pure and is what tests/test_check_commit_trailers.py covers;
main is a thin shell around `git log`, so tests/ never calls an external program.

Exit codes:
    0  history read, no trailer found
    1  at least one trailer found; every hit is printed with its SHA
    2  the check had no input: git missing, git failing, or zero commits read.
       "Did not run" must never look like "clean" (ADR-047).

Written in Python, not in a shell, so it runs the same in PowerShell and in bash.
Run it before every push: python tools/check_commit_trailers.py
"""

from __future__ import annotations

import subprocess
import sys

TRAILER_PREFIXES = ("co-authored-by:", "claude-session:")


def find_trailers(records: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Return (sha, line) for every message line that starts with a forbidden prefix.

    Raises ValueError on an empty list: an empty history is a check with no input, and
    returning [] for it would read as a pass.
    """
    if not records:
        raise ValueError("no commit messages to check; the check had no input")
    hits = []
    for sha, message in records:
        for line in message.splitlines():
            if line.lower().startswith(TRAILER_PREFIXES):
                hits.append((sha, line))
    return hits


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace"
    )


def read_records() -> list[tuple[str, str]]:
    # Each record is SHA, NUL, message, NUL. Splitting on NUL is safe because a commit
    # message cannot contain one, and no shell ever sees the format string.
    result = _git("log", "--all", "--format=%H%x00%B%x00")
    if result.returncode != 0:
        raise RuntimeError(f"git log exited with {result.returncode}: {result.stderr.strip()}")
    fields = result.stdout.split("\0")
    return [(fields[i].strip(), fields[i + 1]) for i in range(0, len(fields) - 1, 2)]


def _ascii(text: str) -> str:
    # A name in a trailer may not be encodable by the console; the message must not break.
    return text.encode("ascii", "backslashreplace").decode("ascii")


def main() -> int:
    try:
        records = read_records()
        shallow = _git("rev-parse", "--is-shallow-repository").stdout.strip()
    except (OSError, RuntimeError) as error:
        print(f"check did not run: {error}")
        return 2
    print(f"commits read: {len(records)} (local history, all refs; shallow: {shallow})")
    try:
        hits = find_trailers(records)
    except ValueError as error:
        print(f"check did not run: {error}")
        return 2
    for sha, line in hits:
        print(f"{sha}  {_ascii(line)}")
    if hits:
        print(f"{len(hits)} trailer line(s) found in commit messages (CONVENTIONS 8)")
        return 1
    print("no authorship or session trailer in the local history")
    return 0


if __name__ == "__main__":
    sys.exit(main())
