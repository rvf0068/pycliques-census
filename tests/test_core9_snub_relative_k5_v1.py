"""Independent finite witnesses and hypotheses for the relative K5 theorem."""
from __future__ import annotations

from itertools import combinations
from pathlib import Path
import sys
import unittest

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import core9_snub_relative_k5_v1 as study  # noqa: E402


class FifthIterateTests(unittest.TestCase):
    def test_all_six_strict_extension_witnesses_without_k5(self):
        result = study.verify()
        self.assertEqual([x["core_id"] for x in result], list(study.EXPECTED_WITNESSES))
        self.assertEqual(sum(x["original_order10_members"] for x in result), 710)
        for row in result:
            self.assertEqual(row["exact_relative_K5_added_vertices"], 2)
            self.assertTrue(all(x > 0 for x in row["attachment_component_orders"]))
            self.assertEqual(
                tuple(zip(
                    row["attachment_component_orders"],
                    row["strict_extension_vertices"],
                )),
                study.EXPECTED_WITNESSES[row["core_id"]],
            )

    def test_invalid_bipartition_or_maximal_attachment_rejected(self):
        # Clique intersection graph is a path 0--1--2--3.
        f = [
            frozenset({0}), frozenset({0, 1}),
            frozenset({1, 2}), frozenset({2}),
        ]
        self.assertEqual(
            study.verify_nonmaximal_components(f, [[0], [3]]),
            ((1, 1), (1, 2)),
        )
        with self.assertRaisesRegex(ValueError, "graph-disjoint"):
            study.verify_nonmaximal_components(f, [[0], [1]])
        with self.assertRaisesRegex(ValueError, "two nonempty"):
            study.verify_nonmaximal_components(f, [[0], []])
        with self.assertRaisesRegex(ValueError, "overlapping"):
            study.verify_nonmaximal_components(f, [[0], [0]])
        # A facet that is a maximal clique (unextendable by any
        # other vertex) makes the two-new-vertices conclusion invalid.
        f2 = [
            frozenset({0}), frozenset({0, 1}),
            frozenset({1}), frozenset({2}),
        ]
        with self.assertRaisesRegex(ValueError, "may be a maximal clique"):
            study.verify_nonmaximal_components(f2, [[0, 1], [3]])

    def test_general_two_clique_extension_formula_on_small_graphs(self):
        # Independently check the structural lemma on connected X with
        # nontrivial A and B, not just on the saved snub examples.
        x = nx.Graph()
        x.add_edges_from(
            combinations((0, 1, 2), 2)
        )
        x.add_edges_from(
            combinations((5, 6, 7), 2)
        )
        x.add_edges_from([(2, 3), (3, 4), (4, 5)])
        a, b = {0, 1}, {6, 7}
        self.assertTrue(nx.is_connected(x))
        self.assertFalse(any(x.has_edge(u, v) for u in a for v in b))
        old = {frozenset(q) for q in nx.find_cliques(x)}
        self.assertTrue(any(a < q for q in old))
        self.assertTrue(any(b < q for q in old))
        y = x.copy()
        y.add_edges_from((8, i) for i in a | b)
        new = {frozenset(q) for q in nx.find_cliques(y)}
        self.assertEqual(
            new,
            old | {frozenset(a | {8}), frozenset(b | {8})},
        )
        p = {q for q in old if q & a}
        q = {facet for facet in old if facet & b}
        self.assertTrue(p and q and not p & q)
        # The maximal old clique containing A (resp. B) is a cone
        # apex for the corresponding new-vertex support in K(X).
        for support, side in ((p, a), (q, b)):
            witness = next(facet for facet in old if side < facet)
            self.assertTrue(all(facet & witness for facet in support))

    def test_maximal_component_hypothesis_is_essential(self):
        x = nx.path_graph(6)
        a, b = {0, 1}, {4, 5}  # Both are maximal cliques of X.
        y = x.copy()
        y.add_edges_from((6, v) for v in a | b)
        old_count = len(list(nx.find_cliques(x)))
        new_count = len(list(nx.find_cliques(y)))
        self.assertEqual(new_count, old_count)
        self.assertNotEqual(new_count, old_count + 2)


if __name__ == "__main__":
    unittest.main()
