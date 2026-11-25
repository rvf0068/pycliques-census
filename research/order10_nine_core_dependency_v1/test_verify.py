"""Regression checks for new positive nine-to-ten P3 certificates."""
import copy
import json
import unittest

from . import verify


class DependencyProofTests(unittest.TestCase):
    def test_archived_bijection_lengths(self):
        data = json.loads(verify.CERTIFICATE.read_text(encoding="utf-8"))
        for record in data["three_p3_equivalences"]:
            n = record["p3_order"]
            self.assertEqual(sorted(record["nine_to_ten_p3"]), list(range(n)))
        self.assertEqual(sum(r["class_members"] for r in
                             data["three_p3_equivalences"]), 65)

    def test_corrupted_complete_map_fails(self):
        data = json.loads(verify.CERTIFICATE.read_text(encoding="utf-8"))
        record = data["three_p3_equivalences"][1]
        a = verify.independent_p3(record["nine_graph6"])
        b = verify.independent_p3(record["ten_rep_graph6"])
        verify.verify_pair(a, b, record["nine_to_ten_p3"])
        broken = copy.copy(record["nine_to_ten_p3"])
        broken[0] = broken[1]
        with self.assertRaises(AssertionError):
            verify.verify_pair(a, b, broken)

    def test_wrong_git_blob_rejected(self):
        with self.assertRaises(AssertionError):
            verify.verified_archive("indeterminate_order_9_v9.txt", "0" * 40)


if __name__ == "__main__":
    unittest.main()
