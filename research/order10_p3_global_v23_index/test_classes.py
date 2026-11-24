"""Adversarial tests for the ten-v23 global third-iterate class index."""
from __future__ import annotations

import copy
import unittest

import networkx as nx

from unittest.mock import patch

from . import classes, independent_verify as independent
from .classes import (
    BoundedSkip, MAX_FACETS, SOURCE_BLOB, clique_graph,
    fingerprint, git_blob, pare, source_rows, verify_witness,
    SOURCE,
)


class ExactP3IndexTests(unittest.TestCase):
    def test_pinned_immutable_ten_v23(self):
        self.assertEqual(git_blob(SOURCE.read_bytes()), SOURCE_BLOB)
        self.assertEqual(len(source_rows()), 629)

    def test_clique_graph_octahedron_growth(self):
        source = nx.complete_multipartite_graph(2, 2, 2)
        target = clique_graph(source, 1, [6])
        self.assertEqual(len(target), 8)
        self.assertTrue(nx.is_isomorphic(
            target, nx.complete_multipartite_graph(2, 2, 2, 2),
        ))

    def test_pare_dismantles_path(self):
        self.assertEqual(len(pare(nx.path_graph(7))), 1)

    def test_fingerprint_invariant_under_relabeling(self):
        original = nx.cycle_graph(9)
        permuted = nx.relabel_nodes(original, {i: (i * 4) % 9
                                                for i in range(9)})
        self.assertEqual(fingerprint(original), fingerprint(permuted))

    def test_reject_noninjective_saved_bijection(self):
        graph = nx.path_graph(5)
        with self.assertRaises(AssertionError):
            verify_witness(graph, graph, [0, 1, 1, 3, 4])

    def test_reject_false_saved_graph_isomorphism(self):
        first = nx.path_graph(5)
        second = nx.star_graph(4)
        with self.assertRaisesRegex(AssertionError, "edges and nonedges"):
            verify_witness(first, second, list(range(5)))

    def test_independent_bron_kerbosch_matches_networkx(self):
        for graph in (
            nx.cycle_graph(7),
            nx.complete_multipartite_graph(2, 2, 2),
            nx.icosahedral_graph(),
        ):
            self.assertEqual(
                independent.maximal_cliques_bk(graph),
                independent.maximal_cliques_nx(graph),
            )
            self.assertEqual(
                independent.independent_pare(graph).number_of_nodes(),
                pare(graph).number_of_nodes(),
            )

    def test_second_clique_enumerator_disagreement_is_detected(self):
        graph = nx.cycle_graph(6)
        with patch.object(
            independent, "maximal_cliques_nx", return_value=[1]
        ):
            with self.assertRaisesRegex(
                AssertionError, "enumerators disagree"
            ):
                independent.independent_clique_graph(
                    graph, stage=2, orders=[6]
                )

    def test_independent_replayer_is_not_builder_alias(self):
        with patch.object(
            independent, "verify_archive", return_value=None
        ) as genuine:
            with patch.object(
                classes, "build", side_effect=AssertionError(
                    "Builder must not verify its own archive"
                )
            ):
                classes.verify()
                genuine.assert_called_once_with()

    def test_corrupted_positive_mapping_fails_independent_check(self):
        graph = nx.cycle_graph(6)
        independent.verify_pair(graph, graph, list(range(6)))
        with self.assertRaisesRegex(
            AssertionError, "saved P3 map"
        ):
            independent.verify_pair(graph, graph, [0, 1, 2, 3, 5, 4])

    def test_reject_resource_limit_as_verdict(self):
        graph = nx.complete_multipartite_graph(*([2] * 10))
        # O_10 has 2^10 = 1024 maximal cliques.
        with self.assertRaises(BoundedSkip) as raised:
            clique_graph(graph, 2, [20])
        self.assertEqual(raised.exception.reason, "maximal_clique_cap")
        self.assertEqual(raised.exception.stage, 2)


if __name__ == "__main__":
    unittest.main()
