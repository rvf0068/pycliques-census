"""Mathematical cross-checks for exhaustive nine-core snub retractions."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import core9_snub_retractions_v2 as study  # noqa: E402


class SnubExhaustiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = study.prepare()
        cls.data = json.loads(
            cls.payload["research/order9_snub_retractions_v2/certificates.json"]
        )
        cls.records = {r["core_id"]: r for r in cls.data["records"]}
        cls.snub = study.decode(study.SNUB_G6)

    def test_exact_29_core_partition_and_3738_originals(self):
        records = list(self.records.values())
        self.assertEqual(len(records), 29)
        self.assertEqual(sum(r["original_order10_members"] for r in records), 3738)
        self.assertEqual(
            {r["core_id"] for r in records if r["status"] == "SNUB_RETRACT"},
            study.EXPECTED_RETRACTS,
        )
        self.assertEqual(
            {r["core_id"] for r in records
             if r["status"] == "INDUCED_SNUB_NO_RETRACT"},
            study.EXPECTED_INDUCED_ONLY,
        )
        self.assertEqual(
            len([r for r in records if r["status"] == "NO_INDUCED_SNUB"]), 14
        )
        self.assertEqual(self.data["counts"]["newly_identified_original_order10_members"], 710)
        self.assertTrue(self.data["no_new_clique_behavior_verdicts"])

    def test_every_positive_projection_and_explicit_induced_snub_map(self):
        for row in self.records.values():
            graph = study.decode(row["core_graph6"])
            for deletion in row["deletions"]:
                v = deletion["removed_vertex"]
                target = graph.subgraph([u for u in graph if u != v])
                perm = deletion["target_to_snub"]
                self.assertEqual(len(perm), 9)
                self.assertIsNone(perm[v])
                self.assertEqual({perm[u] for u in target}, set(self.snub))
                for i in target:
                    for j in target:
                        self.assertEqual(
                            target.has_edge(i, j),
                            self.snub.has_edge(perm[i], perm[j]),
                        )
                for u in deletion["admissible_image_vertices"]:
                    self.assertTrue(
                        all((u == w or target.has_edge(u, w))
                            for w in graph[v]),
                        (row["core_id"], v, u),
                    )
                    self.assertTrue(study.verify_retraction(graph, v, u))
                for u, bad in deletion["rejected_image_obstructions"]:
                    self.assertFalse(study.verify_retraction(graph, v, u))
                    self.assertIn(bad, graph[v])
                    self.assertNotEqual(u, bad)
                    self.assertFalse(target.has_edge(u, bad))

    def test_negative_search_is_exhaustive_over_all_9_deletions(self):
        for row in self.records.values():
            graph = study.decode(row["core_graph6"])
            actual = [
                v for v in graph if nx.is_isomorphic(
                    graph.subgraph([u for u in graph if u != v]),
                    self.snub,
                )
            ]
            recorded = [d["removed_vertex"] for d in row["deletions"]]
            self.assertEqual(actual, recorded)
            for v in actual:
                images = {
                    u for u in graph if u != v
                    if all(
                        (u == w or graph.has_edge(u, w))
                        for w in graph.neighbors(v)
                    )
                }
                rec = next(d for d in row["deletions"] if d["removed_vertex"] == v)
                self.assertEqual(images, set(rec["admissible_image_vertices"]))

    def test_nonadjacent_snub_retraction_six_new_cases(self):
        for i in study.EXPECTED_RETRACTS:
            row = self.records[i]
            graph = study.decode(row["core_graph6"])
            for rec in row["retractions"]:
                v, u = rec["removed_vertex"], rec["image_vertex"]
                self.assertFalse(graph.has_edge(v, u))
                self.assertTrue(set(graph[v]) <= set(graph[u]))
        # An induced snub need not be a retract.
        row = self.records[5418647]
        self.assertEqual(row["status"], "INDUCED_SNUB_NO_RETRACT")
        self.assertEqual(len(row["deletions"]), 1)
        self.assertFalse(row["retractions"])

    def test_exact_second_pared_iterate_isomorphisms_and_obstructions(self):
        snub2 = study.pared_K2(self.snub)
        self.assertEqual((len(snub2), snub2.number_of_edges()), (20, 136))
        matching = set()
        for row in self.records.values():
            core2 = study.pared_K2(study.decode(row["core_graph6"]))
            self.assertEqual(len(core2), row["pared_K2_order"])
            self.assertEqual(core2.number_of_edges(), row["pared_K2_edges"])
            mapping = row["pared_K2_to_snub_pared_K2"]
            if mapping is None:
                self.assertFalse(nx.is_isomorphic(core2, snub2))
                continue
            matching.add(row["core_id"])
            self.assertEqual(set(mapping), set(snub2))
            for i in core2:
                for j in core2:
                    self.assertEqual(
                        core2.has_edge(i, j),
                        snub2.has_edge(mapping[i], mapping[j]),
                    )
        self.assertEqual(matching, study.ORIGINAL_THREE)


if __name__ == "__main__":
    unittest.main()
