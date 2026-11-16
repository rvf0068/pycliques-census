"""Check frozen selection, iterate provenance, bounds, and fail-closed replay."""
from __future__ import annotations

import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
PIN_READY = (
    (ROOT / ".deps/pycliques-project-core9cover-v2/.git").is_dir()
    and (ROOT / ".venv-core9cover-v2/bin/python").exists()
)
# Generic historical smoke discovery must NOT import the newer algorithm.
if PIN_READY:
    import core9iterate_v1 as runner
    import core9iterate_v1_worker as worker


@unittest.skipUnless(PIN_READY, "Requires isolated post-PR14 pin")
class ParedIterateCoverTests(unittest.TestCase):
    def test_frozen_cohort_and_exact_pared_sources(self) -> None:
        selected = runner.cohort()
        self.assertEqual(tuple(selected), runner.EXPECTED_IDS)
        self.assertEqual(len(runner.tasks()), 16)
        self.assertEqual(sum(x["member_count"] for x in selected.values()), 881)
        self.assertEqual({mode for mode, _ in runner.tasks()}, {"g1", "g2"})
        for mode, i in runner.tasks():
            g = runner.nx.from_graph6_bytes(selected[i]["graph6"][mode].encode("ascii"))
            self.assertIn(len(g), ({13,14} if mode == "g1" else {21}))
            self.assertLessEqual(2*g.number_of_edges(), worker.LIMITS[mode]["max_cover_edges"])
        self.assertEqual(worker.LIMITS["g1"]["max_cover_vertices"], 28)
        self.assertEqual(worker.LIMITS["g2"]["max_cover_vertices"], 42)
        self.assertEqual(worker.LIMITS["g2"]["max_n"], 2)
        self.assertEqual(worker.LIMITS["g2"]["max_m"], 3)

    def test_real_g1_result_and_strict_certificates(self) -> None:
        selected = runner.cohort()
        mode, i = "g1", runner.EXPECTED_IDS[0]
        saved = worker.investigate(mode, selected[i]["graph6"][mode])
        row = {"mode": mode, "core_id": i, **saved}
        runner.validate_record(row, mode, i, selected)
        self.assertEqual(saved["search"]["cover_classes_total"], 1)
        self.assertNotIn(saved["status"], {"ERROR", "TIMEOUT"})
        self.assertEqual(saved["eligible"]["covers"][0]["cover_order"],
                         2*len(runner.nx.from_graph6_bytes(
                             selected[i]["graph6"][mode].encode("ascii"))))
        if saved["status"] == "EXHAUSTED":
            wrong = copy.deepcopy(row)
            wrong["search"]["morphisms_complete"] = False
            with self.assertRaisesRegex(ValueError, "False complete-exhaustion"):
                runner.validate_record(wrong, mode, i, selected)
        forged = copy.deepcopy(row)
        forged["status"] = "DIVERGENT"
        forged["search"]["search_status"] = "FOUND"
        forged["proof_status"] = "verified"
        forged["witness"] = {"m": 2, "n": 0}
        with self.assertRaisesRegex(ValueError, "Positive iterate certificate"):
            runner.validate_record(forged, mode, i, selected)

    def test_bounded_resource_failure_can_be_checkpointed_and_resumed(self) -> None:
        selected = runner.cohort()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = root / "historical"
            old.write_text("protected", encoding="utf-8")
            invoked = []
            def fake(mode: str, g6: str) -> dict:
                invoked.append((mode, g6))
                return {"status": "TIMEOUT", "elapsed_seconds": 120.0}
            with (
                patch.object(runner, "ROOT", root),
                patch.object(runner, "OUTPUT", root / "output"),
                patch.object(runner, "require_pin"),
                patch.object(runner, "cohort", return_value=selected),
                patch.object(runner, "manifest", return_value={"stage":"test"}),
                patch.object(runner, "run_worker", side_effect=fake),
            ):
                self.assertTrue(runner.run("0"))
                self.assertTrue(runner.run("0"))
                self.assertEqual(len(invoked), 4)
                self.assertEqual(len(runner.records(selected)), 4)
            self.assertEqual(old.read_text(encoding="utf-8"), "protected")

    def test_invalid_identity_and_false_proof_rejected(self) -> None:
        selected = runner.cohort()
        mode, i = runner.tasks()[0]
        good = {
            "mode": mode, "kind": mode, "core_id": i,
            "input_graph6": selected[i]["graph6"][mode],
            "scope": "pared_iterate_only", "status": "TIMEOUT",
        }
        runner.validate_record(good, mode, i, selected)
        with self.assertRaisesRegex(ValueError, "record identity"):
            runner.validate_record({**good, "scope": "original_ten_graphs"},
                                   mode, i, selected)
        with self.assertRaisesRegex(ValueError, "Resource failures"):
            runner.validate_record({**good, "proof_status":"verified"},
                                   mode, i, selected)

    def test_missing_stage_and_bounded_replay_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "not-created"
            with patch.object(runner, "OUTPUT", folder):
                with self.assertRaisesRegex(ValueError, "Stage has not started"):
                    runner.ensure_manifest({}, create=False)
            self.assertFalse(folder.exists())
            selected = runner.cohort()
            mode, i = runner.tasks()[0]
            good = {
                "mode":mode, "kind":mode, "core_id":i,
                "input_graph6": selected[i]["graph6"][mode],
                "scope":"pared_iterate_only", "status":"LIMIT_REACHED",
                "search":{
                    "search_status":"LIMIT_REACHED", "limits":worker.LIMITS[mode],
                    "cover_classes_total":1, "cover_classes_checked":1,
                    "cover_candidates_checked":1,
                    "configured_source_parameters":[
                        [m,n] for m in range(2,4) for n in range(3)],
                    "morphism_states":0, "morphism_assignments":0,
                },
                "eligible": worker.previous.eligible_sources(
                    runner.nx.from_graph6_bytes(selected[i]["graph6"][mode].encode("ascii")),
                    worker.LIMITS[mode]),
                "proof_status":"none", "witness":None,
            }
            output = Path(tmp) / "replay"
            runner.atomic(output / "manifest.json", {"stage":"test"})
            runner.atomic(output / "records" / f"{mode}_{i:08d}.json", good)
            with (
                patch.object(runner, "OUTPUT", output),
                patch.object(runner, "require_pin"),
                patch.object(runner, "cohort", return_value=selected),
                patch.object(runner, "manifest", return_value={"stage":"test"}),
                patch.object(runner, "run_worker", return_value={"status":"TIMEOUT"}),
            ):
                with self.assertRaisesRegex(ValueError, "Bounded replay failed"):
                    runner.verify(replay=True)


if __name__ == "__main__":
    unittest.main()
