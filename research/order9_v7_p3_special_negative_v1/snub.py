"""Exhaustive exclusion of ordinary P3 retractions onto the snub disphenoid.

Independently enumerates every induced snub target, deduplicates embeddings
by their vertex sets, and checks the necessary local-image-domain obstruction.
There are no search budgets. This does NOT prove convergence or K-nullity.
"""
from __future__ import annotations

import argparse
import sys

import networkx as nx

from research.order9_v7_p3_special_negative_v1.verify import (
    SOURCES, frozen_rows, source_p3,
)

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical assertions")

SNUB = nx.from_graph6_bytes(b"GQyuzw")
PATTERN = {
    v: sum(1 << w for w in SNUB[v])
    for v in SNUB
}
ORDER = sorted(SNUB, key=lambda v: (-SNUB.degree[v], v))
EXPECTED_TARGETS = {
    249576: 13902,
    251628: 26406,
    251759: 1864,
    251902: 300,
    254369: 172,
    260040: 42503,
}


def enumerate_targets_and_obstructions(graph: nx.Graph) -> tuple[int, int, int, int]:
    """Return (distinct induced snubs, embeddings, locally blocked, possible).

    Complete induced-isomorphism DFS: each new host vertex is adjacent to
    precisely the previously chosen vertices adjacent to its counterpart
    in SNUB. For any candidate target T, a retraction fixing T requires
      r(v) in intersection_{w in N_X(v) cap T} N_T[w]
    for every outside vertex v. An empty intersection is a proof that no
    such retraction exists. No other CSP constraints are assumed.
    """
    n = len(graph)
    if n > 63:
        raise ValueError("The complete 64-bit proof enumerator handles <=63 vertices")
    nodes = sorted(graph)
    positions = {v: i for i, v in enumerate(nodes)}
    adj = [
        sum(1 << positions[w] for w in graph[v]) for v in nodes
    ]
    full = (1 << n) - 1
    checked: set[int] = set()
    embedded_maps = 0
    excluded_targets = 0
    locally_possible = 0
    assigned: list[int | None] = [None] * len(SNUB)

    def search(depth: int, chosen: int) -> None:
        nonlocal embedded_maps, excluded_targets, locally_possible
        if depth == len(SNUB):
            embedded_maps += 1
            if chosen in checked:
                return
            checked.add(chosen)
            target = [i for i in range(n) if (chosen >> i) & 1]
            for v in range(n):
                if (chosen >> v) & 1:
                    continue
                target_neighbors = adj[v] & chosen
                if not any(
                    (target_neighbors & ~(adj[t] | (1 << t))) == 0
                    for t in target
                ):
                    excluded_targets += 1
                    return
            locally_possible += 1
            return

        source_vertex = ORDER[depth]
        candidates = full & ~chosen
        for level in range(depth):
            previous_source = ORDER[level]
            previous_target = assigned[previous_source]
            assert previous_target is not None
            if (PATTERN[source_vertex] >> previous_source) & 1:
                candidates &= adj[previous_target]
            else:
                candidates &= full & ~adj[previous_target]

        while candidates:
            bit = candidates & -candidates
            candidates -= bit
            assigned[source_vertex] = bit.bit_length() - 1
            search(depth + 1, chosen | bit)

    search(0, 0)
    return len(checked), embedded_maps, excluded_targets, locally_possible


def test_small_examples() -> None:
    assert (len(SNUB), SNUB.number_of_edges()) == (8, 18)
    # The target itself has a retraction, so its image-domain condition
    # must not spuriously reject it. SNUB has 8 graph automorphisms.
    assert enumerate_targets_and_obstructions(SNUB) == (1, 8, 0, 1)
    # In the cone, an outside universal vertex cannot map into the
    # snub (it has no universal vertex). The induced target still exists.
    cone = SNUB.copy()
    apex = len(SNUB)
    cone.add_node(apex)
    cone.add_edges_from((apex, v) for v in SNUB)
    assert enumerate_targets_and_obstructions(cone) == (1, 8, 1, 0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--networkx-crosscheck", action="store_true",
        help="also exhaust induced embeddings with independent NetworkX VF2 "
             "on the three smallest host cases"
    )
    args = parser.parse_args()
    frozen_rows()
    test_small_examples()
    total = 0

    for index, graph6 in SOURCES.items():
        g = source_p3(graph6)
        targets, embeddings, blocked, possible = enumerate_targets_and_obstructions(g)
        expected = EXPECTED_TARGETS[index]
        assert targets == expected, (index, targets, expected)
        assert (embeddings, blocked, possible) == (8 * expected, expected, 0), (
            index, embeddings, blocked, possible
        )
        if args.networkx_crosscheck and index in (251759, 251902, 254369):
            matcher = nx.algorithms.isomorphism.GraphMatcher(g, SNUB)
            seen = {
                frozenset(m) for m in matcher.subgraph_isomorphisms_iter()
            }
            assert len(seen) == expected, (index, len(seen), expected)
        total += targets
        print(
            f"PASS McKay={index} P3={len(g)} edges={g.number_of_edges()} "
            f"induced_snubs={targets} embeddings={embeddings} "
            f"locally_blocked={blocked} potentially_retractable={possible}",
            flush=True,
        )

    assert total == 85147
    print("PASS: all 85,147 induced snub targets exhaustively excluded")


if __name__ == "__main__":
    main()
