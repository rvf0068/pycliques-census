"""Replay the immutable v20 census proof without changing its old verifier.

Only reads of the mutable order-ten root are redirected to its frozen
ten-v20 snapshot. The source-order-nine current root remains nine-v9.
This allows all historical 220 positive lifts and source proofs to be
replayed after ten-v21 is promoted.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

from research.order9_v9_order10_v20 import verify as old

ROOT = Path(__file__).resolve().parents[2]
MUTABLE = (ROOT / "indeterminate_order_10.txt").resolve()
FROZEN = ROOT / "indeterminate_order_10_v20.txt"
ORIGINAL_READ_BYTES = Path.read_bytes


def historical_bytes(path: Path) -> bytes:
    return ORIGINAL_READ_BYTES(FROZEN if path.resolve() == MUTABLE else path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proofs", action="store_true")
    parser.add_argument("--public", action="store_true")
    args = parser.parse_args()
    if args.public and not args.proofs:
        parser.error("--public requires --proofs")

    with patch.object(Path, "read_bytes", historical_bytes):
        old.verify_indices()
        if args.proofs:
            from research.order9_two_p4_retractions_v1.verify import (
                PROVED as POSITIVES,
                verify_positive,
                verify_ten_lifts,
            )
            if set(POSITIVES) != set(old.PROVED):
                raise AssertionError("Historical source proof identities changed")
            for index in old.PROVED:
                verify_positive(index, public=args.public)
            verify_ten_lifts()


if __name__ == "__main__":
    main()
