"""Exact small-stage regression tests; only official public coaffine solvers."""
from __future__ import annotations

import unittest

from research.order10_three_p2_coaffine_exhaustion_v1.verify import (
    EXPECTED, SNAPSHOT, SNAPSHOT_BLOB, HISTORICAL_CONTROL,
    HISTORICAL_CONTROL_BLOB, source_p2, exhaustive_check,
)
from research.order10_p4_crossdepth_o15_v25.verify import git_blob


class P2ExhaustionTests(unittest.TestCase):
    def test_all_four_immutable_P2_reconstructions(self):
        self.assertEqual(git_blob(SNAPSHOT.read_bytes()), SNAPSHOT_BLOB)
        self.assertEqual(git_blob(HISTORICAL_CONTROL.read_bytes()),
                         HISTORICAL_CONTROL_BLOB)
        for index, shape in EXPECTED.items():
            G, _ = source_p2(index)
            self.assertEqual((len(G), G.number_of_edges()), shape[:2])

    def test_wrong_index_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, "Unrecognized original"):
            source_p2(11716441)

    def test_python_backend_really_exhausts_both_orders(self):
        for index in EXPECTED:
            for order in ("label", "fiber"):
                record = exhaustive_check(index, "python", order)
                self.assertEqual(record["status"], "EXHAUSTED")
                self.assertTrue(record["no_coaffine_weak_endomorphism_at_P2"])
                self.assertTrue(record["does_not_establish_K_convergence"])

    def test_bad_search_policy_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, "Unknown solver"):
            exhaustive_check(next(iter(EXPECTED)), "unknown", "label")


if __name__ == "__main__":
    unittest.main()
