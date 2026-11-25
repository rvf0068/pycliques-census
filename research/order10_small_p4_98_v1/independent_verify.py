"""Second, independent fourth-stage P4 reconstruction for the 98 cores.

This verifier does NOT call p4_from_graph6, p4_facets, raw_from_facets,
fully_pare, or the first verifier's row/dimension helpers. It constructs
the fourth clique graph from literal pairwise maximal-clique intersections
and folds it by closed-neighborhood inclusion, rather than complement
containment. The P3 input uses the existing independent, dual-enumerator
PR #87 constructor, starting from the original archived graph6.

Both exact adjacency matrices must agree with the independently pinned
exploratory evidence for all 98 cases. No isomorphism is inferred from
a hash or graph dimension.
"""
from __future__ import annotations

import hashlib
import sys

if sys.flags.optimize:
    raise RuntimeError("Optimized execution bypasses proof assertions")

import networkx as nx

from research.order10_p3_global_v23_index.independent_verify import independent_p3
from research.order10_small_p4_98_v1.verify import (
    source_catalog, require,
)


def vertex_bits(number: int):
    while number:
        b = number & -number
        yield b.bit_length()-1
        number ^= b


def raw_fourth_graph(p3: nx.Graph) -> list[int]:
    # Independent facet enumeration: NetworkX returns the sets of all
    # maximal cliques; the first verifier also requires Bron--Kerbosch
    # to reproduce this exact family.
    cliques = sorted(
        sum(1 << v for v in q) for q in nx.find_cliques(p3)
    )
    n = len(cliques)
    masks = [0] * n
    for i in range(n):
        for j in range(i+1, n):
            if cliques[i] & cliques[j]:
                masks[i] |= 1 << j
                masks[j] |= 1 << i
    return masks


def closed_neighborhood_folds(raw: list[int]) -> tuple[list[int], list[int]]:
    """Complete simultaneous fold via direct CLOSED neighborhood inclusion.

    For each currently active vertex u, mark u if N[u] is strictly
    contained in N[v], or tied with v's identical closed neighborhood
    and v<u.  This defines an acyclic descent through pairs
    (number of nonneighbors, vertex label). Every deleted vertex has
    a still-surviving terminal dominator in the same initial round,
    and every terminal core is checked stiff by the same direct
    closed-neighborhood rule.
    """
    n = len(raw)
    active = (1 << n) - 1
    rounds = []
    for _ in range(n+1):
        live = list(vertex_bits(active))
        closed = {u: (raw[u] | (1 << u)) & active for u in live}
        deleted = {}
        for u in live:
            cu = closed[u]
            for v in live:
                if (v != u and not (cu & ~closed[v])
                        and (cu != closed[v] or v < u)):
                    deleted[u] = v
                    break
        if not deleted:
            # Terminal core is stiff: no distinct closed N containment.
            require(all(
                bool(closed[u] & ~closed[v])
                for u in live for v in live if u != v
            ), "Independent fourth-iterate fold left domination")
            break
        for u in deleted:
            v = u
            trail = set()
            while v in deleted:
                require(v not in trail, "Cyclic purported fold dominators")
                trail.add(v)
                v = deleted[v]
            require(v not in deleted
                    and not (closed[u] & ~closed[v]),
                    "A marked P4 vertex lacks a surviving dominator")
        active &= ~sum(1 << u for u in deleted)
        rounds.append(len(deleted))
    else:
        raise AssertionError("Independent simultaneous paring not terminating")
    alive = list(vertex_bits(active))
    remap = {v: i for i, v in enumerate(alive)}
    pared = [
        sum(1 << remap[v] for v in alive if raw[u] & (1 << v))
        for u in alive
    ]
    return pared, rounds


def shape(rows: list[int]) -> list[int]:
    n = len(rows)
    require(all(not (row & (1 << u)) and row >> n == 0
                for u, row in enumerate(rows)),
            "Unexpected self-edge or out-of-range adjacency")
    require(all(bool(rows[u] & (1 << v))
                == bool(rows[v] & (1 << u))
                for u in range(n) for v in range(u+1, n)),
            "Independent P4 adjacency is asymmetric")
    return [n, sum(x.bit_count() for x in rows)//2]


def serialize_sha256(rows: list[int]) -> str:
    length = (len(rows) + 7)//8
    digest = hashlib.sha256()
    for row in rows:
        digest.update(row.to_bytes(length, "little"))
    return digest.hexdigest()


def verify_record(record: dict) -> None:
    graph = independent_p3(record["graph6"])
    require(
        [len(graph), graph.number_of_edges()] == record["p3"],
        f"Independent third-iterate source differs for {record['index']}",
    )
    raw = raw_fourth_graph(graph)
    require(len(raw) == record["facets"]
            and shape(raw) == record["raw_p4"],
            f"Independent fourth-clique facet/intersection mismatch "
            f"for {record['index']}")
    pared, rounds = closed_neighborhood_folds(raw)
    require(rounds == record["fold_rounds"]
            and shape(pared) == record["p4"]
            and serialize_sha256(pared) == record["p4_adj_sha256"],
            f"Independent fourth-iterate closed N fold / full "
            f"adjacency SHA disagreement for {record['index']}")


def verify() -> None:
    cases, _ = source_catalog()
    for case in cases:
        verify_record(case)
        print(f"INDEPENDENT PASS small P4 McKay={case['index']} "
              f"stage=4 vertices={case['p4'][0]}",
              flush=True)
    print("INDEPENDENT CERTIFIED: 98 current small P4 graphs reconstructed "
          "from original graph6, fourth-clique pairwise intersections, "
          "independent complete closed-neighborhood paring, exact full "
          "adjacency SHA-256; no census classification changed", flush=True)


if __name__ == "__main__":
    verify()
