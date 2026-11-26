"""Solver-independent coaffine orbit criteria for third-iterate targets.

The known Connected Summand Theorem applies to any *coaffine invariant
induced subgraph*, not only a decomposition of the entire stable image.
Three pairwise completely joined alpha-orbits give a Three Summands
witness; a pair of joined alpha-orbits with one connected factor gives
a Connected Summand witness. Check every vertex and cross-edge.
"""
from __future__ import annotations

from itertools import combinations
import networkx as nx

from research.order10_three_p3_coaffine_native_v1.verify import (
    audit_positive_map,
)


def require(ok: bool, why: str) -> None:
    if not ok:
        raise AssertionError(why)


def orbit_certificate(graph: nx.Graph, f: list[int]) -> dict:
    summary = audit_positive_map(graph, f)
    stable = set(graph)
    while True:
        next_s = {f[v] for v in stable}
        if next_s == stable:
            break
        stable = next_s
    require(len(stable) == summary["stable_order"],
            "Eventual stable image cannot be independently reproduced")

    remaining = set(stable)
    orbits = []
    while remaining:
        v = min(remaining)
        cur = v
        cycle = []
        while cur in remaining:
            remaining.remove(cur)
            cycle.append(cur)
            cur = f[cur]
        require(cur == v, "Stable image permutation is malformed")
        require(len(cycle) >= 2, "Coaffination unexpectedly has a fixed vertex")
        orbits.append(sorted(cycle))
    Y = graph.subgraph(stable)
    require(all(f[v] != v and not graph.has_edge(v, f[v])
                for v in stable),
            "Stable-image symmetry is not coaffine")
    require(all(Y.has_edge(u, v) == Y.has_edge(f[u], f[v])
                for u in stable for v in stable),
            "Stable-image symmetry is not an automorphism")
    compatible = nx.Graph()
    compatible.add_nodes_from(range(len(orbits)))
    for i, j in combinations(range(len(orbits)), 2):
        if all(graph.has_edge(u, v)
               for u in orbits[i] for v in orbits[j]):
            compatible.add_edge(i, j)

    chosen = None
    theorem = None
    for i in range(len(orbits)):
        for j in compatible[i]:
            if j <= i:
                continue
            for k in compatible[i]:
                if k > j and compatible.has_edge(j, k):
                    chosen = [i, j, k]
                    theorem = "LNP09 Theorem 3.6 (three coaffine summands)"
                    break
            if chosen is not None:
                break
        if chosen is not None:
            break
    if chosen is None:
        connected = [
            nx.is_connected(graph.subgraph(orbit))
            for orbit in orbits
        ]
        for i, j in compatible.edges():
            if connected[i] or connected[j]:
                chosen = [i, j]
                theorem = "LNP09 Theorem 4.6 (connected coaffine summand)"
                break

    if chosen is not None:
        factors = [orbits[i] for i in chosen]
        require(all(set(f[x] for x in orbit) == set(orbit)
                    for orbit in factors),
                "Chosen target coaffine factors are not invariant")
        require(all(graph.has_edge(u, v)
                    for A, B in combinations(factors, 2)
                    for u in A for v in B),
                "Some claimed Zykov-sum cross-edge is absent")
        require(len(chosen) >= 3 or any(
            nx.is_connected(graph.subgraph(A)) for A in factors
        ), "Connected summand theorem applied without a connected factor")
    else:
        factors = []
    return {
        "coaffine_orbit_count": len(orbits),
        "compatible_orbit_pair_count": compatible.number_of_edges(),
        "published_divergence_theorem": theorem,
        "certified_invariant_factor_orbits": factors,
        "expansive_coaffine_subgraph_proved": chosen is not None,
        "original_K_divergent_by_retraction_and_coaffine_inclusion":
            chosen is not None,
        "stable_image_originally_retracted_order": len(stable),
    }
