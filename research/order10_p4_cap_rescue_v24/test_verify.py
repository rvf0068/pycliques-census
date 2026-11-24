"""Adversarial tests for fully recovered P4 classes after former facet caps."""
from __future__ import annotations

import base64
import json
import unittest

from .verify import (
    ARCHIVE, check_bijection, fully_pare,
    p4_from_graph6, verify,
)


class RecoveredP4ClassesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cert=json.loads(ARCHIVE.read_text(encoding="utf-8"))

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
