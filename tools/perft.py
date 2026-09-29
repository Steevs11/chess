"""Count perft nodes from a position; a CLI over perft and perft_divide in core/movegen.py.

    python tools/perft.py [--fen FEN] [--depth N] [--divide]

Defaults: the starting position, depth 1. With --divide, one line per root move,
`<uci> <nodes>`, sorted by UCI so the output lines up with other engines; then the total,
the time and nodes per second. The logic lives in core and is tested there (ADR-007).
Standard library only.
"""

from __future__ import annotations

import argparse
import sys
import time

from chess.core.board import Board
from chess.core.fen import STARTING_FEN
from chess.core.movegen import perft, perft_divide
from chess.core.types import InvalidFenError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Count perft nodes from a position.")
    parser.add_argument("--fen", default=STARTING_FEN, help="position (default: start)")
    parser.add_argument("--depth", type=int, default=1, help="plies to search (default: 1)")
    parser.add_argument("--divide", action="store_true", help="split the count by root move")
    args = parser.parse_args(argv)

    try:
        board = Board.from_fen(args.fen)
    except InvalidFenError as exc:
        print(f"invalid FEN: {exc}", file=sys.stderr)
        return 1

    start = time.perf_counter()
    if args.divide:
        if args.depth < 1:
            print("--divide needs --depth of at least 1", file=sys.stderr)
            return 1
        divide = perft_divide(board, args.depth)
        nodes = sum(divide.values())
    else:
        nodes = perft(board, args.depth)
    elapsed = time.perf_counter() - start

    if args.divide:
        for uci, count in sorted((move.to_uci(), count) for move, count in divide.items()):
            print(f"{uci} {count}")
    print(f"nodes {nodes}")
    print(f"time {elapsed:.3f} s")
    print(f"nodes/s {nodes / max(elapsed, 1e-9):.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
