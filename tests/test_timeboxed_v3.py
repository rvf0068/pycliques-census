"""Fast regression checks for the frozen no-S2 local v3 cohort and runner."""
from __future__ import annotations

from collections import Counter
import importlib
from pathlib import Path
import sys
import tempfile
import unittest

import networkx as nx

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import timeboxed_v3 as runner  # noqa: E402


def gf2_rank(vectors: list[int]) -> int:
    basis = {}
    for value in vectors:
        while value:
            pivot = value.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = value
                break
            value ^= basis[pivot]
    return len(basis)


def b2_mod2(graph: nx.Graph) -> int:
    """Compute H_2 over F2 directly from the triangle/tetrahedron boundaries."""
    vertices = list(graph)
    faces = {2: [], 3: [], 4: []}
    from itertools import combinations

    for cardinality in (2, 3, 4):
        for subset in combinations(vertices, cardinality):
            if all(graph.has_edge(u, v) for u, v in combinations(subset, 2)):
                faces[cardinality].append(subset)
    mapping2 = {f: i for i, f in enumerate(faces[2])}
    mapping3 = {f: i for i, f in enumerate(faces[3])}
    boundary3 = [
        sum(1 << mapping2[face[:i] + face[i+1:]]
            for i in range(3))
        for face in faces[3]
    ]
    boundary4 = [
        sum(1 << mapping3[face[:i] + face[i+1:]]
            for i in range(4))
        for face in faces[4]
    ]
    return len(faces[3]) - gf2_rank(boundary3) - gf2_rank(boundary4)


class LocalV3Tests(unittest.TestCase):
    def test_frozen_cohort_matches_historical_results(self):
        eligible, source = runner.cohort()
        self.assertEqual(len(eligible), 153)
        self.assertTrue(all(i in source for i in eligible))
        labels = {}
        with runner.COHORT.open() as file:
            for row in file:
                if row.startswith("#") or row.startswith("index") or not row.strip():
                    continue
                index, g6, label = row.strip().split("\t")
                self.assertIn(int(index), eligible)
                self.assertEqual(b2_mod2(nx.from_graph6_bytes(g6.encode())), 0)
                labels[int(index)] = label
        self.assertEqual(Counter(labels.values()), Counter({"S1": 115, "S3": 35, "S1+S3": 3}))

    def test_separate_upstream_and_unchanged_v2_provenance(self):
        self.assertEqual(runner.CLIQUE_BOUND, 120)
        self.assertEqual(runner.TIMEOUT_SECONDS, 120)
        self.assertEqual(runner.MEMORY_MIB, 2048)
        self.assertEqual(runner.BATCH_SIZE, 5)
        self.assertEqual(runner.current_v3_pin(),
                         runner.V3_PIN.read_text(encoding="ascii").strip())
        cohort, _ = runner.cohort()
        meta = runner.manifest(cohort)
        self.assertEqual(meta["indices"], sorted(cohort))
        self.assertEqual(meta["parallel_workers"], 1)
        self.assertEqual(meta["historical_upstream_commit"],
                         (runner.ROOT / "config" / "pycliques_commit.txt").read_text().strip())

    def test_positive_worker_classification_has_replayable_chain(self):
        import timeboxed_worker_v3
        with tempfile.TemporaryDirectory() as directory:
            journal = str(Path(directory) / "events.jsonl")
            record = timeboxed_worker_v3.classify("ICvbvy}|g", journal)
        self.assertEqual(record["status"], "CONVERGENT")
        self.assertEqual(record["proof_status"], "verified_chain")
        self.assertEqual(record["proof"]["rule"], "eventually_clique_helly")
        self.assertGreaterEqual(record["peak_rss_kib"], 0)
        self.assertEqual(record["bound"], 120)

    def test_v3_refresh_does_not_touch_historical_file(self):
        original = (runner.ROOT / "indeterminate_order_10.txt").read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            original_root = runner.ROOT
            try:
                # Only redirect the generated file; preexisting snapshot remains input.
                import unittest.mock as mock
                with mock.patch.object(runner, "ROOT", Path(directory)):
                    (Path(directory) / "indeterminate_order_10.txt").write_bytes(original)
                    n = runner.refresh_v3({})
                    self.assertEqual(n, 8648)
                    self.assertTrue((Path(directory) / "indeterminate_order_10_v3.txt").exists())
            finally:
                self.assertEqual(
                    (original_root / "indeterminate_order_10.txt").read_bytes(), original
                )


if __name__ == "__main__":
    unittest.main()
