"""Exact mathematical unit tests of coaffine invariant-orbit expansivity."""
from __future__ import annotations

import unittest

import networkx as nx

from research.order10_v28_p3_coaffine_all_v1.orbit_certificates import (
    orbit_certificate,
)


class CoaffineOrbitProofTests(unittest.TestCase):
    def test_three_pairwise_complete_invariant_orbits(self):
        H = nx.Graph()
        H.add_nodes_from(range(6))
        H.add_edges_from([(0, 1), (2, 3), (4, 5)])
        X = nx.complement(H)
        f = [i ^ 1 for i in range(6)]
        report = orbit_certificate(X, f)
        self.assertEqual(report["coaffine_orbit_count"], 3)
        self.assertEqual(report["compatible_orbit_pair_count"], 3)
        self.assertTrue(report["expansive_coaffine_subgraph_proved"])
        self.assertIn("Theorem 3.6", report["published_divergence_theorem"])

    def test_two_disconnected_factors_not_expansive_by_join_criterion(self):
        H = nx.Graph()
        H.add_nodes_from(range(4))
        H.add_edges_from([(0, 1), (2, 3)])
        X = nx.complement(H)
        report = orbit_certificate(X, [1, 0, 3, 2])
        self.assertEqual(report["compatible_orbit_pair_count"], 1)
        self.assertFalse(report["expansive_coaffine_subgraph_proved"])

    def test_connected_factor_joins_single_antipodal_pair(self):
        H = nx.disjoint_union(nx.path_graph(2), nx.cycle_graph(7))
        X = nx.complement(H)
        f = [1, 0] + [2 + ((i + 1) % 7) for i in range(7)]
        report = orbit_certificate(X, f)
        self.assertTrue(report["expansive_coaffine_subgraph_proved"])
        self.assertEqual(report["coaffine_orbit_count"], 2)
        self.assertIn("Theorem 4.6", report["published_divergence_theorem"])
        self.assertEqual(sorted(map(len,
            report["certified_invariant_factor_orbits"])), [2,7])

    def test_connected_coaffine_cycle_alone_not_incorrectly_promoted(self):
        G = nx.complement(nx.cycle_graph(7))
        f = [(i + 1) % 7 for i in range(7)]
        report = orbit_certificate(G, f)
        self.assertEqual(report["coaffine_orbit_count"], 1)
        self.assertFalse(report["expansive_coaffine_subgraph_proved"])

    def test_illegal_noncoaffine_map_is_rejected(self):
        G = nx.complement(nx.cycle_graph(7))
        with self.assertRaisesRegex(AssertionError, "Coaffine"):
            orbit_certificate(G, list(range(7)))


if __name__ == "__main__":
    unittest.main()
