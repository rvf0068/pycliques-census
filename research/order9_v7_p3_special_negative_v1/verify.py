"""Finite exclusion of special octahedra at P3 for all six nine-v7 cores.

Independent NetworkX reconstruction and maximal-clique/antipode enumeration.
No bounded negative searches; no current or historical census file changes.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import sys
from pathlib import Path

import networkx as nx

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical assertions")

ROOT = Path(__file__).resolve().parents[2]
FROZEN = ROOT / "indeterminate_order_9_v7.txt"
FROZEN_BLOB = "6f1e05d6b6bb0f1b4f2638ad73a7163f26ab0345"
SOURCES = {
    249576: "HEhfvzu",
    251628: "HEhvVn{",
    251759: "HEhvtzm",
    251902: "HEhvvzm",
    254369: "HEjfvx}",
    260040: "HQyvex}",
}
# (P3 vertices, edges, maximal cliques, eligible maximal cliques,
#  backtracking nodes, maximal eligible dimension)
EXPECTED = {
    249576: (53, 1044, 783, 0, 0, 0),
    251628: (55, 1156, 1034, 4, 14, 7),
    251759: (43, 701, 416, 4, 24, 6),
    251902: (41, 641, 492, 5, 21, 9),
    254369: (40, 626, 402, 23, 127, 6),
    260040: (58, 1289, 1245, 2, 6, 7),
}


def frozen_rows() -> None:
    data = FROZEN.read_bytes()
    actual = hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()
    assert actual == FROZEN_BLOB, "Frozen nine-v7 file changed"
    rows = [
        line for line in data.decode("ascii").splitlines()
        if line and not line.startswith("#")
    ]
    assert rows == [
        f"{i} 9 {g6} - - -" for i, g6 in SOURCES.items()
    ], "Wrong original McKay identifiers in frozen nine-v7"


def pare(graph: nx.Graph) -> nx.Graph:
    graph = graph.copy()
    while True:
        closed = {v: set(graph[v]) | {v} for v in graph}
        victim = next((
            v for v in sorted(graph)
            if any(v != w and closed[v] <= closed[w] for w in graph)
        ), None)
        if victim is None:
            return graph
        graph.remove_node(victim)


def clique_graph(graph: nx.Graph) -> nx.Graph:
    maximal = list(nx.find_cliques(graph))
    out = nx.empty_graph(len(maximal))
    membership = {v: [] for v in graph}
    for j, clique in enumerate(maximal):
        for v in clique:
            membership[v].append(j)
    for ids in membership.values():
        out.add_edges_from(itertools.combinations(ids, 2))
    return out


def source_p3(graph6: str) -> nx.Graph:
    g = pare(nx.from_graph6_bytes(graph6.encode("ascii")))
    for _ in range(3):
        g = pare(clique_graph(g))
    return g


def all_special_octahedra_test(graph: nx.Graph):
    """Decide existence by exhaustive maximal-clique/antipode assignment.

    A special O_d has a maximal host clique C (d >= 3). For each v in C,
    the antipode a_v lies outside C, is nonadjacent to v, and is adjacent
    to all other vertices of C. The chosen antipodes must form a clique.
    Every maximal host clique is checked; no search cutoffs are allowed.
    """
    maximal = list(nx.find_cliques(graph))
    eligible = 0
    states = 0
    max_eligible = 0
    for maximal_clique in maximal:
        clique = sorted(maximal_clique)
        dimension = len(clique)
        if dimension < 3 or 2 * dimension > len(graph):
            continue
        clique_set = set(clique)
        domains = []
        for v in clique:
            candidates = [
                a for a in graph if a not in clique_set
                and not graph.has_edge(a, v)
                and all(graph.has_edge(a, w) for w in clique if w != v)
            ]
            if not candidates:
                break
            domains.append(candidates)
        if len(domains) != dimension:
            continue
        eligible += 1
        max_eligible = max(max_eligible, dimension)
        order = sorted(range(dimension), key=lambda j: len(domains[j]))
        assigned: dict[int, int] = {}

        def backtrack(k: int) -> bool:
            nonlocal states
            states += 1
            if k == dimension:
                return True
            index = order[k]
            for a in domains[index]:
                if all(graph.has_edge(a, other) for other in assigned.values()):
                    assigned[index] = a
                    if backtrack(k + 1):
                        return True
                    del assigned[index]
            return False

        if backtrack(0):
            pairs = [(clique[i], assigned[i]) for i in range(dimension)]
            selected = {v for pair in pairs for v in pair}
            assert len(selected) == 2 * dimension
            assert {
                frozenset(pair) for pair in pairs
            } == {
                frozenset(edge)
                for edge in nx.complement(graph.subgraph(selected)).edges()
            }
            assert set(clique) in [set(q) for q in maximal]
            return (tuple(pairs), len(maximal), eligible, states, max_eligible)

    return (None, len(maximal), eligible, states, max_eligible)


def test_small_examples() -> None:
    for graph, dimension in (
        (nx.octahedral_graph(), 3),
        (nx.complete_multipartite_graph(2, 2, 2, 2), 4),
    ):
        pairs, *_ = all_special_octahedra_test(graph)
        assert pairs is not None and len(pairs) == dimension
    cone = nx.octahedral_graph()
    apex = len(cone)
    cone.add_node(apex)
    cone.add_edges_from((apex, v) for v in range(apex))
    assert all_special_octahedra_test(cone)[0] is None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public", action="store_true")
    args = parser.parse_args()
    frozen_rows()
    test_small_examples()
    for index, original in SOURCES.items():
        g = source_p3(original)
        pairs, maximal_count, eligible, states, max_dim = all_special_octahedra_test(g)
        assert pairs is None, f"Unexpected special octahedron for {index}: {pairs}"
        result = (
            len(g), g.number_of_edges(), maximal_count,
            eligible, states, max_dim,
        )
        assert result == EXPECTED[index], (index, result)
        if args.public:
            import pycliques
            witness = pycliques.find_special_octahedron_witness(g)
            assert witness is None, f"Public pycliques found a witness for {index}"
        print(
            f"PASS McKay={index} P3={len(g)} edges={g.number_of_edges()} "
            f"maximal_cliques={maximal_count} full_antipode_domains={eligible} "
            f"assignment_states={states} special_Od=NONE",
            flush=True,
        )
    print("PASS: all six P3 special-octahedron searches completed exhaustively")


if __name__ == "__main__":
    main()
