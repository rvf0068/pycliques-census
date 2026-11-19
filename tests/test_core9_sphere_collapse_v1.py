"""Regression tests for exact sphere collapses of two nine-vertex cores."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "core9_sphere_collapse_v1", ROOT / "scripts/core9_sphere_collapse_v1.py"
)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


class SphereCollapseCertificates(unittest.TestCase):
    def test_exact_reproducibility_and_full_replay(self):
        data = study.build()
        self.assertEqual(set(data["graphs"]), {"208409", "248687"})
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "cert.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            study.verify(path)
        for key, record in data["graphs"].items():
            self.assertEqual(
                [len(r["pairs"]) for r in record["iterates"]],
                study.EXPECTED[key]["steps"],
            )
            self.assertEqual(
                [r["remaining"]["fvector"] for r in record["iterates"]],
                study.EXPECTED[key]["residual_f"],
            )

    def test_corrupted_collapse_is_rejected(self):
        graph = study.nx.from_graph6_bytes(study.INPUTS["208409"].encode("ascii"))
        graph = study.raw_K(graph)
        faces = study.simplex_faces(graph)
        _, pairs = study.collapse(faces)
        corrupted = [pair.copy() for pair in pairs]
        corrupted[0][1] = corrupted[0][0]
        with self.assertRaises(ValueError):
            study.replay(faces, corrupted)

    def test_non_sphere_rejected(self):
        with self.assertRaises(ValueError):
            study.sphere({1, 2, 4, 3, 5, 6, 7})


if __name__ == "__main__":
    unittest.main()
