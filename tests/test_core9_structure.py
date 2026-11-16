"""Safe structural diagnostics and immutable-stage regression tests."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import core9_structure as stage
import core9_structure_worker as worker


class StructureTests(unittest.TestCase):
    def test_first_betti_exact_from_triangle_boundaries(self):
        examples = [
            (nx.cycle_graph(5), (1, 0)),
            (nx.complete_graph(5), (0, 10)),
            (nx.octahedral_graph(), (0, 8)),
            (nx.disjoint_union(nx.cycle_graph(5), nx.cycle_graph(3)), (1, 1)),
        ]
        for graph, (betti, triangles) in examples:
            with self.subTest(graph=graph.number_of_nodes()):
                b1, ntriangles, rank = worker.betti1_mod2(graph)
                self.assertEqual((b1, ntriangles), (betti, triangles))
                self.assertEqual(
                    rank, graph.number_of_edges() - graph.number_of_nodes()
                    + nx.number_connected_components(graph) - betti
                )
                self.assertGreaterEqual(rank, 0)

    def test_truncated_clique_count_never_misrepresented(self):
        graph = nx.empty_graph(5)
        exact = worker.clique_sample(graph, limit=10)
        self.assertTrue(exact["exact"])
        self.assertEqual(exact["maximal_cliques_exact"], 5)
        self.assertEqual(exact["partial_size_histogram"], {"1": 5})
        truncated = worker.clique_sample(graph, limit=2)
        self.assertFalse(truncated["exact"])
        self.assertIsNone(truncated["maximal_cliques_exact"])
        self.assertEqual(truncated["maximal_cliques_at_least"], 3)
        self.assertEqual(sum(truncated["partial_size_histogram"].values()), 2)
        with self.assertRaisesRegex(ValueError, "must be positive"):
            worker.clique_sample(graph, limit=0)

    def test_coaffination_is_only_an_observation(self):
        info = worker.coaffination_observation(nx.cycle_graph(4))
        self.assertTrue(info["complete"])
        self.assertIn([2, 3, 0, 1], info["examples"])
        for values in info["examples"]:
            self.assertTrue(all(values[i] != i for i in range(4)))

    def test_frozen_29_selection_includes_G3_exception(self):
        selected = stage.cohort()
        self.assertEqual(len(selected), 29)
        self.assertEqual(sum(x["member_count"] for x in selected.values()), 3738)
        self.assertEqual(selected[10760192]["failure_iterate"], 3)
        self.assertEqual(
            sum(x["failure_iterate"] == 4 for x in selected.values()), 28
        )
        self.assertTrue(all(x["graph6"].startswith("H") for x in selected.values()))

    def test_real_bound120_iterates_and_homology(self):
        selected = stage.cohort()
        for i in (2317843, 10760192):
            with self.subTest(core_id=i):
                record = selected[i]
                result = worker.inspect(
                    record["graph6"], record["expected_iterates"]
                )
                self.assertEqual(result["failure_iterate"],
                                 record["failure_iterate"])
                self.assertEqual(len(result["iterates"]),
                                 record["failure_iterate"])
                for row in result["iterates"]:
                    g = nx.from_graph6_bytes(row["graph6"].encode("ascii"))
                    self.assertEqual(len(g), row["order"])
                    self.assertEqual(g.number_of_edges(), row["edges"])
                    self.assertEqual(
                        row["connected_triangular_double_cover_possible"],
                        row["betti1_mod2"] > 0,
                    )
                    self.assertEqual(
                        row["maximal_cliques"]["exact"],
                        row["maximal_cliques"]["maximal_cliques_exact"] is not None,
                    )
                    if "divergent_induced_clockwork" in row:
                        found = row["divergent_induced_clockwork"]
                        self.assertEqual(
                            found["conclusion"],
                            "induced_observation_only_not_host_divergence",
                        )
                verified = {
                    "core_id": i, "input_graph6": record["graph6"],
                    "member_count": record["member_count"],
                    "status": "OK", "scope": "structural_diagnostics_only",
                    **result,
                }
                stage.validate_record(verified, i, selected)
                # Same nine vertices and same edge count, but NOT the source
                # core. A self-consistent forged checkpoint must be rejected.
                fake = json.loads(json.dumps(verified))
                actual_graph = nx.from_graph6_bytes(
                    record["graph6"].encode("ascii")
                )
                counterfeit = next(
                    g for seed in range(1, 20)
                    if not nx.is_isomorphic(
                        (g := nx.gnm_random_graph(
                            9, actual_graph.number_of_edges(), seed=seed
                        )), actual_graph
                    )
                )
                fake["iterates"][0]["graph6"] = worker.encode(counterfeit)
                with self.assertRaisesRegex(ValueError, "actual clique iterate"):
                    stage.validate_record(fake, i, selected)

                with self.assertRaisesRegex(ValueError, "differs"):
                    changed = json.loads(json.dumps(record["expected_iterates"]))
                    changed[0]["pared_edges"] += 1
                    worker.inspect(record["graph6"], changed)

    def test_resume_keeps_old_census_intact(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            new_dir = root / "runs/order10/core9-structure-v1"
            historical = root / "indeterminate_order_10_v3.txt"
            historical.write_bytes(b"historical census stays immutable\n")
            selected = {
                i: {
                    "graph6": "HCRSv\\}", "member_count": i,
                    "failure_iterate": 4,
                    "expected_iterates": [],
                }
                for i in range(1, 8)
            }
            meta = {"core_ids": sorted(selected), "batch_size": 5}
            attempts = []
            def fake_worker(info):
                attempts.append(info["graph6"])
                return {
                    "status": "TIMEOUT", "scope": "structural_diagnostics_only",
                    "elapsed_seconds": 45.0,
                    "reason": "simulated bounded resource result",
                }
            with (
                patch.object(stage, "ROOT", root),
                patch.object(stage, "FOLDER", new_dir),
                patch.object(stage, "cohort", return_value=selected),
                patch.object(stage, "manifest", return_value=meta),
                patch.object(stage, "run_one", side_effect=fake_worker),
            ):
                self.assertTrue(stage.run("next"))
                self.assertFalse(stage.run("next"))
                self.assertFalse(stage.run("next"))
                stage.verify()
                self.assertEqual(len(attempts), 7)
                self.assertEqual(
                    json.loads((new_dir / "summary.json").read_text())["counts"],
                    {"TIMEOUT": 7},
                )
            self.assertEqual(
                historical.read_bytes(), b"historical census stays immutable\n"
            )

    def test_verify_missing_stage_has_no_side_effect(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "new-stage"
            with (
                patch.object(stage, "FOLDER", output),
                patch.object(stage, "cohort", return_value={}),
                patch.object(stage, "manifest", return_value={"dummy": True}),
            ):
                with self.assertRaisesRegex(ValueError, "has started"):
                    stage.verify()
                self.assertFalse(output.exists())

    def test_stage_record_rejects_forged_status(self):
        selected = {123: {
            "graph6": "HCRSv\\}", "member_count": 70,
            "failure_iterate": 4, "expected_iterates": [],
        }}
        record = {
            "core_id": 123, "input_graph6": "HCRSv\\}",
            "member_count": 70, "scope": "structural_diagnostics_only",
            "status": "TIMEOUT", "reason": "limited",
        }
        stage.validate_record(record, 123, selected)
        for update in (
            {"status": "DIVERGENT"},
            {"input_graph6": "HEhutxm"},
            {"scope": "certified_divergent"},
        ):
            with self.assertRaisesRegex(ValueError, "Invalid structure"):
                stage.validate_record({**record, **update}, 123, selected)


if __name__ == "__main__":
    unittest.main()
