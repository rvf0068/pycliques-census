"""Adversarial checks for the four exact fourth-iterate proof certificates."""
from __future__ import annotations

import base64
import copy
import json
import unittest

from . import verify


class FourthIterateNineLinkTests(unittest.TestCase):
    def get_data(self):
        return json.loads(verify.CERT.read_text(encoding="utf-8"))

    def test_all_four_full_maps_are_code_pinned_permutations(self):
        data = self.get_data()
        self.assertEqual([item["index"] for item in data["records"]],
                         sorted(verify.POSITIVES))
        for item in data["records"]:
            self.assertEqual(
                sorted(verify.decode_map(item)),
                list(range(item["p4"][0])),
            )

    def test_tampered_map_bytes_are_rejected(self):
        item = copy.deepcopy(self.get_data()["records"][0])
        image = bytearray(base64.b64decode(item["map_b64"]))
        image[0] ^= 1
        item["map_b64"] = base64.b64encode(image).decode("ascii")
        with self.assertRaisesRegex(AssertionError, "digest"):
            verify.decode_map(item)

    def test_mutable_certificate_digest_cannot_repin_a_mapping(self):
        item = copy.deepcopy(self.get_data()["records"][1])
        item["map_sha256"] = "0" * 64
        with self.assertRaisesRegex(AssertionError, "digest"):
            verify.decode_map(item)

    def test_identity_maps_refuse_overrides(self):
        for item in self.get_data()["records"][2:]:
            self.assertEqual(
                item["map_encoding"], "identity_uint16_little_endian"
            )
            poisoned = copy.deepcopy(item)
            poisoned["map_b64"] = "AA=="
            with self.assertRaisesRegex(AssertionError, "Identity"):
                verify.decode_map(poisoned)

    def test_immutable_sources_are_code_pinned(self):
        for path in verify.EXPECTED_GIT_BLOBS:
            raw = verify.immutable_bytes(path)
            self.assertEqual(verify.git_blob(raw),
                             verify.EXPECTED_GIT_BLOBS[path])

    def test_unrecognized_archive_path_rejected(self):
        with self.assertRaisesRegex(AssertionError, "Unknown immutable"):
            verify.immutable_bytes("indeterminate_order_10_v24.txt")


if __name__ == "__main__":
    unittest.main()
