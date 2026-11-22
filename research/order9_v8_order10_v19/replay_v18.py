"""Replay the immutable nine-v7 / ten-v18 promotion under newer roots.

The archived v7/v18 verification code and original source snapshots are
preserved. Only reads of mutable authoritative working root byte files
are redirected to the corresponding immutable historical snapshots.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

from research.order9_v7_order10_v18 import verify as old

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_ROOTS = {
    (ROOT / "indeterminate_order_9.txt").resolve():
        ROOT / "indeterminate_order_9_v7.txt",
    (ROOT / "indeterminate_order_10.txt").resolve():
        ROOT / "indeterminate_order_10_v18.txt",
}
ORIGINAL_READ_BYTES = Path.read_bytes


def read_historical(path: Path) -> bytes:
    return ORIGINAL_READ_BYTES(HISTORICAL_ROOTS.get(path.resolve(), path))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proofs", action="store_true")
    parser.add_argument("--public", action="store_true")
    args = parser.parse_args()
    if args.public and not args.proofs:
        parser.error("--public requires --proofs")
    with patch.object(Path, "read_bytes", read_historical):
        old.verify_indices()
        if args.proofs:
            from research.order9_three_p4_retractions_v1 import verify as witness
            witness.check_certificates(public=args.public)
            witness.check_ten_lifts()


if __name__ == "__main__":
    main()
