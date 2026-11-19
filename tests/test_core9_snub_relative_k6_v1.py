"""Independent tests of the cone-bridge clique theorem and snub K6 transfer."""
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
import core9_snub_relative_k6_v1 as study  # noqa: E402


class ConeBridgeLemmaTests(unittest.TestCase):
    def test_both_side_families_can_create_extra_cliques(self):
        z = nx.path_graph(3)
        result = study.verify_general_cone_bridge(z, {0}, {2})
        self.assertEqual(result["extra_side_cliques"], 2)
        self.assertEqual(result["new_cliques"] - result["old_cliques"], 3)
        self.assertEqual(result["clique_component_orders"], (1, 1))
        self.assertTrue(result["bridge_deleted_folds_to_old"])
        self.assertTrue(result["old_graph_induced"])

    def test_maximal_side_cliques_give_fewer_extras(self):
        z = nx.path_graph(5)
        # {1,2} is a maximal clique, while {4} is not.
        result = study.verify_general_cone_bridge(z, {1, 2}, {4})
        self.assertEqual(result["extra_side_cliques"], 1)
        self.assertEqual(result["new_cliques"] - result["old_cliques"], 2)

    def test_nonsingleton_cone_support_is_allowed(self):
        z = nx.Graph()
        z.add_nodes_from(range(7))
        z.add_edges_from([
            (0, 1), (1, 2), (1, 3), (2, 4),
            (3, 4), (4, 5), (5, 6),
        ])
        # Induced P is a 4-vertex cone, but not a complete graph.
        p, q = {0, 1, 2, 3}, {5, 6}
        self.assertTrue(study.is_cone(z, p))
        result = study.verify_general_cone_bridge(z, p, q)
        self.assertTrue(result["bridge_deleted_folds_to_old"])

    def test_invalid_hypotheses_are_rejected(self):
        z = nx.cycle_graph(6)
        for p, q in [
            (set(), {4}),
            ({0, 2, 4}, {5}),  # no universal vertex
            ({0, 1}, {1, 2}),  # overlapping supports
            ({0}, {9}),       # unknown vertex
        ]:
            with self.subTest(p=p, q=q):
                with self.assertRaisesRegex(ValueError, "Cone-bridge hypotheses"):
                    study.verify_general_cone_bridge(z, p, q)
        disconnected = nx.empty_graph(5)
        with self.assertRaisesRegex(ValueError, "Cone-bridge hypotheses"):
            study.verify_general_cone_bridge(disconnected, {0}, {1})

    def test_reproducible_random_nonflag_general_examples(self):
        rng = random.Random(20261119)
        checked = 0
        extras_hist = set()
        for n in range(4, 9):
            for _ in range(48):
                g = nx.gnp_random_graph(
                    n, rng.uniform(0.22, 0.85),
                    seed=rng.randrange(1_000_000_000),
                )
                if not nx.is_connected(g):
                    continue
                supports = [
                    set(vertices)
                    for k in range(1, 4)
                    for vertices in combinations(g, k)
                    if study.is_cone(g, set(vertices))
                ]
                options = [
                    (p, q) for p in supports for q in supports
                    if not p.intersection(q)
                ]
                if not options:
                    continue
                p, q = rng.choice(options)
                result = study.verify_general_cone_bridge(g, p, q)
                self.assertEqual(
                    result["new_cliques"] - result["old_cliques"],
                    1 + result["extra_side_cliques"],
                )
                self.assertEqual(
                    result["extra_side_cliques"], result["domination_count"]
                )
                self.assertTrue(result["old_graph_induced"])
                extras_hist.add(result["extra_side_cliques"])
                checked += 1
        self.assertGreaterEqual(checked, 80)
        self.assertGreaterEqual(len(extras_hist), 2)


class RelativeK6SnubTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = study.verify_six_symbolic_applications()

    def test_six_proven_order10_cohorts_and_no_divergence_claim(self):
        self.assertEqual(
            tuple(row["core_id"] for row in self.results),
            study.EXPECTED_IDS,
        )
        self.assertEqual(sum(row["original_order10_members"]
                             for row in self.results), 710)
        for row in self.results:
            self.assertTrue(row["k5_old_supports_are_disjoint_nonempty_cones"])
            self.assertTrue(row["k6_bridge_deleted_dismantles_to_snub_k6"])
            self.assertTrue(row["k6_old_graph_induced"])
            self.assertTrue(row["k6_bridge_link_two_anticomplete_cliques"])
            self.assertTrue(row["no_divergence_certificate"])
            self.assertEqual(row["k6_order_difference_lower_bound"], 1)
        self.assertEqual(
            sum(row["k6_order_difference_upper_bound"] == 3
                for row in self.results),
            3,
        )

    def test_prior_certificate_code_is_immutably_authenticated(self):
        with tempfile.TemporaryDirectory() as temp:
            changed = Path(temp) / "untrusted.py"
            changed.write_text("# counterfeit old certificate verifier\n")
            with patch.object(study, "PREVIOUS_SOURCE", changed):
                with self.assertRaisesRegex(ValueError, "modified"):
                    study.verify_six_symbolic_applications()
            with patch.object(study, "PREVIOUS_K4_HELPER", changed):
                with self.assertRaisesRegex(ValueError, "modified"):
                    study.verify_six_symbolic_applications()


if __name__ == "__main__":
    unittest.main()
