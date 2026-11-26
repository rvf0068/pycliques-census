"""Reproducibility and mutation tests of seeded coaffine search."""
from __future__ import annotations

import unittest

import networkx as nx

from research.order10_v28_p3_relabelled_coaffine_v1.search import (
    SEEDS, ORDERS, canonical_permutation,
)
from research.order10_v28_p3_coaffine_all_v1.orbit_certificates import (
    orbit_certificate,
)


class SeededCoaffineTests(unittest.TestCase):
    def test_permutations_exact_and_reproducible(self):
        for n in (15, 37, 87):
            for index in (10481909, 11708411):
                seen = []
                for seed in SEEDS:
                    a = canonical_permutation(n, index, seed)
                    self.assertEqual(a, canonical_permutation(n, index, seed))
                    self.assertEqual(sorted(a), list(range(n)))
                    seen.append(tuple(a))
                self.assertEqual(len(set(seen)), len(SEEDS))

    def test_same_graph_with_reordered_node_insertion(self):
        G = nx.cycle_graph(7)
        order = canonical_permutation(7, 10481909, SEEDS[0])
        reordered = nx.Graph()
        reordered.add_nodes_from(order)
        reordered.add_edges_from(G.edges())
        self.assertEqual(list(reordered), order)
        self.assertEqual(set(reordered.edges()), set(G.edges()))

    def test_bad_seed_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, "permutation"):
            canonical_permutation(10, 10481909, 77)

    def test_invariant_orbit_coaffine_positive_is_still_valid(self):
        H = nx.Graph()
        H.add_nodes_from(range(6))
        H.add_edges_from([(0,1), (2,3), (4,5)])
        X = nx.complement(H)
        report = orbit_certificate(X, [v ^ 1 for v in X])
        self.assertTrue(report["expansive_coaffine_subgraph_proved"])


if __name__ == "__main__":
    unittest.main()
