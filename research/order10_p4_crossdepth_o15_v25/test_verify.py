"""Adversarial positive-proof regression tests for ten-v25."""
from __future__ import annotations

import base64
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from . import verify as proof


class CrossDepthO15TenV25Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.certificate = json.loads(proof.CERT.read_text(encoding="utf-8"))
        cls.reference, cls.images, cls.pairs = proof.verify_reference(
            cls.certificate
        )

    def test_complete_positive_v25_proofs(self):
        proof.verify_archive()

    def test_four_sources_reconstruct_to_expected_dimensions(self):
        expected = {
            11551790: (10, 28),
            11552072: (10, 28),
            11555600: (10, 29),
            11707526: (10, 28),
        }
        for row in self.certificate["positives"]:
            stages, host = proof.canonical_stages(row["graph6"])
            self.assertEqual(stages[0], list(expected[row["index"]]))
            self.assertEqual(stages[-1], [132, 7880])
            self.assertEqual(proof.host_sha(host),
                             row["pared_fourth_sha256"])

    def test_reject_co_modified_misleading_source_hash(self):
        forged = copy.deepcopy(self.certificate)
        forged["from_git_blob"] = "0" * 40
        with self.assertRaisesRegex(AssertionError, "Wrong new proof schema"):
            proof.verify_index(forged)

    def test_reject_co_modified_historical_o15_hash(self):
        forged = copy.deepcopy(self.certificate)
        forged["historical_O15_git_blob"] = "0" * 40
        with self.assertRaisesRegex(
            AssertionError, "Historical complete O15 source proof"
        ):
            proof.verify_reference(forged)

    def test_reject_wrong_full_map_even_with_recomputed_checksum(self):
        # Corrupt a complete *permutation* in a coordinated way;
        # updating its own SHA must NOT make a false positive accepted.
        record = copy.deepcopy(self.certificate["positives"][0])
        raw = bytearray(base64.b64decode(record["bijection_b64"]))
        raw[0], raw[1] = raw[1], raw[0]
        record["bijection_b64"] = base64.b64encode(raw).decode("ascii")
        import hashlib
        record["bijection_sha256"] = hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(AssertionError,
                                    "isomorphism failed"):
            proof.verify_positive(
                record, self.reference, self.images, self.pairs
            )

    def test_reject_duplicate_source_index_in_proof(self):
        # Exercise the real archive-loading and validation path, rather
        # than merely comparing the forged list with the expected list.
        forged = copy.deepcopy(self.certificate)
        forged["positives"][1]["index"] = forged["positives"][0]["index"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "forged_certificates.json"
            path.write_text(json.dumps(forged), encoding="utf-8")
            with patch.object(proof, "CERT", path):
                with self.assertRaisesRegex(
                    AssertionError,
                    "Saved positive set does not equal the v25 deletion set",
                ):
                    proof.verify_archive()

    def test_exact_v24_to_v25_four_record_deletion(self):
        old = proof.source_rows(proof.PREVIOUS)
        new = proof.source_rows(proof.LATEST)
        self.assertEqual(len(old), 1056)
        self.assertEqual(len(new), 1052)
        self.assertEqual(set(old)-set(new), set(proof.REMOVED))
        self.assertTrue(all(old[i]==new[i] for i in new))
        proof.verify_index(self.certificate)

    def test_optimized_execution_guard_is_not_optional(self):
        # A real optimized Python subprocess must fail before any proof
        # calculation; checking metadata does not test sys.flags.optimize.
        proc = subprocess.run(
            [
                sys.executable, "-O", "-m",
                "research.order10_p4_crossdepth_o15_v25.verify",
            ],
            cwd=proof.ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn(
            "Optimized Python bypasses positive proof assertions",
            proc.stderr,
        )

    def test_historical_p4_has_real_current_alias(self):
        # Copilot noted a possibly missing CURRENT attribute. It is
        # present in the immutable P4 verifier; do not create a new,
        # unused attribute by passing create=True to patch.object.
        from research.order10_p4_no_octahedral_10820813_v1 import (
            verify as historical,
        )
        self.assertTrue(hasattr(historical, "CURRENT"))
        self.assertTrue(hasattr(historical, "SNAPSHOT"))
        with patch.object(historical, "CURRENT", historical.SNAPSHOT):
            self.assertEqual(historical.CURRENT, historical.SNAPSHOT)


if __name__ == "__main__":
    unittest.main()
