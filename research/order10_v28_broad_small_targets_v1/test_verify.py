"""Adversarial finite graph tests for positive-only small-target pilot."""
from __future__ import annotations

import unittest

import networkx as nx

from research.order10_v28_broad_small_targets_v1.search import (
    divergent_targets, find_retraction, source_records,
)
from research.order10_v28_broad_small_targets_v1.verify import (
    checked_target,
)


class BroadSmallTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.targets = divergent_targets()

    def test_all_atlas_bases_are_checked_against_published_theorem(self):
        self.assertGreater(len(self.targets), 12)
        self.assertTrue(any(t["kind"] == "connected_summand_theorem_4_6"
                            for t in self.targets))
        for t in self.targets:
            independent = checked_target(t)
            self.assertEqual(len(independent), t["order"])
            self.assertTrue(nx.is_isomorphic(independent, t["graph"]))

    def test_positive_octahedral_retraction_with_an_extra_twin(self):
        H = nx.Graph()
        H.add_nodes_from(range(6))
        H.add_edges_from([(0, 1), (2, 3), (4, 5)])
        O3 = nx.complement(H)
        X = O3.copy()
        X.add_node(6)
        X.add_edges_from((6, t) for t in O3.neighbors(0))
        witness = find_retraction(X, self.targets)
        self.assertIsNotNone(witness)
        self.assertEqual(witness["target_order"], 6)
        self.assertEqual(set(witness["target_vertices"]), set(range(6)))
        self.assertEqual(witness["retraction_images"][6], 0)

    def test_nonadjacent_extra_vertex_has_no_false_positive(self):
        X = nx.empty_graph(10)
        self.assertIsNone(find_retraction(X, self.targets))

    def test_all_613_current_stiff_originals_are_present(self):
        self.assertEqual(len(source_records()), 613)

    def test_noncoaffine_automorphism_is_rejected(self):
        record = next(
            dict(t) for t in self.targets
            if t["kind"] == "connected_summand_theorem_4_6"
        )
        record["base_coaffination"] = list(range(
            len(record["base_coaffination"])
        ))
        with self.assertRaisesRegex(AssertionError, "coaffine"):
            checked_target(record)

    def test_malformed_reference_graph_is_rejected(self):
        item = next(dict(t) for t in self.targets
                    if t["kind"] == "cycle_complement_theorem_5_4")
        item["order"] = item["order"] + 1
        with self.assertRaisesRegex(AssertionError, "order"):
            checked_target(item)


if __name__ == "__main__":
    unittest.main()
