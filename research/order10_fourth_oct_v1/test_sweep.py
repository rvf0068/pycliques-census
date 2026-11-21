"""Basic coverage and regression checks for positive-only fourth screening."""
import importlib.util
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from research.order10_fourth_oct_v1 import sweep


class FourthScreenTests(unittest.TestCase):
    def test_pinned_source_selection(self):
        rows = sweep.entries()
        self.assertEqual(len(rows), 1043)
        self.assertEqual(len({i for i, _ in rows}), 1043)
        self.assertEqual(rows, sorted(rows))

    def test_bounded_fixture_has_fourth_iterate(self):
        index, g6 = next(r for r in sweep.entries() if r[0] == 11708411)
        result = sweep.inspect(
            index, g6, bound=1500, max_k3_order=40,
            dims=(3, 4), restarts=12, states=200
        )
        self.assertEqual(result["index"], index)
        self.assertEqual(result["source_graph6"], g6)
        self.assertEqual(result["k3_order"], 15)
        self.assertEqual(result["k4_order"], 30)
        self.assertIn(result["status"], ("INCONCLUSIVE", "CERTIFIED_DIVERGENT"))

    def test_order_guard_excludes_fixture(self):
        index, g6 = next(r for r in sweep.entries() if r[0] == 7002338)
        result = sweep.inspect(
            index, g6, bound=1500, max_k3_order=25,
            dims=(3,), restarts=1, states=1
        )
        self.assertEqual(result["reason"], "K3_ORDER_EXCLUDED")
        self.assertNotIn("certificate", result)


if __name__ == "__main__":
    unittest.main()
