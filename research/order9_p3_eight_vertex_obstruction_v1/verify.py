"""Exact eight-vertex low-degree retraction obstruction for three nine-v9 P3 hosts.

For any ordinary retraction X -> T fixing its induced target of order t,
each outside vertex has at most delta(T)+1 neighbors in T. Therefore it
must have >= t - delta(T) - 1 nonneighbors in T.

For t=8, delta(T)<=5, every outside vertex has at least TWO neighbors
in the complement of X among the eight chosen target vertices.

This file independently enumerates ALL eight-vertex external 2-covers by
pure integer DPLL, then uses exact F2 triangle-boundary homology to
exclude the two surviving unique induced targets. No bounded negative
result, MILP solver, saved candidate target, or native code is trusted.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import itertools
from pathlib import Path
import random
import sys

import networkx as nx

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical assertions")

ROOT = Path(__file__).resolve().parents[2]
FROZEN = ROOT / "indeterminate_order_9_v9.txt"
FROZEN_BLOB = "d18a7a843be935f3a7fe911691dd1c86dac2addd"
SOURCES = {
    249576: {
        "graph6": "HEhfvzu",
        "stages": ((9, 23), (13, 53), (22, 159), (53, 1044)),
        "p3_edge_sha256": "90d104aeede24963a12788396126a27a704285842298acac481f305c124ac2a6",
        "triangles": 10453,
        "rank_d2": 992,
        "eight_covers": (),
        "minimum_two_cover": 9,
        "nine_cover": (1, 14, 16, 22, 35, 42, 45, 47, 48),
    },
    251628: {
        "graph6": "HEhvVn{",
        "stages": ((9, 23), (13, 54), (20, 137), (55, 1156)),
        "p3_edge_sha256": "210c646bb4403eeff3b6a899f8d70b74febaf3653a58ba744d4b3daea6c829df",
        "triangles": 12507,
        "rank_d2": 1102,
        "eight_covers": ((2, 8, 25, 27, 31, 38, 43, 54),),
        "minimum_two_cover": 8,
    },
    260040: {
        "graph6": "HQyvex}",
        "stages": ((9, 23), (13, 53), (21, 151), (58, 1289)),
        "p3_edge_sha256": "4996863f642525acdea1d1732094a86f59aa263b5ebb361857b49c837c6559d5",
        "triangles": 14776,
        "rank_d2": 1232,
        "eight_covers": ((0, 6, 31, 37, 43, 46, 52, 55),),
        "minimum_two_cover": 8,
    },
}


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def verify_frozen_sources() -> None:
    raw = FROZEN.read_bytes()
    check(git_blob(raw) == FROZEN_BLOB, "Frozen nine-v9 source changed")
    lines = [
        line for line in raw.decode("ascii").splitlines()
        if line and not line.startswith("#")
    ]
    check(len(lines) == 3, "Unexpected frozen source population")
    rows = {int(line.split()[0]): line for line in lines}
    check(list(rows) == sorted(rows) and set(rows) == set(SOURCES),
          "Unexpected original McKay source identities")
    for idx, case in SOURCES.items():
        check(rows[idx] == f"{idx} 9 {case['graph6']} - - -",
              f"Unexpected frozen original graph6 for McKay {idx}")


def pare(graph: nx.Graph) -> nx.Graph:
    """Independent repeated dominated-vertex reduction."""
    g = graph.copy()
    while True:
        closed = {v: set(g[v]) | {v} for v in g}
        victim = next(
            (v for v in sorted(g)
             if any(v != w and closed[v] <= closed[w] for w in g)),
            None,
        )
        if victim is None:
            return g
        g.remove_node(victim)


def clique_graph(graph: nx.Graph) -> nx.Graph:
    """Independent clique graph; NetworkX cliques are maximal completes."""
    maximal = list(nx.find_cliques(graph))
    out = nx.empty_graph(len(maximal))
    membership = {v: [] for v in graph}
    for j, complete in enumerate(maximal):
        for v in complete:
            membership[v].append(j)
    for incident in membership.values():
        out.add_edges_from(itertools.combinations(incident, 2))
    return out


def edge_digest(graph: nx.Graph) -> str:
    edges = sorted((min(a, b), max(a, b)) for a, b in graph.edges())
    return hashlib.sha256(
        "\n".join(f"{a},{b}" for a, b in edges).encode("ascii")
    ).hexdigest()


def same_graph(a: nx.Graph, b: nx.Graph) -> bool:
    return set(a) == set(b) and {
        frozenset(e) for e in a.edges()
    } == {
        frozenset(e) for e in b.edges()
    }


def reconstruct_p3(idx: int, *, public: bool = False) -> nx.Graph:
    case = SOURCES[idx]
    g = pare(nx.from_graph6_bytes(case["graph6"].encode("ascii")))
    for level, (order, edges) in enumerate(case["stages"]):
        check((len(g), g.number_of_edges()) == (order, edges),
              f"Incorrect P{level} vertices/edges for McKay {idx}")
        if level == 3:
            break
        raw = clique_graph(g)
        if public:
            import pycliques as pc

            returned = pc.clique_graph(g)
            check(returned is not None, "Public pycliques clique graph missing")
            maximal = [frozenset(c) for c in nx.find_cliques(g)]
            positions = {complete: i for i, complete in enumerate(maximal)}
            check(
                len(returned) == len(positions)
                and all(frozenset(q) in positions for q in returned),
                f"Public maximal cliques disagree at level {level}",
            )
            public_raw = nx.relabel_nodes(
                returned, {q: positions[frozenset(q)] for q in returned}
            )
            check(same_graph(raw, public_raw),
                  f"Public clique-graph edge mismatch at level {level}")
            sorted_raw = nx.Graph()
            sorted_raw.add_nodes_from(sorted(raw))
            sorted_raw.add_edges_from(raw.edges())
            public_pared = pc.completely_pared_graph(sorted_raw)
        g = pare(raw)
        if public:
            check(same_graph(g, public_pared),
                  f"Public dominated-vertex paring mismatch at level {level}")
    normalized = nx.convert_node_labels_to_integers(g, ordering="sorted")
    check(set(normalized) == set(range(len(normalized))),
          "Normalized P3 labels are not consecutive integers")
    check(edge_digest(normalized) == case["p3_edge_sha256"],
          f"Incorrect exact normalized labeled P3 digest for McKay {idx}")
    return normalized


def complement_masks(graph: nx.Graph) -> tuple[int, ...]:
    n = len(graph)
    check(set(graph) == set(range(n)), "Consecutive integer labels required")
    full = (1 << n) - 1
    return tuple(
        full & ~((1 << x) | sum(1 << y for y in graph[x]))
        for x in range(n)
    )


def valid_cover(h: tuple[int, ...], vertices: tuple[int, ...]) -> bool:
    selected = set(vertices)
    return all(
        x in selected or sum((h[x] >> y) & 1 for y in selected) >= 2
        for x in range(len(h))
    )


def search_at_most(h: tuple[int, ...], bound: int) -> tuple[tuple[int, ...] | None, int]:
    """A complete integer DPLL proof or an explicit covering set.

    The rigorous deficit-gain pruning bound sums the largest remaining
    per-variable possible contributions to all currently deficient rows.
    Ignoring overlaps can only overestimate the available coverage.
    """
    n = len(h)
    full = (1 << n) - 1
    nodes = 0

    def dfs(selected: int, excluded: int) -> tuple[int, ...] | None:
        nonlocal nodes
        nodes += 1
        if selected.bit_count() > bound:
            return None
        while True:
            undecided = full & ~(selected | excluded)
            unsatisfied = 0
            demand2 = 0
            total_demand = 0
            changed = False
            for x in range(n):
                bit = 1 << x
                if selected & bit:
                    continue
                count = (h[x] & selected).bit_count()
                if count >= 2:
                    continue
                need = 2 - count
                available = h[x] & undecided
                options = available.bit_count()
                if excluded & bit:
                    if options < need:
                        return None
                    if options == need:
                        selected |= available
                        changed = True
                        break
                elif options < need:
                    selected |= bit
                    changed = True
                    break
                unsatisfied |= bit
                total_demand += need
                if need == 2:
                    demand2 |= bit
            if selected.bit_count() > bound:
                return None
            if not changed:
                break

        if unsatisfied == 0:
            answer = tuple(x for x in range(n) if selected >> x & 1)
            check(valid_cover(h, answer), "False positive cover")
            return answer
        if selected.bit_count() >= bound:
            return None
        undecided = full & ~(selected | excluded)
        left = bound - selected.bit_count()
        if not undecided:
            return None

        gains = []
        chosen = None
        best_priority = -1
        for v in range(n):
            if not (undecided >> v) & 1:
                continue
            gain = (
                ((h[v] | (1 << v)) & unsatisfied).bit_count()
                + int(bool(demand2 >> v & 1))
            )
            gains.append(gain)
            priority = gain * 128 + (h[v] & unsatisfied).bit_count()
            if priority > best_priority:
                chosen, best_priority = v, priority
        gains.sort(reverse=True)
        if sum(gains[:left]) < total_demand:
            return None
        check(chosen is not None, "No undecided branch variable")
        bit = 1 << chosen
        yes = dfs(selected | bit, excluded)
        return yes if yes is not None else dfs(selected, excluded | bit)

    return dfs(0, 0), nodes


def enumerate_minimum_covers(
    h: tuple[int, ...], size: int
) -> tuple[list[tuple[int, ...]], int]:
    """Exhaust all size-'size' covers after separately excluding smaller ones."""
    n = len(h)
    full = (1 << n) - 1
    answers: set[tuple[int, ...]] = set()
    nodes = 0

    def dfs(selected: int, excluded: int) -> None:
        nonlocal nodes
        nodes += 1
        if selected.bit_count() > size:
            return
        while True:
            undecided = full & ~(selected | excluded)
            unsatisfied = 0
            demand2 = 0
            total_demand = 0
            changed = False
            for x in range(n):
                bit = 1 << x
                if selected & bit:
                    continue
                covered = (h[x] & selected).bit_count()
                if covered >= 2:
                    continue
                need = 2 - covered
                available = h[x] & undecided
                capacity = available.bit_count()
                if excluded & bit:
                    if capacity < need:
                        return
                    if capacity == need:
                        selected |= available
                        changed = True
                        break
                elif capacity < need:
                    selected |= bit
                    changed = True
                    break
                unsatisfied |= bit
                total_demand += need
                if need == 2:
                    demand2 |= bit
            if selected.bit_count() > size:
                return
            if not changed:
                break

        if not unsatisfied:
            check(selected.bit_count() == size,
                  "Smaller cover exists; preceding size-1 proof was invalid")
            answer = tuple(x for x in range(n) if selected >> x & 1)
            check(valid_cover(h, answer), "Invalid enumerated cover")
            answers.add(answer)
            return
        if selected.bit_count() >= size:
            return
        undecided = full & ~(selected | excluded)
        slots = size - selected.bit_count()
        if not undecided:
            return
        ranking = []
        for v in range(n):
            if not (undecided >> v & 1):
                continue
            gain = (
                ((h[v] | (1 << v)) & unsatisfied).bit_count()
                + int(bool(demand2 >> v & 1))
            )
            ranking.append((
                gain * 128 + (h[v] & unsatisfied).bit_count(), gain, v
            ))
        ranking.sort(reverse=True)
        if sum(gain for _, gain, _ in ranking[:slots]) < total_demand:
            return
        bit = 1 << ranking[0][2]
        dfs(selected | bit, excluded)
        dfs(selected, excluded | bit)

    dfs(0, 0)
    return sorted(answers), nodes


def first_betti_mod2(graph: nx.Graph) -> tuple[int, int, int]:
    """Exact GF(2) triangle-boundary elimination; returns beta1, #triangles, rank."""
    vertices = list(graph)
    edges = list(graph.edges())
    edge_index = {frozenset((u, v)): i for i, (u, v) in enumerate(edges)}
    pivots: dict[int, int] = {}
    triangles = 0
    for u in vertices:
        greater = [v for v in graph[u] if v > u]
        for i, v in enumerate(greater):
            for w in greater[i + 1:]:
                if w not in graph[v]:
                    continue
                triangles += 1
                boundary = (
                    (1 << edge_index[frozenset((u, v))])
                    | (1 << edge_index[frozenset((u, w))])
                    | (1 << edge_index[frozenset((v, w))])
                )
                while boundary:
                    lead = boundary.bit_length() - 1
                    if lead in pivots:
                        boundary ^= pivots[lead]
                    else:
                        pivots[lead] = boundary
                        break
    dimension = (
        len(edges) - len(graph) + nx.number_connected_components(graph)
        - len(pivots)
    )
    check(dimension >= 0, "Negative Betti number from invalid chain complex")
    return dimension, triangles, len(pivots)


