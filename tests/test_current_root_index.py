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
V13 = ROOT / "indeterminate_order_10_v13.txt"
V14 = ROOT / "indeterminate_order_10_v14.txt"
V15 = ROOT / "indeterminate_order_10_v15.txt"
V16 = ROOT / "indeterminate_order_10_v16.txt"
V17 = ROOT / "indeterminate_order_10_v17.txt"
V18 = ROOT / "indeterminate_order_10_v18.txt"
V19 = ROOT / "indeterminate_order_10_v19.txt"
V20 = ROOT / "indeterminate_order_10_v20.txt"
V21 = ROOT / "indeterminate_order_10_v21.txt"
V22 = ROOT / "indeterminate_order_10_v22.txt"
V23 = ROOT / "indeterminate_order_10_v23.txt"
V24 = ROOT / "indeterminate_order_10_v24.txt"
V25 = ROOT / "indeterminate_order_10_v25.txt"
V26 = ROOT / "indeterminate_order_10_v26.txt"
CURRENT9 = ROOT / "indeterminate_order_9.txt"
V4_9 = ROOT / "indeterminate_order_9_v4.txt"
V5_9 = ROOT / "indeterminate_order_9_v5.txt"
V6_9 = ROOT / "indeterminate_order_9_v6.txt"
V7_9 = ROOT / "indeterminate_order_9_v7.txt"
V8_9 = ROOT / "indeterminate_order_9_v8.txt"
V9_9 = ROOT / "indeterminate_order_9_v9.txt"
HISTORICAL = ROOT / "historical/indeterminate_order_10_pre_v3.txt"


