"""Tamper and replay tests for F_(m,n) finite certificates."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fmn_homology_first_v1 as research  # noqa: E402


def serialized(record):
    return json.loads(json.dumps(record))


class FamilyHomologyCertificateTests(unittest.TestCase):
    def test_graph_identity_and_f_vectors(self):
        for m, n in ((3, 3), (4, 4), (4, 5), (6, 7)):
            with self.subTest(pair=(m, n)):
                g = research.family_graph(m, n)
                h = research.independent_family_graph(m, n)
                self.assertEqual(set(map(frozenset, g.edges())),
                                 set(map(frozenset, h.edges())))
                self.assertEqual(len(g), m + n)
                self.assertEqual(g.number_of_edges(), 3 * (m + n) - 6)

    def test_reference_snub_and_other_sphere(self):
        for pair, expected in (
            ((4, 4), {5: 5}), ((4, 5), {3: 3}),
            ((4, 6), {2: 1}), ((5, 6), {2: 1}),
            ((6, 6), {2: 1}), ((9, 9), {2: 1}),
        ):
            with self.subTest(pair=pair):
                record = research.certify_case(*pair)
                research.verify_case(serialized(record))
                self.assertEqual(
                    {k: v for k, v in record["reduced_betti_mod2"].items() if v},
                    expected,
                )

    def test_replay_rejects_false_open_link_fold(self):
        record = serialized(research.certify_case(4, 6))
        step = next(s for s in record["deletions"] if s["link_folds"])
        x, _ = step["link_folds"][0]
        step["link_folds"][0] = [x, x]
        with self.assertRaises(ValueError):
            research.verify_case(record)

    def test_batch_requires_complete_grid(self):
        result = {
            "schema": 1,
            "max_n": 5,
            "cases": [
                serialized(research.certify_case(m, n))
                for m, n in ((4, 4), (4, 5), (5, 5))
            ],
        }
        self.assertEqual(research.verify_batch(result), 3)
        for malformed in (
            dict(result, cases=result["cases"][:1]),
            dict(result, cases=result["cases"] + [result["cases"][0]]),
            dict(result, cases=list(reversed(result["cases"]))),
            dict(result, max_n=10),
        ):
            with self.assertRaises(ValueError):
                research.verify_batch(malformed)

    def test_optimized_python_cannot_bypass_verifier(self):
        import subprocess
        import tempfile
        result = {
            "schema": 1, "max_n": 4,
            "cases": [serialized(research.certify_case(4, 4))],
        }
        result["cases"][0]["reduced_betti_mod2"]["5"] = 99
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "invalid.json"
            artifact.write_text(json.dumps(result))
            script = Path(__file__).resolve().parents[1] / "scripts" \
                / "fmn_homology_first_v1.py"
            completed = subprocess.run(
                [sys.executable, "-O", str(script), "verify",
                 "--input", str(artifact)],
                capture_output=True, text=True, timeout=60, check=False,
            )
        self.assertNotEqual(completed.returncode, 0)

    def test_replay_rejects_false_homology_and_collapse(self):
        record = serialized(research.certify_case(5, 7))
        bad = deepcopy(record)
        bad["reduced_betti_mod2"]["2"] = 9
        with self.assertRaises(ValueError):
            research.verify_case(bad)
        self.assertIn("elementary_collapses", record)
        bad = deepcopy(record)
        bad["elementary_collapses"].append([[999, 1000], [999]])
        with self.assertRaises(ValueError):
            research.verify_case(bad)


if __name__ == "__main__":
    unittest.main()
