"""Replay historical ten-v28 proofs after ten-v29 becomes the active root.

The immutable v28 verifier and its tests, and the four archived P3 positive
certificates, are not modified. Only one explicit mutable-root read of
each historical checker is redirected IN MEMORY to the exact pinned v28
snapshot. Never modify current or frozen source bytes on disk.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
import unittest

from research.order10_v28_connected_summand import (
    verify as v28, test_verify as v28_tests,
)
from research.order10_v28_p3_coaffine_all_v1 import (
    verify_positives as p3, test_positives as p3_tests,
)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def main() -> None:
    require(v28.WORKING == v28.ROOT / "indeterminate_order_10.txt"
            and v28.LATEST == v28.ROOT / "indeterminate_order_10_v28.txt",
            "Unexpected mutable-root alias or historical ten-v28 file")
    require(p3.SOURCE == p3.ROOT / "indeterminate_order_10_v28.txt",
            "Unexpected immutable four-positive source v28 path")
    original_read_bytes = Path.read_bytes
    active = p3.ROOT / "indeterminate_order_10.txt"

    def historic_read_bytes(path: Path) -> bytes:
        # Specific read redirection used by the old proof-only verifier.
        # Every other read uses its authentic on-disk, untouched bytes.
        if path == active:
            return original_read_bytes(p3.SOURCE)
        return original_read_bytes(path)

    # First replay the complete old ten-v27 -> ten-v28 proof and mutation
    # tests against its immutable v28 snapshot instead of ten-v29.
    with patch.object(v28, "WORKING", v28.LATEST):
        first = v28.verify()
        require(first["population"]["after"] == 1043,
                "Historical ten-v28 promotion population changed")
        first_suite = unittest.defaultTestLoader.loadTestsFromModule(v28_tests)
        first_outcome = unittest.TextTestRunner(verbosity=2).run(first_suite)
        require(first_outcome.wasSuccessful(),
                "Historical ten-v28 positive regression tests failed")

    # Old p3.verify() contained a deliberate assertion that the current
    # mutable root was still v28; replay that one read from frozen v28.
    # All historical graph6/certificate reads and proofs remain genuine.
    with patch.object(Path, "read_bytes", historic_read_bytes):
        second = p3.verify()
        require(second["count_newly_proved_divergent"] == 4,
                "Historical four P3-positive count changed")
        second_suite = unittest.defaultTestLoader.loadTestsFromModule(p3_tests)
        second_outcome = unittest.TextTestRunner(verbosity=2).run(second_suite)
        require(second_outcome.wasSuccessful(),
                "Historical four-positive regression tests failed")

    print("PASS: immutable ten-v28 connected-summand promotion and four "
          "historical P3 positive retraction proofs replayed against "
          "frozen v28 snapshots without changing active ten-v29", flush=True)


if __name__ == "__main__":
    main()
