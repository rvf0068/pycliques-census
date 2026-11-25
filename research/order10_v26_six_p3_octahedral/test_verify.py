"""Adversarial tests for exact v25-to-v26 promotion and positive proof."""
from __future__ import annotations

import unittest

from research.order10_p4_crossdepth_o15_v25.verify import source_rows
from research.order10_v26_six_p3_octahedral.verify import (
    BEFORE, LATEST, EXPECTED_REMOVALS, audit_rows, verify,
)


class TenV26PromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = source_rows(BEFORE)
        cls.after = source_rows(LATEST)
        cls.six = set(EXPECTED_REMOVALS)

    def test_whole_positive_promotion(self):
        certificate = verify()
        self.assertEqual(certificate["population"]["after"], 1046)
        self.assertEqual(
            certificate["proved_divergent_original_indices"],
            list(EXPECTED_REMOVALS),
        )
        self.assertEqual(
            certificate["remaining_unmaterialized_p4_classes"], 5
        )

    def test_exact_six_are_the_only_deletions(self):
        audit_rows(self.before, self.after, self.six)

    def test_changed_remaining_graph6_is_rejected(self):
        corrupted = dict(self.after)
        i = next(iter(corrupted))
        corrupted[i] = corrupted[i].replace(" - - -", " - - replacement")
        with self.assertRaisesRegex(AssertionError, "retained"):
            audit_rows(self.before, corrupted, self.six)

    def test_noncertified_deletion_cannot_replace_one_promoted_original(self):
        corrupted = dict(self.after)
        extra = next(iter(corrupted))
        corrupted.pop(extra)
        corrupted[EXPECTED_REMOVALS[0]] = self.before[EXPECTED_REMOVALS[0]]
        corrupted = dict(sorted(corrupted.items()))
        with self.assertRaisesRegex(AssertionError, "uncertified"):
            audit_rows(self.before, corrupted, self.six)

    def test_changed_proof_index_set_is_rejected(self):
        corrupted = set(self.six)
        corrupted.remove(EXPECTED_REMOVALS[0])
        with self.assertRaisesRegex(AssertionError, "exactly six"):
            audit_rows(self.before, self.after, corrupted)

    def test_stiff_original_graph6_cannot_be_modified(self):
        corrupted = dict(self.before)
        i = EXPECTED_REMOVALS[0]
        corrupted[i] = corrupted[i].replace(" 10 ", " 9 ", 1)
        with self.assertRaisesRegex(AssertionError, "graph6|composition"):
            audit_rows(corrupted, self.after, self.six)

    def test_immutable_nine_v9_and_prior_v25_are_not_rewritten(self):
        certificate = verify()
        self.assertEqual(certificate["previous_snapshot"],
                         "indeterminate_order_10_v25.txt")
        self.assertEqual(certificate["indeterminate_nine_originals_unchanged"], 3)


if __name__ == "__main__":
    unittest.main()
