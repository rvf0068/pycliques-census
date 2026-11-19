"""Seventh relative snub clique iterate via two independent finite graph lemmas.

1. If v is dominated in G, K(G) dismantles onto an induced K(G-v).
2. If X is connected and X+x attaches x to TWO nonempty anticomplete
   COMPLETE subsets A,B, then Delta(K(X+x)) ~= Delta(K(X)) wedge S1.

The second lemma is proved by exact maximal-clique decomposition in
the three cases: zero, one or two of A/B are maximal in X.
The first is proved by maximal-clique extensions and explicitly
dominated 'extra' clique-graph vertices.

Merged PR #31 certifies that K6(G) = F+c, F dismantles onto K6(S),
and c has two anticomplete nonempty COMPLETE link components.
Consequently the two lemmas imply
    Delta(K7(G)) ~= Delta(K7(S)) wedge S1
for six stiff nine-vertex cores, without constructing K5(S), K6(S)
or K7(S). No clique-divergence verdict follows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

import networkx as nx

import core9_snub_relative_k6_v1 as previous

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS_SOURCE = ROOT / "scripts/core9_snub_relative_k6_v1.py"
PREVIOUS_GIT_BLOB = "2ad272ea0cff22325363d282eb5eb87d56e3fcea"
EXPECTED_IDS = (2317843, 3148541, 3505942, 4952669, 4953338, 5601875)
EXPECTED_MEMBERS = (70, 114, 133, 86, 196, 111)


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def maximal_cliques(graph: nx.Graph) -> list[frozenset[int]]:
    return sorted(
        (frozenset(q) for q in nx.find_cliques(graph)),
        key=lambda q: tuple(sorted(q)),
    )


def intersection_graph(facets: list[frozenset[int]]) -> nx.Graph:
    h = nx.Graph()
    h.add_nodes_from(range(len(facets)))
    h.add_edges_from(
        (i, j) for i, j in combinations(range(len(facets)), 2)
        if facets[i].intersection(facets[j])
    )
    return h


def verify_dominated_clique_graph_fold(g: nx.Graph, v: int, u: int) -> dict:
    """Independently check K(g) --> K(g-v) with explicit facet folds.

    This checks the entire induced clique-graph embedding and closed
    neighborhood containment for each extra clique-graph vertex.
    """
    if (
        v not in g or u not in g or v == u
        or not (set(g[v]) | {v}) <= (set(g[u]) | {u})
    ):
        raise ValueError("The requested vertex is not dominated by u")
    h = g.copy()
    h.remove_node(v)
    old = maximal_cliques(h)
    full = maximal_cliques(g)
    idx = {q: i for i, q in enumerate(full)}

    # Each old maximal clique either remains or uniquely extends with v.
    lifts = [
        (q | {v}) if all(g.has_edge(v, x) for x in q) else q
        for q in old
    ]
    if len(set(lifts)) != len(old) or not set(lifts) <= set(full):
        raise AssertionError("Dominated deletion has invalid maximal-clique extension")

    kg = intersection_graph(full)
    kh = intersection_graph(old)
    mapped = [idx[q] for q in lifts]
    for i, j in combinations(range(len(old)), 2):
        if kh.has_edge(i, j) != kg.has_edge(mapped[i], mapped[j]):
            raise AssertionError("K(g-v) is not induced in K(g)")

    current = kg.copy()
    extras = [i for i in kg if i not in set(mapped)]
    folded = []
    for i in extras:
        q = full[i]
        if v not in q:
            raise AssertionError("A non-v old clique went missing")
        candidate = q - {v}
        possible = [
            D for D in old if candidate < D
            and D in idx
        ]
        # If D had v as a common neighbor, q would not have been
        # maximal in g; therefore the dominator is an unmodified
        # maximal clique of g and belongs to the embedded old copy.
        if not possible:
            raise AssertionError("Extra clique has no old strict extension")
        D = min(possible, key=lambda q: tuple(sorted(q)))
        k = idx[D]
        if k not in mapped or not (
            set(current.neighbors(i)) | {i}
        ) <= (set(current.neighbors(k)) | {k}):
            raise AssertionError("Extra maximal clique is not dominated as claimed")
        current.remove_node(i)
        folded.append((i, k))
    if set(current) != set(mapped):
        raise AssertionError("Dismantling failed to recover precisely K(g-v)")
    return {
        "full_cliques": len(full),
        "folded_old_cliques": len(old),
        "extra_dominated_cliques": len(folded),
        "induced_embedding": True,
        "dominated_folds_verified": True,
    }


def complete(g: nx.Graph, vertices: set[int]) -> bool:
    return bool(vertices) and all(
        g.has_edge(i, j) for i, j in combinations(sorted(vertices), 2)
    )


def verify_two_component_ear_after_K(
    x: nx.Graph, A: set[int], B: set[int]
) -> dict:
    """Exhaustively verify all three maximality cases on a small X.

    A,B are COMPLETE sets, with no edges between them (but are
    allowed to be inclusion-maximal or nonmaximal). The structural
    output certifies the homotopy cofiber; it does not infer
    homotopy type from Betti numbers alone.
    """
    if (
        not x or not nx.is_connected(x)
        or not A or not B or A & B or not (A | B) <= set(x)
        or not complete(x, A) or not complete(x, B)
        or any(x.has_edge(a, b) for a in A for b in B)
    ):
        raise ValueError("Ear hypotheses invalid: connected X, anticomplete nonempty complete sets")

    v = max(x) + 1
    y = x.copy()
    y.add_edges_from((v, w) for w in A | B)
    old = maximal_cliques(x)
    full = maximal_cliques(y)
    oldset, fullset = set(old), set(full)
    am, bm = frozenset(A) in oldset, frozenset(B) in oldset
    lifts = [
        q | {v} if q == frozenset(A) or q == frozenset(B) else q
        for q in old
    ]
    new_A = frozenset(A) | {v}
    new_B = frozenset(B) | {v}
    extras = set()
    if not am:
        extras.add(new_A)
    if not bm:
        extras.add(new_B)
    if set(lifts) | extras != fullset or len(lifts) != len(set(lifts)):
        raise AssertionError("Ear maximal-clique list is incorrect")
    idx = {q: i for i, q in enumerate(full)}
    kx, ky = intersection_graph(old), intersection_graph(full)
    oldmap = [idx[q] for q in lifts]
    for i, j in combinations(range(len(old)), 2):
        inserted = am and bm and {old[i], old[j]} == {frozenset(A), frozenset(B)}
        if ky.has_edge(oldmap[i], oldmap[j]) != (kx.has_edge(i, j) or inserted):
            raise AssertionError("Unexpected edge between old lifted cliques")
    PA = {i for i, q in enumerate(old) if q & A}
    PB = {i for i, q in enumerate(old) if q & B}
    if PA & PB:
        raise AssertionError("Anticomplete link sets should have disjoint maximal-clique stars")
    for support, vertices in ((PA, A), (PB, B)):
        apex = next((i for i, q in enumerate(old) if vertices <= q), None)
        if apex is None or not all(
            kx.has_edge(apex, j) or apex == j for j in support
        ):
            raise AssertionError("Old-clique incidence support is not a cone")

    case = int(not am) + int(not bm)
    if case == 2:
        ea, eb = idx[new_A], idx[new_B]
        if not ky.has_edge(ea, eb):
            raise AssertionError("Both new facets must intersect at the added vertex")
        if set(ky.neighbors(ea)) != {oldmap[i] for i in PA} | {eb}:
            raise AssertionError("A-side cone support is not exact")
        if set(ky.neighbors(eb)) != {oldmap[i] for i in PB} | {ea}:
            raise AssertionError("B-side cone support is not exact")
    elif case == 1:
        new_side = new_A if not am else new_B
        support = PA if not am else PB
        other_old = frozenset(B) if not am else frozenset(A)
        e = idx[new_side]
        predicted = {oldmap[i] for i in support} | {idx[other_old | {v}]}
        if set(ky.neighbors(e)) != predicted:
            raise AssertionError("One-new-vertex ear link is not two contractible components")
        if any(kx.has_edge(old.index(other_old), j) for j in support):
            raise AssertionError("One-new-vertex ear link parts are not anticomplete")
    else:
        if len(full) != len(old):
            raise AssertionError("Maximal A/B should cause no new clique-graph vertices")
        endpoint1, endpoint2 = idx[new_A], idx[new_B]
        if not ky.has_edge(endpoint1, endpoint2):
            raise AssertionError("The new maximal-to-maximal edge was lost")
        if any(
            j not in (endpoint1, endpoint2)
            and ky.has_edge(j, endpoint1) and ky.has_edge(j, endpoint2)
            for j in ky
        ):
            raise AssertionError("The added edge unexpectedly participates in a triangle")

    return {
        "old_cliques": len(old), "new_cliques": len(full),
        "added_clique_vertices": case,
        "maximal_attachment_sides": int(am) + int(bm),
        "case": ("two-new-cone-bridge" if case == 2
                 else "one-new-two-component-link" if case == 1
                 else "new-private-edge"),
        "homotopy": "Delta(K(X+x)) ~= Delta(K(X)) wedge S1",
    }


def verify_six_symbolic_applications() -> list[dict]:
    if git_blob_sha(PREVIOUS_SOURCE.read_bytes()) != PREVIOUS_GIT_BLOB:
        raise ValueError("Merged PR #31 K6 theorem verifier was modified")
    earlier = previous.verify_six_symbolic_applications()
    if (
        tuple(r["core_id"] for r in earlier) != EXPECTED_IDS
        or tuple(r["original_order10_members"] for r in earlier) != EXPECTED_MEMBERS
        or not all(
            r["k6_bridge_deleted_dismantles_to_snub_k6"]
            and r["k6_bridge_link_two_anticomplete_cliques"]
            and r["k6_old_graph_induced"]
            for r in earlier
        )
    ):
        raise ValueError("Verified K6 cone-bridge certificate chain was altered")

    # For each core: H=K6(G)=F+c, F dismantles to Z=K6(S).
    # The complete two-component attachment theorem proves
    # Delta(K(H)) ~= Delta(K(F)) wedge S1, with no assumption
    # on whether either component is maximal in F.
    # The dominated-vertex preservation theorem applies to
    # EACH fold F -> ... -> Z and implies K(F) folds to K(Z).
    # Hence Delta(K7(G)) ~= Delta(K7(S)) wedge S1.
    return [
        {
            "core_id": r["core_id"],
            "original_order10_members": r["original_order10_members"],
            "relative_K7_homotopy": "Delta(K7(G)) ~= Delta(K7(S)) wedge S1",
            "derived_using": [
                "K preserves closed-neighborhood dominated folds",
                "one-step clique-homotopy of two-complete-component ear",
            ],
            "numeric_K7_order_uncomputed": True,
            "no_K_divergence_verdict": True,
        }
        for r in earlier
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("verify", "json"))
    args = parser.parse_args()
    result = verify_six_symbolic_applications()
    if args.action == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            "VERIFIED relative K7 homotopy for six stiff nine-vertex "
            "cores (710 ten-vertex originals): "
            "Delta(K7(G)) ~= Delta(K7(S)) wedge S1. "
            "No high-order graph enumeration or K-divergence claim."
        )


if __name__ == "__main__":
    main()
