"""Regression tests for two exact third-iterate wedge-of-three S3 certificates."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "core9_prism_wedge_v1", ROOT / "scripts/core9_prism_wedge_v1.py"
)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


class PrismWedgeCertificates(unittest.TestCase):
    def test_full_replay_and_prism_isomorphism(self):
        cert = study.build()
        self.assertEqual(set(cert["graphs"]), {"208409", "248687"})
        self.assertEqual(cert["prism"]["residual_fvector"], [16, 82, 153, 89])
        self.assertEqual(cert["prism"]["removed_tetrahedra"],
                         [20490, 34849, 36929])
        for k, row in cert["graphs"].items():
            self.assertEqual(len(row["deletions"]), study.EXPECTED[k]["deleted"])
            self.assertEqual(len(row["core_vertices"]), 16)
        study.verify(cert)
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "witness.json"
            file.write_text(json.dumps(cert), encoding="utf-8")
            study.verify(json.loads(file.read_text(encoding="utf-8")))

    def test_invalid_open_neighborhood_fold_is_rejected(self):
        cert = study.build()
        row = cert["graphs"]["208409"]
        graph = study.nx.from_graph6_bytes(row["graph6"].encode("ascii"))
        for _ in range(3):
            graph = study.raw_K(graph)
        trace = [dict(x) for x in row["deletions"]]
        trace[0] = dict(trace[0])
        trace[0]["link_folds"] = [x.copy() for x in trace[0]["link_folds"]]
        trace[0]["link_folds"][0][1] = trace[0]["link_folds"][0][0]
        with self.assertRaises(ValueError):
            study.replay_deletions(graph, trace)

    def test_invalid_removed_tetrahedron_is_rejected(self):
        cert = study.build()
        cert["prism"]["removed_tetrahedra"] = [20490, 20490, 36929]
        with self.assertRaises(ValueError):
            study.verify(cert)


if __name__ == "__main__":
    unittest.main()
