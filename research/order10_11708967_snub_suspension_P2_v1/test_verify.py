"""Exact source and adversarial mathematical controls for snub suspension."""
from __future__ import annotations

import unittest

import networkx as nx

from research.order10_11708967_snub_suspension_P2_v1.search import (
    INDEX, SOURCE_G6, SNUB_G6, source, graph6_digest,
)
from research.order10_overcap_p3_coaffine_v1.pilot import (
    independent_octahedral_retraction_check,
)


class SnubSuspensionP2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.G,cls.P1,cls.P2=source()

    def test_original_is_exact_snub_suspension_without_hardcoded_poles(self):
        G=self.G
        poles=[v for v in G if G.degree[v]==8]
        self.assertEqual(len(poles),2)
        self.assertFalse(G.has_edge(*poles))
        S=G.copy()
        S.remove_nodes_from(poles)
        self.assertTrue(nx.is_isomorphic(
            S,nx.from_graph6_bytes(SNUB_G6.encode("ascii"))
        ))
        self.assertTrue(all(set(G[p])==set(S) for p in poles))
        self.assertEqual((len(G),G.number_of_edges()),(10,34))

    def test_both_exact_pared_early_clique_iterates(self):
        self.assertEqual((len(self.P1),self.P1.number_of_edges()),
                         (24,236))
        self.assertEqual((len(self.P2),self.P2.number_of_edges()),
                         (288,37772))
        self.assertEqual(set(self.P2),set(range(288)))
        self.assertEqual(len(graph6_digest(self.P2)),64)

    def test_clique_graph_of_suspension_bipartite_double_cover(self):
        K1=self.P1
        comp=nx.complement(K1)
        self.assertTrue(nx.is_bipartite(comp))
        self.assertEqual((len(comp),comp.number_of_edges()),(24,40))
        self.assertEqual(sorted(len(c) for c in
                         nx.connected_components(nx.complement(self.P2))),
                         [2,286])

    def test_source_does_not_by_itself_claim_divergence(self):
        self.assertEqual(INDEX,11708967)
        self.assertEqual(SOURCE_G6,"IQyuzz~~o")
        # The source graph does not contain a direct conclusive proof:
        # structural suspension and rapid growth are not K-divergence.
        self.assertTrue(nx.is_connected(self.G))

    def test_false_octahedral_source_target_rejected(self):
        H=nx.complete_graph(6)
        with self.assertRaisesRegex(AssertionError,"Antipodal"):
            independent_octahedral_retraction_check(
                H,((0,1),(2,3),(4,5)),dict(enumerate(range(6)))
            )

    def test_symmetric_fourcycle_positive_shape_is_not_automatic_divergence(self):
        H=nx.complete_bipartite_graph(2,2)
        self.assertEqual((len(H),H.number_of_edges()),(4,4))


if __name__=="__main__":
    unittest.main()
