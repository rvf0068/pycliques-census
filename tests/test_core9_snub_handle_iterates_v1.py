"""Regression tests for exact finite snub-handle homotopy certificates."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import core9_snub_handle_iterates_v1 as study  # noqa: E402


class SnubHandleIteratesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = study.prepare()
        cls.cert = json.loads(cls.data[f"{study.DEST}/certificates.json"])

    def test_six_exact_finite_records_and_original_members(self):
        self.assertEqual(
            [r["core_id"] for r in self.cert["records"]], list(study.EXPECTED_IDS)
        )
        self.assertEqual(
            [r["original_order10_members"] for r in self.cert["records"]],
            list(study.EXPECTED_MEMBERS)
        )
        self.assertEqual(self.cert["original_ten_graphs_represented"], 710)
        self.assertTrue(self.cert["no_all_iterate_theorem"])
        self.assertTrue(self.cert["no_new_K_divergence_verdicts"])

    def test_all_level_maps_and_contractible_link_witnesses(self):
        for rec in self.cert["records"]:
            self.assertEqual(
                [(level["snub_order"], level["core_order"]) for level in rec["levels"]],
                list(study.EXPECTED_SIZE_PAIRS),
            )
            for n, level in enumerate(rec["levels"]):
                phi = level["snub_to_core_vertex_map"]
                self.assertEqual(len(phi), level["snub_order"])
                self.assertEqual(len(set(phi)), len(phi))
                self.assertEqual(
                    len(level["extra_core_vertices"]),
                    1 if n % 2 == 0 else 2,
                )
                link = level["link_certificate"]
                if n % 2 == 0:
                    self.assertEqual(link["kind"], "two_clique_cone_bridge")
                    self.assertEqual(len(link["components"]), 2)
                    self.assertTrue(all(link["components"]))
                else:
                    self.assertEqual(
                        link["kind"], "adjacent_pair_disjoint_cone_links"
                    )
                    p, q = link["supports"]
                    self.assertTrue(p and q and not set(p) & set(q))
                    for u, side in zip(link["cone_apices"], link["supports"]):
                        self.assertIn(u, side)

    def test_raw_iterate_edge_counts_are_exact(self):
        expected_snub = [(8, 18), (12, 46), (20, 136), (56, 1196)]
        for rec in self.cert["records"]:
            self.assertEqual(
                [(x["snub_order"], x["snub_edges"]) for x in rec["levels"][:4]],
                expected_snub,
            )
            self.assertEqual(rec["levels"][4]["core_edges"] -
                             rec["levels"][4]["snub_edges"],
                             sum(map(len, rec["levels"][4]["link_certificate"]["components"])))

    def test_corrupted_historical_source_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for rel in (study.SOURCE, study.SOURCE_MANIFEST, study.CLASS_INDEX):
                destination = root / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / rel, destination)
            payload = (root / study.SOURCE).read_text(encoding="utf-8")
            (root / study.SOURCE).write_text(
                payload.replace('GQyuzw', 'GQyuzx', 1), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "Frozen original"):
                study.frozen_rows(root)

    def test_committed_bytes_match_reconstructed_proof(self):
        study.verify()


if __name__ == "__main__":
    unittest.main()
