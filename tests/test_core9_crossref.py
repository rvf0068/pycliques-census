"""Regression tests for the immutable historical order-nine cross-reference."""
from __future__ import annotations

import json
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
