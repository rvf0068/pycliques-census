"""Cheap tests for the safe, deterministic nonlocal octahedron sweep driver."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "research/order9_nonlocal_oct_sweep_v1/sweep.py"
spec = importlib.util.spec_from_file_location("nonlocal_sweep", SCRIPT)
assert spec and spec.loader
sweep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sweep)


class NonlocalSweepTests(unittest.TestCase):
    def test_thirteen_original_indices_and_graph6(self):
        rows = sweep.entries()
        self.assertEqual(len(rows), 13)
        self.assertEqual(rows[0][0], 208409)
        self.assertEqual(rows[-1][0], 260910)

    def test_plan_does_not_require_pycliques_or_change_index(self):
        original = sweep.SOURCE.read_bytes()
        p = subprocess.run([sys.executable, str(SCRIPT), "plan"],
                           text=True, capture_output=True, check=True)
        self.assertIn('"count": 13', p.stdout)
        self.assertEqual(sweep.SOURCE.read_bytes(), original)

    def _verify_report(self, records):
        payload = {"schema": 1, "source": sweep.SOURCE.name,
                   "settings": {"bound": 1600}, "records": records}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "results.json"
            output.write_text(json.dumps(payload))
            return subprocess.run(
                [sys.executable, str(SCRIPT), "verify",
                 "--input-results", str(output)],
                text=True, capture_output=True,
            )

    def test_replay_requires_all_13_and_unique_mckay_indices(self):
        records = [
            {"index": idx, "source_graph6": graph6, "status": "INCONCLUSIVE"}
            for idx, graph6 in sweep.entries()
        ]
        complete = self._verify_report(records)
        self.assertEqual(complete.returncode, 0, complete.stderr)
        self.assertIn("Verified 13 records", complete.stdout)
        for tampered in ([], records[:-1], records[:-1] + [records[0]]):
            result = self._verify_report(tampered)
            self.assertNotEqual(result.returncode, 0)
            self.assertRegex(result.stderr, "Incomplete or duplicated")

    def test_replay_rejects_wrong_source_or_unknown_result_status(self):
        records = [
            {"index": idx, "source_graph6": graph6, "status": "TIMEOUT"}
            for idx, graph6 in sweep.entries()
        ]
        bad_source = [*records]
        bad_source[0] = {**records[0], "source_graph6": "GQyuzw"}
        result = self._verify_report(bad_source)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Incorrect indexed source", result.stderr)
        bad_status = [*records]
        bad_status[0] = {**records[0], "status": "CLAIMED_EXHAUSTED"}
        result = self._verify_report(bad_status)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown sweep result status", result.stderr)


if __name__ == "__main__":
    unittest.main()
