"""Replay immutable ten-v25 certificates after ten-v26 becomes current.

Historical proof inputs, verifier, tests and Git blob pins are not edited.
Only the former mutable working-root *alias* in the old verifier module
is temporarily pointed to the unchanged historical v25 snapshot.
"""
from __future__ import annotations

import unittest
from unittest.mock import patch

from research.order10_p4_crossdepth_o15_v25 import (
    verify as v25,
    test_verify as v25_tests,
)


def main() -> None:
    if v25.CURRENT != v25.ROOT / "indeterminate_order_10.txt":
        raise AssertionError("Unexpected historical verifier root alias")
    if v25.LATEST != v25.ROOT / "indeterminate_order_10_v25.txt":
        raise AssertionError("Unexpected historical ten-v25 snapshot path")
    # The old verifier checks the original complete retractions and source
    # hashes; it must see its frozen v25 snapshot rather than v26.
    with patch.object(v25, "CURRENT", v25.LATEST):
        v25.verify_archive()
        suite = unittest.defaultTestLoader.loadTestsFromModule(v25_tests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            raise RuntimeError("Historical ten-v25 positive regression failed")
    print("PASS: immutable ten-v25 cross-depth proofs replayed under pinned "
          "in-memory historical snapshot alias", flush=True)


if __name__ == "__main__":
    main()
