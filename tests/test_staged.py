"""Unit tests for staged census cohort selection and surface registration."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import staged  # noqa: E402
import surface_refs  # noqa: E402
from pycliques.small import ReferenceStatus, _reference_match


class StageSelectionTests(unittest.TestCase):
    def setUp(self):
        self.source = {
            10: {"index": 10, "graph6": "HAAAAAAAA"},
            20: {"index": 20, "graph6": "HBBBBBBBB"},
            30: {"index": 30, "graph6": "HCCCCCCCC"},
            40: {"index": 40, "graph6": "HDDDDDDDD"},
            50: {"index": 50, "graph6": "HEEEEEEEE"},
        }
        self.origins = {
            10: "10 9 AA - conjectured_divergent surface10",
            20: "20 9 BB - - -",
            30: "30 9 CC - - -",
            40: "40 9 DD - - -",
            50: "50 9 EE - - -",
        }
        self.c10 = {20: {"status": "RETRACTION_FOUND"}, 30: {"status": "NO_RETRACTION"}}
        self.homotopy = {
            30: {"is_exact": True, "spheres": {"1": 2}},
            40: {"is_exact": True, "spheres": {}},
            50: {"is_exact": False, "spheres": {"1": 1}},
        }

    def records(self, order, stage, source):
        if stage == "c10":
            return self.c10
        if stage == "homotopy":
            return self.homotopy
        return {}

    def test_stage_selection_skips_conjectural_and_proven_c10(self):
        with (
            patch.object(staged, "census", return_value=(Path("."), self.source, self.origins)),
            patch.object(staged, "checked_records", side_effect=self.records),
        ):
            c10, _ = staged.stage_selection(9, "c10")
            self.assertEqual(set(c10), {20, 30, 40, 50})
            bound, _ = staged.stage_selection(9, "bound60")
            self.assertEqual(set(bound), {30, 40, 50})

            hom, _ = staged.stage_selection(10, "homotopy")
            self.assertEqual(set(hom), {10, 30, 40, 50})
            bound70, _ = staged.stage_selection(10, "bound70")
            self.assertEqual(set(bound70), {30, 40})

    def test_selection_is_independent_of_current_stage_results(self):
        with (
            patch.object(staged, "census", return_value=(Path("."), self.source, self.origins)),
            patch.object(staged, "checked_records", side_effect=self.records),
        ):
            before, _ = staged.stage_selection(9, "bound60")
            # No stage's own completed records are consulted: replay is stable.
            self.assertEqual(set(before), {30, 40, 50})

    def test_surface_registry_uses_only_remaining_and_graph6_label(self):
        graph = nx.wheel_graph(9)
        self.assertTrue(staged.is_surface(graph))
        graph6 = nx.to_graph6_bytes(graph, header=False).decode().strip()
        with tempfile.TemporaryDirectory() as td:
            file = Path(td) / "surfaces.tsv"
            with (
                patch.object(staged, "active", return_value=(
                    {1: {"graph6": graph6}},
                    {1: "1 9 foo - - -"},
                    {1: {"graph6": graph6}},
                )),
                patch.object(staged, "reference_file", return_value=file),
            ):
                self.assertEqual(staged.surface_registry(9), 1)
            self.assertEqual(file.read_text().splitlines()[-1], f"1 {graph6}")
            with patch.object(surface_refs, "SURFACE_FILE", file):
                self.assertEqual(surface_refs.load_surface_references(), 1)
            match = _reference_match(graph)
            self.assertIsNotNone(match)
            self.assertEqual(match[1], ReferenceStatus.CONJECTURED)
            self.assertEqual(match[2], graph6)

    def test_baseline_detects_wrong_exception(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "runs" / "baseline-through8-bound30"
            path.mkdir(parents=True)
            (path / "summary.json").write_text(json.dumps({
                "orders": [{"order": n, "connected_total": v}
                           for n, v in ((1,1),(2,1),(3,2),(4,6),(5,21),(6,112),(7,853),(8,11117))],
                "baseline_expectation_met": True,
                "unresolved": [{"order": 8, "index": 999, "graph6": "wrong"}],
            }))
            with patch.object(staged, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "sole historical exception"):
                    staged.check_baseline()


if __name__ == "__main__":
    unittest.main()
