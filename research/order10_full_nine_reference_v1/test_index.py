"""Lightweight adversarial tests for sharded positive-only P3 reference matching."""
import unittest
from unittest.mock import patch

import networkx as nx

from . import index


class FullNineReferenceTests(unittest.TestCase):
    def test_historical_frozen_nine_promotion_chain(self):
        snapshots = [index.rows(f"indeterminate_order_9_v{i}.txt")
                     for i in (1, 2, 3, 9)]
        self.assertEqual([len(s) for s in snapshots], [54, 49, 13, 3])
        self.assertEqual([
            len(set(before) - set(after))
            for before, after in zip(snapshots, snapshots[1:])
        ], [5, 36, 10])
        self.assertTrue(all(
            all(before[k] == after[k] for k in after)
            for before, after in zip(snapshots, snapshots[1:])
        ))

    def test_pared_oct_graph_and_identity(self):
        graph = nx.octahedral_graph()
        p = index.independent_pare(graph)
        self.assertEqual(index.dimensions(p), (6, 12))
        self.assertEqual(index.exact_map(p, p), list(range(6)))

    def test_equal_order_and_edges_not_enough(self):
        a = nx.cycle_graph(6)
        b = nx.disjoint_union(nx.cycle_graph(3), nx.cycle_graph(3))
        self.assertEqual(index.dimensions(a), index.dimensions(b))
        self.assertIsNone(index.exact_map(a, b))

    def test_nontrivial_complete_isomorphism(self):
        left = nx.path_graph(5)
        right = nx.relabel_nodes(left, {0:4, 1:3, 2:2, 3:1, 4:0},
                                 copy=True)
        # The relabelled graph remains exactly the same P5 because
        # path reversal is an automorphism; any complete map is valid.
        result = index.exact_map(left, right)
        self.assertIsNotNone(result)
        self.assertTrue(all(
            left.has_edge(u, v) == right.has_edge(result[u], result[v])
            for u in left for v in left
        ))

    def test_graph6_equality_does_not_allow_wrong_label_mapping(self):
        left = nx.path_graph(4)
        right = nx.relabel_nodes(left, {i: i + 10 for i in range(4)})
        self.assertEqual(index.graph6(left), index.graph6(right))
        with self.assertRaisesRegex(AssertionError, "canonical integer labels"):
            index.exact_map(left, right)

    def test_internal_verifier_error_is_fatal_not_a_resource_skip(self):
        with patch.object(index, "independent_clique_graph",
                          side_effect=AssertionError("Independent enumerators disagree")):
            with self.assertRaisesRegex(AssertionError, "enumerators disagree"):
                index.next_pared(nx.path_graph(4), 1)

    def test_only_explicit_limit_is_inconclusive(self):
        limit = index.LimitHit(1, "maximal_clique_cap", [4])
        with patch.object(index, "independent_clique_graph", side_effect=limit):
            with self.assertRaises(index.ReconstructionLimit):
                index.next_pared(nx.path_graph(4), 1)

    def test_illegal_provenance_blob_is_rejected(self):
        with self.assertRaises(AssertionError):
            index.archive("indeterminate_order_9_v8.txt")

    def test_tampered_host_shape_fails(self):
        host = {
            "schema": 1,
            "records": [
                {"index": n, "graph6": "Dhc", "p3_graph6": "Dhc",
                 "p3": [5, 1000], "members": [n]}
                for n in range(521)
            ],
        }
        inp = {
            "schema": 1,
            "counts": {"total": 10155},
            "sources": [],
        }
        with self.assertRaisesRegex(AssertionError, "signature"):
            index.scan(inp, host, 0, 1)

    def test_aggregate_rejects_missing_shard(self):
        with self.assertRaisesRegex(AssertionError, "Missing"):
            index.aggregate({"sources": []}, {"records": []}, [
                {"shard": 1, "shards": 2, "source_original_count": 0,
                 "positives": []}
            ])


if __name__ == "__main__":
    unittest.main()
