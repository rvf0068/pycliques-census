"""Independent calibration and exact third-iterate GF(2) ranks."""
import importlib.util
from pathlib import Path
import sys
import unittest

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "core9_third_homology_v1", ROOT / "scripts/core9_third_homology_v1.py"
)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


class ThirdIterateHomologyTests(unittest.TestCase):
    def test_calibration_on_octasphere_and_simplex(self):
        self.assertEqual(
            study.homology_through_three(nx.complete_multipartite_graph(2, 2, 2))
            ["betti"], [1, 0, 1, 0],
        )
        self.assertEqual(
            study.homology_through_three(nx.complete_multipartite_graph(2, 2, 2, 2))
            ["betti"], [1, 0, 0, 1],
        )
        self.assertEqual(
            study.homology_through_three(nx.complete_graph(4))["betti"],
            [1, 0, 0, 0],
        )

    def test_all_exact_rank_certificates(self):
        results = study.run()
        self.assertEqual(set(results), {"208409", "248687"})
        for index, record in results.items():
            for key in ("faces", "ranks", "betti"):
                self.assertEqual(record[key], study.EXPECTED[index][key])
            self.assertEqual(record["betti"], [1, 0, 0, 3])


if __name__ == "__main__":
    unittest.main()
