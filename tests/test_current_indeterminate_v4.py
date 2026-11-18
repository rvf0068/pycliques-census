"""Regression tests for versioned, certified order-10 working lists."""
from __future__ import annotations

from pathlib import Path
import csv
import hashlib
from io import StringIO
from unittest.mock import patch
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import current_indeterminate_v4 as v4  # noqa: E402


class CertifiedCurrentListTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in (v4.SOURCE, v4.CLASS_INDEX, v4.ASSIGNMENTS, v4.OLD_CERTIFICATES):
            dest = self.root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, dest)

    def test_reconciles_every_original_index_with_disjoint_certificates(self):
        outputs = v4.generate(self.root)
        unresolved = outputs[v4.OUTPUT].decode("utf-8")
        resolved = outputs[v4.PROVEN_INDEX].decode("utf-8")
        assert unresolved.startswith("# Current order-10 unresolved cases")
        self.assertIn("# Remaining=8233", unresolved)
        self.assertEqual(
            sum(line and not line.startswith("#") for line in unresolved.splitlines()),
            8233,
        )
        self.assertEqual(len(resolved.splitlines()), 301)
        self.assertEqual(
            len({int(line.split("\t")[0]) for line in resolved.splitlines()[1:]}),
            300,
        )
        self.assertEqual(
            sum("conjectured_divergent" in line for line in unresolved.splitlines()),
            4608,
        )

    def test_all_output_bytes_are_reproducible_and_tampering_fails(self):
        outputs = v4.generate(self.root)
        for name, blob in outputs.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(blob)
        v4.check(self.root)
        path = self.root / v4.OUTPUT
        path.write_text(path.read_text(encoding="utf-8") + "extra\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "modified or stale"):
            v4.check(self.root)

    def test_wrong_certificate_member_is_rejected(self):
        path = self.root / v4.OLD_CERTIFICATES
        data = path.read_text(encoding="utf-8")
        old = data.splitlines()
        self.assertGreater(len(old), 2)
        fields = old[1].split("\t")
        fields[0] = "123456789"
        old[1] = "\t".join(fields)
        path.write_text("\n".join(old) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "133 certified"):
            v4.generate(self.root)

    def test_tampered_pared_graph6_is_rejected_even_if_counts_unchanged(self):
        path = self.root / v4.SOURCE
        source = path.read_text(encoding="utf-8")
        self.assertIn("GQyuzw", source)
        path.write_text(source.replace("GQyuzw", "GQyuzx", 1), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "frozen v3"):
            v4.generate(self.root)

    def test_swapping_member_indices_across_cores_is_rejected(self):
        path = self.root / v4.CLASS_INDEX
        rows = list(csv.DictReader(StringIO(path.read_text(encoding="utf-8")), delimiter="\t"))
        by_core = {int(row["core_id"]): row for row in rows}
        a, b = by_core[7454135], by_core[6962151]
        aa, bb = a["member_indices"].split(","), b["member_indices"].split(",")
        # Preserve count, minimum representative and global index set.
        aa[-1], bb[-1] = bb[-1], aa[-1]
        a["member_indices"] = ",".join(aa)
        b["member_indices"] = ",".join(bb)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        amended_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        # Bypass the digest guard ONLY within this unit test to exercise
        # the logically independent assignment-versus-class crosscheck.
        with patch.dict(v4.FROZEN_SHA256, {v4.CLASS_INDEX: amended_digest}):
            with self.assertRaisesRegex(ValueError, "Core membership disagrees"):
                v4.generate(self.root)

    def test_forged_working_index_is_rejected(self):
        path = self.root / v4.SOURCE
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("Remaining=8533", "Remaining=8532", 1))
        with self.assertRaisesRegex(ValueError, "frozen v3"):
            v4.generate(self.root)


if __name__ == "__main__":
    unittest.main()
