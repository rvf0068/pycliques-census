"""Exact clique enumeration and adversarial tests for seventh relative iterate."""
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
import core9_snub_relative_k7_v1 as study  # noqa: E402


class CliqueFoldPreservationTests(unittest.TestCase):
    def test_path_and_star_dominated_folds(self):
        g = nx.path_graph(3)
        r = study.verify_dominated_clique_graph_fold(g, 0, 1)
        self.assertTrue(r["dominated_folds_verified"])
        self.assertEqual(r["extra_dominated_cliques"], 1)
        star = nx.star_graph(5)
        for leaf in range(1, 6):
            r = study.verify_dominated_clique_graph_fold(star, leaf, 0)
            self.assertTrue(r["induced_embedding"])

    def test_reject_false_dominating_map(self):
        g = nx.cycle_graph(5)
        with self.assertRaisesRegex(ValueError, "not dominated"):
            study.verify_dominated_clique_graph_fold(g, 0, 1)
        with self.assertRaisesRegex(ValueError, "not dominated"):
            study.verify_dominated_clique_graph_fold(g, 0, 0)

    def test_many_random_certified_domination_cases(self):
        rng = random.Random(20261120)
        cases = 0
        for n in range(3, 10):
            for _ in range(60):
                g = nx.gnp_random_graph(
                    n, rng.uniform(0.12, 0.9),
                    seed=rng.randrange(1_000_000_000),
                )
                for v in g:
                    for u in g:
                        if v == u or not (
                            set(g[v]) | {v}
                        ) <= (set(g[u]) | {u}):
                            continue
                        result = study.verify_dominated_clique_graph_fold(g, v, u)
                        self.assertTrue(result["induced_embedding"])
                        self.assertTrue(result["dominated_folds_verified"])
                        self.assertEqual(
                            result["full_cliques"] - result["folded_old_cliques"],
                            result["extra_dominated_cliques"],
                        )
                        cases += 1
        self.assertGreaterEqual(cases, 100)


class TwoCompleteComponentEarTests(unittest.TestCase):
    def test_all_three_maximality_cases(self):
        base = nx.path_graph(5)
        targets = (
            ({0}, {4}, "two-new-cone-bridge", 2),
            ({0, 1}, {4}, "one-new-two-component-link", 1),
            ({0, 1}, {3, 4}, "new-private-edge", 0),
        )
        for a, b, tag, extra in targets:
            with self.subTest(case=tag):
                result = study.verify_two_component_ear_after_K(base, a, b)
                self.assertEqual(result["case"], tag)
                self.assertEqual(result["added_clique_vertices"], extra)
                self.assertIn("wedge S1", result["homotopy"])

    def test_invalid_attachment_rejected(self):
        base = nx.cycle_graph(5)
        invalid = (
            (set(), {2}),
            ({0, 1}, {1, 3}),
            ({0, 2}, {4}),  # noncomplete attachment part
            ({0, 1}, {2}),  # cross-edge 1-2
        )
        for a, b in invalid:
            with self.subTest(a=a, b=b):
                with self.assertRaisesRegex(ValueError, "Ear hypotheses"):
                    study.verify_two_component_ear_after_K(base, a, b)

    def test_reproducible_random_exact_maximal_clique_decompositions(self):
        rng = random.Random(20261120)
        seen = set()
        count = 0
        for n in range(4, 9):
            for _ in range(80):
                g = nx.gnp_random_graph(
                    n, rng.uniform(0.2, 0.75),
                    seed=rng.randrange(1_000_000_000),
                )
                if not nx.is_connected(g):
                    continue
                choices = [
                    set(a) for k in (1, 2, 3)
                    for a in combinations(g, k)
                    if study.complete(g, set(a))
                ]
                pairs = [
                    (a, b) for a in choices for b in choices
                    if not a.intersection(b) and all(
                        not g.has_edge(i, j) for i in a for j in b
                    )
                ]
                if not pairs:
                    continue
                a, b = rng.choice(pairs)
                result = study.verify_two_component_ear_after_K(g, a, b)
                self.assertIn(result["added_clique_vertices"], {0, 1, 2})
                self.assertEqual(
                    result["new_cliques"] - result["old_cliques"],
                    result["added_clique_vertices"],
                )
                seen.add(result["case"])
                count += 1
        self.assertGreaterEqual(count, 100)
        self.assertIn("two-new-cone-bridge", seen)
        self.assertIn("one-new-two-component-link", seen)


class SeventhRelativeHomotopyTests(unittest.TestCase):
    def test_six_exact_certified_core_applications(self):
        result = study.verify_six_symbolic_applications()
        self.assertEqual(tuple(x["core_id"] for x in result), study.EXPECTED_IDS)
        self.assertEqual(sum(x["original_order10_members"] for x in result), 710)
        for x in result:
            self.assertTrue(x["numeric_K7_order_uncomputed"])
            self.assertTrue(x["no_K_divergence_verdict"])
            self.assertIn("wedge S1", x["relative_K7_homotopy"])

    def test_tampering_with_merged_k6_verifier_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            forged = Path(temp) / "forged_k6.py"
            forged.write_text("# forged source\n", encoding="utf-8")
            with patch.object(study, "PREVIOUS_SOURCE", forged):
                with self.assertRaisesRegex(ValueError, "modified"):
                    study.verify_six_symbolic_applications()


if __name__ == "__main__":
    unittest.main()
