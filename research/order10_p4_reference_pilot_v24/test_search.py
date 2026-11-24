"""Regressions for bounded v24 reference transfers and complete positive maps."""
from __future__ import annotations

import unittest

import networkx as nx

from .search import (
    REFERENCE_DIMENSIONS, REFERENCE_G6,
    exact_isomorphism, fourth, inspect, plan, representatives, verify_map,
)


class ReferencePilotTests(unittest.TestCase):
    def test_522_surviving_certified_p3_representatives(self):
        cases = representatives()
        self.assertEqual(len(cases), 522)
        self.assertEqual(
            [i for i, _ in cases],
            sorted(i for i, _ in cases),
        )

    def test_all_five_reference_shapes(self):
        for index, g6 in REFERENCE_G6.items():
            with self.subTest(reference=index):
                _, _, host = fourth(g6)
                self.assertEqual(
                    (len(host), host.number_of_edges()),
                    REFERENCE_DIMENSIONS[index],
                )

    def test_previously_certified_v24_positive_is_rediscovered(self):
        # Known proof deliberately outside the current v24 indeterminate list.
        case = inspect(11495390, "ICvbvZs{g", 41, 55)
        self.assertEqual(case["status"], "EXACT_MATCH")
        self.assertIn(10223405, [
            proof["reference"] for proof in case["positives"]
        ])

    def test_unchanged_negative_dimensions_are_not_verdicts(self):
        case = inspect(11625997, "IEjbvjyz_", 41, 55)
        self.assertEqual(case["status"], "NO_REFERENCE_DIMENSION_MATCH")
        self.assertEqual(case["p4"], [184, 14597])

    def test_bijection_checks_reject_noninjective_or_wrong_map(self):
        graph = nx.path_graph(6)
        with self.assertRaises(AssertionError):
            verify_map(graph, graph, [0, 1, 1, 3, 4, 5])
        with self.assertRaises(AssertionError):
            verify_map(graph, graph, [1, 0, 2, 3, 4, 5])
        self.assertEqual(
            exact_isomorphism(graph, graph),
            list(range(6)),
        )


if __name__ == "__main__":
    unittest.main()
