"""Exact special-octahedron obstruction test for snub disphenoid K^0..K^3.

For every maximal clique C, every potential antipode b_c must be outside C,
nonadjacent to c, and adjacent to all vertices of C-{c}. If a domain is
empty, or any two domains have no adjacent pair, C cannot be the privileged
maximal clique of a special octahedron O_d (d>=3). Enumerating ALL maximal
cliques and checking these necessary conditions certifies absence.

This is NOT a clique-convergence or divergence certificate, nor does it
say anything about K^4(S).
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations
import json

import networkx as nx

SNUB = "GQyuzw"
EXPECTED = (
    # level, order, edges, maximal cliques, survive nonempty domains, pair-blocked
    (0, 8, 18, 12, 12, 12),
    (1, 12, 46, 20, 4, 4),
    (2, 20, 136, 56, 0, 0),
    (3, 56, 1196, 1076, 4, 4),
)


def naive_clique_graph(graph: nx.Graph) -> nx.Graph:
    """Independent clique-graph implementation with integer output labels."""
    facets = [frozenset(c) for c in nx.find_cliques(graph)]
    result = nx.Graph()
    result.add_nodes_from(range(len(facets)))
    result.add_edges_from(
        (i, j)
        for i, j in combinations(range(len(facets)), 2)
        if facets[i] & facets[j]
    )
    return result


def inspect_maximal_cliques(graph: nx.Graph) -> dict:
    """Complete finite obstruction to the existence of a special O_d."""
    totals = Counter()
    for facet in nx.find_cliques(graph):
        totals["maximal_cliques"] += 1
        if len(facet) < 3:
            totals["size_too_small"] += 1
            continue
        C = set(facet)
        # Each b_c must be nonadjacent to c and adjacent to all C-{c}.
        domains = {}
        for c in C:
            candidates = set(graph) - C
            for other in C:
                if other != c:
                    candidates.intersection_update(graph.neighbors(other))
                    if not candidates:
                        break
            candidates.difference_update(graph.neighbors(c))
            domains[c] = candidates
        if any(not domain for domain in domains.values()):
            totals["empty_antipode_domain"] += 1
            continue
        totals["all_domains_nonempty"] += 1
        # Antipodes form a clique, so every pair of domains must admit
        # one ADJACENT pair of representatives. Find a decisive failure.
        blocked_pairs = [
            (a, b)
            for a, b in combinations(facet, 2)
            if not any(
                graph.has_edge(u, v)
                for u in domains[a]
                for v in domains[b]
            )
        ]
        if blocked_pairs:
            totals["pair_incompatible"] += 1
        else:
            totals["not_excluded_by_pair_test"] += 1
    return {
        "maximal_cliques": totals["maximal_cliques"],
        "empty_antipode_domain": totals["empty_antipode_domain"],
        "all_domains_nonempty": totals["all_domains_nonempty"],
        "pair_incompatible": totals["pair_incompatible"],
        "not_excluded_by_pair_test": totals["not_excluded_by_pair_test"],
        "size_too_small": totals["size_too_small"],
        "special_octahedron_excluded": (
            totals["not_excluded_by_pair_test"] == 0
            and totals["maximal_cliques"] ==
              totals["empty_antipode_domain"] +
              totals["pair_incompatible"] + totals["size_too_small"]
        ),
    }


def investigate(verify_library: bool = True) -> dict:
    graph = nx.from_graph6_bytes(SNUB.encode("ascii"))
    rows = []
    for level, order, edges, cliques, eligible, blocked in EXPECTED:
        if (len(graph), graph.number_of_edges()) != (order, edges):
            raise AssertionError(f"Unexpected raw iterate size at level {level}")
        test = inspect_maximal_cliques(graph)
        if (
            test["maximal_cliques"] != cliques
            or test["all_domains_nonempty"] != eligible
            or test["pair_incompatible"] != blocked
            or not test["special_octahedron_excluded"]
        ):
            raise AssertionError(
                f"Raw K^{level}(S) fails the pre-recorded exact obstruction"
            )
        if verify_library:
            # Independent bitset-based exhaustive implementation in
            # the pinned monorepo, not the facet/domain code above.
            from pycliques.retractions import find_special_octahedron_witness
            if find_special_octahedron_witness(graph) is not None:
                raise AssertionError("Independent special-octahedron search disagrees")
        rows.append({
            "iterate": level,
            "order": order,
            "edges": edges,
            **test,
        })
        if level < 3:
            next_graph = naive_clique_graph(graph)
            if verify_library:
                from pycliques.cliques import clique_graph
                library_next = clique_graph(graph, bound=1200)
                if library_next is None or not nx.is_isomorphic(library_next, next_graph):
                    raise AssertionError("Independent clique-graph constructions disagree")
            graph = next_graph
    return {
        "schema": 1,
        "source_graph6": SNUB,
        "scope": "raw K^0(S) through K^3(S) only",
        "interpretation": (
            "No special octahedron in these four graphs. "
            "Does not classify K-divergence or K^4(S)."
        ),
        "levels": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--standalone", action="store_true",
        help="Use independent NetworkX proof only, without pycliques cross-check",
    )
    args = parser.parse_args()
    print(json.dumps(investigate(verify_library=not args.standalone),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
