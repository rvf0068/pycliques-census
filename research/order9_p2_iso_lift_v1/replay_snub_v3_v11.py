"""Replay immutable order-nine v3 and order-ten v11 snub certificates under v4/v14.

The archived replay_snub_v11.py already redirects the order-ten current
root to frozen v11. Supply the missing order-nine v3 redirect *outside*
that historical wrapper, preserving all existing research files byte-for-byte.
Both the source-hash checks and the optional historical regression tests run.
No current or versioned census index is written.
"""
from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
ORDER9_CURRENT = (ROOT / "indeterminate_order_9.txt").resolve()
ORDER9_V3 = ROOT / "indeterminate_order_9_v3.txt"
OLD_WRAPPER = ROOT / "research/order10_fourth_oct_v1/replay_snub_v11.py"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tests", action="store_true")
    args = parser.parse_args()

    original = Path.read_bytes

    def historical_order9_read(path: Path) -> bytes:
        return original(ORDER9_V3 if path.resolve() == ORDER9_CURRENT else path)

    old_argv = sys.argv
    try:
        sys.argv = [str(OLD_WRAPPER)] + (["--tests"] if args.tests else [])
        with patch.object(Path, "read_bytes", historical_order9_read):
            # The original wrapper supplies the frozen order-ten v11 read.
            runpy.run_path(str(OLD_WRAPPER), run_name="__main__")
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    main()
