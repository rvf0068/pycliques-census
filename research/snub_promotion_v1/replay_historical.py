"""Replay immutable v2/v10 historical verifiers after a newer current-root update.

Only reads are redirected to the frozen version; no files are rewritten.
The separate v3/v11 verifier checks the actual authoritative current files.
"""
from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--order", type=int, choices=(9, 10), required=True)
    args = parser.parse_args()
    old_version = {9: "v2", 10: "v10"}[args.order]
    frozen = ROOT / f"indeterminate_order_{args.order}_{old_version}.txt"
    authoritative = ROOT / f"indeterminate_order_{args.order}.txt"
    script = (ROOT / f"research/order{args.order}_current_indeterminates_{old_version}"
              / "verify.py")
    real_read_bytes = Path.read_bytes

    def historical_read_bytes(self: Path) -> bytes:
        if self.resolve() == authoritative.resolve():
            return real_read_bytes(frozen)
        return real_read_bytes(self)

    original_argv = sys.argv
    try:
        sys.argv = [str(script)] + (["--self-test"] if args.order == 9 else [])
        with patch.object(Path, "read_bytes", historical_read_bytes):
            runpy.run_path(str(script), run_name="__main__")
    finally:
        sys.argv = original_argv


if __name__ == "__main__":
    main()
