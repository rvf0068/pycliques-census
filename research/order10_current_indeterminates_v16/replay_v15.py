"""Read-only replay of the immutable v14 -> v15 27-certificate proof.

The historical v15 verifier predates the promoted v16 working root. Only its
read of the authoritative root is redirected to the frozen v15 snapshot.
No saved certificate, source data or versioned census file is mutated.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

from research.order10_reference_lifts_pilot import verify as historical

ROOT = Path(__file__).resolve().parents[2]
CURRENT = (ROOT / "indeterminate_order_10.txt").resolve()
FROZEN = ROOT / "indeterminate_order_10_v15.txt"
ORIGINAL = Path.read_bytes


def read_historical(path: Path) -> bytes:
    if path.resolve() == CURRENT:
        return ORIGINAL(FROZEN)
    return ORIGINAL(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--public", action="store_true")
    parser.add_argument("--shard", type=int)
    parser.add_argument("--shards", type=int, default=8)
    args = parser.parse_args()
    with patch.object(Path, "read_bytes", read_historical):
        historical.verify(
            full=args.full,
            public=args.public,
            shard=args.shard,
            shards=args.shards,
        )
