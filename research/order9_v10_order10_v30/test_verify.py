"""Adversarial audits of exact all-nine and 500-original ten promotions."""
from __future__ import annotations

import unittest

from research.order10_p4_crossdepth_o15_v25.verify import source_rows
from research.order9_v10_order10_v30.verify import (
    NINE_BEFORE,NINE_AFTER,NINE_WORKING,
    TEN_BEFORE,TEN_AFTER,TEN_WORKING,
    PROVED_NINE,PROVED_SIX_TEN,
    audit_nine,audit_ten,verify_snapshot_blobs,verify,
)
from research.order9_last_three_incidence_v1.ten_dependents import collect


class FinalOrderNineTenCensusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nine_before=source_rows(NINE_BEFORE)
        cls.nine_after=source_rows(NINE_AFTER)
        cls.ten_before=source_rows(TEN_BEFORE)
        cls.ten_after=source_rows(TEN_AFTER)
        cls.all_dependent=set(map(int,collect()["provenance_by_original_McKay"]))

    def test_exact_roots_and_hashes(self):
        verify_snapshot_blobs(
            NINE_BEFORE.read_bytes(),NINE_AFTER.read_bytes(),
            TEN_BEFORE.read_bytes(),TEN_AFTER.read_bytes(),
        )
        self.assertEqual(NINE_WORKING.read_bytes(),NINE_AFTER.read_bytes())
        self.assertEqual(TEN_WORKING.read_bytes(),TEN_AFTER.read_bytes())

    def test_complete_three_original_positive_proofs_and_500_lifts(self):
        summary=verify(replay_historical=False)
        self.assertEqual(summary["population"],{
            "nine_before":3,"nine_after":0,
            "nine_newly_proved_divergent":3,
            "ten_before":1037,"ten_after":537,
            "ten_newly_proved_divergent":500,
            "ten_pared_nine_originals_removed":430,
            "ten_stiff_originals_removed":70,
            "ten_stiff_originals_retained":537,
        })
        self.assertEqual(summary["original_nine_proved_K_divergent"],list(PROVED_NINE))
        self.assertEqual(summary["all_nine_P4_source_edges_verified"],1325328)
        self.assertEqual(set(summary["ten_positive_originals_exact"]),self.all_dependent)

    def test_three_and_five_hundred_exact_removed(self):
        audit_nine(self.nine_before,self.nine_after,set(PROVED_NINE))
        audit_ten(self.ten_before,self.ten_after,self.all_dependent)
        self.assertEqual(len(self.ten_before)-len(self.ten_after),500)

    def test_mutated_retained_record_rejected(self):
        altered=dict(self.ten_after)
        i=next(iter(altered))
        altered[i]=altered[i].replace(" - - -"," - - FALSE")
        with self.assertRaisesRegex(AssertionError,"retained"):
            audit_ten(self.ten_before,altered,self.all_dependent)

    def test_seventh_unproved_original_deletion_rejected(self):
        altered=dict(self.ten_after)
        altered.pop(next(iter(altered)))
        with self.assertRaisesRegex(AssertionError,"population"):
            audit_ten(self.ten_before,altered,self.all_dependent)

    def test_wrong_replacement_original_rejected(self):
        altered=dict(self.ten_after)
        altered.pop(next(iter(altered)))
        i=min(self.all_dependent)
        altered[i]=self.ten_before[i]
        altered=dict(sorted(altered.items()))
        with self.assertRaisesRegex(AssertionError,"unsupported"):
            audit_ten(self.ten_before,altered,self.all_dependent)

    def test_missing_one_certified_original_rejected(self):
        fewer=set(self.all_dependent)
        fewer.pop()
        with self.assertRaisesRegex(AssertionError,"unsupported"):
            audit_ten(self.ten_before,self.ten_after,fewer)

    def test_unsupported_extra_certified_original_rejected(self):
        more=set(self.all_dependent)
        more.add(next(iter(self.ten_after)))
        with self.assertRaisesRegex(AssertionError,"unsupported"):
            audit_ten(self.ten_before,self.ten_after,more)

    def test_fake_nine_negative_not_a_positive_proof(self):
        with self.assertRaisesRegex(AssertionError,"uncertified"):
            audit_nine(self.nine_before,self.nine_after,{249576,251628})
        bad=dict(self.nine_after)
        bad[249576]=self.nine_before[249576]
        with self.assertRaisesRegex(AssertionError,"counts"):
            audit_nine(self.nine_before,bad,set(PROVED_NINE))

    def test_frozen_source_g6_changed_rejected(self):
        forged=dict(self.nine_before)
        forged[249576]=forged[249576].replace("HEhfvzu","HEhvVn{")
        with self.assertRaisesRegex(AssertionError,"identities"):
            audit_nine(forged,self.nine_after,set(PROVED_NINE))

    def test_new_nine_and_ten_hashes_are_independent_of_current_roots(self):
        nine=NINE_BEFORE.read_bytes()
        nine_latest=NINE_AFTER.read_bytes()
        ten=TEN_BEFORE.read_bytes()
        ten_latest=TEN_AFTER.read_bytes()
        with self.assertRaisesRegex(AssertionError,"Git blob"):
            verify_snapshot_blobs(nine,nine_latest+b"x",ten,ten_latest)
        with self.assertRaisesRegex(AssertionError,"Git blob"):
            verify_snapshot_blobs(nine,nine_latest,ten,ten_latest+b"x")

    def test_six_prior_ten_positive_originals_not_promoted_twice(self):
        self.assertTrue(set(PROVED_SIX_TEN).isdisjoint(self.all_dependent))
        self.assertTrue(set(PROVED_SIX_TEN).isdisjoint(set(self.ten_before)))


if __name__=="__main__":
    unittest.main()
