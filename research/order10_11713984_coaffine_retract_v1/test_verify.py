"""Adversarial replay of the exact 169-to-35 coaffine stable image."""
from __future__ import annotations

import base64
import json
import unittest
import zlib

import networkx as nx

from research.order10_p3_global_v23_index.independent_verify import independent_p3
from research.order10_11713984_coaffine_retract_v1.verify import (
    ARCHIVE, SOURCE_G6, audit_map, audit_connected_coaffine_join, verify,
)


class P3StableImageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = json.loads(ARCHIVE.read_text(encoding="utf-8"))
        cls.G = independent_p3(SOURCE_G6)
        cls.f = list(zlib.decompress(base64.b64decode(
            cls.original["map_zlib_base64"], validate=True)))
        cls.S = set(cls.original["stable_image_vertices"])

    def test_complete_positive_replay_and_homology_bound(self):
        proof = verify()
        self.assertEqual(proof["retraction_image"]["isomorphic_to"],
                         "O14_join_complement_C7")
        self.assertEqual(proof["cliques_of_image"], 114688)
        self.assertEqual(
            proof["next_pared_iterate_free_Z_homology_dimension"], 40959)
        self.assertEqual(proof["next_pared_iterate_minimum_vertices"], 81920)
        self.assertTrue(proof["original_K_divergent"])
        self.assertTrue(proof["connected_summand_certificate"]["expansive_retract"])
        self.assertTrue(
            proof["connected_summand_certificate"]["both_coaffinations_verified_on_all_pairs"]
        )
        self.assertEqual(proof["ten_v27_indeterminate_population_unchanged"], 1044)

    def test_connected_coaffine_summand_hypotheses(self):
        Y, _ = audit_map(self.G, self.f, self.S)
        pairs = self.original["complement_two_vertex_components"]
        seven = self.original["complement_seven_cycle_vertices"]
        summary = audit_connected_coaffine_join(Y, self.f, pairs, seven)
        self.assertEqual(summary["coaffine_octahedral_factor_dimension"], 14)
        self.assertEqual(summary["connected_coaffine_factor"], "complement_C7")

    def test_broken_join_cross_edge_invalidates_divergence_certificate(self):
        Y, _ = audit_map(self.G, self.f, self.S)
        pairs = self.original["complement_two_vertex_components"]
        seven = self.original["complement_seven_cycle_vertices"]
        bad = Y.copy()
        bad.remove_edge(pairs[0][0], seven[0])
        with self.assertRaisesRegex(AssertionError, "join cross-edges"):
            audit_connected_coaffine_join(bad, self.f, pairs, seven)

    def test_broken_connected_factor_coaffination_is_rejected(self):
        Y, _ = audit_map(self.G, self.f, self.S)
        pairs = self.original["complement_two_vertex_components"]
        seven = self.original["complement_seven_cycle_vertices"]
        broken = self.f.copy()
        broken[seven[0]] = seven[0]
        with self.assertRaisesRegex(AssertionError, "coaffine"):
            audit_connected_coaffine_join(Y, broken, pairs, seven)

    def test_original_map_has_exact_idempotent_fourteenth_power(self):
        Y, r = audit_map(self.G, self.f, self.S)
        self.assertEqual((len(Y), Y.number_of_edges()), (35, 574))
        self.assertTrue(all(r[v] == v for v in self.S))
        self.assertTrue(all(r[u] == r[v] or self.G.has_edge(r[u], r[v])
                            for u, v in self.G.edges()))

    def test_fixed_point_invalidates_coaffinity(self):
        broken = self.f.copy()
        broken[0] = 0
        with self.assertRaisesRegex(AssertionError, "Coaffine"):
            audit_map(self.G, broken, self.S)

    def test_wrong_stable_image_cannot_pass(self):
        with self.assertRaisesRegex(AssertionError, "invariant image"):
            audit_map(self.G, self.f, self.S - {next(iter(self.S))})

    def test_new_edge_between_vertex_and_coaffine_image_is_rejected(self):
        wrong = self.G.copy()
        wrong.add_edge(0, self.f[0])
        with self.assertRaisesRegex(AssertionError, "Coaffine"):
            audit_map(wrong, self.f, self.S)


if __name__ == "__main__":
    unittest.main()
