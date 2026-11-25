"""Exact degree-obstruction and replay guard regressions."""
from __future__ import annotations

import unittest

import networkx as nx

from . import pilot


class CoaffineTenCoreTests(unittest.TestCase):
    def test_every_one_of_the_ten_has_degree_obstruction(self):
        hosts = pilot.source_catalog()
        self.assertEqual(len(hosts), 521)
        for idx in pilot.TEN_P3_OVERCAP:
            with self.subTest(McKay=idx):
                g = nx.from_graph6_bytes(
                    hosts[idx]["p3_graph6"].encode("ascii")
                )
                result = pilot.degree_obstruction(g)
                v = result["vertex"]
                H = nx.complement(g)
                self.assertGreater(H.degree(v), 0)
                self.assertTrue(all(
                    H.degree(v) != H.degree(w) for w in H[v]
                ))

    def test_no_false_obstruction_on_octagedron(self):
        # In O3 all vertices have the same degree and an antipode
        # outside the closed neighborhood, so degree cannot prohibit
        # its genuine coaffination.
        with self.assertRaisesRegex(AssertionError, "No degree"):
            pilot.degree_obstruction(nx.octahedral_graph())

    def test_malformed_coaffine_endomorphism_rejected(self):
        g = nx.cycle_graph(4)
        f = {v: v for v in g}
        with self.assertRaisesRegex(AssertionError, "closed"):
            pilot.independent_coaffine_check(g, f)

    def test_malformed_retraction_rejected(self):
        g = nx.octahedral_graph()
        H = nx.complement(g)
        pairs = tuple(tuple(edge) for edge in H.edges())
        self.assertEqual(len(pairs), 3)
        ret = {v: v for v in g}
        pilot.independent_octahedral_retraction_check(g, pairs, ret)
        ret[0] = 1
        with self.assertRaisesRegex(AssertionError, "does not fix"):
            pilot.independent_octahedral_retraction_check(g, pairs, ret)


if __name__ == "__main__":
    unittest.main()
