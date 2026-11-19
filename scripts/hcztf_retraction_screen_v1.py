"""Exhaustive small-target retraction obstructions for HCZTf\}.

Screen raw K(G) and K²(G) against fixed proved-divergent nine-cores,
their clique graphs, and the still-conditional snub family.
For every induced target, exhibit a vertex outside the target whose
retraction-image domain is empty. All target copies are enumerated,
not timeboxed. This does NOT classify the source graph's K behavior.
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations
import json

import networkx as nx

SOURCE_GRAPH6 = r"HCZTf\}"
EXPECTED = (
    (1, "GQyuzw", 2),
    (1, "HEher^{", 0),
    (2, "HEht}pl", 12),
    (2, "HQyuzpt", 44),
    (2, "GQyuzw", 76),
    (2, "K:GQyuzw", 6),
    (2, "HEher^{", 0),
    (2, "K:HEher^{", 0),
    (2, "K:HEht}pl", 0),
    (2, "K:HQyuzpt", 0),
)


def decode(graph6: str) -> nx.Graph:
    return nx.from_graph6_bytes(graph6.encode("ascii"))


def clique_graph(graph: nx.Graph) -> nx.Graph:
    """Independent deterministic maximal-clique intersection construction."""
    cliques = sorted(
        (frozenset(q) for q in nx.find_cliques(graph)),
        key=lambda q: sum(1 << v for v in q),
    )
    result = nx.Graph()
    result.add_nodes_from(range(len(cliques)))
    result.add_edges_from(
        (i, j) for i, j in combinations(range(len(cliques)), 2)
        if cliques[i] & cliques[j]
    )
    return result


def target_graph(spec: str) -> nx.Graph:
    return clique_graph(decode(spec[2:])) if spec.startswith("K:") else decode(spec)


def obstructed_outside_vertex(
    host: nx.Graph, target: tuple[int, ...]
) -> int | None:
    """Exact necessary failure for a graph retraction fixing the target."""
    fixed = set(target)
    compatible = {
        v: {v} | (set(host[v]) & fixed) for v in fixed
    }
    for outside in sorted(set(host) - fixed):
        possible = set(fixed)
        for t in host[outside]:
            if t in fixed:
                possible.intersection_update(compatible[t])
                if not possible:
                    return outside
    return None


def screen(host: nx.Graph, target: nx.Graph) -> dict:
    copies: set[tuple[int, ...]] = set()
    for embedding in nx.isomorphism.GraphMatcher(
        host, target
    ).subgraph_isomorphisms_iter():
        copies.add(tuple(sorted(embedding)))
    witnesses = []
    for vertices in sorted(copies):
        if not nx.is_isomorphic(host.subgraph(vertices), target):
            raise AssertionError("Induced copy failed independent verification")
        outside = obstructed_outside_vertex(host, vertices)
        if outside is None:
            raise AssertionError("A target escaped the necessary local test")
        witnesses.append({"vertices": list(vertices), "outside": outside})
    return {"induced_target_sets": len(copies),
            "failed_local_condition": len(witnesses),
            "witnesses": witnesses}


def run() -> dict:
    source = decode(SOURCE_GRAPH6)
    first = clique_graph(source)
    second = clique_graph(first)
    assert (len(source), source.number_of_edges()) == (9, 21)
    assert (len(first), first.number_of_edges()) == (14, 59)
    assert (len(second), second.number_of_edges()) == (23, 158)
    host = {1: first, 2: second}
    cases = []
    for level, target_spec, expected_copies in EXPECTED:
        target = target_graph(target_spec)
        result = screen(host[level], target)
        if result["induced_target_sets"] != expected_copies:
            raise AssertionError("Induced-target count differs from fixed result")
        cases.append({"level": level, "target": target_spec,
                      "target_order": len(target), **result})
    return {"schema": 1, "source_graph6": SOURCE_GRAPH6,
            "scope": "raw K and K² ordinary graph retractions only",
            "interpretation": "No positive or negative K-behavior verdict",
            "cases": cases}


def verify(saved: dict) -> None:
    fresh = run()
    if saved != fresh:
        raise ValueError("Saved retraction-obstruction report disagrees")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "verify"))
    parser.add_argument("--file", type=argparse.FileType("r"))
    args = parser.parse_args()
    result = run()
    if args.command == "verify":
        if args.file is None:
            parser.error("verify requires --file")
        verify(json.load(args.file))
    else:
        print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
