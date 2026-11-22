"""Replay the archived nine-v5 / ten-v16 audit under newer working roots.

Redirect only read_bytes() on the two mutable working index filenames to
their immutable v5/v16 snapshots. The earlier proof, source hashes,
promotional manifest and all historical scripts remain unchanged.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

from research.order10_current_indeterminates_v16 import verify as old

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL = {
    (ROOT / "indeterminate_order_9.txt").resolve():
        ROOT / "indeterminate_order_9_v5.txt",
    (ROOT / "indeterminate_order_10.txt").resolve():
        ROOT / "indeterminate_order_10_v16.txt",
}
ORIGINAL = Path.read_bytes


def read_historical(path: Path) -> bytes:
    return ORIGINAL(HISTORICAL.get(path.resolve(), path))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--surfaces", action="store_true")
    parser.add_argument("--f45", action="store_true")
    parser.add_argument("--o15", action="store_true")
    parser.add_argument("--o15-full", action="store_true")
    args = parser.parse_args()
    with patch.object(Path, "read_bytes", read_historical):
        old.verify_indices()
        if args.surfaces:
            old.verify_surfaces()
        if args.f45:
            old.replay_f45()
        if args.o15 or args.o15_full:
            old.replay_o15(full=args.o15_full)


if __name__ == "__main__":
    main()
