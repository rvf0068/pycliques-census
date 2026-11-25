"""Adversarial tests for 98 reconstructed ten-P4 graph certificates."""
from __future__ import annotations

from copy import deepcopy
import unittest
from unittest.mock import patch

import networkx as nx

from . import verify, independent_verify


SMALL_IDX = 11708411
LARGE_IDX = 11651780


class SmallP4CertificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Complete current P3 representative enumeration from the original
        # ten-v25 source: one costly, authenticating call for all the tests.
        cls.records, cls.ten = verify.source_catalog()
        cls.byidx = {r["index"]: r for r in cls.records}

    def test_exact_complete_98_source_set(self):
        self.assertEqual(len(self.records), 98)
        self.assertEqual(len(self.byidx), 98)
        self.assertEqual([r["index"] for r in self.records],
                         sorted(self.byidx))
        self.assertEqual(self.byidx[SMALL_IDX]["p4"], [30, 390])
        self.assertEqual(self.byidx[LARGE_IDX]["p4"], [1010, 504797])

    def test_primary_one_small_proof_from_original_graph6(self):
        original = self.byidx[SMALL_IDX]
        raw, pared = verify.verify_record(original)
        self.assertEqual(verify.dims(raw), [40, 694])
        self.assertEqual(verify.dims(pared), [30, 390])
        self.assertEqual(original["fold_rounds"], [10])

    def test_independent_one_small_proof(self):
        independent_verify.verify_record(self.byidx[SMALL_IDX])

    def test_tampering_complete_adjacency_digest_is_rejected(self):
        record = deepcopy(self.byidx[SMALL_IDX])
        record["p4_adj_sha256"] = "0" * 64
        with self.assertRaisesRegex(AssertionError, "SHA mismatch"):
            verify.verify_record(record)
        with self.assertRaisesRegex(AssertionError, "SHA disagreement"):
            independent_verify.verify_record(record)

    def test_tampering_folding_round_is_rejected(self):
        record = deepcopy(self.byidx[SMALL_IDX])
        record["fold_rounds"] = []
        with self.assertRaises(AssertionError):
            verify.verify_record(record)
        with self.assertRaises(AssertionError):
            independent_verify.verify_record(record)

    def test_tampering_original_p3_source_is_rejected(self):
        record = deepcopy(self.byidx[SMALL_IDX])
        record["p3"] = [record["p3"][0], record["p3"][1] + 1]
        with self.assertRaises(AssertionError):
            verify.verify_record(record)
        with self.assertRaises(AssertionError):
            independent_verify.verify_record(record)

    def test_independent_fold_uses_closed_N_and_fixes_terminal_core(self):
        # The four-vertex path folds all the way to K1, using a truly
        # independent adjacency-row implementation.
        path_rows = [
            1 << 1,
            (1 << 0) | (1 << 2),
            (1 << 1) | (1 << 3),
            1 << 2,
        ]
        pared, rounds = independent_verify.closed_neighborhood_folds(
            path_rows
        )
        self.assertEqual(pared, [0])
        self.assertGreaterEqual(sum(rounds), 3)

    def test_p4_adjacency_symmetry_guard(self):
        with self.assertRaisesRegex(AssertionError, "Asymmetric"):
            verify.dims([2, 0])
        with self.assertRaisesRegex(AssertionError, "asymmetric"):
            independent_verify.shape([2, 0])

    def test_independent_fourth_facet_mismatch_is_fatal(self):
        with patch.object(independent_verify, "maximal_cliques_bk",
                          return_value=[0]):
            with self.assertRaisesRegex(AssertionError, "clique mismatch"):
                independent_verify.raw_fourth_graph(nx.path_graph(4))

    def test_unknown_immutable_path_rejected(self):
        with self.assertRaisesRegex(AssertionError, "Unexpected"):
            verify.read_pinned("indeterminate_order_10.txt")


if __name__ == "__main__":
    unittest.main()
