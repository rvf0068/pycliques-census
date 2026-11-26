"""Replay frozen ten-v27 proofs after the ten-v28 root becomes current.

Redirect only the historical verifier's mutable-root alias *in memory* to
its unchanged immutable v27 snapshot. Neither index nor certificate is edited.
"""
from __future__ import annotations

import unittest
from unittest.mock import patch

from research.order10_v27_two_p3_o11 import (
    verify as v27, test_verify as v27_tests,
)


def main() -> None:
    if v27.WORKING != v27.ROOT / "indeterminate_order_10.txt":
        raise AssertionError("Unexpected historical ten-v27 mutable root")
    if v27.LATEST != v27.ROOT / "indeterminate_order_10_v27.txt":
        raise AssertionError("Unexpected historical ten-v27 snapshot path")
    with patch.object(v27, "WORKING", v27.LATEST):
        result = v27.verify()
        if result["population"]["after"] != 1044:
            raise AssertionError("Historical v27 count was changed")
        suite = unittest.defaultTestLoader.loadTestsFromModule(v27_tests)
        outcome = unittest.TextTestRunner(verbosity=2).run(suite)
        if not outcome.wasSuccessful():
            raise RuntimeError("Frozen historical ten-v27 positive proofs failed")
    print("PASS: immutable ten-v27 O11 proof and regression tests "
          "replayed against frozen historical v27 index", flush=True)


if __name__ == "__main__":
    main()
