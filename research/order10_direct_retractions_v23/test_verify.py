"""Mutation tests for the 149 certified ten-v23 direct retractions."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from .verify import (
    CERT, CURRENT, V22, V23, BY_REFERENCE,
    check_witness, git_blob, rows, verify_archive,
)


class DirectRetractionsV23Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads(CERT.read_text(encoding="utf-8"))
        cls.old = rows(V22)
        cls.new = rows(V23)

    def test_exact_index_delta_and_reference_counts(self):
        self.assertEqual((len(self.old), len(self.new)), (1208, 1059))
        self.assertEqual(CURRENT.read_bytes(), V23.read_bytes())
        self.assertEqual(len(set(self.old) - set(self.new)), 149)
        self.assertEqual([w["original_index"] for w in self.archive["witnesses"]],
                         sorted(set(self.old) - set(self.new)))
        self.assertEqual(sum(BY_REFERENCE.values()), 149)
        self.assertEqual(git_blob(V22.read_bytes()),
                         self.archive["source_v22_git_blob"])

    def test_every_saved_projection_independently(self):
        verify_archive(replay_sources=False)

    def test_reject_bad_reference_permutation(self):
        witness = copy.deepcopy(self.archive["witnesses"][0])
        witness["target_bijection"][0] = witness["target_bijection"][1]
        with self.assertRaises(AssertionError):
            check_witness(witness, self.old[witness["original_index"]])

    def test_reject_nonadjacent_projection(self):
        witness = copy.deepcopy(self.archive["witnesses"][0])
        # Search a forbidden projection image, not simply a different label:
        # this guards against falsely treating any image as a retraction.
        from networkx import from_graph6_bytes
        graph = from_graph6_bytes(witness["original_graph6"].encode("ascii"))
        u = witness["deleted_vertex"]
        keep = witness["target_vertices"]
        for candidate in keep:
            if any(graph.has_edge(u, w) and candidate != w
                   and not graph.has_edge(candidate, w) for w in keep):
                witness["image"] = candidate
                break
        else:
            self.skipTest("First certificate admits all possible images")
        with self.assertRaises(AssertionError):
            check_witness(witness, self.old[witness["original_index"]])

    def test_reject_graph_identity_substitution(self):
        witness = copy.deepcopy(self.archive["witnesses"][0])
        witness["original_graph6"] = "I?betrfZo"
        with self.assertRaises(AssertionError):
            check_witness(witness, self.old[witness["original_index"]])


if __name__ == "__main__":
    unittest.main()
