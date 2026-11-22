"""Replay historical nine-v8 / ten-v19 promotion under newer mutable roots.

Previously certified proof logic is unchanged. Only reads of the
authoritative mutable working roots are redirected to the immutable
nine-v8 and ten-v19 snapshots during historical verification.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

from research.order9_v8_order10_v19 import verify as old

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_ROOTS = {
    (ROOT / "indeterminate_order_9.txt").resolve():
        ROOT / "indeterminate_order_9_v8.txt",
    (ROOT / "indeterminate_order_10.txt").resolve():
        ROOT / "indeterminate_order_10_v19.txt",
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
            from research.order9_251902_p4_o17_v1.verify import (
                verify_positive, verify_ten_lifts,
            )
            verify_positive(public=args.public)
            verify_ten_lifts()


if __name__ == "__main__":
    main()
