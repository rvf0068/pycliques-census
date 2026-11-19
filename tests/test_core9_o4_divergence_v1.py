"""Exact K^3 -> O4 positive and exhaustive-O4 negative replay tests."""
from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "core9_o4_divergence_v1", ROOT / "scripts/core9_o4_divergence_v1.py"
)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


class Order9O4RetractionTests(unittest.TestCase):
    def test_positive_complete_ordinary_retraction(self):
        row = study.positive_second_graph()
        self.assertEqual(row["source_vertices"], 60)
        self.assertEqual(row["source_edges"], 1225)
        self.assertEqual(len(row["retraction"]), 60)
        self.assertEqual(len(row["target_missing_pairs"]), 4)

    def test_mutated_positive_map_rejected(self):
        graph = study.third_iterate(study.GRAPHS["248687"])
        broken = list(study.PROJECTION)
        broken[study.TARGET[0]] = study.TARGET[1]
        with self.assertRaises(ValueError):
            study.verify_retraction(graph, study.TARGET, tuple(broken))

    def test_exhaustive_induced_o4_negative_peer(self):
        self.assertEqual(study.negative_first_graph(), study.EXPECTED_NEGATIVE)

    def test_oct_doubling_identity(self):
        O4 = study.nx.complete_multipartite_graph(2, 2, 2, 2)
        O8 = study.nx.complete_multipartite_graph(*([2] * 8))
        self.assertTrue(study.nx.is_isomorphic(study.raw_K(O4), O8))


if __name__ == "__main__":
    unittest.main()
