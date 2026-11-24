"""Mutation and independent finite checks for the ten-v22 proof routines."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import random
import unittest
from unittest.mock import patch

import networkx as nx

from research.order10_p3_reference_lifts_v22 import verify as proof


class PositiveV22CertificateTests(unittest.TestCase):
    def test_original_frozen_manifest_and_exact_20_indices(self) -> None:
        rows = proof.read_rows(proof.V21)
        self.assertEqual(len(rows), 1228)
        self.assertEqual(proof.git_blob(proof.V21.read_bytes()), proof.V21_BLOB)
        promoted = proof.read_rows(proof.V22)
        self.assertEqual(len(promoted), 1208)
        self.assertEqual(set(rows) - set(promoted), set(proof.EXPECTED))
        self.assertTrue(all(rows[i] == promoted[i] for i in promoted))

    def test_retractions_and_adversarial_outside_images(self) -> None:
        saved = json.loads(proof.CERT.read_text(encoding="ascii"))
        for item in saved["certified"]:
            proof.verify_small_retraction(item["index"], item["value"])
            changed = deepcopy(item["value"])
            outside = next(iter(changed["outside_images"]))
            # A projected vertex outside the fixed target violates a
            # complete ordinary retraction's codomain requirement.
            changed["outside_images"][outside] = int(outside)
            with self.assertRaisesRegex(AssertionError, "retraction"):
                proof.verify_small_retraction(item["index"], changed)

    def test_bad_target_bijection_fails(self) -> None:
        saved = json.loads(proof.CERT.read_text(encoding="ascii"))
        item = deepcopy(saved["certified"][0])
        label = item["value"]["target_bijection"]
        first, second = list(label)[:2]
        label[first] = label[second]
        with self.assertRaisesRegex(AssertionError, "isomorphism"):
            proof.verify_small_retraction(item["index"], item["value"])

    def test_f45_source_identity_cannot_be_substituted(self) -> None:
        # The archived independent O9 witness reconstructs an explicitly
        # specified F45. Its proved divergence cannot be silently
        # transferred to an unrelated original nine-vertex graph6.
        with patch.dict(proof.REFERENCES, {208409: "HEhfvx}"}):
            with self.assertRaisesRegex(AssertionError, "not F45"):
                proof.verify_reference_divergence()

    def test_bron_kerbosch_independent_on_small_random_graphs(self) -> None:
        rng = random.Random(20261124)
        for n in range(4, 12):
            for _ in range(12):
                graph = nx.Graph()
                graph.add_nodes_from(range(n))
                probability = rng.uniform(0.15, 0.8)
                graph.add_edges_from(
                    (u, v) for u in range(n) for v in range(u + 1, n)
                    if rng.random() < probability
                )
                self.assertEqual(
                    proof.independent_maximal_cliques(graph),
                    {frozenset(c) for c in nx.find_cliques(graph)},
                )


if __name__ == "__main__":
    unittest.main()
