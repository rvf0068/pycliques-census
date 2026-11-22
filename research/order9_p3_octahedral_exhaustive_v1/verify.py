"""Exhaustive exclusion of octahedral retractions from P3 of nine order-9 cores.

Independent NetworkX reconstruction; positive results must be certified, while
bounded/incomplete searches are never presented as negative results.
"""
from __future__ import annotations

import argparse
import itertools
import random
from collections import deque
from pathlib import Path

import networkx as nx

# McKay original index -> canonical completely pared original graph6.
SOURCES = {
    249436: "HEhff^{",
    249574: "HEhfvx}",
    249576: "HEhfvzu",
    250814: "HEhuvzm",
    251628: "HEhvVn{",
    251759: "HEhvtzm",
    251902: "HEhvvzm",
    254369: "HEjfvx}",
    260040: "HQyvex}",
}

# (order, edges, maximal compatibility cliques, distinct O_d with d>=3,
#  complement-dominating candidates, maximum induced-octahedral dimension).
EXPECTED = {
    249436: (52, 963, 41419, 40875, 14526, 4),
    249574: (36, 496, 11600, 15938, 2683, 4),
    249576: (53, 1044, 94019, 131368, 26967, 6),
    250814: (38, 533, 9569, 13442, 3043, 4),
    251628: (55, 1156, 169953, 267540, 34860, 5),
    251759: (43, 701, 34301, 48223, 8949, 5),
    251902: (41, 641, 23096, 40984, 12234, 5),
    254369: (40, 626, 20132, 28622, 4081, 5),
    260040: (58, 1289, 249187, 389255, 54319, 5),
}

class IncompleteSearch(RuntimeError):
    """A resource limit was hit; this MUST NOT be recorded as a negative."""


def completely_pared(graph: nx.Graph) -> nx.Graph:
    g = graph.copy()
    while True:
        closed = {v: set(g[v]) | {v} for v in g}
        dominated = next(
            (v for v in sorted(g) if any(
                v != w and closed[v] <= closed[w] for w in g
            )), None
        )
        if dominated is None:
            return g
        g.remove_node(dominated)


def clique_graph(graph: nx.Graph) -> nx.Graph:
    cliques = list(nx.find_cliques(graph))
    out = nx.empty_graph(len(cliques))
    memberships: dict[int, list[int]] = {v: [] for v in graph}
    for j, clique in enumerate(cliques):
        for v in clique:
            memberships[v].append(j)
    for indices in memberships.values():
        for a, b in itertools.combinations(indices, 2):
            out.add_edge(a, b)
    return out


def source_p3(g6: str) -> nx.Graph:
    g = completely_pared(nx.from_graph6_bytes(g6.encode("ascii")))
    for _ in range(3):
        g = completely_pared(clique_graph(g))
    return nx.convert_node_labels_to_integers(g, ordering="sorted")


def check_retraction(g: nx.Graph, pairs: list[tuple[int, int]], r: dict[int, int]) -> bool:
    target = {v for pair in pairs for v in pair}
    if len(target) != 2 * len(pairs) or set(r) != set(g):
        return False
    if any(r[v] != v for v in target) or not set(r.values()) <= target:
        return False
    if any(g.has_edge(u, v) for u, v in pairs):
        return False
    if any(not g.has_edge(u, v) for i, p in enumerate(pairs)
           for q in pairs[i+1:] for u in p for v in q):
        return False
    return all(r[u] == r[v] or g.has_edge(r[u], r[v]) for u, v in g.edges)


