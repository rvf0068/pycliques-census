"""Positive/negative controls for the complete finite octahedral proof."""
from __future__ import annotations

import copy
import json
import unittest

import networkx as nx

from .verify import (
    ARCHIVE, EXPECTED_COUNTS, neighborhood_masks, reconstruct,
    reconstruct_all, screen_target, verify_earlier_stages, verify_result,
)


class CompleteOctahedralObstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cert = json.loads(ARCHIVE.read_text(encoding="utf-8"))
        cls.host = reconstruct(cls.cert)
        cls.edges, cls.nonedges = neighborhood_masks(cls.host)

    def test_prior_pared_iterates_have_no_octahedral_retractions(self):
        stages = reconstruct_all(self.cert)
        self.assertEqual(
            [(len(g), g.number_of_edges()) for g in stages],
            [tuple(item) for item in self.cert["completely_pared_orders_edges"]],
        )
        verify_earlier_stages(self.cert, stages[:4])

    def test_reject_earlier_stage_certificate_mutation(self):
        mutated = copy.deepcopy(self.cert)
        mutated["earlier_stages"]["P3"]["propagated_contradiction_O3"] -= 1
        stages = reconstruct_all(self.cert)
        with self.assertRaisesRegex(AssertionError, "P3 proof metadata"):
            verify_earlier_stages(mutated, stages[:4])

    def test_positive_control_o3_can_retract_onto_itself(self):
        # Its complement is exactly three independent edges.
        h = nx.Graph()
        h.add_nodes_from(range(6))
        h.add_edges_from(((0, 1), (2, 3), (4, 5)))
        octahedron = nx.complement(h)
        edge_masks, nonedge_masks = neighborhood_masks(octahedron)
        self.assertEqual(
            screen_target(
                edge_masks, nonedge_masks,
                ((0, 1), (2, 3), (4, 5))
            ), "survives",
        )

    def test_o3_direct_fixed_image_contradiction(self):
        self.assertEqual(
            screen_target(
                self.edges, self.nonedges,
                ((1, 26), (2, 65), (14, 54)),
            ),
            "direct_contradiction",
        )

    def test_o4_requires_sound_propagation(self):
        self.assertEqual(
            screen_target(
                self.edges, self.nonedges,
                ((0, 65), (1, 26), (6, 48), (10, 30)),
            ),
            "propagated_contradiction",
        )

    def test_o5_requires_sound_propagation(self):
        self.assertEqual(
            screen_target(
                self.edges, self.nonedges,
                ((0, 69), (2, 41), (18, 56), (27, 43), (35, 62)),
            ),
            "propagated_contradiction",
        )

    def test_verify_rejects_false_global_negative_certificate(self):
        fake = copy.deepcopy(self.cert)
        fake["counts"]["O4"]["survives"] = 1
        observed = {
            "induced_O1": self.cert["induced_O1"],
            "induced_O2": self.cert["induced_O2"],
            "counts": self.cert["counts"],
        }
        with self.assertRaisesRegex(AssertionError, "disagrees"):
            verify_result(fake, observed)

    def test_all_dimensions_and_unbounded_end_of_enumeration_pinned(self):
        self.assertEqual(
            EXPECTED_COUNTS,
            {d: tuple(self.cert["counts"][f"O{d}"][key]
                      for key in (
                          "induced", "dominating", "initial_empty",
                          "direct_contradiction",
                          "propagated_contradiction", "survives",
                      )) for d in range(3, 9)},
        )
        self.assertEqual(self.cert["counts"]["O8"]["induced"], 0)


if __name__ == "__main__":
    unittest.main()
