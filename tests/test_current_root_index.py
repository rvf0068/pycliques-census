"""Invariant tests for the authoritative order-10 unresolved working index.

The frozen pre-v3 baseline is preserved for reproducibility. Post-v3
certificate lifts remove only independently proven divergent graphs.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import unittest

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "indeterminate_order_10.txt"
V6 = ROOT / "indeterminate_order_10_v6.txt"
V7 = ROOT / "indeterminate_order_10_v7.txt"
V8 = ROOT / "indeterminate_order_10_v8.txt"
V9 = ROOT / "indeterminate_order_10_v9.txt"
V10 = ROOT / "indeterminate_order_10_v10.txt"
V11 = ROOT / "indeterminate_order_10_v11.txt"
V12 = ROOT / "indeterminate_order_10_v12.txt"
HISTORICAL = ROOT / "historical/indeterminate_order_10_pre_v3.txt"


def rows(path: Path) -> list[str]:
    return [line for line in path.read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#")]


class CurrentOrder10IndexTests(unittest.TestCase):
    def test_current_root_matches_latest_certified_version(self):
        self.assertEqual(CURRENT.read_bytes(), V12.read_bytes())

    def test_historical_baseline_preserved_and_only_proofs_excluded(self):
        historical_bytes = HISTORICAL.read_bytes()
        blob_hash = hashlib.sha1(
            b"blob " + str(len(historical_bytes)).encode("ascii")
            + b"\0" + historical_bytes
        ).hexdigest()
        self.assertEqual(blob_hash, "05f52c6db0b5642d2b6a856cef53c8fe07309c52")
        old, new = rows(HISTORICAL), rows(CURRENT)
        self.assertEqual((len(old), len(new)), (8648, 2788))
        self.assertEqual(len(old), len(set(old)))
        self.assertEqual(len(new), len(set(new)))
        self.assertEqual(len(set(old) - set(new)), 5860)
        self.assertEqual(len(rows(V6)) - len(rows(V7)), 99)
        self.assertEqual(len(rows(V7)) - len(rows(V8)), 192)
        self.assertEqual(len(rows(V8)) - len(rows(V9)), 12)
        self.assertEqual(len(rows(V9)) - len(rows(V10)), 701)
        self.assertEqual(len(rows(V10)) - len(rows(V11)), 4389)
        self.assertEqual(len(rows(V11)) - len(new), 42)
        self.assertTrue(set(new).issubset(set(rows(V11))))
        self.assertTrue(set(new).issubset(set(rows(V10))))
        self.assertEqual(set(new) - set(old), set())
        self.assertEqual(
            sum(line.split()[4] == "conjectured_divergent" for line in old),
            4608,
        )
        self.assertEqual(
            sum(line.split()[4] == "conjectured_divergent" for line in new),
            120,
        )


if __name__ == "__main__":
    unittest.main()
