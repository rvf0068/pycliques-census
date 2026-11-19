"""Adversarial verification of the independent PR #39 O4 proof replay."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase, mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import heher_divergence_class_lift_v1 as lift


class IndependentlyReplayedReferenceTests(TestCase):
    def test_reconstructs_all_iterates_and_1225_edges_without_delegation(self):
        # The lift may use the immutable witness *data*, never the older checker.
        with mock.patch.object(
            lift.proof, "positive_second_graph",
            side_effect=AssertionError("delegated verification forbidden"),
        ), mock.patch.object(
            lift.proof, "third_iterate",
            side_effect=AssertionError("delegated construction forbidden"),
        ), mock.patch.object(
            lift.proof, "raw_K",
            side_effect=AssertionError("delegated K forbidden"),
        ):
            witness = lift.independently_replay_nine_vertex_divergence()
        self.assertEqual(witness["source_vertices"], 60)
        self.assertEqual(witness["source_edges"], 1225)
        self.assertEqual(len(witness["target_missing_pairs"]), 4)
        self.assertEqual(witness["verification"],
                         "independent_iterate_and_all_edge_constraints")

    def test_modified_witness_data_is_rejected(self):
        broken = list(lift.proof.PROJECTION)
        broken[lift.proof.TARGET[0]] = lift.proof.TARGET[1]
        with mock.patch.object(lift.proof, "PROJECTION", tuple(broken)):
            with self.assertRaisesRegex(ValueError, "does not fix"):
                lift.independently_replay_nine_vertex_divergence()

    def test_modified_proof_file_digest_is_rejected(self):
        with mock.patch.object(lift, "PROOF_SOURCE_BLOB", "0" * 40):
            with self.assertRaisesRegex(ValueError, "Proof source changed"):
                lift.independently_replay_nine_vertex_divergence()


if __name__ == "__main__":
    import unittest
    unittest.main()
