"""Regression tests for the immutable historical order-nine cross-reference."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
import sys
import tempfile
import unittest

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import core9_crossref as cross


class Core9CrossrefTests(unittest.TestCase):
    def test_graph6_vertex_order_is_not_used_as_canonical_name(self):
        cycle = nx.cycle_graph(9)
        moved = nx.relabel_nodes(cycle, {
            0: 4, 1: 3, 2: 5, 3: 0, 4: 8, 5: 6, 6: 1, 7: 2, 8: 7,
        })
        prism = nx.circular_ladder_graph(5)
        cores = {
            15: {"graph": cycle},
            28: {"graph": prism},
        }
        matched = cross.match_source(
            cores, iter((nx.path_graph(9), moved, prism)), expected_count=3
        )
        self.assertEqual(matched[15]["order9_index"], 1)
        self.assertEqual(matched[28]["order9_index"], 2)
        self.assertTrue(nx.is_isomorphic(
            nx.from_graph6_bytes(matched[15]["order9_graph6"].encode()), cycle
        ))
        self.assertRaisesRegex(
            ValueError, "multiple source entries",
            cross.match_source, {15: {"graph": cycle}},
            iter((cycle, moved)), expected_count=2,
        )
        self.assertRaisesRegex(
            ValueError, "source count changed",
            cross.match_source, {15: {"graph": cycle}},
            iter((cycle,)), expected_count=2,
        )
        self.assertRaisesRegex(
            ValueError, "Unmatched",
            cross.match_source, {15: {"graph": cycle}, 16: {"graph": prism}},
            iter((cycle,)), expected_count=1,
        )

    def test_history_rejects_inconsistent_positive_and_working_list(self):
        initial = {
            "verdict": "INDETERMINATE", "stage": "initial",
            "reason": "clique count exceeded bound",
            "rule": "clique count exceeded bound", "record_path": "initial",
        }
        r = {
            "bound60": {
                "verdict": "DIVERGENT",
                "reason": "eventually has a special octahedron",
                "certificate_rule": "-",
                "_record_path": "bound60 record",
            },
            "bound70": None,
        }
        result = cross.historical_verdict(initial, r, False)
        self.assertEqual(result["verdict"], "DIVERGENT")
        self.assertEqual(result["first_positive_stage"], "bound60")
        with self.assertRaisesRegex(ValueError, "final order-nine list"):
            cross.historical_verdict(initial, r, True)
        with self.assertRaisesRegex(ValueError, "Contradictory"):
            cross.historical_verdict(initial, {
                **r, "bound70": {
                    "verdict": "CONVERGENT", "reason": "eventually Helly",
                    "certificate_rule": "-",
                    "_record_path": "bound70 record",
                }
            }, False)

    def test_all_four_new_core_certificates_rediscover_old_positive_verdicts(self):
        _, _, original_unresolved = cross.initial_data()
        bound60, _ = cross.load_stage_records(
            "bound60", original_unresolved
        )
        bound70, _ = cross.load_stage_records(
            "bound70", original_unresolved
        )
        expected = {
            250684: ("bound70", 4),
            253557: ("bound70", 4),
            255039: ("bound70", 7),
            259791: ("bound60", 4),
        }
        still = cross.final_unresolved()
        for idx, (stage, dimension) in expected.items():
            with self.subTest(order9_index=idx):
                self.assertNotIn(idx, still)
                record = (bound70 if stage == "bound70" else bound60)[idx]
                self.assertEqual(record["verdict"], "DIVERGENT")
                self.assertEqual(record["bound"], int(stage.removeprefix("bound")))
                self.assertIn("special octahedron", record["reason"])
                self.assertIn(f"dimension {dimension}", record["reason"])

    def test_real_frozen_core_index_and_connected_data_hash(self):
        cores = cross.frozen_cores()
        self.assertEqual(len(cores), 35)
        self.assertEqual(sum(r["members"] for r in cores.values()), 4038)
        initial, _, _ = cross.initial_data()
        actual = cross.validate_dataset(initial)
        self.assertEqual(
            actual, initial["bundled_connected_graph6_sha256"]["9"]
        )
        # These two 9-cores never entered the initial 9-vertex
        # unresolved cohort: they were already classified at bound 30.
        _, _, old_unresolved = cross.initial_data()
        unresolved_graphs = [
            nx.from_graph6_bytes(record["graph6"].encode("ascii"))
            for record in old_unresolved.values()
        ]
        initially_classified = {
            core_id for core_id, core in cores.items()
            if not any(nx.is_isomorphic(core["graph"], old)
                       for old in unresolved_graphs)
        }
        self.assertEqual(initially_classified, {10768817, 11363569})

    def test_historical_chain_and_final_rows_detect_tampering(self):
        _, _, originals = cross.initial_data()
        stages = {
            name: cross.load_stage_records(name, originals)[0]
            for name in cross.STAGES
        }
        expected = cross.validate_complete_history(originals, stages)
        self.assertEqual(expected, cross.final_unresolved())

        with self.assertRaisesRegex(ValueError, "Bound-60 cohort"):
            changed = {k: dict(v) for k, v in stages.items()}
            changed["bound60"].pop(next(iter(changed["bound60"])))
            cross.validate_complete_history(originals, changed)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            origin = root / "runs/order9/initial/order9/indeterminate_order_9.txt"
            origin.parent.mkdir(parents=True)
            shutil.copyfile(
                cross.ROOT / "runs/order9/initial/order9/indeterminate_order_9.txt",
                origin,
            )
            final = root / "indeterminate_order_9.txt"
            shutil.copyfile(cross.FINAL9, final)
            self.assertEqual(
                cross.validate_complete_history(originals, stages, root),
                expected,
            )

            lines = final.read_text().splitlines()
            k = next(i for i, line in enumerate(lines)
                     if line and not line.startswith("#"))
            saved = lines[k]
            fields = saved.split()
            fields[2] = "HEnb~jl" if fields[2] != "HEnb~jl" else "HEht}pl"
            lines[k] = " ".join(fields)
            final.write_text("\n".join(lines) + "\n")
            with self.assertRaisesRegex(ValueError, "source/paring fields"):
                cross.validate_complete_history(originals, stages, root)

            # Keep the same row count, substitute an already-resolved index.
            lines[k] = saved
            fields = lines[k].split()
            fields[0] = "250684"
            lines[k] = " ".join(fields)
            final.write_text("\n".join(lines) + "\n")
            with self.assertRaisesRegex(ValueError, "unresolved set"):
                cross.validate_complete_history(originals, stages, root)

    def test_stage_predecessor_and_status_counts_cannot_be_forged(self):
        _, _, originals = cross.initial_data()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for path in (
                "runs/order9/initial/summary.json",
                "runs/order9/c10/summary.json",
                "runs/order9/bound60/summary.json",
                "runs/order9/bound60/manifest.json",
            ):
                dest = root / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(cross.ROOT / path, dest)
            records = root / "runs/order9/bound60/records"
            records.mkdir(parents=True)
            for source in sorted(
                (cross.ROOT / "runs/order9/bound60/records").glob("*.json")
            ):
                shutil.copyfile(source, records / source.name)
            loaded, _ = cross.load_stage_records("bound60", originals, root)
            self.assertEqual(len(loaded), 23)

            record_path = next(iter(records.glob("*.json")))
            original_bytes = record_path.read_bytes()
            changed = json.loads(original_bytes)
            changed["verdict"] = (
                "DIVERGENT" if changed["verdict"] == "INDETERMINATE"
                else "INDETERMINATE"
            )
            record_path.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, "status counts"):
                cross.load_stage_records("bound60", originals, root)
            record_path.write_bytes(original_bytes)

            predecessor = root / "runs/order9/c10/summary.json"
            predecessor.write_bytes(predecessor.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "predecessor provenance"):
                cross.load_stage_records("bound60", originals, root)

    def test_build_is_immutable_and_missing_file_rejected(self):
        expected = {
            "matches.tsv": b"header\n",
            "unclassified.tsv": b"header\n",
            "summary.md": b"# Report\n",
            "manifest.json": b"{}\n",
        }
        with tempfile.TemporaryDirectory() as t:
            folder = Path(t) / "index"
            cross.build(folder, expected)
            cross.verify_saved(folder, expected)
            cross.build(folder, expected)
            (folder / "matches.tsv").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "output changed"):
                cross.verify_saved(folder, expected)
            with self.assertRaisesRegex(ValueError, "output changed"):
                cross.build(folder, expected)
            self.assertEqual((folder / "matches.tsv").read_bytes(), b"tampered")


if __name__ == "__main__":
    unittest.main()
