"""Replay and deliberately corrupt the four-core O4 divergence proofs."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import order10_four_o4_lift_v1 as proof


class FourCoreO4DivergenceTests(unittest.TestCase):
    def test_both_complete_nine_vertex_retractions(self):
        for graph6, witness in proof.PROOFS.items():
            result = proof.verify_core(graph6, witness)
            self.assertEqual(result["edge_constraints_verified"],
                             result["final_retract_source_edges"])
            self.assertEqual(len(result["o4_target"]), 8)
        self.assertEqual(proof.verify()["newly_proved_divergent_original_order10"], 192)

    def test_isomorphic_three_covers_thirteen_original_graphs(self):
        canonical = proof.decode("HQqvUx}")
        self.assertTrue(proof.nx.is_isomorphic(canonical, proof.decode("HEhutzm")))
        self.assertTrue(proof.nx.is_isomorphic(canonical, proof.decode("HEht}rl")))
        self.assertFalse(proof.nx.is_isomorphic(canonical, proof.decode("HEnfbzm")))
        groups, associations = proof.certified_coverage()
        self.assertEqual(len(groups), 147)
        self.assertEqual(sum(map(len, groups.values())), 192)
        self.assertEqual(set(associations.values()), set(proof.SEED_REFERENCES))
        for graph6, seed in associations.items():
            self.assertTrue(proof.nx.is_isomorphic(
                proof.decode(graph6), proof.decode(seed)))

    def test_mutated_graph_retraction_is_rejected(self):
        witness = copy.deepcopy(proof.PROOFS["HQqvUx}"])
        witness["projection"][0][1] = witness["target"][1]
        with self.assertRaisesRegex(ValueError, "fixed retraction section"):
            proof.verify_core("HQqvUx}", witness)

    def test_broken_dominated_fold_is_rejected(self):
        witness = copy.deepcopy(proof.PROOFS["HQqvUx}"])
        witness["folds"][2][0] = [7, 7]
        with self.assertRaisesRegex(ValueError, "Invalid dominated-vertex fold"):
            proof.verify_core("HQqvUx}", witness)

    def test_wrong_octahedron_target_is_rejected(self):
        witness = copy.deepcopy(proof.PROOFS["HEnfbzm"])
        witness["target"][0] = 1
        with self.assertRaises(ValueError):
            proof.verify_core("HEnfbzm", witness)

    def test_frozen_v7_and_exact_v8_root(self):
        rows = proof.frozen_v7_rows()
        self.assertEqual(len(rows), 8124)
        self.assertEqual(proof.V8.read_text(), proof.next_index_content())
        self.assertEqual(proof.CURRENT.read_text(), proof.next_index_content())


if __name__ == "__main__":
    unittest.main()