def verify_small_enumerator() -> None:
    """An independent brute-force oracle catches branch pruning errors."""
    rng = random.Random(534722)
    tested = 0
    for n in range(4, 10):
        for _ in range(12):
            graph = nx.fast_gnp_random_graph(
                n, 0.3 + 0.4 * rng.random(), seed=rng.randrange(2**30)
            )
            h = complement_masks(graph)
            for k in (2, 3):
                smaller, _ = search_at_most(h, k - 1)
                if smaller is not None:
                    continue
                enumerated, _ = enumerate_minimum_covers(h, k)
                brute = [
                    target for target in itertools.combinations(range(n), k)
                    if valid_cover(h, target)
                ]
                check(enumerated == brute, "DPLL disagrees with direct brute force")
                tested += 1
    print(f"PASS: independent small-graph brute-force comparisons={tested}", flush=True)


def verify(*, public: bool = False) -> None:
    verify_frozen_sources()
    verify_small_enumerator()
    for idx, case in SOURCES.items():
        host = reconstruct_p3(idx, public=public)
        h = complement_masks(host)
        below8, nodes7 = search_at_most(h, 7)
        check(below8 is None, f"A sub-eight external double cover exists at {idx}")
        covers, nodes8 = enumerate_minimum_covers(h, 8)
        check(tuple(covers) == case["eight_covers"],
              f"Unexpected external double covering sets at {idx}")
        b1, triangles, rank = first_betti_mod2(host)
        check(
            (b1, triangles, rank)
            == (0, case["triangles"], case["rank_d2"]),
            f"Incorrect P3 first Betti or exact triangle boundary at {idx}",
        )
        if idx == 249576:
            nine, nine_nodes = search_at_most(h, 9)
            check(nine is not None and len(nine) == 9,
                  "External double domination minimum is not nine")
            check(nine == case["nine_cover"],
                  "Unexpected reproducible minimum-nine covering witness")
            check(case["minimum_two_cover"] == 9, "Wrong certified minimum")
        else:
            check(len(covers) == 1 and case["minimum_two_cover"] == 8,
                  "Wrong minimum and uniqueness of eight-vertex cover")
            target = host.subgraph(covers[0])
            check(
                sorted(dict(target.degree()).values()) == [5] * 8,
                "The unique eight-cover target is not 5-regular",
            )
            complement = nx.complement(target)
            check(
                sorted(len(c) for c in nx.connected_components(complement)) == [4, 4]
                and all(degree == 2 for _, degree in complement.degree()),
                "Unique target is not complement of two disjoint four-cycles",
            )
            target_b1, target_triangles, target_rank = first_betti_mod2(target)
            check(
                (target_b1, target_triangles, target_rank) == (1, 16, 12),
                "Unique target unexpectedly has no first homology",
            )
        print(
            f"PROVED McKay={idx} P3={len(host)}/{host.number_of_edges()} "
            f"eight_external_double_covers={len(covers)} "
            f"gamma_external_2={case['minimum_two_cover']} "
            f"host_beta1_F2={b1} size7_DPLL_nodes={nodes7} "
            f"size8_exhaustive_nodes={nodes8} "
            f"no_retraction_to_8_vertex_maxdegree_le_5=YES "
            f"public_pycliques_replay={public}",
            flush=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public", action="store_true")
    args = parser.parse_args()
    verify(public=args.public)


if __name__ == "__main__":
    main()
