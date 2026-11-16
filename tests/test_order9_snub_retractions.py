"""Regression checks for the three explicit snub-disphenoid retracts."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_order9_snub_retractions import (  # noqa: E402
    CERTS, EXPECTED, SNUB, decode,
    verify_all, verify_retraction_certificate,
)


class SnubRetractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(CERTS.read_text(encoding="utf-8"))

    def test_all_three_retractions_and_two_g2_isomorphisms_replay(self):
        result = verify_all(self.payload)
        self.assertEqual(result["order9_indices"], sorted(EXPECTED))
        self.assertEqual(result["verified_g2_isomorphism_pairs"], 2)
        self.assertEqual(result["original_ten_vertex_members_represented"], 512)

    def test_all_three_retractions_are_nonadjacent_identifications(self):
        snub = decode(SNUB)
        for row in self.payload["certificates"]:
            with self.subTest(index=row["order9_index"]):
                g = decode(row["original_graph6"])
                self.assertFalse(g.has_edge(1, 2))
                self.assertEqual(set(g.neighbors(2)), {5, 6, 7, 8})
                self.assertEqual(set(g.neighbors(1)), {4, 5, 6, 7, 8})
                verify_retraction_certificate(row, snub)

    def test_reject_forged_image_and_induced_target_isomorphism(self):
        snub = decode(SNUB)
        for row in self.payload["certificates"]:
            with self.subTest(index=row["order9_index"]):
                wrong = deepcopy(row)
                wrong["image_vertex"] = 0
                with self.assertRaisesRegex(ValueError, "not a graph morphism|containment"):
                    verify_retraction_certificate(wrong, snub)

                wrong = deepcopy(row)
                images = wrong["induced_target_to_snub"]
                images[0], images[1] = images[1], images[0]
                with self.assertRaisesRegex(ValueError, "not an isomorphism"):
                    verify_retraction_certificate(wrong, snub)

    def test_cross_reference_identity_is_essential(self):
        wrong = deepcopy(self.payload)
        wrong["certificates"][0]["order9_index"] = 244584
        with self.assertRaisesRegex(ValueError, "Duplicate or unexpected"):
            verify_all(wrong)
        wrong = deepcopy(self.payload)
        wrong["certificates"][0]["original_graph6"] = "HCvbvZu"
        with self.assertRaisesRegex(ValueError, "does not match frozen census"):
            verify_all(wrong)


if __name__ == "__main__":
    unittest.main()
