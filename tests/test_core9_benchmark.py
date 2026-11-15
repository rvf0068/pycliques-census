"""Regressions for independent benchmark of order-nine pared-core classes."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import networkx as nx

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import core9_benchmark as benchmark
from pycliques import retractions

V3_TEST_ENV = (
    Path(sys.prefix).resolve() ==
    (SCRIPTS.parent / ".deps" / "pycliques-project-v3" / ".venv").resolve()
    and hasattr(retractions, "verify_special_octahedron_witness")
    and hasattr(retractions, "verify_retraction_witness")
)

S1_CORE = "HEiv^p{"


class Core9BenchmarkTests(unittest.TestCase):
    def test_core_cohort_has_exact_35_representatives(self):
        selected = benchmark.cohort()
        self.assertEqual(len(selected), 35)
        self.assertEqual(sum(v["member_count"] for v in selected.values()), 4038)
        self.assertEqual(list(selected), sorted(selected))
        self.assertTrue(all(len(nx.from_graph6_bytes(v["graph6"].encode())) == 9
                            for v in selected.values()))
        self.assertEqual(len({
            i for item in selected.values() for i in item["member_indices"]
        }), 4038)
        self.assertEqual(
            Counter(v["member_count"] for v in selected.values())[33], 0
        )

    def test_manifest_refuses_changes_and_corrupt_records(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "stage"
            meta = {
                "schema": 1, "stage": benchmark.STAGE, "core_ids": [17, 18],
                "bound": benchmark.CLIQUE_BOUND, "upstream_commit": "a" * 40,
            }
            benchmark.ensure_manifest(folder, meta)
            self.assertEqual(json.loads((folder / "manifest.json").read_text()), meta)
            with self.assertRaisesRegex(ValueError, "resume refused"):
                benchmark.ensure_manifest(folder, {**meta, "bound": 300})
            selected = {
                17: {"graph6": S1_CORE, "member_count": 10},
                18: {"graph6": S1_CORE, "member_count": 20},
            }
            (folder / "records").mkdir()
            record = {
                "core_id": 17, "graph6": S1_CORE, "member_count": 10,
                "scope": "pared_core_only", "bound": 120,
                "status": "BOUND_EXCEEDED", "verdict": "INDETERMINATE",
            }
            path = folder / "records" / "00000017.json"
            path.write_text(json.dumps(record))
            self.assertEqual(len(benchmark.saved_records(folder, selected)), 1)
            for changes in (
                {"graph6": "HEivrzk"},
                {"member_count": 9},
                {"status": "FALSIFIED"},
                {"scope": "original_graph"},
            ):
                path.write_text(json.dumps({**record, **changes}))
                with self.assertRaisesRegex(ValueError, "Malformed saved"):
                    benchmark.saved_records(folder, selected)

    def test_batch_next_resume_does_not_modify_original_census(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "runs" / "order10" / benchmark.STAGE
            selected = {
                i: {
                    "graph6": S1_CORE, "member_count": i,
                    "member_indices": list(range(i)), "conjectured_members": 0,
                }
                for i in range(1, 12)
            }
            meta = {
                "stage": benchmark.STAGE, "core_ids": list(selected),
                "bound": 120, "batch_size": benchmark.BATCH_SIZE,
            }
            saved_list = root / "indeterminate_order_10_v3.txt"
            saved_list.write_bytes(b"Original census entries are unchanged.\n")
            calls = []
            def fake_worker(graph6: str, folder: Path) -> dict:
                calls.append(graph6)
                return {
                    "status": "BOUND_EXCEEDED", "verdict": "INDETERMINATE",
                    "scope": "pared_core_only", "bound": 120,
                    "reason": "clique count exceeded bound",
                    "elapsed_seconds": 0.01,
                    "iterates": [{"index": 1, "status": "clique_bound_exceeded"}],
                    "methods_tried": [],
                }
            with (
                patch.object(benchmark, "ROOT", root),
                patch.object(benchmark, "FOLDER", out),
                patch.object(benchmark, "cohort", return_value=selected),
                patch.object(benchmark, "manifest", return_value=meta),
                patch.object(benchmark, "run_one", side_effect=fake_worker),
            ):
                self.assertTrue(benchmark.run("next"))
                self.assertEqual(len(list((out / "records").glob("*.json"))), 5)
                self.assertTrue(benchmark.run("next"))
                self.assertFalse(benchmark.run("next"))
                self.assertFalse(benchmark.run("next"))
                self.assertEqual(len(calls), 11)
                benchmark.verify()
                self.assertTrue((out / "report.md").is_file())
                self.assertEqual(
                    json.loads((out / "summary.json").read_text())["processed"], 11
                )
            self.assertEqual(
                saved_list.read_bytes(), b"Original census entries are unchanged.\n"
            )

    def test_worker_timeout_and_failure_cannot_be_positive(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            with patch.object(benchmark, "TIMEOUT_SECONDS", 0.001):
                r = benchmark.run_one(S1_CORE, folder)
            self.assertIn(r["status"], {"TIMEOUT", "ERROR"})
            self.assertEqual(r["verdict"], "INDETERMINATE")
            self.assertFalse(list(folder.iterdir()))

    @unittest.skipUnless(V3_TEST_ENV, "Needs separate v3 witness-capable environment")
    def test_real_core_certificate_and_isolated_worker(self):
        import core9_worker
        with tempfile.TemporaryDirectory() as tmp:
            journal = str(Path(tmp) / "events.jsonl")
            row = core9_worker.classify(S1_CORE, journal)
            self.assertEqual(row["status"], "CONVERGENT")
            self.assertEqual(row["proof_status"], "verified_chain")
            self.assertEqual(row["scope"], "pared_core_only")
            result = benchmark.run_one(S1_CORE, Path(tmp))
            self.assertEqual(result["status"], "CONVERGENT", result.get("stderr_excerpt"))
            self.assertEqual(result["diagnostic_schema"], 3)
            self.assertTrue(result["iterates"])
            verified = {
                "core_id": 1, "graph6": S1_CORE, "member_count": 1,
                **result,
            }
            benchmark.check_positive(1, verified, S1_CORE)
            changed = json.loads(json.dumps(verified))
            changed["proof"]["origin_graph6"] = "HEivrzk"
            with self.assertRaisesRegex(ValueError, "Nonreplayable"):
                benchmark.check_positive(1, changed, S1_CORE)


if __name__ == "__main__":
    unittest.main()
