"""Run every gate of this project in one command; exit 0 only if all of them pass.

    python tools/check.py

Gates, in order: unit tests, ruff check, ruff format --check, layer check, commit-message
trailers, and ignored paths that already entered git history (CONVENTIONS 8, 9). The
Python gates run through the interpreter that runs this script, so a venv is respected.
Standard library only; the last two gates need git on PATH.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(name: str, cmd: list[str]) -> bool:
    """Run `cmd` from the repo root, print a verdict, and return True if it exited with 0."""
    print(f"== {name}: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=ROOT)
    passed = result.returncode == 0
    print(f"   {'PASS' if passed else 'FAIL'} (exit {result.returncode})\n")
    return passed


def ignored_paths_in_history() -> bool:
    """Return True if no path in any commit matches .gitignore (CONVENTIONS 8).

    `git status` only sees the working tree; this walks every tree of every commit.
    `--no-index` is required, otherwise check-ignore skips tracked files - and a tracked
    file that .gitignore describes is exactly what we are looking for.
    """
    print("== ignored paths in history")
    objects = subprocess.run(
        ["git", "rev-list", "--objects", "--all"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    # Each line is "<sha> <path>"; commits have no path and the root tree has an empty one.
    paths = sorted(
        {path for _, _, path in (line.partition(" ") for line in objects.splitlines()) if path}
    )
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "--verbose", "--stdin"],
        cwd=ROOT,
        input="\n".join(paths) + "\n",
        capture_output=True,
        text=True,
    )
    # check-ignore exits 1 when nothing matched (clean), 0 when something did, 128 on error.
    if result.returncode == 1:
        print(f"   PASS ({len(paths)} paths, none ignored)\n")
        return True
    print(result.stdout, end="")
    print(f"   FAIL (exit {result.returncode})\n")
    return False


def main() -> int:
    py = sys.executable
    results = [
        run("unit tests", [py, "-m", "unittest", "discover", "-s", "tests"]),
        run("ruff check", [py, "-m", "ruff", "check", "."]),
        run("ruff format", [py, "-m", "ruff", "format", "--check", "."]),
        run("layer check", [py, "tools/layer_check.py"]),
        run("commit trailers", [py, "tools/check_commit_trailers.py"]),
        ignored_paths_in_history(),
    ]
    failed = results.count(False)
    print("ALL GATES PASSED" if failed == 0 else f"{failed} GATE(S) FAILED")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
