"""Tests for the targeted order-9 K(G) -> complement(C10) post-pass."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

import networkx as nx
from pycliques.named import complement_of_cycle, suspension_of_cycle

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "postpasses"))
import clique_retract_comp_c10 as postpass  # noqa: E402


class CliqueRetractionPostpassTests(unittest.TestCase):
    def test_known_positive_on_clique_graph_of_suspension_c5(self):
        # The existing upstream pycliques test confirms this retraction.
        graph = suspension_of_cycle(5)
        outcome = postpass.search_retraction(
            graph, max_embeddings=200, max_states=10000, max_assignments=100000
        )
        self.assertEqual(outcome["status"], "RETRACTION_FOUND")
        self.assertEqual(outcome["K_order"], 10)
        witness = outcome["witness"]
        self.assertEqual(len(witness["K_vertex_to_target_vertex"]), 10)
        self.assertEqual(set(witness["K_vertex_to_target_vertex"]), set(range(10)))
        target = complement_of_cycle(10)
        kgraph = postpass.clique_graph(graph)
        numbered = nx.relabel_nodes(
            kgraph,
            {
                frozenset(vertices): i
                for i, vertices in enumerate(outcome["K_vertex_cliques"])
            },
        )
        for u, v in numbered.edges():
            x, y = (witness["K_vertex_to_target_vertex"][z] for z in (u, v))
            self.assertTrue(x == y or target.has_edge(x, y))

    def test_negative_if_clique_graph_too_small(self):
        outcome = postpass.search_retraction(nx.complete_graph(4))
        self.assertEqual(outcome["status"], "NO_RETRACTION")
        self.assertEqual(outcome["K_order"], 1)
        self.assertIsNone(outcome["witness"])

    def test_cohort_excludes_only_conjectured_divergent_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            (run / "order9").mkdir()
            manifest = {"min_order": 9, "max_order": 9, "upstream_commit": "abc"}
            (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            summary = {
                "manifest": manifest,
                "orders": [{"order": 9, "connected_total": 261080, "indeterminate": 2}],
                "unresolved": [
                    {"order": 9, "index": 7, "graph6": "HCRSv\\}",
                     "reason": "conditional on conjectured divergence"},
                    {"order": 9, "index": 9, "graph6": "HEhfvzu",
                     "reason": "clique count exceeded bound"},
                ],
            }
            (run / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
            (run / "order9" / "indeterminate_order_9.txt").write_text(
                "7 9 HCRSv\\} retracts conjectured_divergent snub_disphenoid\n"
                "9 9 HEhfvzu - - -\n",
                encoding="utf-8",
            )
            metadata, selected = postpass.load_candidates(run)
            self.assertEqual(metadata["total_indeterminate"], 2)
            self.assertEqual(metadata["conjectured_excluded"], 1)
            self.assertEqual([item["index"] for item in selected], [9])

    def test_cohort_rejects_inconsistent_conjectural_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            (run / "order9").mkdir()
            manifest = {"min_order": 9, "max_order": 9, "upstream_commit": "abc"}
            (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            summary = {
                "manifest": manifest,
                "orders": [{"order": 9, "connected_total": 261080, "indeterminate": 1}],
                "unresolved": [{"order": 9, "index": 1, "graph6": "HCRSv\\}",
                                "reason": "conditional on conjectured divergence"}],
            }
            (run / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
            (run / "order9" / "indeterminate_order_9.txt").write_text(
                "1 9 HCRSv\\} - - -\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "Inconsistent conjectured"):
                postpass.load_candidates(run)


if __name__ == "__main__":
    unittest.main()
