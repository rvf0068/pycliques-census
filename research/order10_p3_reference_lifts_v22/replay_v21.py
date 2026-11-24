"""Replay historically certified ten-v21 against its immutable working root.

The original v21 verifier remains byte-for-byte unchanged. Redirect only
reads of the mutable ten-vertex working root to the frozen v21 snapshot.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from research.order10_p2_reference_lifts_v21 import verify as old

ROOT = Path(__file__).resolve().parents[2]
MUTABLE = (ROOT / "indeterminate_order_10.txt").resolve()
FROZEN = ROOT / "indeterminate_order_10_v21.txt"
ORIGINAL_READ_BYTES = Path.read_bytes


def historical_bytes(path: Path) -> bytes:
    return ORIGINAL_READ_BYTES(FROZEN if path.resolve() == MUTABLE else path)


def main() -> None:
    with patch.object(Path, "read_bytes", historical_bytes):
        old.verify_archive()


if __name__ == "__main__":
    main()
