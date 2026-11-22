"""Read-only replay of the archived order-nine v4 / order-ten v14 proof.

The old verifier checks that the working order-ten root is exactly v14.
Under v16, redirect its two historical root reads to frozen v14/v4 snapshots.
Never edit the old checker, its source inputs, saved certificates, or root.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from research.order9_p2_iso_lift_v1 import verify as historical

ROOT = Path(__file__).resolve().parents[2]
CURRENT10 = (ROOT / "indeterminate_order_10.txt").resolve()
CURRENT9 = (ROOT / "indeterminate_order_9.txt").resolve()
FROZEN14 = ROOT / "indeterminate_order_10_v14.txt"
FROZEN9V4 = ROOT / "indeterminate_order_9_v4.txt"
ORIGINAL = Path.read_bytes


def read_historical(path: Path) -> bytes:
    if path.resolve() == CURRENT10:
        return ORIGINAL(FROZEN14)
    if path.resolve() == CURRENT9:
        return ORIGINAL(FROZEN9V4)
    return ORIGINAL(path)


if __name__ == "__main__":
    with patch.object(Path, "read_bytes", read_historical):
        historical.verify()
