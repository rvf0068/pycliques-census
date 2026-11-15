"""Fast regression checks for the frozen no-S2 local v3 cohort and runner."""
from __future__ import annotations

from collections import Counter
import json
import subprocess
from unittest.mock import Mock, patch
from pathlib import Path
import sys
import tempfile
import unittest

import networkx as nx

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import staged  # noqa: E402
import timeboxed_v3 as runner  # noqa: E402


def gf2_rank(vectors: list[int]) -> int:
    basis = {}
    for value in vectors:
        while value:
            pivot = value.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = value
                break
            value ^= basis[pivot]
    return len(basis)


def b2_mod2(graph: nx.Graph) -> int:
    """Compute H_2 over F2 directly from the triangle/tetrahedron boundaries."""
    vertices = list(graph)
    faces = {2: [], 3: [], 4: []}
    from itertools import combinations

    for cardinality in (2, 3, 4):
        for subset in combinations(vertices, cardinality):
            if all(graph.has_edge(u, v) for u, v in combinations(subset, 2)):
                faces[cardinality].append(subset)
    mapping2 = {f: i for i, f in enumerate(faces[2])}
    mapping3 = {f: i for i, f in enumerate(faces[3])}
    boundary3 = [
        sum(1 << mapping2[face[:i] + face[i+1:]]
            for i in range(3))
        for face in faces[3]
    ]
    boundary4 = [
        sum(1 << mapping3[face[:i] + face[i+1:]]
            for i in range(4))
        for face in faces[4]
    ]
    return len(faces[3]) - gf2_rank(boundary3) - gf2_rank(boundary4)


