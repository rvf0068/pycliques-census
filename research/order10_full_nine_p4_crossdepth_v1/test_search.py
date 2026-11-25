"""Adversarial regressions for authenticated full nine to ten-P4 search."""
from __future__ import annotations

import unittest
from unittest.mock import patch

import networkx as nx

from . import search


class CrossDepthIndexTests(unittest.TestCase):
    def test_all_210_existing_p4_shapes_are_certified_and_current(self):
        result = search.host_catalog()
        self.assertEqual(result["counts"], search.EXPECTED_HOST_COUNTS)
        self.assertEqual(len(result["records"]), 210)
        self.assertEqual(len(set(x["index"] for x in result["records"])), 210)
        self.assertEqual(
            sum(x["p4"][0] <= 750 for x in result["records"]), 202
        )

    def test_unknown_historical_provenance_rejected(self):
        with self.assertRaisesRegex(AssertionError, "Unrecognized"):
            search.frozen("research/mutable_unproved_ref.json")

    def test_mask_nonedge_and_edge_symmetry(self):
        self.assertEqual(
            search.dims(search.as_graph([0b010, 0b001])), (2, 1)
        )
        with self.assertRaisesRegex(AssertionError, "not symmetric"):
            search.as_graph([0, 1])
        with self.assertRaisesRegex(AssertionError, "not symmetric"):
            search.as_graph([2, 0])
        with self.assertRaisesRegex(AssertionError, "Malformed"):
            search.as_graph([1])

    def test_exact_reconstruction_does_not_use_shapes_as_proofs(self):
        # The source graph is a cycle, the host is two triangles. Their
        # dimensions match, but these are not isomorphic.
        a = nx.cycle_graph(6)
        b = nx.disjoint_union(nx.cycle_graph(3), nx.cycle_graph(3))
        self.assertEqual(search.dims(a), search.dims(b))
        with patch.object(search, "rebuild_p4",
                          return_value=([0] * 6, b)):
            record = {"index": 42, "p4": [6, 6]}
            self.assertIsNone(search.exact_p4_map(a, record, {}))

    def test_missing_shards_are_rejected(self):
        with patch.object(search, "validate_inventory", return_value=None):
            with self.assertRaisesRegex(AssertionError, "Missing/overlapping"):
                search.replay(
                    {"counts": {"total": 10155}, "sources": []},
                    {"counts": search.EXPECTED_HOST_COUNTS, "records": []},
                    [{"shard": 1, "shards": 2,
                      "kind": "cross_depth_p4_positive_only_shard",
                      "source_original_count": 10155, "positives": []}],
                )

    def test_unpinned_historical_inventory_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, "proof provenance"):
            search.validate_inventory({
                "schema": 1,
                "kind": "authenticated_historical_divergent_nine_reference_inventory",
                "frozen_git_blobs": {},
                "counts": {"total": 10155},
                "sources": [],
            })

    def test_replay_rejects_false_shard_membership(self):
        sources = [
            {"original_order": 9, "original_index": i} for i in range(10155)
        ]
        inventory = {"counts": {"total": 10155}, "sources": sources}
        shards = [
            {"shard": k, "shards": 8,
             "kind": "cross_depth_p4_positive_only_shard",
             "source_original_count": len(sources[k::8]),
             "source_original_keys": [
                 [9, s["original_index"]] for s in sources[k::8]
             ], "positives": [], "different_p0_classes_in_shard": 0,
             "levels": {}, "bounded_reconstruction_skips": [],
             "comparison_timeouts": []}
            for k in range(8)
        ]
        shards[0]["source_original_keys"][0] = [9, 999999]
        with patch.object(search, "validate_inventory", return_value=None):
            with self.assertRaisesRegex(AssertionError, "misplaced"):
                search.replay(inventory, {
                    "counts": search.EXPECTED_HOST_COUNTS,
                    "records": [],
                }, shards)

    def test_reconstruction_integrity_failure_must_abort_shard(self):
        catalog = search.host_catalog()
        inventory = {
            "schema": 1, "counts": {"total": 10155},
            "sources": [
                {"graph6": "Dhc", "original_index": i,
                 "original_order": 5}
                for i in range(10155)
            ]
        }
        # Inject one root only, representing all identical inputs;
        # an underlying enumerator assertion must not be swallowed.
        with patch.object(search, "validate_inventory", return_value=None):
            with patch.object(search.old, "next_pared",
                              side_effect=AssertionError("False facet equality")):
                with self.assertRaisesRegex(AssertionError, "False facet equality"):
                    search.scan(inventory, catalog, 0, 8)


if __name__ == "__main__":
    unittest.main()
