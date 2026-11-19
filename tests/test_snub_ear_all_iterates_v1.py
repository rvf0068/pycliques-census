"""Independently test complete-ear K^2 induction invariant and six cores."""
from __future__ import annotations

from itertools import combinations
from pathlib import Path
import random
import sys
import tempfile
import unittest
from unittest.mock import patch

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import snub_ear_all_iterates_v1 as study  # noqa: E402


class ExactTwoStepEarInvariantTests(unittest.TestCase):
    def test_all_three_maximality_branches_have_marked_k2_bridge(self):
        x = nx.path_graph(5)
        cases = (
            ({0}, {4}, 0),
            ({0, 1}, {4}, 1),
            ({0, 1}, {3, 4}, 2),
        )
        for a, b, expected in cases:
            with self.subTest(maximal_sides=expected):
                result = study.verify_marked_ear_two_step(x, a, b)
                self.assertEqual(result["case_maximal_sides"], expected)
                self.assertTrue(result["induced_old_k2"])
                self.assertTrue(result["deleted_bridge_folds_to_old_k2"])
                self.assertTrue(all(result["bridge_link_component_orders"]))

    def test_invalid_complete_ear_hypotheses_fail_closed(self):
        x = nx.cycle_graph(6)
        for a, b in (
            (set(), {3}),
            ({0, 2}, {4}),  # first set is not complete
            ({0, 1}, {1, 4}),  # overlap
            ({0, 1}, {2}),  # forbidden cross edge
            ({0}, {22}),  # not a vertex of X
        ):
            with self.subTest(a=a, b=b):
                with self.assertRaisesRegex(ValueError, "Marked-ear hypotheses"):
                    study.verify_marked_ear_two_step(x, a, b)

    def test_random_small_graphs_complete_two_step_certificate(self):
        rng = random.Random(20261119)
        checked = 0
        case_counts = set()
        extras_counts = set()
        for n in range(4, 9):
            for _ in range(80):
                g = nx.gnp_random_graph(
                    n, rng.uniform(0.17, 0.83),
                    seed=rng.randrange(1_000_000_000),
                )
                if not nx.is_connected(g):
                    continue
                comps = [
                    set(q) for k in (1, 2, 3)
                    for q in combinations(g, k)
                    if all(g.has_edge(a, b) for a, b in combinations(q, 2))
                ]
                opts = [
                    (a, b) for a in comps for b in comps
                    if not a.intersection(b)
                    and all(not g.has_edge(u, v) for u in a for v in b)
                ]
                if not opts:
                    continue
                a, b = rng.choice(opts)
                cert = study.verify_marked_ear_two_step(g, a, b)
                self.assertTrue(cert["induced_old_k2"])
                self.assertTrue(cert["deleted_bridge_folds_to_old_k2"])
                self.assertEqual(
                    cert["new_k2_order"] - cert["old_k2_order"],
                    cert["extra_dominated_vertices"] + 1,
                )
                case_counts.add(cert["case_maximal_sides"])
                extras_counts.add(cert["extra_dominated_vertices"])
                checked += 1
        self.assertGreaterEqual(checked, 100)
        self.assertEqual(case_counts, {0, 1, 2})
        self.assertGreaterEqual(len(extras_counts), 2)

    def test_base_dominated_fold_does_not_invalidate_two_step_invariant(self):
        x = nx.path_graph(6)
        f = x.copy()
        # Vertex 6 is dominated by 2, since its neighbors are 1,2,3.
        f.add_edges_from(((6, 1), (6, 2), (6, 3)))
        previous = study.previous
        folded = previous.verify_dominated_clique_graph_fold(f, 6, 2)
        self.assertTrue(folded["dominated_folds_verified"])
        cert = study.verify_marked_ear_two_step(f, {0}, {5})
        self.assertTrue(cert["deleted_bridge_folds_to_old_k2"])


class AllIterateSnubHomotopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = study.verify_six_all_iterates()

    def test_all_six_are_induced_complete_ears_of_snub(self):
        self.assertEqual(
            [row["core_id"] for row in self.records], list(study.EXPECTED_IDS)
        )
        self.assertEqual(
            [row["original_order10_members"] for row in self.records],
            list(study.EXPECTED_MEMBERS),
        )
        self.assertEqual(sum(r["original_order10_members"] for r in self.records), 710)
        for row in self.records:
            self.assertTrue(row["two_step_induced_and_dismantled_certificate"]
                            ["deleted_bridge_folds_to_old_k2"])
            self.assertTrue(row["not_a_clique_divergence_proof"])
            self.assertIn("For all j>=0", row["relative_all_iterates_homotopy"])

    def test_tampered_older_k7_verifier_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "modified_k7.py"
            bad.write_text("# modified old theorem verifier\n")
            with patch.object(study, "PREVIOUS_SOURCE", bad):
                with self.assertRaisesRegex(ValueError, "modified"):
                    study.verify_six_all_iterates()


if __name__ == "__main__":
    unittest.main()
