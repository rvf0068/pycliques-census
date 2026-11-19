"""Exact O4 retraction of K^3(HEher^{) and exhaustive negative peer.

The ordinary retraction fixes an induced O4 pointwise and maps every
source edge to an edge or the same vertex. This proves K-divergence of
the second nine-vertex graph independently of the snub conjecture.
For HCZTf\}, exhaustive induced-O4 enumeration in K^3 and complete
necessary arc-consistency obstructions exclude every ordinary O4 retract.
"""
from __future__ import annotations

from collections import Counter
import json

import networkx as nx

GRAPHS = {"208409": r"HCZTf\}", "248687": "HEher^{"}
TARGET = (0, 5, 11, 21, 45, 47, 49, 53)
PROJECTION = (
    0, 0, 0, 0, 0, 5, 11, 0, 5, 47, 11, 11, 0, 0, 0,
    0, 0, 0, 0, 11, 11, 21, 11, 11, 11, 11, 11, 11, 11, 0,
    0, 0, 0, 21, 11, 11, 11, 49, 49, 49, 47, 47, 47, 47, 47,
    45, 47, 47, 45, 49, 49, 47, 47, 53, 49, 49, 49, 49, 49, 49,
)
EXPECTED_NEGATIVE = {"targets": 359, "local_obstruction": 101,
                     "arc_obstruction": 258, "not_excluded": 0}


def raw_K(graph: nx.Graph) -> nx.Graph:
    maximal = sorted(
        (frozenset(c) for c in nx.find_cliques(graph)),
        key=lambda q: sum(1 << v for v in q),
    )
    result = nx.Graph()
    result.add_nodes_from(range(len(maximal)))
    result.add_edges_from(
        (i, j) for i in range(len(maximal))
        for j in range(i + 1, len(maximal)) if maximal[i] & maximal[j]
    )
    return result


def third_iterate(graph6: str) -> nx.Graph:
    graph = nx.from_graph6_bytes(graph6.encode("ascii"))
    for _ in range(3):
        graph = raw_K(graph)
    return graph


def verify_retraction(graph: nx.Graph, target: tuple[int, ...],
                      projection: tuple[int, ...]) -> dict:
    if len(projection) != len(graph) or tuple(sorted(target)) != target:
        raise ValueError("Invalid map domain/target order")
    if set(projection) != set(target) or any(projection[v] != v for v in target):
        raise ValueError("Retraction fails fixed induced section condition")
    induced = graph.subgraph(target)
    O4 = nx.complete_multipartite_graph(2, 2, 2, 2)
    if not nx.is_isomorphic(induced, O4):
        raise ValueError("Target is not induced O4")
    for u, v in graph.edges():
        if projection[u] != projection[v] and not graph.has_edge(
            projection[u], projection[v]
        ):
            raise ValueError(f"Invalid graph morphism at edge {(u, v)}")
    return {"source_vertices": len(graph),
            "source_edges": graph.number_of_edges(),
            "target_vertices": list(target),
            "target_missing_pairs": [list(e) for e in nx.complement(induced).edges()],
            "retraction": list(projection)}


def all_o4_targets(graph: nx.Graph):
    """Complete enumeration: complement of an induced O4 is four K2."""
    C = nx.complement(graph)
    edges = sorted(tuple(sorted(e)) for e in C.edges())
    closed = {u: set(C[u]) | {u} for u in C}

    def rec(chosen, available):
        if len(chosen) == 4:
            yield tuple(sorted(v for edge in chosen for v in edge))
            return
        for i, e in enumerate(available):
            forbidden = closed[e[0]] | closed[e[1]]
            remaining = [f for f in available[i + 1:]
                         if f[0] not in forbidden and f[1] not in forbidden]
            yield from rec(chosen + [e], remaining)

    yield from rec([], edges)


def exact_arc_obstruction(graph: nx.Graph, target: tuple[int, ...]) -> str:
    """Sound necessary condition; an empty domain proves no retraction.

    Each vertex outside the target must map to an image compatible with
    all its fixed target neighbors. Propagate compatibility along every
    edge joining two outside vertices. Removing unsupported domain values
    cannot exclude any valid graph morphism (equality of images allowed).
    """
    T = set(target)
    compat = {a: {b for b in target if a == b or graph.has_edge(a, b)}
              for a in target}
    outside = set(graph) - T
    domains = {}
    for v in outside:
        possible = set(target)
        for t in graph[v]:
            if t in T:
                possible.intersection_update(compat[t])
        if not possible:
            return "local_obstruction"
        domains[v] = possible
    queue = list(outside)
    while queue:
        v = queue.pop()
        for u in graph[v]:
            if u not in outside:
                continue
            possible = {a for a in domains[u] if compat[a] & domains[v]}
            if not possible:
                return "arc_obstruction"
            if possible != domains[u]:
                domains[u] = possible
                queue.append(u)
    return "not_excluded"


def negative_first_graph() -> dict:
    graph = third_iterate(GRAPHS["208409"])
    if (len(graph), graph.number_of_edges()) != (56, 1060):
        raise ValueError("Unexpected first host iterate")
    counts = Counter()
    for target in all_o4_targets(graph):
        counts["targets"] += 1
        counts[exact_arc_obstruction(graph, target)] += 1
    result = {key: counts[key] for key in EXPECTED_NEGATIVE}
    if result != EXPECTED_NEGATIVE:
        raise AssertionError("Exhaustive negative-O4 certificate changed")
    return result


def positive_second_graph() -> dict:
    graph = third_iterate(GRAPHS["248687"])
    if (len(graph), graph.number_of_edges()) != (60, 1225):
        raise ValueError("Unexpected second host iterate")
    witness = verify_retraction(graph, TARGET, PROJECTION)
    O4 = nx.complete_multipartite_graph(2, 2, 2, 2)
    O8 = nx.complete_multipartite_graph(*([2] * 8))
    if not nx.is_isomorphic(raw_K(O4), O8):
        raise AssertionError("K(O4) must be O8")
    return witness


def run() -> dict:
    return {"schema": 1,
            "proved_divergent": {"order9_index": 248687,
                                 "graph6": GRAPHS["248687"],
                                 "witness": positive_second_graph()},
            "unclassified_peer_negative_screen": {
                "order9_index": 208409,
                "graph6": GRAPHS["208409"],
                "no_o4_retractions_in_K3": negative_first_graph(),
            }}


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
