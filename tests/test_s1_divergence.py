"""Certify the order-10 S^1 divergence search, including IEjdnpy^O."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "postpasses"))

from s1_divergence import (
    verify_witness,
    scan,
)


class DivergenceSearchTests(unittest.TestCase):
    def test_bounded_negative_does_not_become_a_divergence_proof(self):
        graph = nx.cycle_graph(5)
        # No simulated miss may classify a graph as divergent.
        class FakeStatus:
            name = "LIMIT_REACHED"

        class FakeResult:
            status = FakeStatus()
            certificate = None
            cover_classes_total = 2
            cover_classes_checked = 1
            cover_candidates_checked = 1
            morphism_states = 0
            morphism_assignments = 0
            cover_classes_complete = False
            morphisms_complete = False
            configured_source_parameters = ((2, 0),)
            limits = (("max_cover_classes", 1),)
            reasons = ("limit reached",)

        with patch("s1_divergence.search_covering_divergence", return_value=FakeResult()):
            result = scan(graph)
        self.assertEqual(result["status"], "INDETERMINATE")
        self.assertIsNone(result["witness"])
        self.assertEqual(result["cover_search"]["status"], "LIMIT_REACHED")

    def test_known_ie_example_recovers_replayable_divergence_certificate(self):
        graph = nx.from_graph6_bytes(b"IEjdnpy^O")
        result = scan(graph)
        self.assertEqual(result["status"], "DIVERGENT")
        self.assertEqual(result["rule"], "triangular_cover_pair")
        self.assertEqual(result["witness"]["kind"], "triangular_cover_pair")
        self.assertTrue(verify_witness(graph, result["witness"]))

        tampered = dict(result["witness"])
        changed = [list(edge) for edge in tampered["voltages"]]
        changed[0][2] ^= 1
        tampered["voltages"] = changed
        self.assertFalse(verify_witness(graph, tampered))


if __name__ == "__main__":
    unittest.main()