def find_fixed_target_retraction(
    g: nx.Graph, pairs: list[tuple[int, int]], *, max_states: int = 100000
) -> tuple[dict[int, int] | None, int]:
    """Complete CSP with forbidden antipodal image-pairs and singleton propagation.

    Source edges may map to edges or equality. All target vertices are fixed.
    Raising IncompleteSearch is distinct from returning None.
    """
    t = [v for pair in pairs for v in pair]
    k = len(t)
    position = {v: i for i, v in enumerate(t)}
    if len(position) != k:
        raise ValueError("Repeated target vertex")
    neighbors = [list(g[v]) for v in range(len(g))]
    domains = [0] * len(g)
    for v in g:
        if v in position:
            domains[v] = 1 << position[v]
        else:
            # r(v)=t[i] is possible exactly when v is not adjacent to t[i^1].
            domains[v] = sum(
                (1 << i) for i in range(k) if not g.has_edge(v, t[i ^ 1])
            )
        if not domains[v]:
            return None, 0

    states = 0

    def dfs(d: list[int]) -> dict[int, int] | None:
        nonlocal states
        states += 1
        if states > max_states:
            raise IncompleteSearch("CSP state budget reached")
        queue = deque(v for v in g if d[v].bit_count() == 1)
        processed: set[int] = set()
        while queue:
            v = queue.popleft()
            if v in processed:
                continue
            processed.add(v)
            forbidden = 1 << ((d[v].bit_length() - 1) ^ 1)
            for u in neighbors[v]:
                new = d[u] & ~forbidden
                if not new:
                    return None
                if new != d[u]:
                    d[u] = new
                    if new.bit_count() == 1:
                        queue.append(u)
        undecided = [v for v in g if d[v].bit_count() > 1]
        if not undecided:
            r = {v: t[d[v].bit_length() - 1] for v in g}
            if not check_retraction(g, pairs, r):
                raise AssertionError("Invalid positive certificate")
            return r
        v = min(undecided, key=lambda v: (d[v].bit_count(), -len(neighbors[v])))
        for i in range(k):
            if d[v] & (1 << i):
                new = d.copy()
                new[v] = 1 << i
                hit = dfs(new)
                if hit is not None:
                    return hit
        return None

    return dfs(domains), states


def audit_one(index: int, *, public: bool = False) -> dict[str, int]:
    g = source_p3(SOURCES[index]); n = len(g)
    if public:
        import pycliques

        # Compare the two implementations on exactly the SAME labeled input
        # at each level. A final generic graph-isomorphism test can take an
        # impractical amount of time on dense, highly symmetric P3 cores.
        # Cliques have an explicit correspondence as sets of input vertices,
        # so there is no need to search for an isomorphism.
        def same_graph(a: nx.Graph, b: nx.Graph) -> bool:
            return set(a) == set(b) and {
                frozenset(edge) for edge in a.edges
            } == {frozenset(edge) for edge in b.edges}

        original = nx.from_graph6_bytes(SOURCES[index].encode("ascii"))
        independent = completely_pared(original)
        public_pared = pycliques.completely_pared_graph(original)
        if not same_graph(independent, public_pared):
            raise AssertionError(f"Independent/public P0 mismatch: {index}")

        for level in range(1, 4):
            # Independent maximal-clique indices agree with the ordering
            # used by our independently built clique_graph().
            cliques = list(nx.find_cliques(independent))
            index_of_clique = {
                frozenset(clique): i for i, clique in enumerate(cliques)
            }
            independent_raw = clique_graph(independent)
            public_raw = pycliques.clique_graph(independent)
            if public_raw is None or len(public_raw) != len(index_of_clique):
                raise AssertionError(f"Public K{level} vertex mismatch: {index}")
            if any(frozenset(clique) not in index_of_clique for clique in public_raw):
                raise AssertionError(f"Public K{level} clique mismatch: {index}")
            normalized_public_raw = nx.relabel_nodes(
                public_raw,
                {clique: index_of_clique[frozenset(clique)] for clique in public_raw},
            )
            if not same_graph(independent_raw, normalized_public_raw):
                raise AssertionError(f"Independent/public K{level} mismatch: {index}")

            independent_pared = completely_pared(independent_raw)
            public_pared = pycliques.completely_pared_graph(normalized_public_raw)
            if not same_graph(independent_pared, public_pared):
                raise AssertionError(f"Independent/public P{level} mismatch: {index}")
            independent = independent_pared

        normalized_p3 = nx.convert_node_labels_to_integers(
            independent, ordering="sorted"
        )
        if not same_graph(g, normalized_p3):
            raise AssertionError(f"Public replay changed certified P3: {index}")

    nonedges = [(u, v) for u in g for v in g if u < v and not g.has_edge(u, v)]
    compatibility = nx.empty_graph(len(nonedges))
    adj = [(sum(1 << w for w in g[v])) for v in g]
    full = (1 << n) - 1
    for i, (u, v) in enumerate(nonedges):
        for j in range(i + 1, len(nonedges)):
            x, y = nonedges[j]
            if len({u, v, x, y}) == 4 and all(
                g.has_edge(a, b) for a in (u, v) for b in (x, y)
            ):
                compatibility.add_edge(i, j)

    maximal = 0; max_dimension = 0; candidates = 0; dominating = 0; csp_states = 0
    seen: set[tuple[int, ...]] = set()
    for m in nx.find_cliques(compatibility):
        maximal += 1
        max_dimension = max(max_dimension, len(m))
        for d in range(3, len(m) + 1):
            for indices in itertools.combinations(sorted(m), d):
                if indices in seen:
                    continue
                seen.add(indices)
                candidates += 1
                pairs = [nonedges[i] for i in indices]
                # Necessary condition: no outside vertex is adjacent to ALL of T.
                common = full
                for a, b in pairs:
                    common &= adj[a] & adj[b]
                if common:
                    continue
                dominating += 1
                r, states = find_fixed_target_retraction(g, pairs)
                csp_states += states
                if r is not None:
                    raise AssertionError(f"New positive O{d} retraction at {index}: {pairs}")

    result = (n, g.number_of_edges(), maximal, candidates, dominating, max_dimension)
    if result != EXPECTED[index]:
        raise AssertionError(f"Exhaustive count mismatch for {index}: {result} != {EXPECTED[index]}")
    return dict(index=index, order=n, edges=g.number_of_edges(), maximal=maximal,
                induced_octahedra=candidates, dominating=dominating,
                maximum_dimension=max_dimension, csp_states=csp_states)


