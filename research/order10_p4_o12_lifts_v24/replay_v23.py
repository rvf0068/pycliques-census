"""Read-only replay of immutable ten-v23 proof archives under current v24.

Only the former *mutable root Path alias* is redirected to its
previous frozen v23 snapshot; the actual working files are untouched.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import unittest
from unittest.mock import patch

from research.order10_direct_retractions_v23 import (
    verify as old_direct, scan as old_scan, test_verify as old_direct_tests,
)
from research.order10_p3_global_v23_index import (
    classes as old_p3, independent_verify as old_p3_verify,
    test_classes as old_p3_tests,
)

V23 = Path(__file__).resolve().parents[2] / "indeterminate_order_10_v23.txt"


def run_suite(module) -> None:
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    report = unittest.TextTestRunner(verbosity=2).run(suite)
    if not report.wasSuccessful():
        raise RuntimeError("Failed historical test module: " + module.__name__)


def replay_direct() -> None:
    with (
        patch.object(old_direct, "CURRENT", V23),
        patch.object(old_direct_tests, "CURRENT", V23),
    ):
        old_direct.verify_archive()
        old_scan.screen()
        run_suite(old_direct_tests)
    print("PASS: immutable ten-v23 149 direct-retraction proofs"
          " and complete independent nine-reference scan")


def replay_p3() -> None:
    with (
        patch.object(old_p3, "CURRENT", V23),
        patch.object(old_p3_verify, "CURRENT", V23),
    ):
        result = old_p3.build()
        if result["counts"]["exact_isomorphism_classes"] != 525:
            raise ValueError("Historic v23 global P3 index changed")
        old_p3_verify.verify_archive()
        run_suite(old_p3_tests)
    print("PASS: immutable ten-v23 global P3 525 exact isomorphism"
          " classes and full all-pairs proof replay")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("stage", choices=("direct", "p3", "all"))
    args = p.parse_args()
    if args.stage in ("direct", "all"):
        replay_direct()
    if args.stage in ("p3", "all"):
        replay_p3()


if __name__ == "__main__":
    main()
