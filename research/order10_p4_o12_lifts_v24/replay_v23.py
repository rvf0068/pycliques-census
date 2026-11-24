"""Replay immutable v23 proof stages against the frozen v23 index.

Historic v23 code assumes its once-current root is v23. After a new
certified census advancement, redirect *only* that root Path reference
for historical replay; never modify the repository working root.
"""
from __future__ import annotations

import unittest
from unittest.mock import patch

from research.order10_direct_retractions_v23 import (
    verify as historical, scan, test_verify,
)
from research.order10_p3_global_v23_index import (
    classes as p3builder, independent_verify as p3verifier, test_classes,
)

from pathlib import Path

V23 = Path(__file__).resolve().parents[2] / "indeterminate_order_10_v23.txt"


def run() -> None:
    with (
        patch.object(historical, "CURRENT", V23),
        patch.object(test_verify, "CURRENT", V23),
    ):
        historical.verify_archive()
        scan.screen()
        tests = unittest.defaultTestLoader.loadTestsFromModule(test_verify)
        report = unittest.TextTestRunner(verbosity=2).run(tests)
        if not report.wasSuccessful():
            raise RuntimeError("Historical v23 direct-retraction tests failed")
    with (
        patch.object(p3builder, "CURRENT", V23),
        patch.object(p3verifier, "CURRENT", V23),
    ):
        result = p3builder.build()
        if result["counts"]["exact_isomorphism_classes"] != 525:
            raise ValueError("Changed historical v23 P3 isomorphism census")
        p3verifier.verify_archive()
        tests = unittest.defaultTestLoader.loadTestsFromModule(test_classes)
        report = unittest.TextTestRunner(verbosity=2).run(tests)
        if not report.wasSuccessful():
            raise RuntimeError("Historical v23 P3 class tests failed")
    print("PASS: historical ten-v23 direct 149 and global P3 525"
          " certificate replays on immutable frozen indices")


if __name__ == "__main__":
    run()
