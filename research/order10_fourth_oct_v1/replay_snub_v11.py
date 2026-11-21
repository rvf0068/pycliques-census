"""Replay immutable v11 snub-promotion proof against the historical current root.

Version v12 is the authoritative root now. The archived v11 verifier and
its tests explicitly asserted that the working root was v11. Rather than
rewrite that historical proof, redirect read_bytes() for that one root path
to the untouched frozen v11 file while replaying it.
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
HISTORICAL_VERIFY = ROOT / "research/snub_promotion_v1/verify.py"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tests", action="store_true")
    args = parser.parse_args()
    original = Path.read_bytes

    def historical_read(path: Path) -> bytes:
        return original(FROZEN if path.resolve() == CURRENT else path)

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
