"""Regression tests for exact HCZTf early-iterate target-retraction exclusions."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "hcztf_retraction_screen_v1", ROOT / "scripts/hcztf_retraction_screen_v1.py"
)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


class EarlySphereRetractionTests(unittest.TestCase):
    def test_exhaustive_induced_targets_and_local_obstructions(self):
        result = study.run()
        self.assertEqual(len(result["cases"]), 10)
        self.assertEqual(
            sum(c["induced_target_sets"] for c in result["cases"]), 140
        )
        for (_, spec, expected), row in zip(study.EXPECTED, result["cases"]):
            self.assertEqual(row["target"], spec)
            self.assertEqual(row["induced_target_sets"], expected)
            self.assertEqual(row["failed_local_condition"], expected)
        study.verify(result)

    def test_changed_certificate_is_rejected(self):
        record = study.run()
        tampered = copy.deepcopy(record)
        tampered["cases"][0]["witnesses"][0]["outside"] = -1
        with self.assertRaises(ValueError):
            study.verify(tampered)

    def test_initial_sphere_is_nonisomorphic_to_divergent_reference(self):
        graph = study.decode(study.SOURCE_GRAPH6)
        known_divergent = study.decode("HEher^{")
        self.assertFalse(study.nx.is_isomorphic(graph, known_divergent))


if __name__ == "__main__":
    unittest.main()
