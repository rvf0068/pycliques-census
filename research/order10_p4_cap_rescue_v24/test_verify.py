"""Adversarial tests for fully recovered P4 classes after former facet caps."""
from __future__ import annotations

import base64
import copy
from unittest.mock import patch
import json
import unittest

from . import verify as proof
from .verify import (
    ARCHIVE, check_bijection, fully_pare,
    p4_from_graph6, verify,
)


class RecoveredP4ClassesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cert=json.loads(ARCHIVE.read_text(encoding="utf-8"))

    def test_immutable_upstream_p3_and_p4_blobs(self):
        self.assertEqual(
            proof.EXPECTED_PRIOR_GIT_BLOB,
            "171908472fe4037e0653a08056877fb956bd8d54",
        )
        self.assertEqual(
            proof.EXPECTED_P3_GIT_BLOB,
            "ab5a9f1c075dfad63b111929368147884519f2a3",
        )
        prior, p3 = proof.verify_upstream_archives(self.cert)
        self.assertEqual(prior["counts"]["selected"], 206)
        self.assertEqual(p3["counts"]["exact_isomorphism_classes"], 525)

    def test_co_mutated_certificate_and_historical_archive_hashes_fail(self):
        # Model a malicious rewrite in which the attacker also updates
        # BOTH checksum fields in the new certificate. The hashes are
        # self-consistent but mismatch the immutable expected values.
        fake = copy.deepcopy(self.cert)
        fake["from_git_blob"] = "f" * 40
        fake["global_p3_git_blob"] = "f" * 40
        with patch.object(proof, "blob", return_value="f" * 40):
            with self.assertRaisesRegex(
                AssertionError, "Immutable historical P3/P4 pilot"
            ):
                proof.verify_upstream_archives(fake)

    def test_mutated_original_p4_archive_without_certificate_edit_fails(self):
        with patch.object(proof, "blob", return_value="0" * 40):
            with self.assertRaisesRegex(
                AssertionError, "Immutable historical P3/P4 pilot"
            ):
                proof.verify_upstream_archives(self.cert)

    def test_replay_all_26_exact_fourth_iterates(self):
        verify()

    def test_two_round_fold_is_not_misclassified_as_complete_after_one(self):
        # The path P4 loses endpoints in the first simultaneous step;
        # its remaining edge consists of twins needing a second step.
        raw=[
            1<<1,
            (1<<0)|(1<<2),
            (1<<1)|(1<<3),
            1<<2,
        ]
        survivors,pared,rounds=fully_pare(raw)
        self.assertEqual(survivors,[1])
        self.assertEqual(pared,[0])
        self.assertEqual(rounds,[2,1])

    def test_complete_map_rejects_nonpermutation_and_false_edges(self):
        first=[1<<1,(1<<0)|(1<<2),1<<1]
        check_bijection(first,first,[0,1,2])
        with self.assertRaisesRegex(AssertionError,"complete P4 vertex bijection"):
            check_bijection(first,first,[0,1,1])
        with self.assertRaisesRegex(AssertionError,"adjacency or nonadjacency"):
            check_bijection(first,first,[1,0,2])

    def test_positive_witness_provenance_and_exact_dimensions(self):
        c=self.cert["positive_isomorphism"]
        self.assertEqual((c["from_index"],c["to_index"]),
                         (7044680,11614797))
        self.assertEqual(c["vertices"],685)
        self.assertEqual(c["merged_originals"],18)
        self.assertEqual(
            len(base64.b64decode(c["map_b64"],validate=True)),
            2*c["vertices"],
        )

    def test_dimension_collision_not_a_false_positive(self):
        recorded={
            x["index"]:x for x in self.cert["recovered_records"]
        }
        self.assertEqual(recorded[6927388]["P4"],
                         recorded[10302846]["P4"])
        self.assertEqual(recorded[7044680]["P4"],
                         recorded[11614797]["P4"])
        self.assertEqual(
            self.cert["aggregate"]["exact_P4_isomorphism_classes"],205
        )


if __name__=="__main__":
    unittest.main()
