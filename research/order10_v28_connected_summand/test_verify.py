"""Mutation tests for the exact ten-v27 -> ten-v28 one-original promotion."""
from __future__ import annotations

import unittest

from research.order10_p4_crossdepth_o15_v25.verify import source_rows
from research.order10_v28_connected_summand.verify import (
    BEFORE, LATEST, EXPECTED_REMOVALS, NINE, NINE_FROZEN,
    audit_nine, audit_rows, verify,
)


class TenV28PromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = source_rows(BEFORE)
        cls.after = source_rows(LATEST)
        cls.certified = set(EXPECTED_REMOVALS)

    def test_full_positive_theorem_and_exact_promotion(self):
        result = verify()
        self.assertEqual(result["population"]["after"], 1043)
        self.assertEqual(result["proved_divergent_original_indices"], [11713984])
        self.assertEqual(result["retraction_target"], "O14_join_complement_C7")

    def test_no_other_original_modified_or_deleted(self):
        audit_rows(self.before, self.after, self.certified)

    def test_retained_row_mutation_is_rejected(self):
        changed = dict(self.after)
        index = next(iter(changed))
        changed[index] = changed[index].replace(" - - -", " - - bad")
        with self.assertRaisesRegex(AssertionError, "retained"):
            audit_rows(self.before, changed, self.certified)

    def test_uncertified_deletion_is_rejected(self):
        changed = dict(self.after)
        changed.pop(next(iter(changed)))
        changed[EXPECTED_REMOVALS[0]] = self.before[EXPECTED_REMOVALS[0]]
        changed = dict(sorted(changed.items()))
        with self.assertRaisesRegex(AssertionError, "uncertified"):
            audit_rows(self.before, changed, self.certified)

    def test_wrong_positive_original_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, "exactly one"):
            audit_rows(self.before, self.after, {11595632})

    def test_wrong_promoted_graph6_is_rejected(self):
        changed = dict(self.before)
        i = EXPECTED_REMOVALS[0]
        changed[i] = changed[i].replace(" 10 ", " 9 ", 1)
        with self.assertRaisesRegex(AssertionError, "graph6"):
            audit_rows(changed, self.after, self.certified)

    def test_extra_original_deletion_is_rejected(self):
        changed = dict(self.after)
        changed.pop(next(iter(changed)))
        with self.assertRaisesRegex(AssertionError, "counts"):
            audit_rows(self.before, changed, self.certified)

    def test_nine_v9_snapshot_is_independently_authenticated(self):
        audit_nine(NINE.read_bytes(), NINE_FROZEN.read_bytes())

    def test_identical_corruption_of_both_nine_files_is_rejected(self):
        frozen = NINE_FROZEN.read_bytes()
        corrupted = b"X" + frozen[1:]
        self.assertNotEqual(corrupted, frozen)
        with self.assertRaisesRegex(AssertionError, "Git blob"):
            audit_nine(corrupted, corrupted)

    def test_only_active_nine_root_corruption_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, "working root"):
            audit_nine(NINE.read_bytes() + b"x", NINE_FROZEN.read_bytes())


if __name__ == "__main__":
    unittest.main()
