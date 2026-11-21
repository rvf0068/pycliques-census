"""Replay the immutable v3/v11 snub-promotion proof with historical roots.

The historical verifier and its tests require *both* working index files
to equal their original snapshots (order nine v3, order ten v11). Redirect
only those two read_bytes() calls to the frozen files. Neither verifier,
its source hashes, nor the current v4/v14 census files are modified.
"""
from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path
from unittest import TestLoader, TextTestRunner
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_ROOTS = {
    (ROOT / "indeterminate_order_9.txt").resolve():
        ROOT / "indeterminate_order_9_v3.txt",
    (ROOT / "indeterminate_order_10.txt").resolve():
        ROOT / "indeterminate_order_10_v11.txt",
}
HISTORICAL_VERIFY = ROOT / "research/snub_promotion_v1/verify.py"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tests", action="store_true")
    args = parser.parse_args()
    original = Path.read_bytes

    def historical_read(path: Path) -> bytes:
        return original(HISTORICAL_ROOTS.get(path.resolve(), path))

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
