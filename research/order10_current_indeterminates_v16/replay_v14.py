"""Read-only v16-compatible replay of the immutable v4/v14 proof.

The archived verifier requires the nine-vertex working root to be frozen
v4 and the ten-vertex working root to be frozen v14. Redirect only those
two reads in-memory; never mutate versioned files or archived code.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from research.order9_p2_iso_lift_v1 import verify as historical

ROOT = Path(__file__).resolve().parents[2]
CURRENT9 = (ROOT / "indeterminate_order_9.txt").resolve()
CURRENT10 = (ROOT / "indeterminate_order_10.txt").resolve()
FROZEN9 = ROOT / "indeterminate_order_9_v4.txt"
FROZEN10 = ROOT / "indeterminate_order_10_v14.txt"
ORIGINAL = Path.read_bytes


def read_historical(path: Path) -> bytes:
    if path.resolve() == CURRENT9:
        return ORIGINAL(FROZEN9)
    if path.resolve() == CURRENT10:
        return ORIGINAL(FROZEN10)
    return ORIGINAL(path)


if __name__ == "__main__":
    with patch.object(Path, "read_bytes", read_historical):
        historical.verify()
