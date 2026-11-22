"""Replay the immutable nine-v6 / ten-v17 census audit under v7/v18 roots.

Historical v17 files and proof logic remain untouched. Redirect only reads
of the mutable order-nine and order-ten root files to their frozen v6/v17
snapshots; all other paths and library calls use their original behavior.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

from research.order10_current_indeterminates_v17 import verify as old

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL = {
    (ROOT / "indeterminate_order_9.txt").resolve():
        ROOT / "indeterminate_order_9_v6.txt",
    (ROOT / "indeterminate_order_10.txt").resolve():
        ROOT / "indeterminate_order_10_v17.txt",
}
ORIGINAL = Path.read_bytes


def read_historical(path: Path) -> bytes:
    return ORIGINAL(HISTORICAL.get(path.resolve(), path))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--families", action="store_true")
    parser.add_argument("--surfaces", action="store_true")
    parser.add_argument("--proofs", action="store_true")
    parser.add_argument("--public", action="store_true")
    args = parser.parse_args()
    if args.public and not args.proofs:
        parser.error("--public requires --proofs")
    with patch.object(Path, "read_bytes", read_historical):
        old.verify_indices()
        if args.families:
            old.verify_families()
        if args.surfaces:
            old.verify_surfaces()
        if args.proofs:
            old.verify_proofs(public=args.public)


if __name__ == "__main__":
    main()
