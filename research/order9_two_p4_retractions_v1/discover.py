"""Unseeded reproducible rediscovery of O15 and O13 via native pycliques.

Starting from original graph6 and the fixed general-purpose random
vertex-ordering seeds 73 and 19, no saved target or projection is used
as input. Every positive native result is independently verified again
by the public pycliques graph-morphism and octahedral-target checkers.

A resource limit or timeout is ALWAYS inconclusive, never a negative proof.
"""
from __future__ import annotations

import random
import sys

import networkx as nx
import pycliques as pc

from research.order9_two_p4_retractions_v1.verify import PROVED, reconstruct

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical assertions")


def main() -> None:
    native_executable = pc.build_coaffine_native()
    print(f"Built pinned native coaffine backend: {native_executable}", flush=True)
    for index, case in PROVED.items():
        host = reconstruct(index)
        rng = random.Random(case["seed"])
        random_keys = {vertex: rng.random() for vertex in host}
        # Use the graph's actual insertion order, never a saved target or
        # a source-coordinate permutation derived from a witness.
        ordering = sorted(host, key=lambda vertex: random_keys[vertex])
        ordered = nx.Graph()
        ordered.add_nodes_from(ordering)
        ordered.add_edges_from(host.edges())
        assert set(ordered) == set(host)
        assert {frozenset(e) for e in ordered.edges()} == {
            frozenset(e) for e in host.edges()
        }
        result = pc.find_octahedral_retraction_coaffine(
            ordered,
            min_dimension=5,
            max_states=8000,
            time_limit=30,
            backend="native",
        )
        assert result.status is pc.RetractionSearchStatus.FOUND, (
            f"Bounded rediscovery for {index} did not find a positive witness",
            result.status.name,
            result.states_explored,
        )
        assert result.dimension == case["dimension"], (
            f"Found unexpected dimension for {index}", result.dimension,
        )
        assert result.antipodal_pairs and result.retraction and result.inclusion
        target = {v for a, b in result.antipodal_pairs for v in (a, b)}
        assert len(target) == 2 * result.dimension
        assert pc.verify_induced_octahedron(ordered, result.antipodal_pairs)
        assert pc.verify_retraction_witness(
            ordered, ordered.subgraph(target),
            (result.retraction, result.inclusion),
        )
        assert len(result.retraction) == len(ordered)
        print(
            f"UNSEEDED_CERTIFIED McKay={index} seed={case['seed']} "
            f"P4={len(host)} target=O{result.dimension} "
            f"states={result.states_explored} "
            f"all_{len(host)}_images_independently_checked=PASS",
            flush=True,
        )


if __name__ == "__main__":
    main()
