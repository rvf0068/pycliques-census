"""Adversarial checks of complete fifth-stage growth and O20 witness."""
from __future__ import annotations

import copy
import json
import unittest

import networkx as nx

from .verify import (
    ARCHIVE,
    build_raw,
    check_octahedron,
    digest,
    fourth,
    pare_raw,
)


class FifthStageGrowthProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cert = json.loads(ARCHIVE.read_text(encoding="utf-8"))
        cls.g4 = fourth(cls.cert)
        cls.faces, cls.raw = build_raw(cls.g4)
        cls.kept, cls.pared, cls.deleted = pare_raw(cls.raw)

    def test_exact_p5_order_size_and_shas(self):
        self.assertEqual(len(self.faces), 1977)
        self.assertEqual(len(self.deleted), 81)
        self.assertEqual(len(self.kept), 1896)
        self.assertEqual(
            digest(self.raw),
            self.cert["raw_K5"]["little_endian_adjacency_sha256"],
        )
        self.assertEqual(
            digest(self.pared),
            self.cert["one_round_pared"]["little_endian_adjacency_sha256"],
        )

    def test_o20_induced_and_dominating_but_forced_images_conflict(self):
        witness = self.cert["witness"]
        m, forced = check_octahedron(
            self.pared, witness["antipodal_pairs"]
        )
        self.assertEqual(m, 194777)
        self.assertEqual(len(forced), 210)
        x, y = witness["forced_conflict"]["host_edge"]
        a, b = witness["forced_conflict"]["forced_target_images"]
        self.assertEqual((forced[x], forced[y]), (a, b))
        self.assertTrue(self.pared[x] & (1 << y))
        self.assertIn([b, a], [
            [pair[1], pair[0]]
            for pair in witness["antipodal_pairs"]
        ])

    def test_reject_substituted_historical_certificate_blob(self):
        forged = copy.deepcopy(self.cert)
        forged["previous_proof_git_blob"] = "0" * 40
        with self.assertRaisesRegex(AssertionError, "source substitution"):
            fourth(forged)

    def test_reject_invalid_o20_target(self):
        corrupted = copy.deepcopy(
            self.cert["witness"]["antipodal_pairs"]
        )
        corrupted[1][0] = corrupted[0][0]
        with self.assertRaisesRegex(AssertionError, "Invalid O_d target"):
            check_octahedron(self.pared, corrupted)

    def test_positive_o3_retracts_to_itself_so_no_false_conflict(self):
        o3 = nx.complement(nx.Graph([(0, 1), (2, 3), (4, 5)]))
        o3.add_nodes_from(range(6))
        rows = [sum(1 << v for v in o3[u]) for u in range(6)]
        edges, forced = check_octahedron(
            rows, [[0, 1], [2, 3], [4, 5]]
        )
        self.assertEqual(edges, 3)
        self.assertEqual(forced, {})


if __name__ == "__main__":
    unittest.main()
