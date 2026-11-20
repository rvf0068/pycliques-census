"""Replay a certificate for reduced mod-2 homology vanishing at pared K^3.

McKay 260910, graph6 HUZvvzu. This script uses only NetworkX:
no MILP/LP solver, no uncommitted search artifact, no enormous host boundary.
"""
from __future__ import annotations

import argparse
import itertools
from collections import defaultdict
from math import prod
from pathlib import Path

import networkx as nx

SOURCE = "HUZvvzu"
STAGES = ((9, 26), (12, 52), (21, 176), (132, 7880))
WEIGHT3 = (0, 27, 42, 87, 91, 108)
WEIGHT1 = (24, 38, 45, 47, 51, 66, 68, 69)
TARGET_BETTI = {
    8: (2, 1), 9: (3, 4), 10: (3, 1),
    11: (5, 1), 12: (7, 12), 13: (7, 1),
}


def require(condition: bool, explanation: str) -> None:
    if not condition:
        raise ValueError(explanation)


def bitset_maximal_cliques(g: nx.Graph) -> tuple[int, ...]:
    """Standalone Bron--Kerbosch enumerator, independently of find_cliques."""
    n = len(g)
    require(set(g) == set(range(n)), "Expected consecutive vertex labels")
    adj = tuple(sum(1 << j for j in g[i]) for i in range(n))
    maximal: list[int] = []

    def visit(facet: int, pending: int, excluded: int) -> None:
        if not (pending or excluded):
            maximal.append(facet)
            return
        union = pending | excluded
        pivot = max(
            (i for i in range(n) if (union >> i) & 1),
            key=lambda i: (pending & adj[i]).bit_count(),
            default=None,
        )
        available = pending & ~(adj[pivot] if pivot is not None else 0)
        while available:
            bit = available & -available
            v = bit.bit_length() - 1
            visit(facet | bit, pending & adj[v], excluded & adj[v])
            pending ^= bit
            excluded |= bit
            available ^= bit

    visit(0, (1 << n) - 1, 0)
    require(len(set(maximal)) == len(maximal), "Repeated maximal clique")
    return tuple(sorted(maximal))


def clique_graph(g: nx.Graph) -> nx.Graph:
    facets = bitset_maximal_cliques(g)
    out = nx.Graph()
    out.add_nodes_from(range(len(facets)))
    out.add_edges_from(
        (i, j) for i in out for j in out if i < j
        and facets[i] & facets[j]
    )
    return out


def pare(g: nx.Graph) -> nx.Graph:
    h = g.copy()
    while True:
        deleted = False
        for v in h:
            closed = set(h[v]) | {v}
            if any(closed <= (set(h[u]) | {u}) for u in h[v]):
                h.remove_node(v)
                deleted = True
                break
        if not deleted:
            return nx.convert_node_labels_to_integers(h)


def reconstruct() -> list[nx.Graph]:
    source_index = Path(__file__).resolve().parents[2] / "indeterminate_order_9.txt"
    rows = [line.split() for line in source_index.read_text().splitlines()
            if line.strip() and not line.startswith("#")]
    source_rows = [row for row in rows if row[0] == "260910"]
    require(len(source_rows) == 1 and source_rows[0][:3] == [
        "260910", "9", SOURCE
    ], "Historical McKay 260910 input changed")
    current = nx.from_graph6_bytes(SOURCE.encode("ascii"))
    sequence = []
    for i, expected in enumerate(STAGES):
        current = pare(current)
        require((len(current), current.number_of_edges()) == expected,
                f"P{i} order/edge count differs")
        sequence.append(current)
        if i < 3:
            reference_facets = {
                sum(1 << v for v in q) for q in nx.find_cliques(current)
            }
            require(set(bitset_maximal_cliques(current)) == reference_facets,
                    f"Independent maximal-clique enumerators disagree at P{i}")
            current = clique_graph(current)
    return sequence


def verify_weighted_witness(p3: nx.Graph, weights: dict[int, int]) -> dict:
    """A 14-vertex exact rational certificate scaled to integers."""
    c = nx.complement(p3)
    require(len(weights) == 14 and set(weights) <= set(c),
            "Wrong support for weighted certificate")
    require(sum(weights.values()) == 26 and all(w > 0 for w in weights.values()),
            "Incorrect positive integer weight total")
    require(all(not c.has_edge(u, v)
                for u, v in itertools.combinations(weights, 2)),
            "Weighted set is not independent in the complement")
    loads = {
        x: sum(weights.get(y, 0) for y in c[x])
        for x in c
    }
    maximum_load = max(loads.values())
    require(0 < maximum_load <= 3,
            "Failed open-neighborhood weight bound")
    total_weight = sum(weights.values())
    lower_bound = (total_weight + maximum_load - 1) // maximum_load
    require(lower_bound >= 9,
            "Weighted certificate does not establish the intended lower bound")
    return {
        "support_size": 14, "total_weight": total_weight,
        "maximum_open_neighbor_load": maximum_load,
        "open_domination_lower_bound_for_support": lower_bound,
        "mod2_homology_vanishing_through": 7,
    }


