"""Independent graph6 / first-K octahedron divergence certificate tests."""
from __future__ import annotations

import itertools
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import first_clique_octahedron_retract_v1 as stage  # noqa: E402


class FirstCliqueOctahedronTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.stats = stage.investigate()
        cls.output = stage.generate()

    def test_exact_positive_source_and_unbounded_octahedron_target(self):
        self.assertEqual(len(self.rows), 1)
        row = self.rows[0]
        self.assertEqual(row["original_index"], 11634099)
        self.assertEqual(row["original_graph6"], "IEjer^{lo")
        self.assertEqual(row["clique_graph_order"], 17)
        self.assertEqual(row["clique_graph_edges"], 87)
        self.assertEqual(tuple(row["target_O3_vertices"]), stage.EXPECTED_TARGET)
        self.assertEqual(tuple(row["retraction"]), stage.EXPECTED_MAP)
        self.assertEqual(self.stats["positive_induced_O3_retractions"], 1)
        self.assertEqual(self.stats["csp_limit_reached"], 0)
        stage.verify_oct_divergence()

    def test_each_of_seventeen_source_facets_and_exact_projection(self):
        row = self.rows[0]
        G = nx.from_graph6_bytes(row["original_graph6"].encode("ascii"))
        facets = sorted(
            (frozenset(q) for q in nx.find_cliques(G)),
            key=lambda q: sum(1 << v for v in q),
        )
        self.assertEqual(
            [sorted(q) for q in facets], row["full_source_facets"]
        )
        H = nx.Graph()
        H.add_nodes_from(range(len(facets)))
        H.add_edges_from(
            (i, j) for i, j in itertools.combinations(H, 2)
            if facets[i].intersection(facets[j])
        )
        T = row["target_O3_vertices"]
        self.assertEqual(
            sorted((u, v) for u, v in itertools.combinations(T, 2)
                   if not H.has_edge(u, v)),
            [(1, 15), (5, 10), (9, 14)],
        )
        self.assertTrue(nx.is_isomorphic(
            H.subgraph(T), nx.complete_multipartite_graph(2, 2, 2)
        ))
        projection = row["retraction"]
        self.assertEqual([projection[t] for t in T], T)
        for u, v in H.edges():
            self.assertTrue(
                projection[u] == projection[v]
                or H.has_edge(projection[u], projection[v]),
                (u, v),
            )
        self.assertFalse(any(
            u != v and (set(G[u]) | {u}) <= (set(G[v]) | {v})
            for u in G for v in G
        ))

    def test_forged_target_or_morphism_is_rejected(self):
        row = self.rows[0]
        K, _ = stage.raw_clique_graph(nx.from_graph6_bytes(
            row["original_graph6"].encode("ascii")
        ))
        target = tuple(row["target_O3_vertices"])
        projection = tuple(row["retraction"])
        stage.verify_oct_retraction(K, target, projection)
        with self.assertRaises(ValueError):
            stage.verify_oct_retraction(K, (0, 1, 2, 3, 4, 5), projection)
        bad = list(projection)
        outside = next(v for v in K if v not in target)
        forbidden = next(
            w for w in target
            if any(
                w != projection[u] and not K.has_edge(w, projection[u])
                for u in K[outside]
            )
        )
        bad[outside] = forbidden
        with self.assertRaises(ValueError):
            stage.verify_oct_retraction(K, target, tuple(bad))

    def test_exact_v6_population_and_unchanged_survivors(self):
        old = [
            line for line in (ROOT / "indeterminate_order_10_v5.txt").read_text().splitlines()
            if line and not line.startswith("#")
        ]
        new = [
            line for line in self.output[stage.NEW_LIST].decode().splitlines()
            if line and not line.startswith("#")
        ]
        self.assertEqual(len(old), 8224)
        self.assertEqual(len(new), 8223)
        self.assertEqual(
            [line for line in old if int(line.split()[0]) != 11634099],
            new,
        )

    def test_mutating_the_historical_v5_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for source in (
                "indeterminate_order_10_v5.txt",
                "scripts/direct_divergent_ninecore_retracts_v1.py",
            ):
                dst = root / source
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / source, dst)
            v5 = root / "indeterminate_order_10_v5.txt"
            v5.write_bytes(v5.read_bytes().replace(
                b"11634099 10", b"11634098 10", 1
            ))
            with self.assertRaisesRegex(ValueError, "v5 unresolved"):
                stage.frozen_sources(root)

    def test_committed_versioned_artifacts_are_byte_reproducible(self):
        stage.verify()


if __name__ == "__main__":
    unittest.main()
