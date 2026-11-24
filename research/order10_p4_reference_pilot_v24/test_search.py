"""Regressions for bounded v24 reference transfers and complete positive maps."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import networkx as nx

from .reference_provenance import check_reference_provenance
from .verify_results import audit, check_shard
from .search import (
    REFERENCE_DIMENSIONS, REFERENCE_G6,
    exact_isomorphism, fourth, inspect, plan, representatives, verify_map,
)


class ReferencePilotTests(unittest.TestCase):
    def test_522_surviving_certified_p3_representatives(self):
        cases = representatives()
        self.assertEqual(len(cases), 522)
        self.assertEqual(
            [i for i, _ in cases],
            sorted(i for i, _ in cases),
        )

    def test_exact_206_case_archive_with_zero_dimension_collisions(self):
        result = audit()
        self.assertEqual(result["counts"]["complete_p4"], 180)
        self.assertEqual(result["counts"]["p4_facet_cap"], 26)

    def test_reject_mutated_shard_replay(self):
        data = audit()
        cohort = data["records"][0::12]
        with tempfile.TemporaryDirectory() as temp:
            name = Path(temp) / "corrupt.json"
            altered = {
                "schema": 1, "source": "indeterminate_order_10_v24.txt",
                "selected_total": 206, "representatives": 522,
                "settings": {
                    "shards": 12, "shard": 0,
                    "min_p3": 41, "max_p3": 55, "timeout_sec": 24,
                },
                "records": [dict(row) for row in cohort],
                "status_counts": data["shard_summaries"][0]["counts"],
            }
            altered["records"][0]["p3"] = [99, 99]
            name.write_text(json.dumps(altered), encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "disagree"):
                check_shard(data, name, 0)

    def test_reference_sources_and_host_digests_pinned_to_historical_proofs(self):
        check_reference_provenance()

    def test_reject_self_consistent_but_uncertified_reference_substitution(self):
        original = REFERENCE_G6[10223405]
        try:
            REFERENCE_G6[10223405] = "ICpVUjx|_"
            with self.assertRaisesRegex(AssertionError, "Uncertified reference"):
                check_reference_provenance()
        finally:
            REFERENCE_G6[10223405] = original

    def test_timeout_remains_inconclusive_and_is_preserved(self):
        # Replay artifacts must be uploaded even if a worker times out.
        data = audit()
        cohort = [dict(row) for row in data["records"][0::12]]
        first = cohort[0]
        cohort[0] = {
            "index": first["index"],
            "graph6": first["graph6"],
            "p3": [first["p3"][0]],
            "status": "TIMEOUT",
        }
        with tempfile.TemporaryDirectory() as directory:
            name = Path(directory) / "timed-out.json"
            statuses = {}
            for row in cohort:
                statuses[row["status"]] = statuses.get(row["status"], 0) + 1
            payload = {
                "schema": 1, "source": "indeterminate_order_10_v24.txt",
                "selected_total": 206, "representatives": 522,
                "settings": {
                    "shards": 12, "shard": 0,
                    "min_p3": 41, "max_p3": 55, "timeout_sec": 24,
                },
                "records": cohort,
                "status_counts": statuses,
            }
            name.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(
                check_shard(data, name, 0),
                [first["index"]],
            )
            payload["records"][0]["graph6"] = "I?????????"
            name.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "TIMEOUT source"):
                check_shard(data, name, 0)

    def test_all_five_reference_shapes(self):
        for index, g6 in REFERENCE_G6.items():
            with self.subTest(reference=index):
                _, _, host = fourth(g6)
                self.assertEqual(
                    (len(host), host.number_of_edges()),
                    REFERENCE_DIMENSIONS[index],
                )

    def test_previously_certified_v24_positive_is_rediscovered(self):
        # Known proof deliberately outside the current v24 indeterminate list.
        case = inspect(11495390, "ICvbvZs{g", 41, 55)
        self.assertEqual(case["status"], "EXACT_MATCH")
        self.assertIn(10223405, [
            proof["reference"] for proof in case["positives"]
        ])

    def test_unchanged_negative_dimensions_are_not_verdicts(self):
        case = inspect(11625997, "IEjbvjyz_", 41, 55)
        self.assertEqual(case["status"], "NO_REFERENCE_DIMENSION_MATCH")
        self.assertEqual(case["p4"], [184, 14597])

    def test_bijection_checks_reject_noninjective_or_wrong_map(self):
        graph = nx.path_graph(6)
        with self.assertRaises(AssertionError):
            verify_map(graph, graph, [0, 1, 1, 3, 4, 5])
        with self.assertRaises(AssertionError):
            verify_map(graph, graph, [1, 0, 2, 3, 4, 5])
        self.assertEqual(
            exact_isomorphism(graph, graph),
            list(range(6)),
        )


if __name__ == "__main__":
    unittest.main()
