"""Regression checks for new positive nine-to-ten P3 certificates."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

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

    def test_certificates_cannot_repin_modified_archives(self):
        """A matching certificate-supplied hash cannot replace a code pin."""
        path = "indeterminate_order_9_v9.txt"
        original = (verify.ROOT / path).read_bytes()
        modified = original + b"# tampered historical snapshot\\n"
        forged_sha = verify.git_blob(modified)
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / path).write_bytes(modified)
            with patch.object(verify, "ROOT", Path(tmp)):
                with self.assertRaisesRegex(AssertionError,
                                            "independently pinned"):
                    verify.verified_archive(path, forged_sha)

    def test_only_known_provenance_paths_are_accepted(self):
        with self.assertRaisesRegex(AssertionError, "Unrecognized"):
            verify.verified_archive("other/certificates.json", "0" * 40)

    def test_all_code_pins_match_archived_sources(self):
        for path, expected in verify.EXPECTED_ARCHIVE_GIT_BLOBS.items():
            self.assertEqual(verify.verified_archive(path, expected),
                             (verify.ROOT / path).read_bytes())


if __name__ == "__main__":
    unittest.main()
