"""Exact direct K^3(G) -> O5 retraction, McKay nine-vertex index 242316.

Original graph6: HCrlvhz. No dominated-vertex reductions are used:
raw K(G), K^2(G) and K^3(G) have orders 15, 21 and 60.

The explicit 60-entry projection fixes the induced O5 and respects
every source edge (adjacent vertices may map to equal vertices).
The result proves K-divergence by the Retraction Theorem.
"""
from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

import networkx as nx

INDEX = 242316
GRAPH6 = "HCrlvhz"
EXPECTED_STAGES = ((9, 22), (15, 71), (21, 150), (60, 1361))
TARGET = (0, 2, 6, 10, 13, 29, 32, 42, 44, 50)
MISSING_PAIRS = ((0, 50), (2, 29), (6, 32), (10, 42), (13, 44))
PROJECTION = (
    0, 0, 2, 2, 0, 0, 6, 2, 2, 2,
    10, 0, 0, 13, 0, 2, 42, 42, 0, 0,
    10, 0, 0, 0, 10, 0, 10, 10, 10, 29,
    32, 32, 32, 32, 32, 10, 29, 29, 2, 2,
    2, 42, 42, 44, 44, 44, 44, 32, 32, 32,
    50, 32, 32, 44, 44, 32, 44, 32, 44, 32,
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
    """Replay complete O5 target, section, and all ordinary graph morphisms."""
    if len(source) != 60 or set(source) != set(range(60)):
        raise ValueError("Unexpected source vertex set")
    if len(projection) != len(source):
        raise ValueError("Projection must specify every source vertex")
    if len(target) != 10 or len(set(target)) != 10 or set(target) - set(source):
        raise ValueError("The alleged O5 has incorrect vertices")
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
                nx.complete_multipartite_graph(2, 2, 2, 2, 2),
            )):
        raise ValueError("Induced target is not O5")

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
        "o5_target_vertices": list(target),
        "o5_missing_pairs": [list(pair) for pair in actual_missing_pairs],
        "projection": list(projection),
        "source_edges_checked": source.number_of_edges(),
        "invalid_source_edges": 0,
        "classification": "K_DIVERGENT",
        "justification": "ordinary K3 to O5 retraction and Neumann-Lara theorem",
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
    print("VERIFIED McKay index 242316: raw K3 retracts onto O5")
    print("RAW iterates", result["raw_clique_iterate_order_and_size"])
    print("CHECKED", result["source_edges_checked"], "source-edge constraints")
    print("CONCLUSION K_DIVERGENT")


if __name__ == "__main__":
    main()
