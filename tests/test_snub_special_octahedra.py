"""Exact snub special-octahedron obstruction tests, no divergence claims."""
from pathlib import Path
import sys
import unittest

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_snub_special_octahedra import (
    EXPECTED, inspect_maximal_cliques, investigate, naive_clique_graph,
)


class SnubSpecialOctahedronTests(unittest.TestCase):
    def test_exact_independent_negative_census_through_k3(self) -> None:
        result = investigate(verify_library=False)
        self.assertEqual(len(result["levels"]), 4)
        self.assertEqual(result["source_graph6"], "GQyuzw")
        self.assertIn("Does not classify", result["interpretation"])
        for row, expected in zip(result["levels"], EXPECTED):
            self.assertTrue(row["special_octahedron_excluded"])
            self.assertEqual(row["maximal_cliques"], expected[3])
            self.assertEqual(row["all_domains_nonempty"], expected[4])
            self.assertEqual(row["pair_incompatible"], expected[5])
            self.assertEqual(row["not_excluded_by_pair_test"], 0)

    def test_positive_octahedron_not_falsely_excluded(self) -> None:
        octahedron = nx.octahedral_graph()
        self.assertFalse(
            inspect_maximal_cliques(octahedron)["special_octahedron_excluded"]
        )

    def test_clique_graph_matches_cycle_example(self) -> None:
        C = nx.cycle_graph(5)
        self.assertTrue(nx.is_isomorphic(C, naive_clique_graph(C)))

    @unittest.skipUnless(
        (ROOT / ".deps/pycliques-project-core9cover-v2/.git").is_dir()
        and (ROOT / ".venv-core9cover-v2/bin/python").exists(),
        "Requires isolated post-PR14 pycliques project pin",
    )
    def test_independent_library_replay(self) -> None:
        full = investigate(verify_library=True)
        self.assertTrue(all(x["special_octahedron_excluded"] for x in full["levels"]))


if __name__ == "__main__":
    unittest.main()
