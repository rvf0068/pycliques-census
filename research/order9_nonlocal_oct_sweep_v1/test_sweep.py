"""Cheap tests for the safe, deterministic nonlocal octahedron sweep driver."""
from __future__ import annotations

import importlib.util
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


if __name__ == "__main__":
    unittest.main()
