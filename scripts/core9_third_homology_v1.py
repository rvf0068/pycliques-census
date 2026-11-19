"""Exact F_2 homology in degrees 0..3 of raw K^3 for two nine-cores.

Enumerates *all* cliques of size <=5 and reduces the exact simplicial
boundary matrices over GF(2). In particular beta_3 is not truncated.
"""
from __future__ import annotations

import argparse
from itertools import combinations
import json

import networkx as nx

from core9_sphere_collapse_v1 import INPUTS, raw_K

EXPECTED = {
    "208409": {"faces": [56, 1060, 9728, 52237, 186480],
               "ranks": [55, 1005, 8723, 43511], "betti": [1, 0, 0, 3]},
    "248687": {"faces": [60, 1225, 12096, 69836, 267888],
               "ranks": [59, 1166, 10930, 58903], "betti": [1, 0, 0, 3]},
}


def insert_column(pivots: dict[int, int], vector: int) -> None:
    """Reduce a GF(2) column; highest set bit is the elimination pivot."""
    while vector:
        head = vector.bit_length() - 1
        old = pivots.get(head)
        if old is None:
            pivots[head] = vector
            return
        vector ^= old


def homology_through_three(graph: nx.Graph) -> dict:
    simplices: dict[int, dict[tuple[int, ...], int]] = {
        i: {} for i in range(1, 5)
    }
    pivots = {k: {} for k in range(1, 5)}
    face_counts = [0] * 5
    for clique in nx.enumerate_all_cliques(graph):
        size = len(clique)
        if size > 5:
            break
        face_counts[size - 1] += 1
        face = tuple(sorted(clique))
        if size > 1:
            prev = simplices[size - 1]
            column = sum(1 << prev[subface]
                         for subface in combinations(face, size - 1))
            insert_column(pivots[size - 1], column)
        if size <= 4:
            simplices[size][face] = len(simplices[size])
    ranks = [len(pivots[k]) for k in range(1, 5)]
    betti = [face_counts[0] - ranks[0],
             face_counts[1] - ranks[0] - ranks[1],
             face_counts[2] - ranks[1] - ranks[2],
             face_counts[3] - ranks[2] - ranks[3]]
    return {"faces": face_counts, "ranks": ranks, "betti": betti}


def run() -> dict:
    result = {}
    for original_index, graph6 in INPUTS.items():
        graph = nx.from_graph6_bytes(graph6.encode("ascii"))
        for _ in range(3):
            graph = raw_K(graph)
        found = homology_through_three(graph)
        if found != EXPECTED[original_index]:
            raise AssertionError("Third-iterate homology fingerprint differs")
        result[original_index] = {"graph6": graph6, **found}
    return result


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(run(), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
