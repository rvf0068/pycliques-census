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
            10: "10 10 AA - conjectured_divergent surface10",
            20: "20 10 BB - - -",
            30: "30 10 CC - - -",
            40: "40 10 DD - - -",
            50: "50 9 EE - - -",
        }
        self.c10 = {20: {"status": "RETRACTION_FOUND"}, 30: {"status": "NO_RETRACTION"}}
        self.homotopy = {
            10: {"is_exact": True, "is_limited": False, "spheres": {"1": 3}},
            30: {"is_exact": True, "is_limited": False, "spheres": {"1": 2}},
            40: {"is_exact": True, "is_limited": False, "spheres": {}},
            50: {"is_exact": False, "is_limited": False, "spheres": {"1": 1}},
        }

    def records(self, order, stage, source):
        if stage == "c10":
            return self.c10
        if stage == "homotopy":
            return self.homotopy
        if stage == "s1divergence":
            return {}
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
            # Graph 10 is conjectural; 20 was resolved by C10; 50 pares
            # to order nine. None is eligible for the homotopy stage.
            self.assertEqual(set(hom), {30, 40})
            # Order 10 uses exact contractible/wedges of S^1, but never
            # conjectural cases, even if their homotopy verdict is exact.
            order10_bound70, _ = staged.stage_selection(10, "bound70")
            self.assertEqual(set(order10_bound70), {30, 40})
            order9_bound70, _ = staged.stage_selection(9, "bound70")
            self.assertEqual(set(order9_bound70), {30, 40, 50})

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

    def test_post_stages_are_resumable_and_refresh_working_file(self):
        """Bound 70 removes a now-determined surface from the reference file."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run = root / "runs" / "order9" / "initial"
            order_dir = run / "order9"
            order_dir.mkdir(parents=True)

            wheel = nx.wheel_graph(9)
            cycle = nx.cycle_graph(9)
            path = nx.path_graph(9)
            # The same surface under another original index is just a fixture
            # for distinguishing a conditional reference from a newly resolved one.
            graph6 = {
                10: nx.to_graph6_bytes(wheel, header=False).decode().strip(),
                20: nx.to_graph6_bytes(cycle, header=False).decode().strip(),
                30: nx.to_graph6_bytes(path, header=False).decode().strip(),
                40: nx.to_graph6_bytes(wheel, header=False).decode().strip(),
            }
            to_g6 = lambda graph: nx.to_graph6_bytes(graph, header=False).decode().strip()
            manifest = {"min_order": 9, "max_order": 9, "upstream_commit": "a" * 40}
            (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            summary = {
                "manifest": manifest,
                "orders": [{"order": 9, "connected_total": 261080, "indeterminate": 4}],
                "unresolved": [
                    {"order": 9, "index": index, "graph6": graph6[index],
                     "reason": "conjectured divergent reference" if index == 10 else "bound exceeded"}
                    for index in (10, 20, 30, 40)
                ],
            }
            (run / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
            original = "\n".join([
                f"10 9 {graph6[10]} reference conjectured_divergent snub",
                f"20 9 {graph6[20]} - - -",
                f"30 9 {graph6[30]} - - -",
                f"40 9 {graph6[40]} - - -",
            ]) + "\n"
            original_file = order_dir / "indeterminate_order_9.txt"
            original_file.write_text(original, encoding="utf-8")

            def fake_compute(_order, stage, graph):
                name = to_g6(graph)
                if stage == "c10":
                    return (
                        {"status": "RETRACTION_FOUND", "witness": {"test": True}}
                        if name == graph6[20]
                        else {"status": "NO_RETRACTION", "witness": None}
                    )
                if stage == "bound70" and name == graph6[40]:
                    verdict = "DIVERGENT"
                else:
                    verdict = "INDETERMINATE"
                return {
                    "verdict": verdict, "reason": "fixture result",
                    "pared_order": 9, "pared_graph6": name,
                    "certificate_rule": "-", "certificate_target_status": "-",
                    "certificate_target_label": "-",
                }

            with (
                patch.object(staged, "ROOT", root),
                patch.object(staged, "current_pin", return_value="a" * 40),
                patch.object(staged, "compute", side_effect=fake_compute) as calculation,
            ):
                staged.run_stage(9, "c10")
                self.assertEqual(calculation.call_count, 3)
                working = root / "indeterminate_order_9.txt"
                self.assertEqual(
                    [int(x.split()[0]) for x in working.read_text().splitlines()
                     if not x.startswith("#")],
                    [10, 30, 40],
                )
                staged.run_stage(9, "c10")
                self.assertEqual(calculation.call_count, 3)

                staged.run_stage(9, "bound60")
                self.assertEqual(calculation.call_count, 5)
                # Previously the surface registry was generated by bound60;
                # now it is finalized by bound70.
                surfaces = root / "config" / "conjectured_surfaces_order9.tsv"
                self.assertFalse(surfaces.exists())
                staged.run_stage(9, "bound70")
                self.assertEqual(calculation.call_count, 7)
                self.assertEqual(surfaces.read_text().splitlines()[-1], f"10 {graph6[10]}")
                self.assertEqual(
                    [int(x.split()[0]) for x in working.read_text().splitlines()
                     if not x.startswith("#")],
                    [10, 30],
                )
                staged.run_stage(9, "bound70")
                self.assertEqual(calculation.call_count, 7)
                self.assertEqual(original_file.read_text(), original)

    def test_order10_bound70_requires_completed_homotopy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            initial = root / "runs" / "order10" / "initial"
            initial.mkdir(parents=True)
            (initial / "summary.json").write_text("{}", encoding="utf-8")
            registry = root / "config" / "conjectured_surfaces_order9.tsv"
            registry.parent.mkdir()
            registry.write_text("# test reference file\n", encoding="utf-8")

            with (
                patch.object(staged, "ROOT", root),
                patch.object(staged, "current_pin", return_value="a" * 40),
                patch.object(staged, "load_surface_references", return_value=0),
                patch.object(staged, "stage_selection", return_value=({}, {})),
            ):
                with self.assertRaisesRegex(ValueError, "Finish order-10 stage c10"):
                    staged.run_stage(10, "bound70")

    def test_order10_bound70_filter_rejects_other_types_and_limited(self):
        source = {
            index: {"index": index, "graph6": "HAAAAAAAA"}
            for index in range(10, 21)
        }
        origins = {index: f"{index} 10 HAAAAAAAA - - -" for index in source}
        origins[10] = "10 10 HAAAAAAAA reference conjectured_divergent snub"
        origins[19] = "19 9 HAAAAAAAA - - -"
        c10 = {11: {"status": "RETRACTION_FOUND"}}
        homotopy = {
            10: {"is_exact": True, "is_limited": False, "spheres": {"1": 2}},
            12: {"is_exact": True, "is_limited": False, "spheres": {}},
            13: {"is_exact": True, "is_limited": False, "spheres": {"1": 3}},
            14: {"is_exact": True, "is_limited": False, "spheres": {"2": 1}},
            15: {"is_exact": False, "is_limited": False, "spheres": {"1": 1}},
            16: {"is_exact": True, "is_limited": True, "spheres": {}},
            17: {"is_exact": True, "is_limited": False, "spheres": {"0": 1}},
            18: {"is_exact": True, "is_limited": False, "spheres": {"1": 0}},
            19: {"is_exact": True, "is_limited": False, "spheres": {"1": 2}},
            20: {"is_exact": True, "is_limited": False, "spheres": {"1": 2}},
        }

        def records(order, stage, _source):
            self.assertEqual(order, 10)
            if stage == "c10":
                return c10
            if stage == "homotopy":
                return homotopy
            if stage == "s1divergence":
                return {}
            self.fail(f"Current stage's own records should never affect selection: {stage}")

        with (
            patch.object(staged, "census", return_value=(Path("."), source, origins)),
            patch.object(staged, "checked_records", side_effect=records),
        ):
            homotopy_selection, _ = staged.stage_selection(10, "homotopy")
            self.assertEqual(set(homotopy_selection), set(range(12, 19)) | {20})
            selection, _ = staged.stage_selection(10, "bound70")
            # Despite a suitable exact homotopy type, index 19 pares to
            # nine vertices, so is excluded from both stages.
            self.assertEqual(set(selection), {12, 13, 20})

    def test_order10_s1_divergence_cohort_exactly_one_circle(self):
        """No wedges of two circles, contractibles, conjectural, or C10 proofs."""
        source = {
            i: {"index": i, "graph6": "I????????"}
            for i in range(101, 108)
        }
        origins = {i: f"{i} 10 I???????? - - -" for i in source}
        origins[103] = "103 10 I???????? reference conjectured_divergent snub"
        origins[107] = "107 9 I???????? - - -"
        c10 = {102: {"status": "RETRACTION_FOUND"}}
        homotopy = {
            101: {"is_exact": True, "is_limited": False, "spheres": {"1": 1}},
            102: {"is_exact": True, "is_limited": False, "spheres": {"1": 1}},
            103: {"is_exact": True, "is_limited": False, "spheres": {"1": 1}},
            104: {"is_exact": True, "is_limited": False, "spheres": {"1": 2}},
            105: {"is_exact": True, "is_limited": False, "spheres": {}},
            106: {"is_exact": False, "is_limited": True, "spheres": {"1": 1}},
            107: {"is_exact": True, "is_limited": False, "spheres": {"1": 1}},
        }
        s1 = {
            101: {
                "status": "DIVERGENT", "rule": "triangular_cover_pair",
                "witness": {"kind": "triangular_cover_pair"},
            }
        }

        def checked(order, stage, _source):
            self.assertEqual(order, 10)
            if stage == "c10":
                return c10
            if stage == "homotopy":
                return homotopy
            if stage == "s1divergence":
                return s1
            return {}

        with (
            patch.object(staged, "census", return_value=(Path("."), source, origins)),
            patch.object(staged, "checked_records", side_effect=checked),
        ):
            selection, _ = staged.stage_selection(10, "s1divergence")
            # Own-stage results must not affect the fixed, resumable cohort.
            self.assertEqual(set(selection), {101})
            selection, _ = staged.stage_selection(10, "bound70")
            # The S^1 graph proven divergent is excluded from later bound70.
            self.assertEqual(set(selection), {104, 105})
            surviving, _, _ = staged.active(10)
            self.assertNotIn(101, surviving)
            self.assertIn(104, surviving)

    def test_completed_stage_survives_upgrade_and_new_stage_pins_its_revision(self):
        """Do not relabel or recompute original/c10 records after upgrading."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            old_pin, new_pin = "a" * 40, "b" * 40
            g6 = nx.to_graph6_bytes(nx.cycle_graph(10), header=False).decode().strip()
            initial = root / "runs" / "order10" / "initial"
            (initial / "order10").mkdir(parents=True)
            initial_manifest = {
                "min_order": 10,
                "max_order": 10,
                "upstream_commit": old_pin,
            }
            (initial / "manifest.json").write_text(
                json.dumps(initial_manifest), encoding="utf-8"
            )
            initial_summary = {
                "manifest": initial_manifest,
                "orders": [{"order": 10, "connected_total": 11716571, "indeterminate": 1}],
                "unresolved": [{
                    "order": 10, "index": 17, "graph6": g6,
                    "reason": "clique count exceeded bound",
                }],
            }
            original_summary = json.dumps(initial_summary)
            (initial / "summary.json").write_text(
                original_summary, encoding="utf-8"
            )
            (initial / "order10" / "indeterminate_order_10.txt").write_text(
                f"17 10 {g6} - - -\n", encoding="utf-8"
            )
            registry = root / "config" / "conjectured_surfaces_order9.tsv"
            registry.parent.mkdir(parents=True)
            registry.write_text("# fixtures\n", encoding="utf-8")

            previous = root / "runs" / "order10" / "c10"
            (previous / "records").mkdir(parents=True)
            previous_manifest = {
                "schema": 1, "stage": "c10", "order": 10,
                "upstream_commit": old_pin, "indices": [17],
            }
            previous_manifest_text = json.dumps(previous_manifest)
            previous_summary_text = json.dumps({
                "manifest": previous_manifest,
                "processed": 1,
                "counts": {"NO_RETRACTION": 1},
            })
            (previous / "manifest.json").write_text(
                previous_manifest_text, encoding="utf-8"
            )
            (previous / "summary.json").write_text(
                previous_summary_text, encoding="utf-8"
            )
            (previous / "records" / "00000017.json").write_text(
                json.dumps({
                    "index": 17, "graph6": g6,
                    "status": "NO_RETRACTION", "witness": None,
                }), encoding="utf-8"
            )
            def exact_homotopy(_order, _stage, _graph):
                return {
                    "is_exact": True,
                    "is_limited": False,
                    "spheres": {},
                    "verdict": "Contractible",
                    "reason": "test fixture",
                }
            with (
                patch.object(staged, "ROOT", root),
                patch.object(staged, "current_pin", return_value=new_pin),
                patch.object(staged, "load_surface_references", return_value=0),
                patch.object(staged, "compute", side_effect=exact_homotopy) as compute,
            ):
                # Reading historical data does not require the new package
                # revision to match the revision used by the initial census.
                run, source, origins = staged.census(10)
                self.assertEqual(run, initial)
                self.assertEqual(set(source), {17})
                self.assertEqual(origins[17].split()[4], "-")

                staged.run_stage(10, "homotopy")
                self.assertEqual(compute.call_count, 1)
                new_manifest = json.loads(
                    (root / "runs" / "order10" / "homotopy" / "manifest.json").read_text()
                )
                self.assertEqual(new_manifest["upstream_commit"], new_pin)
                self.assertEqual(new_manifest["c10_summary_sha256"], staged.filehash(
                    previous / "summary.json"
                ))
                staged.run_stage(10, "homotopy")
                self.assertEqual(compute.call_count, 1)  # resumed without work
                self.assertEqual((initial / "summary.json").read_text(), original_summary)
                self.assertEqual((previous / "manifest.json").read_text(), previous_manifest_text)
                self.assertEqual((previous / "summary.json").read_text(), previous_summary_text)
                with patch.object(staged, "current_pin", return_value=old_pin):
                    with self.assertRaisesRegex(ValueError, "changed inputs"):
                        staged.run_stage(10, "homotopy")

    def test_initial_summary_must_match_original_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "runs" / "order10" / "initial"
            folder.mkdir(parents=True)
            manifest = {"min_order": 10, "max_order": 10, "upstream_commit": "a" * 40}
            (folder / "manifest.json").write_text(json.dumps(manifest))
            (folder / "summary.json").write_text(json.dumps({
                "manifest": {**manifest, "upstream_commit": "b" * 40},
                "orders": [{"connected_total": 11716571, "indeterminate": 0}],
                "unresolved": [],
            }))
            with patch.object(staged, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "not complete or not validated"):
                    staged.census(10)

    def test_initial_batch_sizes_are_order_specific(self):
        """The entry point must keep order 9 at 10000 and order 10 at 100000."""
        script = (ROOT / "scripts" / "stage.sh").read_text(encoding="utf-8")
        self.assertIn('  BATCH=10000', script)
        self.assertIn('if [[ "$ORDER" == 10 ]]; then BATCH=100000; fi', script)
        self.assertNotIn('BATCH=5000', script)

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
