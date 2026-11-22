"""Exhaustive octahedral-retraction exclusions for six ten-vertex flag spheres.

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

# The six surviving ten-vertex flag spheres: original McKay index -> graph6.
SOURCES = {
    6499365: "I?ovUqv\\o",
    8559181: "ICQbQrvno",
    10803453: "ICp`epv~_",
    11031156: "ICpderm\\o",
    11138607: "ICperXumW",
    11548392: "IEherhmmO",
}

# (P3 order, edges, maximal compatibility cliques, induced O_d targets,
#  complement-dominating targets, maximum octahedral dimension.)
EXPECTED = {
    6499365: (48, 720, 5994, 2524, 1552, 4),
    8559181: (37, 447, 3144, 1367, 1290, 4),
    10803453: (24, 198, 667, 368, 362, 3),
    11031156: (60, 1089, 10496, 2140, 848, 4),
    11138607: (56, 957, 9206, 1603, 628, 4),
    11548392: (72, 1548, 19154, 2482, 120, 4),
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


def check_frozen_v17() -> None:
    path = Path(__file__).resolve().parents[2] / "indeterminate_order_10_v17.txt"
    rows = {}
    for line in path.read_text(encoding="utf8").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 6 or int(parts[0]) in rows:
            raise AssertionError("Malformed frozen ten-v17 census")
        rows[int(parts[0])] = parts
    if set(rows) != set(SOURCES):
        raise AssertionError("Frozen ten-v17 cohort mismatch")
    for index, g6 in SOURCES.items():
        if rows[index][1:] != ["10", g6, "-", "-", "-"]:
            raise AssertionError(f"Frozen ten-v17 source mismatch: {index}")


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



def audit_fourth_10803453(*, public: bool = False) -> dict[str, object]:
    """Exhaust all dominating induced octahedra of P4(G_10803453).

    In the complement graph, an induced O_d is an induced matching of d
    edges. Every octahedral retract requires the matching's endpoints
    to dominate every vertex in the complement. We branch on an
    undominated vertex, so every possible dominating matching is visited.
    No non-dominating matching is used for an unsupported negative claim.
    """
    import time
    from collections import Counter

    index = 10803453
    third = source_p3(SOURCES[index])
    independent_raw = clique_graph(third)
    fourth = nx.convert_node_labels_to_integers(
        completely_pared(independent_raw), ordering="sorted"
    )
    if (len(fourth), fourth.number_of_edges()) != (60, 1339):
        raise AssertionError("Unexpected certified fourth iterate size")

    if public:
        import pycliques
        cliques = list(nx.find_cliques(third))
        labels = {frozenset(q): i for i, q in enumerate(cliques)}
        public_raw = pycliques.clique_graph(third)
        if public_raw is None or len(public_raw) != len(labels):
            raise AssertionError("Public K(P3) has wrong order")
        if any(frozenset(q) not in labels for q in public_raw):
            raise AssertionError("Public K(P3) has unexpected clique")
        relabeled = nx.relabel_nodes(
            public_raw,
            {q: labels[frozenset(q)] for q in public_raw}
        )
        # The public fold uses graph insertion order, while the independent
        # fold removes the least labeled dominated vertex. Normalize both.
        ordered = nx.Graph()
        ordered.add_nodes_from(sorted(relabeled))
        ordered.add_edges_from(relabeled.edges)
        def same(a: nx.Graph, b: nx.Graph) -> bool:
            return set(a) == set(b) and {
                frozenset(edge) for edge in a.edges
            } == {frozenset(edge) for edge in b.edges}
        if not same(independent_raw, ordered):
            raise AssertionError("Independent/public fourth raw clique graph mismatch")
        public_pared = pycliques.completely_pared_graph(ordered)
        if not same(completely_pared(independent_raw), public_pared):
            raise AssertionError("Independent/public fourth pared graph mismatch")

    n = len(fourth)
    full = (1 << n) - 1
    adj = [sum(1 << v for v in fourth[u]) for u in range(n)]
    nonneighbors = [full & ~(adj[u] | (1 << u)) for u in range(n)]
    complement_edges = [
        (u, v) for u in range(n) for v in range(u + 1, n)
        if nonneighbors[u] & (1 << v)
    ]
    if len(complement_edges) != 431:
        raise AssertionError("Unexpected complement edge count")
    # Bitmasks of vertices dominated by each complement edge, and its endpoints.
    covers = [
        nonneighbors[u] | nonneighbors[v] for u, v in complement_edges
    ]
    endpoint_masks = [
        (1 << u) | (1 << v) for u, v in complement_edges
    ]
    edges_covering = [[] for _ in range(n)]
    for edge_id, covered in enumerate(covers):
        bits = covered
        while bits:
            bit = bits & -bits
            bits -= bit
            edges_covering[bit.bit_length() - 1].append(edge_id)

    seen: set[tuple[int, ...]] = set()
    dimensions: Counter[int] = Counter()
    states = 0
    csp_states = 0
    max_states = 1_000_000

    def traverse(covered: int, selected: tuple[int, ...]) -> None:
        nonlocal states, csp_states
        states += 1
        if states > max_states:
            raise IncompleteSearch("Dominating matching enumeration state limit")
        if covered == full:
            if len(selected) >= 3:
                key = tuple(sorted(selected))
                if key in seen:
                    return
                seen.add(key)
                dimensions[len(key)] += 1
                pairs = [complement_edges[i] for i in key]
                witness, used = find_fixed_target_retraction(
                    fourth, pairs, max_states=100_000
                )
                csp_states += used
                if witness is not None:
                    raise AssertionError(
                        f"New positive P4 -> O{len(pairs)}: {pairs}"
                    )
                if used != 1:
                    raise AssertionError(
                        "Expected unit-propagation-only P4 obstruction"
                    )
            return

        # An uncovered vertex must be a complement-neighbor of a future
        # selected endpoint. Branch on its fewest eligible covering edges.
        uncovered = full & ~covered
        candidates = None
        least = len(complement_edges) + 1
        bits = uncovered
        while bits:
            bit = bits & -bits
            bits -= bit
            v = bit.bit_length() - 1
            available = [
                e for e in edges_covering[v]
                if not (endpoint_masks[e] & covered)
            ]
            if not available:
                return
            if len(available) < least:
                least = len(available)
                candidates = available
                if least == 1:
                    break
        assert candidates is not None
        candidates.sort(
            key=lambda e: -(covers[e] & uncovered).bit_count()
        )
        for e in candidates:
            traverse(covered | covers[e], selected + (e,))

    traverse(0, ())
    expected_dimensions = {3: 2129, 4: 75480}
    if dict(dimensions) != expected_dimensions or len(seen) != 77609:
        raise AssertionError(
            f"Fourth-iterate candidate count mismatch: {dict(dimensions)}"
        )
    if csp_states != 77609:
        raise AssertionError("Fourth-iterate propagation count mismatch")
    return {
        "index": index,
        "order": n,
        "edges": fourth.number_of_edges(),
        "dominating_octahedra": len(seen),
        "dimensions": dict(dimensions),
        "csp_states": csp_states,
        "search_nodes": states,
    }


def main() -> None:
    if not __debug__:
        raise RuntimeError("Optimized Python bypasses proof-critical assertions")
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=int, choices=sorted(SOURCES))
    parser.add_argument("--public", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument(
        "--fourth", action="store_true",
        help="also exhaust all P4 octahedral targets of McKay 10803453"
    )
    args = parser.parse_args()
    check_frozen_v17()
    if args.self_test:
        brute_force_selftest()
    for index in ([args.case] if args.case else SOURCES):
        print(audit_one(index, public=args.public), flush=True)
    print("PASS: all six sphere P3 octahedral-retraction searches EXHAUSTED")
    if args.fourth:
        print(audit_fourth_10803453(public=args.public), flush=True)
        print("PASS: McKay 10803453 P4 octahedral-retraction search EXHAUSTED")


if __name__ == "__main__":
    main()
