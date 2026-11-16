"""No-original-graph-verdict checks for the post-PR14 core9 covering stage."""
from __future__ import annotations

import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
NEW_PIN_AVAILABLE = (
    (ROOT / ".deps/pycliques-project-core9cover-v2/.git").is_dir()
    and (ROOT / ".venv-core9cover-v2/bin/python").exists()
)
# Historical smoke must not import or execute the new pinned worker.
if NEW_PIN_AVAILABLE:
    import core9cover_v2 as runner
    import core9cover_v2_worker as worker


@unittest.skipUnless(NEW_PIN_AVAILABLE, "Requires the isolated post-PR14 environment")
class CoverAC3V2Tests(unittest.TestCase):
    def test_original_census_pinned_and_eight_cases_exact(self) -> None:
        selected = runner.cohort()
        self.assertEqual(tuple(selected), runner.EXPECTED_IDS)
        self.assertEqual(sum(row["member_count"] for row in selected.values()), 881)
        self.assertEqual(len(runner.tasks()), 16)
        self.assertEqual(runner.PIN, "005f6cc06a3bf1332bf6e729af73eea8ff26a40d")
        self.assertEqual(worker.BASELINE["max_source_order"], 18)
        self.assertEqual(worker.EXPANDED["max_source_order"], 42)
        self.assertEqual(worker.BASELINE["max_n"], 0)
        self.assertEqual(worker.EXPANDED["max_n"], 2)
        self.assertEqual(worker.BASELINE["max_morphism_assignments"], 100000)

    def test_one_baseline_search_repeats_exact_exhaustion(self) -> None:
        selected = runner.cohort()
        record = worker.investigate("baseline", selected[2317843]["graph6"])
        self.assertEqual(record["status"], "EXHAUSTED")
        self.assertEqual(record["search"]["cover_classes_total"], 1)
        self.assertEqual(record["search"]["cover_classes_checked"], 1)
        self.assertEqual(record["search"]["cover_classes_complete"], True)
        self.assertEqual(record["search"]["morphisms_complete"], True)
        self.assertTrue(record["eligible"]["covers"][0]["source_parameters_eligible"])
        self.assertLess(record["search"]["morphism_assignments"], 100000)
        runner.validate_record(
            {"mode": "baseline", "core_id": 2317843, **record},
            "baseline", 2317843, selected,
        )

    def test_deck_geometry_prunes_nominally_eligible_parameters(self) -> None:
        selected = runner.cohort()
        graph6 = selected[2317843]["graph6"]
        graph = runner.nx.from_graph6_bytes(graph6.encode("ascii"))
        baseline = worker.eligible_sources(graph, worker.BASELINE)["covers"][0]
        expanded = worker.eligible_sources(graph, worker.EXPANDED)["covers"][0]
        self.assertEqual(baseline["cover_order"], 18)
        self.assertEqual(expanded["deck_radius"], baseline["deck_radius"])
        self.assertTrue(set(map(tuple, baseline["source_parameters_eligible"])).issubset(
            set(map(tuple, expanded["source_parameters_eligible"]))
        ))
        self.assertTrue(
            any(n > 0 for _, n in expanded["source_parameters_eligible"]),
            "Expanded configuration must actually test different source families",
        )

    def test_invalid_negative_result_cannot_claim_exhaustive(self) -> None:
        selected = runner.cohort()
        i = 2317843
        record = worker.investigate("baseline", selected[i]["graph6"])
        good = {"mode": "baseline", "core_id": i, **record}
        runner.validate_record(good, "baseline", i, selected)
        changed = copy.deepcopy(good)
        changed["search"]["morphisms_complete"] = False
        with self.assertRaisesRegex(ValueError, "False complete-exhaustion"):
            runner.validate_record(changed, "baseline", i, selected)
        changed = copy.deepcopy(good)
        changed["search"]["limits"]["max_n"] = 8
        with self.assertRaisesRegex(ValueError, "finite family"):
            runner.validate_record(changed, "baseline", i, selected)
        changed = copy.deepcopy(good)
        changed["status"] = "DIVERGENT"
        changed["search"]["search_status"] = "FOUND"
        changed["proof_status"] = "verified"
        changed["witness"] = {"m": 3, "n": 0}
        with self.assertRaisesRegex(ValueError, "Positive divergence"):
            runner.validate_record(changed, "baseline", i, selected)

    def test_missing_stage_is_not_created_by_verifier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "not_started"
            with patch.object(runner, "OUTPUT", path):
                with self.assertRaisesRegex(ValueError, "Stage has not started"):
                    runner.ensure_manifest({}, create=False)
            self.assertFalse(path.exists())

    def test_malformed_core_identity_and_resource_failure(self) -> None:
        selected = runner.cohort()
        i = runner.EXPECTED_IDS[0]
        good = {
            "core_id": i, "mode": "baseline", "kind": "baseline",
            "status": "TIMEOUT", "scope": "nine_vertex_core_only",
            "input_graph6": selected[i]["graph6"],
        }
        runner.validate_record(good, "baseline", i, selected)
        with self.assertRaisesRegex(ValueError, "Resource failure"):
            runner.validate_record(
                {**good, "proof_status": "verified"}, "baseline", i, selected
            )
        with self.assertRaisesRegex(ValueError, "record identity"):
            runner.validate_record(
                {**good, "scope": "original_ten_graph_classification"},
                "baseline", i, selected,
            )

    def test_worker_timeout_is_checkpointed_without_repeating_work(self) -> None:
        selected = runner.cohort()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "output"
            original = root / "historical.txt"
            original.write_text("unchanged", encoding="utf-8")
            calls = []
            def fake_worker(mode: str, graph6: str) -> dict:
                calls.append((mode, graph6))
                return {"status": "TIMEOUT", "elapsed_seconds": 90.0}
            with (
                patch.object(runner, "ROOT", root),
                patch.object(runner, "OUTPUT", output),
                patch.object(runner, "require_pin"),
                patch.object(runner, "cohort", return_value=selected),
                patch.object(runner, "manifest", return_value={"stage": "test"}),
                patch.object(runner, "run_worker", side_effect=fake_worker),
            ):
                self.assertTrue(runner.run("0"))
                self.assertTrue(runner.run("0"))
                self.assertEqual(len(calls), 4)
                saved = runner.records(selected)
                self.assertEqual(len(saved), 4)
                self.assertTrue(all(x["status"] == "TIMEOUT" for x in saved.values()))
                self.assertTrue(all(x["kind"] == "baseline" for x in saved.values()))
            self.assertEqual(original.read_text(encoding="utf-8"), "unchanged")

    def test_dirty_pinned_dependency_is_rejected(self) -> None:
        with patch.object(runner.subprocess, "check_output", side_effect=[
            runner.PIN + "\n", " M packages/pycombtop/src/example.py\n"
        ]):
            with self.assertRaisesRegex(ValueError, "working tree is dirty"):
                runner.require_pin()

    def test_replay_timeout_is_explicit_failure(self) -> None:
        selected = runner.cohort()
        mode, i = runner.tasks()[0]
        recorded = {
            "mode": mode, "core_id": i,
            **worker.investigate(mode, selected[i]["graph6"]),
        }
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "results"
            runner.atomic(output / "manifest.json", {"stage": "test"})
            runner.atomic(output / "records" / f"{mode}_{i:08d}.json", recorded)
            with (
                patch.object(runner, "OUTPUT", output),
                patch.object(runner, "require_pin"),
                patch.object(runner, "cohort", return_value=selected),
                patch.object(runner, "manifest", return_value={"stage": "test"}),
                patch.object(runner, "run_worker", return_value={"status": "TIMEOUT"}),
            ):
                with self.assertRaisesRegex(ValueError, "Bounded replay failed"):
                    runner.verify(replay=True)


if __name__ == "__main__":
    unittest.main()
