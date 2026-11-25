"""Replay immutable ten-v26 proofs after ten-v27 becomes current.

The historical ten-v26 files and positive certificates stay untouched.
Only its mutable-root alias is redirected in memory to the frozen snapshot.
"""
from __future__ import annotations

import unittest
from unittest.mock import patch

from research.order10_v26_six_p3_octahedral import (
    verify as v26,
    test_verify as v26_tests,
)


def main() -> None:
    if v26.WORKING != v26.ROOT / "indeterminate_order_10.txt":
        raise AssertionError("Unexpected historical v26 mutable root")
    if v26.LATEST != v26.ROOT / "indeterminate_order_10_v26.txt":
        raise AssertionError("Unexpected historical v26 snapshot path")
    with patch.object(v26, "WORKING", v26.LATEST):
        v26.verify()
        suite = unittest.defaultTestLoader.loadTestsFromModule(v26_tests)
        outcome = unittest.TextTestRunner(verbosity=2).run(suite)
        if not outcome.wasSuccessful():
            raise RuntimeError("Historical ten-v26 positive proofs failed")
    print("PASS: immutable ten-v26 six-positive proof and regression tests "
          "replayed against frozen historical v26 index", flush=True)


if __name__ == "__main__":
    main()
