"""Adversarial tests for strictly six-record ten-v28-to-v29 promotion."""
from __future__ import annotations

import unittest

from research.order10_p4_crossdepth_o15_v25.verify import source_rows
from research.order10_v29_six_coaffine_joins.verify import (
    BEFORE, LATEST, WORKING, NINE, NINE_FROZEN,
    EXPECTED_REMOVALS, EXPECTED_GRAPH6, P1_REMOVALS, P3_REMOVALS,
    audit_nine, audit_rows, verify,
)


class SixCoaffinePositiveTenV29Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = source_rows(BEFORE)
        cls.after = source_rows(LATEST)
        cls.proved = set(EXPECTED_REMOVALS)

    def test_complete_positive_proofs_and_exact_six_original_promotion(self):
        result = verify()
        self.assertEqual(result["proved_K_divergent_originals"],
                         list(EXPECTED_REMOVALS))
        self.assertEqual(result["population"], {
            "before": 1043, "after": 1037, "removed": 6,
            "nine_pared_originals_unchanged": 430,
            "stiff_ten_before": 613, "stiff_ten_after": 607,
        })
        self.assertEqual(set(P1_REMOVALS) | set(P3_REMOVALS), self.proved)
        self.assertTrue(result["retained_rows_verbatim"])

    def test_exact_six_removed_and_all_other_original_rows_unchanged(self):
        audit_rows(self.before, self.after, self.proved)

    def test_one_retained_six_column_record_mutated(self):
        corrupted = dict(self.after)
        i = next(iter(corrupted))
        corrupted[i] = corrupted[i].replace(" - - -", " - - altered")
        with self.assertRaisesRegex(AssertionError, "retained"):
            audit_rows(self.before, corrupted, self.proved)

    def test_wrong_original_instead_of_certified_one(self):
        corrupted = dict(self.after)
        corrupted.pop(next(iter(corrupted)))
        i = EXPECTED_REMOVALS[0]
        corrupted[i] = self.before[i]
        corrupted = dict(sorted(corrupted.items()))
        with self.assertRaisesRegex(AssertionError, "uncertified"):
            audit_rows(self.before, corrupted, self.proved)

    def test_seventh_uncertified_deletion(self):
        corrupted = dict(self.after)
        corrupted.pop(next(iter(corrupted)))
        with self.assertRaisesRegex(AssertionError, "counts"):
            audit_rows(self.before, corrupted, self.proved)

    def test_forged_set_of_proved_originals(self):
        with self.assertRaisesRegex(AssertionError, "six"):
            audit_rows(self.before, self.after, {11715667, 11716441})

    def test_original_graph6_and_pared_order_pinned_for_each_case(self):
        for i,g6 in EXPECTED_GRAPH6.items():
            self.assertEqual(self.before[i], f"{i} 10 {g6} - - -")
        corrupted = dict(self.before)
        i = EXPECTED_REMOVALS[0]
        corrupted[i] = corrupted[i].replace(" 10 ", " 9 ", 1)
        with self.assertRaisesRegex(AssertionError, "graph6"):
            audit_rows(corrupted, self.after, self.proved)

    def test_nine_vertex_originals_still_identical_to_historical_v9(self):
        audit_nine(NINE.read_bytes(), NINE_FROZEN.read_bytes())

    def test_forged_both_nine_snapshots_rejected_by_pin(self):
        raw = NINE_FROZEN.read_bytes()
        altered = b"X" + raw[1:]
        with self.assertRaisesRegex(AssertionError, "Git blob"):
            audit_nine(altered, altered)

    def test_only_current_nine_root_changes(self):
        with self.assertRaisesRegex(AssertionError, "working root"):
            audit_nine(NINE.read_bytes()+b"x", NINE_FROZEN.read_bytes())

    def test_current_root_equals_frozen_ten_v29(self):
        self.assertEqual(WORKING.read_bytes(), LATEST.read_bytes())
        self.assertNotEqual(LATEST.read_bytes(), BEFORE.read_bytes())


if __name__ == "__main__":
    unittest.main()
