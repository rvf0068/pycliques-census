"""Tests for the readable, resumable order-10 homotopy TSV export."""

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import export_homotopy  # noqa: E402
import staged  # noqa: E402


class HomotopyExportTests(unittest.TestCase):
    def test_no_export_before_stage(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.object(staged, "ROOT", Path(td)):
                self.assertIsNone(export_homotopy.export_homotopy())
                self.assertFalse((Path(td) / "homotopy_order_10.tsv").exists())

    def test_partial_and_complete_export_preserves_original_indices_and_types(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            folder = root / "runs" / "order10" / "homotopy"
            folder.mkdir(parents=True)
            source = {
                3: {"graph6": "IABCDEFGH"},
                8: {"graph6": "IJKLMNOPQ"},
                12: {"graph6": "IRSTUVWXZ"},
            }
            origins = {
                3: "3 10 IABCDEFGH - - -",
                8: "8 10 IJKLMNOPQ - - -",
                12: "12 10 IRSTUVWXZ - - -",
            }
            # Index 12 belongs to the nonconjectural unresolved initial
            # cohort but is not in the current homotopy selection.
            selection = {index: source[index] for index in (3, 8)}
            record3 = {
                "index": 3, "graph6": source[3]["graph6"],
                "is_exact": True, "is_limited": False,
                "verdict": "exact", "spheres": {"1": 2},
                "reason": "two circles\nverified by theorem",
            }
            record8 = {
                "index": 8, "graph6": source[8]["graph6"],
                "is_exact": False, "is_limited": True,
                "verdict": "Betti numbers only", "spheres": None,
                "reason": "limited\tresources",
            }
            complete = {3: record3, 8: record8}
            active = {3: record3}

            with (
                patch.object(staged, "ROOT", root),
                patch.object(staged, "stage_selection", return_value=(selection, source)),
                patch.object(staged, "checked_records", side_effect=lambda *_: active),
                patch.object(staged, "census", return_value=(Path("."), source, origins)),
            ):
                self.assertEqual(export_homotopy.export_homotopy(), 1)
                path = root / "homotopy_order_10.tsv"
                with path.open(newline="", encoding="utf-8") as stream:
                    rows = list(csv.DictReader(stream, delimiter="\t"))
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["original_index"], "3")
                self.assertEqual(rows[0]["original_graph6"], source[3]["graph6"])
                self.assertEqual(rows[0]["homotopy_type"], "wedge of 2 copies of S^1")
                self.assertEqual(rows[0]["spheres"], '{"1":2}')
                self.assertEqual(rows[0]["reason"], record3["reason"])

                active = complete
                self.assertEqual(export_homotopy.export_homotopy(), 2)
                with path.open(newline="", encoding="utf-8") as stream:
                    rows = list(csv.DictReader(stream, delimiter="\t"))
                self.assertEqual([row["original_index"] for row in rows], ["3", "8"])
                self.assertEqual(rows[1]["homotopy_type"], "not certified")
                self.assertEqual(rows[1]["is_limited"], "true")
                self.assertEqual(rows[1]["reason"], "limited\tresources")
                self.assertFalse((root / "homotopy_order_10.tsv.partial").exists())

                active = {**complete, 12: {
                    **record3, "index": 12, "graph6": source[12]["graph6"],
                }}
                with self.assertRaisesRegex(ValueError, "outside the selected cohort"):
                    export_homotopy.export_homotopy()
                with path.open(newline="", encoding="utf-8") as stream:
                    self.assertEqual(len(list(csv.DictReader(stream, delimiter="\t"))), 2)

    def test_contractible_and_higher_dimensional_wedges(self):
        self.assertEqual(export_homotopy.describe_homotopy({
            "is_exact": True, "is_limited": False, "spheres": {},
        }), "contractible")
        self.assertEqual(export_homotopy.describe_homotopy({
            "is_exact": True, "is_limited": False, "spheres": {"2": 1, "1": 3},
        }), "wedge of 3 copies of S^1, 1 copy of S^2")
        self.assertEqual(export_homotopy.describe_homotopy({
            "is_exact": False, "is_limited": False, "spheres": {},
        }), "not certified")


if __name__ == "__main__":
    unittest.main()
