"""Positive and negative controls for first-iterate expansive coaffine joins."""
from __future__ import annotations

import unittest

import networkx as nx

from research.order10_v28_p1_coaffine_join_v1.search import (
    classify_P1, reconstruct_P1, current_stiff_sources,
)


def join_target(complement_parts: list[nx.Graph]) -> nx.Graph:
    return nx.complement(nx.disjoint_union_all(complement_parts))


class FirstIterateCoaffineJoinTests(unittest.TestCase):
    def test_two_historical_skipped_P3_sources_are_divergent_at_P1(self):
        originals = current_stiff_sources()
        for index in (11715667, 11716441):
            P1 = reconstruct_P1(originals[index])
            self.assertEqual((len(P1), P1.number_of_edges()), (11, 46))
            result = classify_P1(P1)
            self.assertIsNotNone(result)
            self.assertTrue(result["original_K_divergent"])
            self.assertEqual(
                [f["kind"] for f in result["complement_components"]],
                ["K2", "K2", "C7"],
            )
            self.assertIn("Theorem 3.6", result["theorem"])

    def test_three_octahdral_summands_are_expansive(self):
        G = join_target([nx.path_graph(2) for _ in range(3)])
        self.assertIn("Theorem 3.6", classify_P1(G)["theorem"])

    def test_connected_coaffine_cycle_summand_is_expansive(self):
        G = join_target([nx.path_graph(2), nx.cycle_graph(7)])
        self.assertIn("Theorem 4.6", classify_P1(G)["theorem"])

    def test_fourcycle_target_is_not_divergent_by_claimed_theorem(self):
        G = join_target([nx.path_graph(2), nx.path_graph(2)])
        self.assertIsNone(classify_P1(G))

    def test_single_cycle_complement_threshold_exact(self):
        self.assertIsNone(classify_P1(nx.complement(nx.cycle_graph(7))))
        self.assertIn("Theorem 5.4",
                      classify_P1(nx.complement(nx.cycle_graph(8)))["theorem"])

    def test_arbitrary_noncoaffine_factor_is_not_accepted(self):
        H = nx.disjoint_union(nx.path_graph(2), nx.path_graph(3))
        G = nx.complement(H)
        self.assertIsNone(classify_P1(G))

    def test_all_613_current_stiff_originals_present(self):
        self.assertEqual(len(current_stiff_sources()), 613)


if __name__ == "__main__":
    unittest.main()