def rows(path: Path) -> list[str]:
    return [line for line in path.read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#")]


class CurrentOrder10IndexTests(unittest.TestCase):
    def test_current_root_matches_latest_certified_version(self):
        self.assertEqual(CURRENT.read_bytes(), V26.read_bytes())

    def test_historical_baseline_preserved_and_only_proofs_excluded(self):
        historical_bytes = HISTORICAL.read_bytes()
        blob_hash = hashlib.sha1(
            b"blob " + str(len(historical_bytes)).encode("ascii")
            + b"\0" + historical_bytes
        ).hexdigest()
        self.assertEqual(blob_hash, "05f52c6db0b5642d2b6a856cef53c8fe07309c52")
        old, new = rows(HISTORICAL), rows(V25)
        # Historical stage checks are pinned to the immutable v25 snapshot;
        # only the separately certified six-positive transition changes
        # the active v26 root.
        latest = rows(CURRENT)
        self.assertEqual((len(new), len(latest)), (1052, 1046))
        self.assertTrue(set(latest).issubset(set(new)))
        self.assertEqual(
            {int(line.split()[0]) for line in new} -
            {int(line.split()[0]) for line in latest},
            {11367777, 11611429, 11623375, 11651749,
             11708546, 11713770},
        )
        self.assertEqual((len(old), len(new)), (8648, 1052))
        self.assertEqual(len(rows(V19)), 1531)
        self.assertEqual(len(rows(V19)) - len(new), 479)
        self.assertEqual(len(rows(V20)), 1311)
        self.assertEqual(len(rows(V20)) - len(new), 259)
        self.assertEqual(len(rows(V21)), 1228)
        self.assertEqual(len(rows(V21)) - len(new), 176)
        self.assertTrue(set(new).issubset(set(rows(V21))))
        self.assertEqual(len(rows(V22)) - len(new), 156)
        self.assertTrue(set(new).issubset(set(rows(V22))))
        self.assertEqual(len(rows(V23)) - len(new), 7)
        self.assertTrue(set(new).issubset(set(rows(V23))))
        self.assertEqual(
            {int(line.split()[0]) for line in rows(V23)} -
            {int(line.split()[0]) for line in rows(V24)},
            {11495390, 11533866, 11556387},
        )
        self.assertEqual(len(rows(V24)) - len(new), 4)
        self.assertEqual(
            {int(line.split()[0]) for line in rows(V24)} -
            {int(line.split()[0]) for line in new},
            {11551790, 11552072, 11555600, 11707526},
        )
        self.assertEqual(
            {int(line.split()[0]) for line in rows(V23)} -
            {int(line.split()[0]) for line in new},
            {11495390, 11533866, 11556387,
             11551790, 11552072, 11555600, 11707526},
        )
        self.assertTrue(set(new).issubset(set(rows(V20))))
        self.assertTrue(set(new).issubset(set(rows(V19))))
        self.assertEqual(len(rows(V18)), 1681)
        self.assertEqual(len(rows(V18)) - len(rows(V19)), 150)
        self.assertTrue(set(new).issubset(set(rows(V18))))
        self.assertEqual(len(rows(V17)), 2025)
        self.assertEqual(len(rows(V17)) - len(rows(V18)), 344)
        self.assertTrue(set(new).issubset(set(rows(V17))))
        self.assertEqual(len(old), len(set(old)))
        self.assertEqual(len(new), len(set(new)))
        self.assertEqual(len(set(old) - set(new)), 7596)
        self.assertEqual(len(rows(V6)) - len(rows(V7)), 99)
        self.assertEqual(len(rows(V7)) - len(rows(V8)), 192)
        self.assertEqual(len(rows(V8)) - len(rows(V9)), 12)
        self.assertEqual(len(rows(V9)) - len(rows(V10)), 701)
        self.assertEqual(len(rows(V10)) - len(rows(V11)), 4389)
        self.assertEqual(len(rows(V11)) - len(new), 1778)
        self.assertEqual(len(rows(V12)) - len(new), 1736)
        self.assertEqual(len(rows(V13)) - len(new), 1735)
        self.assertEqual(len(rows(V14)) - len(new), 1516)
        self.assertEqual(len(rows(V15)) - len(new), 1489)
        self.assertEqual(len(rows(V16)) - len(new), 1289)
        self.assertTrue(set(new).issubset(set(rows(V11))))
        self.assertTrue(set(new).issubset(set(rows(V10))))
        self.assertEqual(set(new) - set(old), set())
        self.assertEqual(
            sum(line.split()[4] == "conjectured_divergent" for line in old),
            4608,
        )
        self.assertEqual(
            sum(line.split()[4] == "conjectured_divergent" for line in new),
            0,
        )

    def test_historical_order_nine_v6_v7_v8_and_current_v9(self):
        self.assertEqual(CURRENT9.read_bytes(), V9_9.read_bytes())
        old = rows(V4_9)
        new = rows(V6_9)
        self.assertEqual((len(old), len(new)), (12, 9))
        old_ids = {int(row.split()[0]) for row in old}
        new_ids = {int(row.split()[0]) for row in new}
        self.assertEqual(old_ids - new_ids, {208409, 260910, 253650})
        self.assertTrue(set(new).issubset(set(old)))
        self.assertEqual(len(rows(V5_9)) - len(new), 1)
        current = rows(V7_9)
        self.assertEqual(len(current), 6)
        latest = rows(V8_9)
        self.assertEqual(len(latest), 5)
        self.assertTrue(set(latest).issubset(set(current)))
        current_v9 = rows(V9_9)
        self.assertEqual(len(current_v9), 3)
        self.assertTrue(set(current_v9).issubset(set(latest)))
        self.assertEqual(
            {int(line.split()[0]) for line in latest} -
            {int(line.split()[0]) for line in current_v9},
            {251759, 254369},
        )
        self.assertEqual(
            {int(line.split()[0]) for line in current} -
            {int(line.split()[0]) for line in latest}, {251902},
        )
        self.assertTrue(set(current).issubset(set(new)))
        self.assertEqual(
            {int(line.split()[0]) for line in new} -
            {int(line.split()[0]) for line in current},
            {249436, 249574, 250814},
        )
        self.assertEqual(
            {int(line.split()[0]) for line in rows(V5_9)} - new_ids,
            {253650},
        )


if __name__ == "__main__":
    unittest.main()
