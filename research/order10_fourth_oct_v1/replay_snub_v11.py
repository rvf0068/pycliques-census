"""Replay immutable v11 snub-promotion proof against the historical current root.

The archived v11 verifier and
its tests assert that the working order-ten root is v11 and the
order-nine root is v3. Redirect only read_bytes() for those two paths
to the untouched frozen v11 and v3 inputs during historical replay.
"""
from __future__ import annotations
import argparse
import runpy
import sys
from pathlib import Path
from unittest import TestLoader, TextTestRunner
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
CURRENT = (ROOT / "indeterminate_order_10.txt").resolve()
FROZEN = ROOT / "indeterminate_order_10_v11.txt"
CURRENT9 = (ROOT / "indeterminate_order_9.txt").resolve()
FROZEN9 = ROOT / "indeterminate_order_9_v3.txt"
HISTORICAL_VERIFY = ROOT / "research/snub_promotion_v1/verify.py"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tests", action="store_true")
    args = parser.parse_args()
    original = Path.read_bytes

    def historical_read(path: Path) -> bytes:
        requested = path.resolve()
        if requested == CURRENT:
            return original(FROZEN)
        if requested == CURRENT9:
            return original(FROZEN9)
        return original(path)

    old_argv = sys.argv
    try:
        sys.argv = [str(HISTORICAL_VERIFY)]
        with patch.object(Path, "read_bytes", historical_read):
            runpy.run_path(str(HISTORICAL_VERIFY), run_name="__main__")
            if args.tests:
                suite = TestLoader().discover(
                    str(ROOT / "research/snub_promotion_v1"),
                    pattern="test_verify.py",
                )
                result = TextTestRunner(verbosity=2).run(suite)
                if not result.wasSuccessful():
                    raise SystemExit(1)
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    main()
