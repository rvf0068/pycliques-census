"""Mutations proving the independent octahedral positive-map audit is strict."""
from __future__ import annotations

import unittest

import networkx as nx

from research.order10_v28_p3_octahedral_511_v1.verify import verify_positive


class P3OctahedralPilotTests(unittest.TestCase):
    @staticmethod
    def host():
        H = nx.Graph()
        H.add_nodes_from(range(6))
        H.add_edges_from([(0, 1), (2, 3), (4, 5)])
        return nx.complement(H)

    def test_induced_octahedron_has_an_ordinary_identity_retraction(self):
        from research.order10_overcap_p3_coaffine_v1.pilot import (
            independent_octahedral_retraction_check,
        )
        O3 = self.host()
        pairs = [(0, 1), (2, 3), (4, 5)]
        independent_octahedral_retraction_check(
            O3, tuple(pairs), dict(enumerate(range(6))))
        self.assertEqual(len(O3), 6)

    def test_illegal_target_cross_edge_is_rejected(self):
        from research.order10_overcap_p3_coaffine_v1.pilot import (
            independent_octahedral_retraction_check,
        )
        O3 = self.host()
        O3.remove_edge(0, 2)
        with self.assertRaisesRegex(AssertionError, "cross-edge"):
            independent_octahedral_retraction_check(
                O3, ((0, 1), (2, 3), (4, 5)),
                dict(enumerate(range(6))),
            )

    def test_unsafe_projection_is_rejected(self):
        from research.order10_overcap_p3_coaffine_v1.pilot import (
            independent_octahedral_retraction_check,
        )
        O3 = self.host()
        bad = dict(enumerate(range(6)))
        bad[0] = 2
        with self.assertRaisesRegex(AssertionError, "fix"):
            independent_octahedral_retraction_check(
                O3, ((0, 1), (2, 3), (4, 5)), bad
            )

    def test_malformed_positive_map_is_rejected_before_graph_replay(self):
        original = {
            "index": 100,
            "graph6": nx.to_graph6_bytes(
                self.host(), header=False).decode().strip(),
            "p3": [6, 12],
            "p3_graph6_sha256": "x",
            "members": [100],
        }
        witness = {
            "target_pairs": [[0, 1], [2, 3], [4, 5]],
            "target_dimension": 3,
            "complete_retraction_map": [0, 1, 2, 3, 4, 5],
            "originals_proven_divergent": [100],
            "value_order": "label",
        }
        with self.assertRaisesRegex(AssertionError, "independently reconstructed"):
            verify_positive(original, witness)


if __name__ == "__main__":
    unittest.main()
