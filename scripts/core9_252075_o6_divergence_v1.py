"""Exact direct K^3(G) -> O6 retraction, McKay nine-vertex index 252075.

Original graph6: HEh~dzm. No dominated-vertex reductions are used:
raw K(G), K^2(G) and K^3(G) have orders 13, 20 and 56.

The explicit 56-entry projection fixes the induced O6 and respects
every source edge (adjacent vertices may map to equal vertices).
The result proves K-divergence by the Retraction Theorem.
"""
from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

import networkx as nx

INDEX = 252075
GRAPH6 = "HEh~dzm"
EXPECTED_STAGES = ((9, 23), (13, 54), (20, 137), (56, 1201))
TARGET = (0, 4, 7, 12, 21, 24, 35, 38, 40, 41, 43, 53)
MISSING_PAIRS = ((0, 53), (4, 43), (7, 35), (12, 38), (21, 40), (24, 41))
PROJECTION = (
    0, 0, 0, 0, 4, 4, 4, 7, 4, 4,
    0, 0, 12, 0, 0, 0, 21, 7, 4, 7,
    4, 21, 21, 21, 24, 4, 4, 4, 4, 40,
    24, 24, 24, 35, 35, 35, 38, 41, 38, 38,
    40, 41, 38, 43, 38, 38, 35, 35, 38, 40,
    35, 35, 35, 53, 38, 38,
)


def raw_clique_graph(graph: nx.Graph) -> nx.Graph:
    """Raw maximal-clique intersection graph with stable bitmask labels."""
    if set(graph) != set(range(len(graph))):
        raise ValueError("Expected consecutive zero-based vertex labels")
    maximal_cliques = sorted(
        (frozenset(vertices) for vertices in nx.find_cliques(graph)),
        key=lambda clique: sum(1 << v for v in clique),
    )
    result = nx.Graph()
    result.add_nodes_from(range(len(maximal_cliques)))
    result.add_edges_from(
        (i, j)
        for i, j in combinations(range(len(maximal_cliques)), 2)
        if maximal_cliques[i].intersection(maximal_cliques[j])
    )
    return result


def reconstruct() -> list[nx.Graph]:
    graph = nx.from_graph6_bytes(GRAPH6.encode("ascii"))
    stages = [graph]
    for level in range(1, 4):
        stages.append(raw_clique_graph(stages[-1]))
    actual = tuple((len(g), g.number_of_edges()) for g in stages)
    if actual != EXPECTED_STAGES:
        raise ValueError(f"Wrong raw K iterates: {actual}")
    return stages


def verify_projection(
    source: nx.Graph,
    *,
    target: tuple[int, ...] = TARGET,
    projection: tuple[int, ...] = PROJECTION,
) -> dict:
    """Replay complete O6 target, section, and all ordinary graph morphisms."""
    if len(source) != 56 or set(source) != set(range(56)):
        raise ValueError("Unexpected source vertex set")
    if len(projection) != len(source):
        raise ValueError("Projection must specify every source vertex")
    if len(target) != 12 or len(set(target)) != 12 or set(target) - set(source):
        raise ValueError("The alleged O6 has incorrect vertices")
    if set(projection) != set(target):
        raise ValueError("Projection image is not exactly the target")
    if any(projection[v] != v for v in target):
        raise ValueError("Projection does not fix every target vertex")

    actual_missing_pairs = tuple(sorted(
        tuple(sorted((u, v)))
        for u, v in combinations(sorted(target), 2)
        if not source.has_edge(u, v)
    ))
    if (actual_missing_pairs != MISSING_PAIRS
            or not nx.is_isomorphic(
                source.subgraph(target),
                nx.complete_multipartite_graph(2, 2, 2, 2, 2, 2),
            )):
        raise ValueError("Induced target is not O6")

    invalid_edges = [
        (u, v) for u, v in source.edges()
        if projection[u] != projection[v]
        and not source.has_edge(projection[u], projection[v])
    ]
    if invalid_edges:
        raise ValueError("Graph-morphism edge constraint failed")
    return {
        "nine_vertex_mckay_index": INDEX,
        "nine_vertex_graph6": GRAPH6,
        "raw_clique_iterate_order_and_size": [
            list(pair) for pair in EXPECTED_STAGES
        ],
        "retraction_source": "raw_K3",
        "o6_target_vertices": list(target),
        "o6_missing_pairs": [list(pair) for pair in actual_missing_pairs],
        "projection": list(projection),
        "source_edges_checked": source.number_of_edges(),
        "invalid_source_edges": 0,
        "classification": "K_DIVERGENT",
        "justification": "ordinary K3 to O6 retraction and Neumann-Lara theorem",
    }


def verify() -> dict:
    stages = reconstruct()
    return verify_projection(stages[3])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", nargs="?", choices=("verify", "certificates"), default="verify"
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify()
    if args.command == "certificates":
        if args.output is None:
            parser.error("certificates requires --output PATH")
        args.output.write_text(
            json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
    print("VERIFIED McKay index 252075: raw K3 retracts onto O6")
    print("RAW iterates", result["raw_clique_iterate_order_and_size"])
    print("CHECKED", result["source_edges_checked"], "source-edge constraints")
    print("CONCLUSION K_DIVERGENT")


if __name__ == "__main__":
    main()
