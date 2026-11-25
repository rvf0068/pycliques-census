"""Adversarial tests for the exact ten-v26 to ten-v27 promotion."""
from __future__ import annotations

import unittest

from research.order10_p4_crossdepth_o15_v25.verify import source_rows
from research.order10_v27_two_p3_o11.verify import (
    BEFORE, LATEST, EXPECTED_REMOVALS, audit_rows, verify,
)


class TenV27PromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = source_rows(BEFORE)
        cls.after = source_rows(LATEST)
        cls.certified = set(EXPECTED_REMOVALS)

    def test_full_two_original_positive_proof_and_transition(self):
        summary = verify()
        self.assertEqual(summary["population"]["after"], 1044)
        self.assertEqual(
            summary["proved_divergent_original_indices"],
            list(EXPECTED_REMOVALS),
        )

    def test_exactly_two_deletions(self):
        audit_rows(self.before, self.after, self.certified)

    def test_retained_row_mutation_is_rejected(self):
        changed = dict(self.after)
        index = next(iter(changed))
        changed[index] = changed[index].replace(" - - -", " - - bad")
        with self.assertRaisesRegex(AssertionError, "retained"):
            audit_rows(self.before, changed, self.certified)

    def test_wrong_original_deletion_is_rejected(self):
        changed = dict(self.after)
        changed.pop(next(iter(changed)))
        changed[EXPECTED_REMOVALS[0]] = self.before[EXPECTED_REMOVALS[0]]
        changed = dict(sorted(changed.items()))
        with self.assertRaisesRegex(AssertionError, "uncertified"):
            audit_rows(self.before, changed, self.certified)

    def test_wrong_certified_indices_are_rejected(self):
        with self.assertRaisesRegex(AssertionError, "exactly two"):
            audit_rows(self.before, self.after, {EXPECTED_REMOVALS[0]})

    def test_frozen_promoted_source_graph6_is_required(self):
        changed = dict(self.before)
        i = EXPECTED_REMOVALS[0]
        changed[i] = changed[i].replace(" 10 ", " 9 ", 1)
        with self.assertRaisesRegex(AssertionError, "graph6"):
            audit_rows(changed, self.after, self.certified)

    def test_wrong_population_is_rejected(self):
        changed = dict(self.after)
        changed.pop(next(iter(changed)))
        with self.assertRaisesRegex(AssertionError, "counts"):
            audit_rows(self.before, changed, self.certified)


if __name__ == "__main__":
    unittest.main()
