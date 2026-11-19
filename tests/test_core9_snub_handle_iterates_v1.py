"""Regression tests for exact finite snub-handle homotopy certificates."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import core9_snub_handle_iterates_v1 as study  # noqa: E402


class SnubHandleIteratesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = study.prepare()
        cls.cert = json.loads(cls.data[f"{study.DEST}/certificates.json"])

    def test_six_exact_finite_records_and_original_members(self):
        self.assertEqual(
            [r["core_id"] for r in self.cert["records"]], list(study.EXPECTED_IDS)
        )
        self.assertEqual(
            [r["original_order10_members"] for r in self.cert["records"]],
            list(study.EXPECTED_MEMBERS)
        )
        self.assertEqual(self.cert["original_ten_graphs_represented"], 710)
        self.assertTrue(self.cert["no_all_iterate_theorem"])
        self.assertTrue(self.cert["no_new_K_divergence_verdicts"])

    def test_all_level_maps_and_contractible_link_witnesses(self):
        for rec in self.cert["records"]:
            self.assertEqual(
                [(level["snub_order"], level["core_order"]) for level in rec["levels"]],
                list(study.EXPECTED_SIZE_PAIRS),
            )
            for n, level in enumerate(rec["levels"]):
                phi = level["snub_to_core_vertex_map"]
                self.assertEqual(len(phi), level["snub_order"])
                self.assertEqual(len(set(phi)), len(phi))
                self.assertEqual(
                    len(level["extra_core_vertices"]),
                    1 if n % 2 == 0 else 2,
                )
                link = level["link_certificate"]
                if n % 2 == 0:
                    self.assertEqual(link["kind"], "two_clique_cone_bridge")
                    self.assertEqual(len(link["components"]), 2)
                    self.assertTrue(all(link["components"]))
                else:
                    self.assertEqual(
                        link["kind"], "adjacent_pair_disjoint_cone_links"
                    )
                    p, q = link["supports"]
                    self.assertTrue(p and q and not set(p) & set(q))
                    for u, side in zip(link["cone_apices"], link["supports"]):
                        self.assertIn(u, side)

    def test_raw_iterate_edge_counts_are_exact(self):
        expected_snub = [(8, 18), (12, 46), (20, 136), (56, 1196)]
        for rec in self.cert["records"]:
            self.assertEqual(
                [(x["snub_order"], x["snub_edges"]) for x in rec["levels"][:4]],
                expected_snub,
            )
            self.assertEqual(rec["levels"][4]["core_edges"] -
                             rec["levels"][4]["snub_edges"],
                             sum(map(len, rec["levels"][4]["link_certificate"]["components"])))

    def test_corrupted_historical_source_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for rel in (study.SOURCE, study.SOURCE_MANIFEST, study.CLASS_INDEX):
                destination = root / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / rel, destination)
            payload = (root / study.SOURCE).read_text(encoding="utf-8")
            (root / study.SOURCE).write_text(
                payload.replace('GQyuzw', 'GQyuzx', 1), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "Frozen original"):
                study.frozen_rows(root)

    def test_attachment_checks_reject_forged_links(self):
        import networkx as nx

        # A connected noncomplete three-vertex link is not the
        # disjoint union of two cliques.
        h = nx.path_graph(3)
        g = h.copy()
        g.add_node(3)
        g.add_edges_from(((3, 0), (3, 1), (3, 2)))
        with self.assertRaisesRegex(ValueError, "disjoint complete link components"):
            study.even_attachment(h, g, [0, 1, 2], 3)

        # Two disconnected old-neighbor sets are insufficient: each
        # must be contractible, as witnessed by a cone apex.
        h = nx.cycle_graph(4)
        g = h.copy()
        g.add_nodes_from([4, 5])
        g.add_edge(4, 5)
        g.add_edges_from([(4, 0), (4, 2), (5, 1), (5, 3)])
        with self.assertRaisesRegex(ValueError, "not a verified cone"):
            study.odd_attachment(h, g, [0, 1, 2, 3], [4, 5])

    def test_embedding_checks_both_edges_and_nonedges(self):
        import networkx as nx

        h = nx.path_graph(3)
        g = nx.complete_graph(3)
        with self.assertRaisesRegex(ValueError, "adjacency matrices disagree"):
            study.verify_small_embedding(h, g, [0, 1, 2])

    def test_convergent_cycle_analogue_has_exact_two_period(self):
        import networkx as nx

        # A persistent +1,+2 vertex difference from a K-fixed base
        # is NOT by itself a proof of K-divergence.
        for n in range(5, 16):
            cycle = nx.cycle_graph(n)
            g = cycle.copy()
            g.add_edges_from([(n, 0), (n, 2)])
            first = study.clique_graph_from_facets(study.facets(g))
            second = study.clique_graph_from_facets(study.facets(first))
            self.assertEqual((len(g), len(first), len(second)), (n + 1, n + 2, n + 1))
            self.assertTrue(nx.is_isomorphic(second, g))
            self.assertTrue(nx.is_isomorphic(
                study.clique_graph_from_facets(study.facets(cycle)), cycle
            ))

    def test_committed_bytes_match_reconstructed_proof(self):
        study.verify()


if __name__ == "__main__":
    unittest.main()
