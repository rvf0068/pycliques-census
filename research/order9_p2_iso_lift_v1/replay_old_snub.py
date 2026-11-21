"""Read-only v4-compatible wrapper for the immutable v11 snub proof.

The original historical replay expects working order-nine v3 and order-ten
v11. Its own wrapper already redirects the order-ten working index. This
additional shim redirects only order-nine root reads to frozen v3 while
delegating all other operations to the original replay without changing
historical files or modifying the current roots.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from research.order10_fourth_oct_v1 import replay_snub_v11

ROOT = Path(__file__).resolve().parents[2]
CURRENT9 = (ROOT / "indeterminate_order_9.txt").resolve()
FROZEN9 = ROOT / "indeterminate_order_9_v3.txt"
ORIGINAL_READ = Path.read_bytes


def version_aware_read(path: Path) -> bytes:
    if path.resolve() == CURRENT9:
        return ORIGINAL_READ(FROZEN9)
    return ORIGINAL_READ(path)


if __name__ == "__main__":
    with patch.object(Path, "read_bytes", version_aware_read):
        replay_snub_v11.main()
