"""Small positive graph tests and adversarial checks for coaffine audit."""
from __future__ import annotations

import unittest

import networkx as nx

from research.order10_three_p3_coaffine_native_v1.verify import (
    audit_positive_map, power_map,
)


def octahedron(m: int) -> tuple[nx.Graph, list[int]]:
    H = nx.Graph()
    H.add_nodes_from(range(2 * m))
    H.add_edges_from((2 * i, 2 * i + 1) for i in range(m))
    X = nx.complement(H)
    f = [i ^ 1 for i in range(2 * m)]
    return X, f


class CoaffineNativePilotTests(unittest.TestCase):
    def test_power_exponentiation_agrees_with_direct_composition(self):
        f = [1, 2, 0, 4, 3]
        for e in range(1, 18):
            direct = list(range(len(f)))
            for _ in range(e):
                direct = [f[v] for v in direct]
            self.assertEqual(power_map(f, e), direct)

    def test_three_coaffine_summands_are_expansive(self):
        X, f = octahedron(3)
        report = audit_positive_map(X, f)
        self.assertTrue(report["ordinary_retraction_verified_on_all_edges"])
        self.assertEqual(report["stable_order"], 6)
        self.assertEqual(report["coaffine_component_orbit_factor_sizes"],
                         [2, 2, 2])
        self.assertEqual(report["expansive_witness"]["theorem"],
                         "Larrion--Neumann-Lara--Pizana 2009 Theorem 3.6")

    def test_two_discrete_summands_do_not_pass_connected_theorem(self):
        X, f = octahedron(2)
        report = audit_positive_map(X, f)
        self.assertFalse(report["expansive_witness"]["proved"])

    def test_connected_coaffine_summand(self):
        H = nx.disjoint_union(nx.path_graph(2), nx.cycle_graph(7))
        Y = nx.complement(H)
        f = [1, 0] + [2 + ((i + 1) % 7) for i in range(7)]
        report = audit_positive_map(Y, f)
        self.assertEqual(report["coaffine_component_orbit_factor_sizes"],
                         [2, 7])
        self.assertEqual(report["connected_coaffine_factors"], 1)
        self.assertEqual(report["expansive_witness"]["theorem"],
                         "Larrion--Neumann-Lara--Pizana 2009 Theorem 4.6")

    def test_eventual_stable_image_yields_actual_retraction(self):
        Y, fy = octahedron(3)
        X = Y.copy()
        # Add a false twin of vertex 0: its edges are the same as 0's
        # but it is not adjacent to 0. Map it to the image fy[0].
        X.add_node(6)
        X.add_edges_from((6, v) for v in Y.neighbors(0))
        f = fy + [fy[0]]
        report = audit_positive_map(X, f)
        self.assertEqual(report["stable_order"], 6)
        self.assertEqual(report["transient_depth"], 1)
        self.assertTrue(report["expansive_witness"]["proved"])

    def test_non_coaffine_map_is_rejected(self):
        X, f = octahedron(3)
        f[0] = 0
        with self.assertRaisesRegex(AssertionError, "Coaffine"):
            audit_positive_map(X, f)

    def test_broken_source_adjacency_preservation_rejected(self):
        X, f = octahedron(3)
        f[0] = 3
        with self.assertRaises(AssertionError):
            audit_positive_map(X, f)

    def test_malformed_power_rejected(self):
        with self.assertRaisesRegex(AssertionError, "power exponent"):
            power_map([1, 0], 0)


if __name__ == "__main__":
    unittest.main()
