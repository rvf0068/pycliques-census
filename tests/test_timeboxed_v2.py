"""Regression checks for the independent bound-120 v2 continuation."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import staged
import timeboxed_v2
import timeboxed_worker_v2
from timeboxed_trace_v2 import DEFAULT_METHODS
from pycliques import small


def g6(graph):
    return nx.to_graph6_bytes(graph, header=False).decode("ascii").strip()


class VersionTwoTests(unittest.TestCase):
    def test_original_graph_selection_and_conjectured_cases(self):
        cycle = g6(nx.cycle_graph(10))
        wheel = g6(nx.wheel_graph(10))
        source = {
            1: {"index": 1, "graph6": cycle},
            2: {"index": 2, "graph6": wheel},
            3: {"index": 3, "graph6": cycle},
        }
        origins = {
            1: f"1 10 {cycle} reference conjectured_divergent snub",
            2: f"2 9 {wheel} - - -",
            3: f"3 10 {cycle} - - -",
        }
        with patch.object(staged, "active", return_value=(source, origins, source)) as active:
            selected, _ = timeboxed_v2.cohort()
        self.assertEqual(list(selected), [1, 3])
        active.assert_called_once_with(10, include_timeboxed=False)

    def test_depth_two_and_no_conjectural_shortcuts(self):
        graph6 = g6(nx.cycle_graph(10))
        saved = small._REFERENCE_GRAPHS
        fixture = {
            b"known": (nx.cycle_graph(4), small.ReferenceStatus.PROVEN, "known"),
            b"unproved": (
                nx.cycle_graph(5), small.ReferenceStatus.CONJECTURED, "unproved"
            ),
        }

        def mock_classify(g, *, bound, retraction_depth):
            self.assertEqual(bound, 120)
            self.assertEqual(retraction_depth, 2)
            self.assertEqual(list(small._REFERENCE_GRAPHS), [b"known"])
            return SimpleNamespace(
                verdict=SimpleNamespace(name="INDETERMINATE"),
                certificate=None,
                pared_graph=g,
                bound_exceeded=False,
                reason="fixture",
                iterations_checked=1,
            )

        with (
            patch.object(timeboxed_worker_v2, "load_surface_references"),
            patch.object(small, "_REFERENCE_GRAPHS", fixture),
            patch.object(small, "classify_clique_behavior", side_effect=mock_classify),
        ):
            result = timeboxed_worker_v2.classify(graph6)
            self.assertEqual(result["retraction_depth"], 2)
            self.assertEqual(result["status"], "INDETERMINATE")
            self.assertIs(small._REFERENCE_GRAPHS, fixture)
        self.assertIs(small._REFERENCE_GRAPHS, saved)

    def test_method_labels_match_new_classifier_order(self):
        methods = small._default_classifiers(tries=9, retraction_depth=2)
        self.assertEqual(len(methods), len(DEFAULT_METHODS))
        self.assertEqual(DEFAULT_METHODS[2], "retraction_suspension_C5_G0")
        self.assertEqual(DEFAULT_METHODS[6], "retraction_suspension_C5_G1")
        self.assertEqual(DEFAULT_METHODS[-1], "eventually_special_octahedra")

    def test_v2_validates_results_separately_from_v1(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "runs" / "order10" / timeboxed_v2.STAGE
            (folder / "records").mkdir(parents=True)
            manifest = {
                "stage": timeboxed_v2.STAGE, "order": 10,
                "upstream_commit": "a" * 40, "indices": [7],
            }
            (folder / "manifest.json").write_text(json.dumps(manifest))
            graph6 = g6(nx.cycle_graph(10))
            record = {
                "index": 7, "graph6": graph6,
                "status": "TIMEOUT", "verdict": "INDETERMINATE", "bound": 120,
            }
            (folder / "records" / "00000007.json").write_text(json.dumps(record))
            source = {7: {"index": 7, "graph6": graph6}}
            with patch.object(staged, "ROOT", root):
                self.assertEqual(
                    staged.checked_records(10, timeboxed_v2.STAGE, source)[7]["status"],
                    "TIMEOUT",
                )

    def test_restarts_at_batch_zero_and_retains_saved_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "config" / "conjectured_surfaces_order9.tsv"
            registry.parent.mkdir(parents=True)
            registry.write_text("# fixture\n")
            code = g6(nx.cycle_graph(10))
            source = {i: {"index": i, "graph6": code} for i in range(1, 12)}
            manifest = {
                "stage": timeboxed_v2.STAGE, "order": 10,
                "upstream_commit": "a" * 40, "indices": list(source),
                "batch_size": 5,
            }
            dest = root / "runs" / "order10" / timeboxed_v2.STAGE
            attempts = []
            def fake_worker(graph6, _dest):
                attempts.append(graph6)
                return {
                    "status": "INDETERMINATE", "verdict": "INDETERMINATE",
                    "bound": 120, "elapsed_seconds": 0.01, "reason": "fixture",
                }
            with (
                patch.object(timeboxed_v2, "ROOT", root),
                patch.object(staged, "ROOT", root),
                patch.object(timeboxed_v2, "cohort", return_value=(source, source)),
                patch.object(timeboxed_v2, "expected_manifest", return_value=manifest),
                patch.object(timeboxed_v2, "run_one", side_effect=fake_worker),
                patch.object(staged, "refresh", return_value={"remaining": 11}),
                patch("surface_refs.load_surface_references", return_value=0),
            ):
                timeboxed_v2.run()
                self.assertEqual(len(attempts), 5)
                self.assertTrue((dest / "batches" / "00000.json").is_file())
                timeboxed_v2.run()
                self.assertEqual(len(attempts), 10)
                timeboxed_v2.run()
                self.assertEqual(len(attempts), 11)
                self.assertTrue((dest / "summary.json").is_file())
                timeboxed_v2.run()
                self.assertEqual(len(attempts), 11)


if __name__ == "__main__":
    unittest.main()