class LocalV3Tests(unittest.TestCase):
    def test_frozen_cohort_matches_historical_results(self):
        eligible, source = runner.cohort()
        self.assertEqual(len(eligible), 153)
        self.assertTrue(all(i in source for i in eligible))
        labels = {}
        with runner.COHORT.open() as file:
            for row in file:
                if row.startswith("#") or row.startswith("index") or not row.strip():
                    continue
                index, g6, label = row.strip().split("\t")
                self.assertIn(int(index), eligible)
                self.assertEqual(b2_mod2(nx.from_graph6_bytes(g6.encode())), 0)
                labels[int(index)] = label
        self.assertEqual(Counter(labels.values()), Counter({"S1": 115, "S3": 35, "S1+S3": 3}))

    def test_separate_upstream_and_unchanged_v2_provenance(self):
        self.assertEqual(runner.CLIQUE_BOUND, 120)
        self.assertEqual(runner.TIMEOUT_SECONDS, 120)
        self.assertEqual(runner.MEMORY_MIB, 2048)
        self.assertEqual(runner.BATCH_SIZE, 5)
        self.assertEqual(runner.current_v3_pin(),
                         runner.V3_PIN.read_text(encoding="ascii").strip())
        cohort, _ = runner.cohort()
        meta = runner.manifest(cohort)
        self.assertEqual(meta["indices"], sorted(cohort))
        self.assertEqual(meta["parallel_workers"], 1)
        self.assertEqual(meta["historical_upstream_commit"],
                         (runner.ROOT / "config" / "pycliques_commit.txt").read_text().strip())

    def test_positive_worker_classification_has_replayable_chain(self):
        import timeboxed_worker_v3
        with tempfile.TemporaryDirectory() as directory:
            journal = str(Path(directory) / "events.jsonl")
            record = timeboxed_worker_v3.classify("ICvbvy}|g", journal)
        self.assertEqual(record["status"], "CONVERGENT")
        self.assertEqual(record["proof_status"], "verified_chain")
        self.assertEqual(record["proof"]["rule"], "eventually_clique_helly")
        self.assertGreaterEqual(record["peak_rss_kib"], 0)
        self.assertEqual(record["bound"], 120)

    def test_real_isolated_worker_under_2gib_limit(self):
        # Exercise the exact subprocess/RLIMIT_AS path without creating
        # census records or re-running any of the 153 research cases.
        with tempfile.TemporaryDirectory() as directory:
            result = runner.run_one("ICvbvy}|g", Path(directory))
        self.assertEqual(result["status"], "CONVERGENT", result.get("stderr_excerpt"))
        self.assertEqual(result["proof_status"], "verified_chain")
        self.assertEqual(result["diagnostic_schema"], 3)
        self.assertGreaterEqual(result["elapsed_seconds"], 0)

    @staticmethod
    def sandbox(root: Path, indices: list[int]):
        """Small stage fixture using a real original order-10 graph6."""
        graph6 = "ICvbvy}|g"
        source = {i: {"index": i, "graph6": graph6} for i in indices}
        meta = {
            "schema": 3, "stage": runner.STAGE, "order": 10,
            "upstream_commit": "a" * 40, "indices": indices,
            "batch_size": runner.BATCH_SIZE, "bound": runner.CLIQUE_BOUND,
        }
        rows = [
            "# Unresolved test graphs",
            *(f"{i} 10 {graph6} - - -" for i in indices),
        ]
        (root / "indeterminate_order_10.txt").write_text(
            "\n".join(rows) + "\n", encoding="utf-8"
        )
        return source, meta

    def test_run_resumes_five_graph_batches_without_repeating_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, meta = self.sandbox(root, list(range(1, 12)))
            snapshot = (root / "indeterminate_order_10.txt").read_bytes()
            calls = []
            def worker(graph6, _folder):
                calls.append(graph6)
                return {
                    "status": "BOUND_EXCEEDED", "verdict": "INDETERMINATE",
                    "bound": 120, "elapsed_seconds": .01, "reason": "fixture",
                }
            with (
                patch.object(runner, "ROOT", root),
                patch.object(staged, "ROOT", root),
                patch.object(runner, "cohort", return_value=(source, source)),
                patch.object(runner, "manifest", return_value=meta),
                patch.object(runner, "run_one", side_effect=worker),
            ):
                self.assertTrue(runner.run("next"))
                folder = staged.stage_dir(10, runner.STAGE)
                self.assertEqual(len(list((folder / "records").glob("*.json"))), 5)
                self.assertTrue((folder / "batches" / "00000.json").exists())
                self.assertTrue(runner.run("next"))
                self.assertFalse(runner.run("next"))
                self.assertFalse(runner.run("next"))
                self.assertEqual(len(calls), 11)
                self.assertEqual(json.loads((folder / "summary.json").read_text())["processed"], 11)
                self.assertEqual(json.loads((folder / "progress.json").read_text())["complete_batches"], 3)
                self.assertEqual((root / "indeterminate_order_10.txt").read_bytes(), snapshot)
                self.assertIn("Remaining=11", (root / "indeterminate_order_10_v3.txt").read_text())

    def test_partial_batch_restart_keeps_atomic_graph_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, meta = self.sandbox(root, list(range(1, 7)))
            attempts = []
            def worker(graph6, _folder):
                attempts.append(graph6)
                if len(attempts) == 3:
                    raise KeyboardInterrupt("simulated interruption")
                return {
                    "status": "INDETERMINATE", "verdict": "INDETERMINATE",
                    "bound": 120, "elapsed_seconds": .01,
                }
            with (
                patch.object(runner, "ROOT", root),
                patch.object(staged, "ROOT", root),
                patch.object(runner, "cohort", return_value=(source, source)),
                patch.object(runner, "manifest", return_value=meta),
                patch.object(runner, "run_one", side_effect=worker),
            ):
                with self.assertRaises(KeyboardInterrupt):
                    runner.run("next")
                folder = staged.stage_dir(10, runner.STAGE)
                self.assertEqual(len(list((folder / "records").glob("*.json"))), 2)
                self.assertTrue(runner.run("next"))
                self.assertEqual(len(list((folder / "records").glob("*.json"))), 5)
                self.assertEqual(len(attempts), 6)
                self.assertFalse(runner.run("next"))
                self.assertEqual(len(list((folder / "records").glob("*.json"))), 6)

    def test_timeout_and_worker_exit_are_not_positive_proofs(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            proc = Mock()
            proc.wait.side_effect = subprocess.TimeoutExpired("worker", runner.TIMEOUT_SECONDS)
            with (
                patch.object(runner.subprocess, "Popen", return_value=proc),
                patch.object(runner, "kill_group") as kill,
            ):
                result = runner.run_one("ICvbvy}|g", folder)
                kill.assert_called_once_with(proc)
            self.assertEqual(result["status"], "TIMEOUT")
            self.assertEqual(result["verdict"], "INDETERMINATE")
            self.assertEqual(list(folder.glob("*.partial")), [])
            proc = Mock()
            proc.wait.return_value = None
            proc.returncode = 2
            with patch.object(runner.subprocess, "Popen", return_value=proc):
                result = runner.run_one("ICvbvy}|g", folder)
            self.assertEqual(result["status"], "ERROR")
            self.assertEqual(result["verdict"], "INDETERMINATE")
            self.assertEqual(list(folder.glob("*.partial")), [])

    def test_manifest_mismatch_blocks_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / "runs" / "order10" / runner.STAGE
            baseline = {"stage": runner.STAGE, "timeout_seconds": 120}
            runner.ensure_manifest(folder, baseline)
            runner.ensure_manifest(folder, dict(baseline))
            with self.assertRaisesRegex(ValueError, "resume refused"):
                runner.ensure_manifest(folder, {**baseline, "timeout_seconds": 600})
            self.assertEqual(json.loads((folder / "manifest.json").read_text()), baseline)

    def test_verify_and_resume_reject_tampered_positive_proof(self):
        from timeboxed_worker_v3 import classify
        graph6 = "ICvbvy}|g"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, meta = self.sandbox(root, [7])
            folder = root / "runs" / "order10" / runner.STAGE
            (folder / "records").mkdir(parents=True)
            (folder / "manifest.json").write_text(json.dumps(meta), encoding="utf-8")
            record = classify(graph6, str(root / "journal.jsonl"))
            record.update(index=7, graph6=graph6, batch=0, elapsed_seconds=.1)
            self.assertEqual(record["status"], "CONVERGENT")
            file = folder / "records" / "00000007.json"
            file.write_text(json.dumps(record), encoding="utf-8")
            with (
                patch.object(runner, "ROOT", root),
                patch.object(staged, "ROOT", root),
                patch.object(runner, "cohort", return_value=(source, source)),
                patch.object(runner, "manifest", return_value=meta),
            ):
                runner.verify()  # Genuine certificate passes independent replay.
                modified = json.loads(file.read_text())
                # A valid proof belonging to another source graph is forbidden,
                # even with the status string claiming full chain verification.
                modified["proof"]["origin_graph6"] = "I????????"
                file.write_text(json.dumps(modified), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "positive v3 certificate"):
                    runner.verify()
                with self.assertRaisesRegex(ValueError, "positive v3 certificate"):
                    runner.run("next")
                self.assertFalse((root / "indeterminate_order_10_v3.txt").exists())

    def test_v3_refresh_does_not_touch_historical_file(self):
        original = (runner.ROOT / "indeterminate_order_10.txt").read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            original_root = runner.ROOT
            try:
                # Only redirect the generated file; preexisting snapshot remains input.
                import unittest.mock as mock
                with mock.patch.object(runner, "ROOT", Path(directory)):
                    (Path(directory) / "indeterminate_order_10.txt").write_bytes(original)
                    n = runner.refresh_v3({})
                    self.assertEqual(n, 8648)
                    self.assertTrue((Path(directory) / "indeterminate_order_10_v3.txt").exists())
            finally:
                self.assertEqual(
                    (original_root / "indeterminate_order_10.txt").read_bytes(), original
                )


if __name__ == "__main__":
    unittest.main()
