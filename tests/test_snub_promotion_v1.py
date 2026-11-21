"""Regression checks for positive-only snub divergence promotion."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "research/snub_promotion_v1/verify.py"
spec = importlib.util.spec_from_file_location("snub_promotion_verify", MODULE)
assert spec and spec.loader
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


class SnubPromotionTests(unittest.TestCase):
    def test_order9_exact_certificate_replay(self):
        result = verify.verify_order(9)
        self.assertEqual((result["old"], result["new"], result["proven_divergent"]),
                         (49, 13, 36))
        self.assertEqual(result["rules"],
                         {"reference": 25, "retracts": 9,
                          "non_triangle_edge": 1, "inverse_cutpoint_extension": 1})

    def test_order10_exact_certificate_replay(self):
        result = verify.verify_order(10)
        self.assertEqual((result["old"], result["new"], result["proven_divergent"]),
                         (7219, 2830, 4389))
        self.assertEqual(result["rules"],
                         {"reference": 2092, "retracts": 2018,
                          "non_triangle_edge": 227, "inverse_cutpoint_extension": 52})

    def test_universal_extension_is_not_a_snub_retract(self):
        host = verify.SNUB.copy()
        u = max(host) + 1
        host.add_edges_from((u, v) for v in verify.SNUB)
        self.assertIsNone(verify.induced_snub_retraction(host))

    def test_pared_closed_neighborhood_fold(self):
        host = verify.SNUB.copy()
        v = max(host) + 1
        host.add_node(v)
        host.add_edges_from((v, w) for w in list(verify.SNUB[0]) + [0])
        pared, folds = verify.pare(host)
        self.assertTrue(folds)
        self.assertIsNotNone(verify.induced_snub_retraction(pared))

    def test_snub_retract_itself(self):
        witness = verify.induced_snub_retraction(verify.SNUB)
        self.assertIsNotNone(witness)
        self.assertEqual(len(witness["target"]), 8)
        self.assertEqual(witness["outside_images"], [])

    def test_source_hash_pinned(self):
        for order, details in verify.FROZEN.items():
            name, _, expected_sha, *_ = details
            self.assertEqual(
                verify.blob_sha((ROOT / name).read_bytes()), expected_sha,
                f"historical order-{order} source altered",
            )


if __name__ == "__main__":
    unittest.main()
