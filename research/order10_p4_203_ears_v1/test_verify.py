"""Focused mutation tests for 203 P4 reconstructions and 14 complete ears."""
from __future__ import annotations

import copy
import unittest

from research.order10_p4_203_ears_v1 import (
    ears, independent_verify, verify,
)


class CensusP4CertificatesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases, cls.hosts = verify.validated_catalog()
        cls.byidx = {r["index"]: r for r in cls.cases}

    def test_exact_521_class_partition(self):
        self.assertEqual(len(self.cases), 203)
        self.assertEqual(len(self.hosts), 521)
        self.assertEqual(len(verify.TEN_P3_OVERCAP), 10)
        self.assertEqual(
            max(x["facets"] for x in self.cases), 2223
        )

    def test_tampered_source_path_rejected(self):
        with self.assertRaisesRegex(AssertionError, "Unrecognized"):
            verify.frozen("research/unsourced_p4_fake.json")

    def test_first_reconstruction_two_implementations(self):
        record = self.cases[0]
        a, primary = verify.replay_primary_p4(record)
        b, independent = independent_verify.replay_independent_p4(record)
        self.assertEqual(len(a), record["raw_p4"][0])
        self.assertEqual(len(b), len(a))
        self.assertEqual(primary, independent)

    def test_corrupted_full_adjacency_digest_rejected(self):
        record = copy.deepcopy(self.cases[0])
        record["p4_adj_sha256"] = "0" * 64
        with self.assertRaisesRegex(AssertionError, "SHA"):
            verify.replay_primary_p4(record)
        with self.assertRaisesRegex(AssertionError, "matrix"):
            independent_verify.replay_independent_p4(record)

    def test_corrupted_folding_rounds_rejected(self):
        record = copy.deepcopy(self.cases[0])
        record["fold_rounds"] = [1]
        with self.assertRaises(AssertionError):
            verify.replay_primary_p4(record)
        with self.assertRaises(AssertionError):
            independent_verify.replay_independent_p4(record)

    def test_corrupted_ear_permutation_rejected(self):
        data = __import__("json").loads(verify.frozen(
            "research/order10_p4_203_ears_v1/ear_retractions.json"
        ))
        item = copy.deepcopy(data["records"][0])
        item["nine_to_ten_core_map_sha256"] = "0" * 64
        self.assertIn(item["ten_index"], self.byidx)
        nine = ears.source_nine()
        _raw, pared, _rounds, _p3 = ears.p4_from_graph6(
            nine[item["nine_index"]]
        )
        with self.assertRaisesRegex(AssertionError, "permutation changed"):
            ears.prove_one(
                item, self.byidx, nine, {item["nine_index"]: pared}
            )

    def test_bogus_ear_attachment_neighbor_rejected(self):
        data = __import__("json").loads(verify.frozen(
            "research/order10_p4_203_ears_v1/ear_retractions.json"
        ))
        item = copy.deepcopy(data["records"][0])
        item["neighbor_images_in_nine"] = [0, 0]
        nine = ears.source_nine()
        _raw, pared, _rounds, _p3 = ears.p4_from_graph6(
            nine[item["nine_index"]]
        )
        with self.assertRaises(AssertionError):
            ears.prove_one(
                item, self.byidx, nine, {item["nine_index"]: pared}
            )

    def test_bad_shard_number_rejected(self):
        with self.assertRaisesRegex(AssertionError, "shard"):
            verify.verify_shard(-1, 4)

    def test_adversarial_malformed_graph_mask_fails_closed(self):
        with self.assertRaisesRegex(AssertionError, "Asymmetric"):
            verify.replay_primary_p4.__module__  # noqa: B018
            from research.order10_small_p4_98_v1.verify import dims
            dims([0b10, 0])


if __name__ == "__main__":
    unittest.main()
