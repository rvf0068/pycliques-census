"""Mutation checks for candidate-specific octahedral target obstructions."""
from __future__ import annotations

import unittest

import networkx as nx

from research.order10_overcap_p3_coaffine_v1.pilot import source_catalog
from research.order10_five_p3_native_v1.matching_obstructions import (
    CANDIDATE_CERTIFICATES, verify_all, verify_candidate,
)


class MatchingNecessaryConditionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = source_catalog()

    def test_four_induced_total_dominating_matchings_and_conflicts(self):
        cert = verify_all()
        self.assertEqual(len(cert["records"]), 4)
        self.assertTrue(cert["cannot_promote_any_census_classification"])
        self.assertEqual(
            [x["original_mckay_index"] for x in cert["records"]],
            sorted(CANDIDATE_CERTIFICATES),
        )
        self.assertTrue(all(
            rec["specified_target_cannot_be_a_retract"]
            and rec["all_complement_vertices_totally_dominated"]
            for rec in cert["records"]
        ))

    def test_swapped_forced_image_witness_is_rejected(self):
        for idx, (matching, (u,v,a,b)) in CANDIDATE_CERTIFICATES.items():
            with self.subTest(original=idx):
                g = nx.from_graph6_bytes(
                    self.sources[idx]["p3_graph6"].encode("ascii")
                )
                with self.assertRaisesRegex(AssertionError, "contradiction"):
                    verify_candidate(g, matching, (u,v,b,a))

    def test_deleting_one_target_edge_breaks_the_certificate(self):
        for idx, (matching, conflict) in CANDIDATE_CERTIFICATES.items():
            with self.subTest(original=idx):
                g = nx.from_graph6_bytes(
                    self.sources[idx]["p3_graph6"].encode("ascii")
                )
                broken = matching[1:]
                with self.assertRaises(AssertionError):
                    verify_candidate(g, broken, conflict)


if __name__ == "__main__":
    unittest.main()
