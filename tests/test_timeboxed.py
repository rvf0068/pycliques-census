"""Isolated worker and batch-stage regression tests for the 10-vertex timeboxed census."""
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
import timeboxed
import timeboxed_worker
from timeboxed_trace import ProgressTrace, summarize_events, trace_classifier
from pycliques import small


def g6(graph):
    return nx.to_graph6_bytes(graph, header=False).decode("ascii").strip()


class TimeboxedStageTests(unittest.TestCase):
    def test_cohort_filters_original_dominated_vertices_but_keeps_conjectures(self):
        cycle = g6(nx.cycle_graph(10))
        # Wheel has a dominated outer vertex, while the cycle has no dominated vertex.
        wheel = g6(nx.wheel_graph(10))
        source = {
            11: {"index": 11, "graph6": cycle},
            12: {"index": 12, "graph6": wheel},
            13: {"index": 13, "graph6": cycle},
        }
        origins = {
            11: f"11 10 {cycle} reference conjectured_divergent reference",
            12: f"12 9 {wheel} - - -",
            13: f"13 10 {cycle} - - -",
        }
        with patch.object(staged, "active", return_value=(source, origins, source)) as active:
            eligible, data = timeboxed.cohort()
        self.assertEqual(sorted(eligible), [11, 13])
        self.assertIs(data, source)
        active.assert_called_once_with(10, include_timeboxed=False)

    def test_worker_suppresses_unproved_reference_but_restores_registry(self):
        cycle = g6(nx.cycle_graph(10))
        saved = small._REFERENCE_GRAPHS
        key1, key2 = b"known", b"unproved"
        fixture = {
            key1: (nx.cycle_graph(4), small.ReferenceStatus.PROVEN, "known"),
            key2: (nx.cycle_graph(5), small.ReferenceStatus.CONJECTURED, "unproved"),
        }
        def classifier(graph, *, bound):
            self.assertEqual(bound, 120)
            self.assertEqual(list(small._REFERENCE_GRAPHS), [key1])
            return SimpleNamespace(
                verdict=SimpleNamespace(name="INDETERMINATE"),
                certificate=None, pared_graph=graph, bound_exceeded=False,
                reason="fixture", iterations_checked=2,
            )
        with (
            patch.object(timeboxed_worker, "load_surface_references"),
            patch.object(small, "_REFERENCE_GRAPHS", fixture),
            patch.object(small, "classify_clique_behavior", side_effect=classifier),
        ):
            result = timeboxed_worker.classify(cycle)
            self.assertEqual(result["status"], "INDETERMINATE")
            self.assertIs(small._REFERENCE_GRAPHS, fixture)
        self.assertIs(small._REFERENCE_GRAPHS, saved)

    def test_worker_rejects_dominated_original(self):
        with self.assertRaisesRegex(ValueError, "dominated"):
            timeboxed_worker.classify(g6(nx.wheel_graph(10)))

    def test_worker_timeout_reaps_the_process_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "timeboxed_worker.py").write_text(
                "import time\ntime.sleep(10)\n", encoding="utf-8"
            )
            with (
                patch.object(timeboxed, "ROOT", root),
                patch.object(timeboxed, "TIMEOUT_SECONDS", 0.1),
            ):
                result = timeboxed.run_one(g6(nx.cycle_graph(10)), root)
            self.assertEqual(result["status"], "TIMEOUT")
            self.assertEqual(result["verdict"], "INDETERMINATE")
            self.assertLess(result["elapsed_seconds"], 3)
            self.assertEqual(list(root.glob("*.partial")), [])

    def test_one_batch_per_call_and_per_graph_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "config" / "conjectured_surfaces_order9.tsv"
            registry.parent.mkdir(parents=True)
            registry.write_text("# fixture\n", encoding="utf-8")
            code = g6(nx.cycle_graph(10))
            source = {i: {"index": i, "graph6": code} for i in range(1, 13)}
            target = root / "runs" / "order10" / timeboxed.STAGE
            manifest = {
                "schema": 1, "order": 10, "stage": timeboxed.STAGE,
                "upstream_commit": "a"*40, "indices": list(source),
                "batch_size": 5,
            }
            attempts = []
            def fake_worker(graph6, dest):
                attempts.append(graph6)
                return {
                    "status": "INDETERMINATE", "verdict": "INDETERMINATE",
                    "bound": 120, "elapsed_seconds": 0.02, "reason": "fixture"
                }
            with (
                patch.object(staged, "ROOT", root),
                patch.object(timeboxed, "ROOT", root),
                patch.object(timeboxed, "cohort", return_value=(source, source)),
                patch.object(timeboxed, "expected_manifest", return_value=manifest),
                patch.object(timeboxed, "run_one", side_effect=fake_worker),
                patch.object(staged, "refresh", return_value={"remaining": 12}),
                patch("surface_refs.load_surface_references", return_value=0),
            ):
                timeboxed.run()
                self.assertEqual(len(attempts), 5)
                self.assertEqual(len(list((target/"records").glob("*.json"))), 5)
                self.assertFalse((target/"summary.json").exists())
                timeboxed.run()
                self.assertEqual(len(attempts), 10)
                # Explicitly revisit an already complete batch: no work repeated.
                timeboxed.run("0")
                self.assertEqual(len(attempts), 10)
                timeboxed.run()
                self.assertEqual(len(attempts), 12)
                self.assertTrue((target/"summary.json").is_file())
                progress = json.loads((target/"progress.json").read_text())
                self.assertEqual(progress["batches_complete"], 3)
                self.assertEqual(progress["processed"], 12)
                timeboxed.run()
                self.assertEqual(len(attempts), 12)
                self.assertEqual(
                    json.loads((target/"summary.json").read_text())["counts"],
                    {"INDETERMINATE": 12},
                )

    def test_timeboxed_validation_and_previous_stage_preservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / "runs" / "order10" / timeboxed.STAGE
            (p / "records").mkdir(parents=True)
            manifest = {
                "stage": timeboxed.STAGE, "order": 10,
                "upstream_commit": "a"*40, "indices": [21],
            }
            (p / "manifest.json").write_text(json.dumps(manifest))
            code = g6(nx.cycle_graph(10))
            row = {"index": 21, "graph6": code, "status": "TIMEOUT",
                   "verdict": "INDETERMINATE", "bound": 120}
            path = p / "records" / "00000021.json"
            path.write_text(json.dumps(row))
            source = {21: {"index": 21, "graph6": code}}
            with patch.object(staged, "ROOT", root):
                self.assertEqual(staged.checked_records(10, timeboxed.STAGE, source)[21]["status"], "TIMEOUT")
                row["status"] = "DIVERGENT"
                path.write_text(json.dumps(row))
                with self.assertRaisesRegex(ValueError, "inconsistent"):
                    staged.checked_records(10, timeboxed.STAGE, source)


    def test_live_root_iterates_and_rules_are_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = Path(tmp) / "events.partial"
            graph = nx.cycle_graph(10)
            with ProgressTrace(journal) as trace:
                with trace_classifier(trace):
                    result = small.classify_clique_behavior(graph, bound=120)
            observations = summarize_events(journal)
            self.assertEqual(result.verdict.name, "CONVERGENT")
            self.assertEqual(observations["iterates"][0]["index"], 0)
            self.assertEqual(observations["iterates"][0]["pared_order"], 10)
            self.assertTrue(observations["methods_tried"])
            self.assertTrue(any(
                m["outcome"] == "no_certificate"
                for m in observations["methods_tried"]
            ))
            self.assertTrue(any(
                m["method"] == "eventually_clique_helly"
                for m in observations["methods_tried"]
            ))
            # Every completed root iteration has both the raw and pared orders.
            for row in observations["iterates"][1:]:
                if row.get("status") == "completed":
                    self.assertIsInstance(row["raw_order"], int)
                    self.assertIsInstance(row["pared_order"], int)
                    self.assertIsInstance(row["pared_edges"], int)

    def test_timeout_preserves_partial_graph_and_method_journal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "timeboxed_worker.py").write_text(
                """import sys, time, json
from pathlib import Path
p = Path(sys.argv[-1])
events = [
    {"event": "initial_pared", "order": 10, "edges": 15},
    {"event": "iterate_start", "iterate": 1},
    {"event": "clique_graph_complete", "iterate": 1, "order": 14, "edges": 35},
    {"event": "pared_iterate_complete", "iterate": 1, "order": 12, "edges": 29},
    {"event": "method_start", "id": 1, "method": "local_bridge_contraction"},
]
with p.open("w") as f:
    for event in events:
        f.write(json.dumps(event) + chr(10))
time.sleep(10)
""",
                encoding="utf-8",
            )
            with (
                patch.object(timeboxed, "ROOT", root),
                patch.object(timeboxed, "TIMEOUT_SECONDS", 1.0),
            ):
                result = timeboxed.run_one(g6(nx.cycle_graph(10)), root)
            self.assertEqual(result["status"], "TIMEOUT")
            self.assertEqual(result["iterates"][1]["index"], 1)
            self.assertEqual(result["iterates"][1]["raw_order"], 14)
            self.assertEqual(result["iterates"][1]["pared_order"], 12)
            self.assertEqual(result["in_progress_method"], "local_bridge_contraction")
            self.assertEqual(result["methods_tried"][0]["outcome"], "interrupted")
            self.assertEqual(list(root.glob("*.partial")), [])

    def test_legacy_manifest_resume_keeps_original_hashes_and_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "stage"
            dest.mkdir()
            old = {
                "order": 10, "stage": timeboxed.STAGE, "bound": 120,
                "timeout_seconds": 600, "memory_mib": 6144,
                "indices": [42, 43], "batch_size": 5,
                "runner_sha256": "old-runner-hash",
                "worker_sha256": "old-worker-hash",
            }
            (dest / "manifest.json").write_text(json.dumps(old))
            current = {
                **old,
                "runner_sha256": "new-runner-hash",
                "worker_sha256": "new-worker-hash",
                "trace_sha256": "new-trace-hash",
            }
            hashes = {
                "scripts/timeboxed.py": "old-runner-hash",
                "scripts/timeboxed_worker.py": "old-worker-hash",
            }
            with patch.object(timeboxed, "_legacy_filehash", side_effect=hashes.__getitem__):
                timeboxed.enforce_manifest(dest, current)
                self.assertEqual(json.loads((dest / "manifest.json").read_text()), old)
                changed_bound = dict(current, bound=121)
                with self.assertRaisesRegex(ValueError, "changed cohort"):
                    timeboxed.enforce_manifest(dest, changed_bound)
                fake_old = dict(old, worker_sha256="unrecognized")
                (dest / "manifest.json").write_text(json.dumps(fake_old))
                with self.assertRaisesRegex(ValueError, "unrecognized implementation"):
                    timeboxed.enforce_manifest(dest, current)

    def test_incomplete_journal_line_does_not_discard_completed_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = Path(tmp) / "interrupted.partial"
            journal.write_text(
                chr(10).join([
                    '{"event":"initial_pared","order":10,"edges":26}',
                    '{"event":"iterate_start","iterate":1}',
                    '{"event":"clique_graph_complete","iterate":1,"order":20,"edges":50}',
                    '{"event":',
                ]),
                encoding="utf-8",
            )
            summary = summarize_events(journal)
            self.assertEqual(summary["iterates"][0]["pared_order"], 10)
            self.assertEqual(summary["iterates"][1]["raw_order"], 20)
            self.assertEqual(summary["iterates"][1]["status"], "unpared_built")


if __name__ == "__main__":
    unittest.main()
