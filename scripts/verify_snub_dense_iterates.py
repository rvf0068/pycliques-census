"""Reproduce the high-density simply-connected K^4(snub disphenoid) finding.

Run in the existing isolated post-PR14 pycliques-project environment:
    bash scripts/bootstrap_core9cover_v2.sh
    .venv-core9cover-v2/bin/python scripts/verify_snub_dense_iterates.py

This does NOT prove clique divergence. It studies *raw* K^4(S); previous
iterates are also raw because none undergoes dominated-vertex paring.
"""
from __future__ import annotations

from itertools import combinations
import json

import networkx as nx
from pycliques.cliques import clique_graph
from pycliques.dominated import completely_pared_graph

SNUB_GRAPH6 = "GQyuzw"
# Each order/edge/degree is checked from independently reconstructed graphs.
EXPECTED = (
    (8, 18, 4),
    (12, 46, 7),
    (20, 136, 12),
    (56, 1196, 40),
    (1076, 504360, 832),
)
EXPECTED_B1_MOD2 = (0, 0, 0, 0)
# These are resource guards, never graph-theoretic conclusions.
MAX_CLIQUES = 1200
MAX_CLIQUE_EDGES = 550000


def betti1_mod2(graph: nx.Graph) -> int:
    """Exact rank of the triangle-boundary map over GF(2), not a homotopy claim."""
    vertices = list(graph)
    edges = list(graph.edges())
    positions = {frozenset(e): i for i, e in enumerate(edges)}
    pivots: dict[int, int] = {}
    rank = 0
    # Enumerate distinct triangles once using insertion-order indices.
    index = {vertex: j for j, vertex in enumerate(vertices)}
    for u in vertices:
        for v in graph[u]:
            if index[v] <= index[u]:
                continue
            for w in (set(graph[u]) & set(graph[v])):
                if index[w] <= index[v]:
                    continue
                boundary = (
                    (1 << positions[frozenset((u, v))])
                    ^ (1 << positions[frozenset((u, w))])
                    ^ (1 << positions[frozenset((v, w))])
                )
                while boundary:
                    pivot = boundary.bit_length() - 1
                    if pivot in pivots:
                        boundary ^= pivots[pivot]
                    else:
                        pivots[pivot] = boundary
                        rank += 1
                        break
    return len(edges) - len(vertices) + nx.number_connected_components(graph) - rank


def is_flag_sphere_triangulation(graph: nx.Graph) -> bool:
    """Check that this 8-vertex graph is a connected triangulated 2-sphere.

    Uses elementary surface facts: all links are connected 1-spheres,
    the complex is 2-dimensional and has Euler characteristic 2.
    """
    if not nx.is_connected(graph) or max(len(c) for c in nx.find_cliques(graph)) != 3:
        return False
    triangles = sum(1 for a,b,c in combinations(graph,3)
                    if graph.has_edge(a,b) and graph.has_edge(a,c) and graph.has_edge(b,c))
    if len(graph) - graph.number_of_edges() + triangles != 2:
        return False
    for vertex in graph:
        link = graph.subgraph(graph.neighbors(vertex))
        if (
            len(link) < 3 or not nx.is_connected(link)
            or any(deg != 2 for _,deg in link.degree())
        ):
            return False
    # A connected closed triangulated surface with chi=2 is S^2.
    return True


def verify() -> dict:
    current = nx.from_graph6_bytes(SNUB_GRAPH6.encode("ascii"))
    if not is_flag_sphere_triangulation(current):
        raise AssertionError("Snub graph6 no longer certifies a flag triangulation of S^2")
    rows = []
    for level, (order, edges, minimum_degree) in enumerate(EXPECTED):
        got = (
            current.number_of_nodes(),
            current.number_of_edges(),
            min(degree for _, degree in current.degree()),
        )
        if got != (order, edges, minimum_degree):
            raise AssertionError(f"K^{level}(S): observed {got}, expected {(order, edges, minimum_degree)}")
        row = {
            "iterate": level, "order": got[0], "edges": got[1],
            "minimum_degree": got[2],
            "kind": "raw_clique_iterate",
        }
        if level <= 3:
            b1 = betti1_mod2(current)
            if b1 != EXPECTED_B1_MOD2[level]:
                raise AssertionError(f"K^{level}(S): unexpected GF(2) first Betti number {b1}")
            row["betti1_mod2"] = b1
        rows.append(row)
        if level == 4:
            break
        next_graph = clique_graph(
            current, bound=MAX_CLIQUES, max_edges=MAX_CLIQUE_EDGES,
        )
        if next_graph is None:
            raise AssertionError(f"Exceeded explicit K^{level+1} construction bounds")
        if level < 3:
            pared = completely_pared_graph(next_graph)
            if (
                pared.number_of_nodes() != next_graph.number_of_nodes()
                or pared.number_of_edges() != next_graph.number_of_edges()
            ):
                raise AssertionError("Unexpected dominated-vertex paring in K(S)..K^3(S)")
            current = pared
        else:
            # We study raw K^4, NOT its potentially expensive pared reduction.
            current = next_graph
    n = rows[-1]["order"]
    delta = rows[-1]["minimum_degree"]
    if not 4 * delta > 3 * n:
        raise AssertionError("Dense graph fails the claimed pi1 criterion")
    # Delta > 3n/4 implies every 4 vertices have a common neighbor:
    # count the complements of their open neighborhoods. Fill 4-cycles
    # by coning, and shorten longer loops via triangles from any four
    # consecutive vertices to a common neighbor. Thus pi1=0.
    return {
        "schema": 1,
        "source_graph6": SNUB_GRAPH6,
        "flag_complex_of_source": "triangulated_S2",
        "steps": rows,
        "four_neighbor_criterion": "4*minimum_degree > 3*number_of_vertices",
        "k4_flag_complex_simply_connected": True,
        "k4_nontrivial_connected_triangular_covers": False,
        "no_divergence_verdict": True,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))
