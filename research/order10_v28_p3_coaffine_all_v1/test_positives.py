"""Adversarial tests for four permanently archived complete positive maps."""
from __future__ import annotations

import base64
import json
import unittest
import zlib

import networkx as nx

from research.order10_v28_p3_coaffine_all_v1.verify_positives import (
    CERTIFICATE, EXPECTED_INDICES, SOURCE,
    audit_endomorphism, audit_stable_retraction, verify,
    verify_factor_theorem,
)
from research.order10_p3_global_v23_index.independent_verify import independent_p3


class FourPermanentRetractionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cert = json.loads(CERTIFICATE.read_text(encoding="utf-8"))
        cls.source = {
            x["original_index"]: (
                independent_p3(x["original_graph6"]),
                list(zlib.decompress(base64.b64decode(
                    x["map_zlib_base64"], validate=True))),
                x,
            )
            for x in cls.cert["positives"]
        }

    def test_all_four_complete_proofs(self):
        positive = verify()
        self.assertEqual(
            positive["originals_proven_K_divergent"], list(EXPECTED_INDICES)
        )
        self.assertEqual(positive["count_newly_proved_divergent"], 4)
        self.assertTrue(
            positive["common_17_vertex_expansive_target_isomorphism_verified"]
        )

    def test_noncoaffine_fixed_point_is_rejected(self):
        G, f, _ = self.source[10481909]
        bad = f.copy()
        bad[0] = 0
        with self.assertRaisesRegex(AssertionError, "Coaffine"):
            audit_endomorphism(G, bad)

    def test_wrong_retraction_power_is_rejected(self):
        G, f, _ = self.source[11438191]
        with self.assertRaisesRegex(AssertionError, "power"):
            audit_stable_retraction(G, f, 1)

    def test_false_nonedge_in_claimed_join_is_rejected(self):
        G, f, cert = self.source[10586728]
        Y, _ = audit_stable_retraction(G, f, cert["power_exponent"])
        H = nx.complement(Y)
        factors = sorted(
            (sorted(c) for c in nx.connected_components(H)), key=len
        )
        bad = Y.copy()
        bad.remove_edge(factors[0][0], factors[1][0])
        with self.assertRaisesRegex(AssertionError, "complement components"):
            verify_factor_theorem(
                bad, f, "O1_join_connected_coaffine_15"
            )

    def test_missing_connected_summand_assumption_is_rejected(self):
        G, f, cert = self.source[10481909]
        Y, _ = audit_stable_retraction(G, f, cert["power_exponent"])
        proof = verify_factor_theorem(
            Y, f, "O1_join_connected_coaffine_15"
        )
        self.assertTrue(proof["at_least_one_connected_coaffine_factor"])
        self.assertEqual(proof["complement_component_orders"], [2, 15])

    def test_o2_C7_uses_three_summands_theorem(self):
        G, f, cert = self.source[11438191]
        Y, _ = audit_stable_retraction(G, f, cert["power_exponent"])
        proof = verify_factor_theorem(
            Y, f, "O2_join_complement_C7"
        )
        self.assertEqual(proof["complement_component_orders"], [2, 2, 7])
        self.assertIn("Theorem 3.6", proof["published_expansivity_theorem"])


if __name__ == "__main__":
    unittest.main()
