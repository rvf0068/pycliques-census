"""Invariant tests for the authoritative order-10 unresolved working index.

The frozen pre-v3 baseline is preserved for reproducibility. Post-v3
certificate lifts remove only independently proven divergent graphs.
"""
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "indeterminate_order_10.txt"
V6 = ROOT / "indeterminate_order_10_v6.txt"
HISTORICAL = ROOT / "historical/indeterminate_order_10_pre_v3.txt"


def rows(path: Path) -> list[str]:
    return [line for line in path.read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#")]


class CurrentOrder10IndexTests(unittest.TestCase):
    def test_current_root_matches_latest_certified_version(self):
        self.assertEqual(CURRENT.read_bytes(), V6.read_bytes())

    def test_historical_baseline_preserved_and_only_proofs_excluded(self):
        old, new = rows(HISTORICAL), rows(CURRENT)
        self.assertEqual((len(old), len(new)), (8648, 8223))
        self.assertEqual(len(old), len(set(old)))
        self.assertEqual(len(new), len(set(new)))
        self.assertEqual(len(set(old) - set(new)), 425)
        self.assertEqual(set(new) - set(old), set())
        self.assertEqual(
            sum(line.split()[4] == "conjectured_divergent" for line in old),
            4608,
        )
        self.assertEqual(
            sum(line.split()[4] == "conjectured_divergent" for line in new),
            4608,
        )


if __name__ == "__main__":
    unittest.main()