def check_frozen_v6() -> None:
    path = Path(__file__).resolve().parents[2] / "indeterminate_order_9_v6.txt"
    rows = {}
    for line in path.read_text(encoding="utf8").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 6 or int(parts[0]) in rows:
            raise AssertionError("Malformed frozen nine-v6 census")
        rows[int(parts[0])] = parts
    if set(rows) != set(SOURCES):
        raise AssertionError("Frozen nine-v6 cohort mismatch")
    for index, g6 in SOURCES.items():
        if rows[index][1:] != ["9", g6, "-", "-", "-"]:
            raise AssertionError(f"Frozen nine-v6 source mismatch: {index}")


def brute_force_selftest() -> None:
    base = nx.octahedral_graph()
    pairs = [tuple(sorted(pair)) for pair in nx.non_edges(base)]
    rng = random.Random(43128)
    for _ in range(250):
        g = base.copy()
        for v in range(6, 6 + rng.randint(0, 3)):
            g.add_node(v)
            for u in range(v):
                if rng.random() < 0.5:
                    g.add_edge(u, v)
        outside = [v for v in g if v >= 6]
        def brute_witness(images: tuple[int, ...]) -> bool:
            r = {v: v for v in range(6)}
            r.update(zip(outside, images))
            return all(r[u] == r[v] or g.has_edge(r[u], r[v]) for u, v in g.edges)

        brute = any(
            brute_witness(images)
            for images in itertools.product(range(6), repeat=len(outside))
        )
        actual, _ = find_fixed_target_retraction(g, pairs)
        if (actual is not None) != brute:
            raise AssertionError("CSP disagrees with independent brute force")
    print("PASS 250 brute-force O3-extension cross-checks")


def main() -> None:
    if not __debug__:
        raise RuntimeError("Optimized Python bypasses proof-critical assertions")
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=int, choices=sorted(SOURCES))
    parser.add_argument("--public", action="store_true", help="compare public pycliques reconstruction")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    check_frozen_v6()
    if args.self_test:
        brute_force_selftest()
    for index in ([args.case] if args.case else SOURCES):
        print(audit_one(index, public=args.public), flush=True)
    print("PASS: all requested P3 octahedral-retraction searches EXHAUSTED")


if __name__ == "__main__":
    main()
