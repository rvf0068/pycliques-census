"""Independent replay and adversarial tests for the raw third-iterate O6 proof."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import core9_252075_o6_divergence_v1 as proof


def independent_maximal_cliques(graph: nx.Graph) -> list[int]:
    """A bitset Bron--Kerbosch algorithm, independent of nx.find_cliques."""
    n = len(graph)
    if set(graph) != set(range(n)):
        raise ValueError("Expected consecutive integer labels")
    neighbors = [
        sum(1 << j for j in graph[i]) for i in range(n)
    ]
    maximal = []

    def recurse(selected: int, candidates: int, excluded: int) -> None:
        if not candidates and not excluded:
            maximal.append(selected)
            return
        remaining = candidates | excluded
        pivot = max(
            (v for v in range(n) if remaining & (1 << v)),
            key=lambda v: (candidates & neighbors[v]).bit_count(),
            default=None,
        )
        choices = (
            candidates & ~neighbors[pivot]
            if pivot is not None else candidates
        )
        while choices:
            low = choices & -choices
            vertex = low.bit_length() - 1
            recurse(
                selected | low,
                candidates & neighbors[vertex],
                excluded & neighbors[vertex],
            )
            candidates &= ~low
            excluded |= low
            choices &= ~low

    recurse(0, (1 << n) - 1, 0)
    return sorted(maximal)


def independent_raw_k(graph: nx.Graph) -> nx.Graph:
    cliques = independent_maximal_cliques(graph)
    h = nx.Graph()
    h.add_nodes_from(range(len(cliques)))
    for i in range(len(cliques)):
        for j in range(i + 1, len(cliques)):
            if cliques[i] & cliques[j]:
                h.add_edge(i, j)
    return h


class DirectO6RetractionTest(unittest.TestCase):
    def test_proof_rebuilds_raw_iterates_and_all_1201_edges(self):
        result = proof.verify()
        self.assertEqual(result["nine_vertex_mckay_index"], 252075)
        self.assertEqual(result["raw_clique_iterate_order_and_size"],
                         [[9, 23], [13, 54], [20, 137], [56, 1201]])
        self.assertEqual(result["source_edges_checked"], 1201)
        self.assertEqual(result["classification"], "K_DIVERGENT")
        self.assertEqual(result["o6_missing_pairs"],
                         [[0, 53], [4, 43], [7, 35], [12, 38], [21, 40], [24, 41]])

    def test_independent_bron_kerbosch_rebuild_with_original_generator_blocked(self):
        original = proof.reconstruct()
        with mock.patch.object(
            nx, "find_cliques",
            side_effect=AssertionError("NetworkX clique enumeration reused"),
        ), mock.patch.object(
            proof, "raw_clique_graph",
            side_effect=AssertionError("Original K constructor reused"),
        ):
            other = [nx.from_graph6_bytes(b"HEh~dzm")]
            for _ in range(3):
                other.append(independent_raw_k(other[-1]))
            self.assertEqual(
                [(len(g), g.number_of_edges()) for g in other],
                list(proof.EXPECTED_STAGES),
            )
            for a, b in zip(original, other):
                self.assertEqual(set(map(frozenset, a.edges())),
                                 set(map(frozenset, b.edges())))
            result = proof.verify_projection(other[3])
        self.assertEqual(result["source_edges_checked"], 1201)

    def test_mutating_projection_fixed_target_rejected(self):
        source = proof.reconstruct()[-1]
        corrupted = list(proof.PROJECTION)
        corrupted[proof.TARGET[0]] = proof.TARGET[1]
        with self.assertRaisesRegex(ValueError, "does not fix"):
            proof.verify_projection(source, projection=tuple(corrupted))

    def test_mutating_non_target_image_rejected(self):
        source = proof.reconstruct()[-1]
        corrupted = list(proof.PROJECTION)
        # This source edge cannot map to opposite O6 poles.
        u, v = next(
            (u, v) for u, v in source.edges()
            if u not in proof.TARGET and v in proof.TARGET
            and not source.has_edge(proof.TARGET[0], v)
        )
        corrupted[u] = proof.TARGET[0]
        with self.assertRaisesRegex(ValueError, "edge constraint"):
            proof.verify_projection(source, projection=tuple(corrupted))

    def test_mutating_target_rejected(self):
        source = proof.reconstruct()[-1]
        altered = list(proof.TARGET)
        altered[-1] = 1  # The altered twelve-element set is not an induced O6.
        with self.assertRaises(ValueError):
            proof.verify_projection(source, target=tuple(altered))


if __name__ == "__main__":
    unittest.main()