def exact_reduced_betti(g: nx.Graph) -> dict[int, int]:
    """Full mod-2 boundary reduction on each SMALL target component."""
    faces: dict[int, list[tuple[int, ...]]] = defaultdict(list)
    for face in nx.enumerate_all_cliques(g):
        faces[len(face)].append(tuple(sorted(face)))
    require(bool(faces), "No faces in target component")
    ranks: dict[int, int] = {}
    for size in range(2, max(faces) + 1):
        index = {face: j for j, face in enumerate(faces[size - 1])}
        pivots: dict[int, int] = {}
        for face in faces[size]:
            bits = 0
            for smaller in itertools.combinations(face, size - 1):
                bits ^= 1 << index[smaller]
            while bits:
                lead = bits.bit_length() - 1
                if lead in pivots:
                    bits ^= pivots[lead]
                else:
                    pivots[lead] = bits
                    break
        ranks[size] = len(pivots)
    result = {
        size - 1: len(faces[size]) - ranks.get(size, 0)
        - ranks.get(size + 1, 0) - (size == 1)
        for size in faces
    }
    require(all(beta >= 0 for beta in result.values()),
            "Negative Betti number")
    return result


def verify_targets(c: nx.Graph) -> dict:
    """Exclude cycle-complement clique targets n=8..13, 17, >=18."""
    result = {}
    for n in range(8, 18):
        source = nx.complement(nx.cycle_graph(n))
        target = clique_graph(source)
        comp = nx.complement(target)
        if n <= 13:
            component_betti = []
            for vs in nx.connected_components(comp):
                graph = nx.complement(comp.subgraph(vs).copy())
                nonzero = {
                    i: beta for i, beta in exact_reduced_betti(graph).items()
                    if beta
                }
                require(len(nonzero) == 1,
                        f"Unexpected component homology at n={n}")
                component_betti.append(next(iter(nonzero.items())))
            degree = sum(i for i, _ in component_betti) + len(component_betti) - 1
            rank = prod(beta for _, beta in component_betti)
            require((degree, rank) == TARGET_BETTI[n],
                    f"Target n={n} homology changed")
            result[n] = (len(target), degree, rank)
        else:
            result[n] = (len(target), comp.number_of_edges())
    omitted = len(c) - result[17][0]
    top_degrees = sorted((d for _, d in c.degree()), reverse=True)[:omitted]
    lower_bound = c.number_of_edges() - sum(top_degrees)
    require((len(c), c.number_of_edges()) == (132, 766),
            "P3 complement counts differ")
    require((omitted, sum(top_degrees), lower_bound, result[17]) ==
            (13, 238, 528, (119, 323)),
            "Incorrect 17-cycle complement-edge exclusion")
    require(len(clique_graph(nx.complement(nx.cycle_graph(18)))) == 158,
            "Order obstruction at n>=18 changed")
    return result


def verify(self_test: bool = False) -> None:
    seq = reconstruct()
    expected_early = {0: {2: 1}, 1: {2: 1}, 2: {4: 1}}
    for i in range(3):
        positive = {dim: val for dim, val in exact_reduced_betti(seq[i]).items()
                    if val}
        require(positive == expected_early[i], f"P{i} Betti mismatch")
    weights = {v: 3 for v in WEIGHT3}
    weights.update({v: 1 for v in WEIGHT1})
    proof = verify_weighted_witness(seq[3], weights)
    targets = verify_targets(nx.complement(seq[3]))

    if self_test:
        tampered = dict(weights)
        tampered[91] += 1
        try:
            verify_weighted_witness(seq[3], tampered)
        except ValueError:
            pass
        else:
            raise AssertionError("Tampered certificate was accepted")
        tampered_graph = seq[3].copy()
        require(tampered_graph.has_edge(0, 27),
                "No expected edge for adversarial graph mutation")
        tampered_graph.remove_edge(0, 27)
        try:
            verify_weighted_witness(tampered_graph, weights)
        except ValueError:
            pass
        else:
            raise AssertionError("Tampered graph was accepted")

    print(f"VERIFIED McKay 260910 {SOURCE}: four pared stages {STAGES}")
    print(f"VERIFIED weights: {proof}")
    print(f"VERIFIED target homologies/edge obstructions: {targets}")
    print("No K-behavior classification is inferred; n=14,15,16 remain.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    verify(parser.parse_args().self_test)
