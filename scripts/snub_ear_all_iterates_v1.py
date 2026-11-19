"""Certify an ALL-ITERATE clique-complex homotopy theorem for complete ears.

THEOREM: For any finite connected X and nonempty disjoint anticomplete
COMPLETE subsets A,B, let Y=X+x with N_Y(x)=A union B. Then for
EVERY j >= 0,
    Delta(K^j(Y)) ~= Delta(K^j(X)) wedge S^1.

Proof: the class of "one complete-two-component ear over a graph
dismantling to X" is preserved by K^2. Its two-step closure has
three explicitly treated cases (neither/one/both ear components
maximal). K preserves dominated folds; the intermediate odd
iterate follows from the complete-ear K-homotopy lemma.

This verifier authenticates PR #32 and the full older source chain,
checks the six ORIGINAL level-zero snub ears, and independently
constructs the marked K^2 bridge plus EVERY closed-neighborhood
domination in numerous small-graph examples. No enormous iterate
is constructed and NO convergence/divergence verdict is inferred.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

import networkx as nx

import core9_snub_relative_k7_v1 as previous
import core9_snub_handle_iterates_v1 as early

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS_SOURCE = ROOT / "scripts/core9_snub_relative_k7_v1.py"
PREVIOUS_GIT_BLOB = "ed35c8db9c455da56942195d0ff51692ed05b1b1"
INITIAL_CERT = ROOT / "research/order9_snub_handle_iterates_v1/certificates.json"
PINNED_INITIAL_SHA256 = "16587a7997d377a2c2df9e23c656f9793992436c513e78b5e6e5a9526e385d3d"
EXPECTED_IDS = (2317843, 3148541, 3505942, 4952669, 4953338, 5601875)
EXPECTED_MEMBERS = (70, 114, 133, 86, 196, 111)


def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def max_facets(g: nx.Graph) -> list[frozenset[int]]:
    return previous.maximal_cliques(g)


def K(facets: list[frozenset[int]]) -> nx.Graph:
    return previous.intersection_graph(facets)


def verify_marked_ear_two_step(
    x: nx.Graph, A: set[int], B: set[int],
) -> dict:
    """Complete, independent small-graph checker for K²-ear closure.

    The input is X plus one extra vertex x attached to complete
    anticomplete A,B. Construct K(X), K(Y), K²(X), K²(Y).
    Find the UNIQUE designated bridge facet {a,b} in K(Y).
    Verify its two anticomplete complete link components in K²(Y),
    the induced embedded K²(X) and a dominating old vertex for each
    extra vertex of K²(Y)-bridge.
    """
    if (
        not x or not nx.is_connected(x)
        or not A or not B or A & B or not (A | B) <= set(x)
        or not previous.complete(x, A)
        or not previous.complete(x, B)
        or any(x.has_edge(a, b) for a in A for b in B)
    ):
        raise ValueError("Marked-ear hypotheses invalid")
    if not all(isinstance(v, int) for v in x):
        raise ValueError("Marked-ear checker expects integer graph vertices")
    new = max(x) + 1
    y = x.copy()
    y.add_edges_from((new, u) for u in A | B)

    xf, yf = max_facets(x), max_facets(y)
    yi = {face: j for j, face in enumerate(yf)}
    a_face, b_face = frozenset(A) | {new}, frozenset(B) | {new}
    ai, bi = yi[a_face], yi[b_face]
    bothmax = (frozenset(A) in xf, frozenset(B) in xf)
    # The first old embedding K(X) -> K(Y) may alter the labels of
    # cliques A or B when either was inclusion-maximal in X.
    old_to_new: dict[int, int] = {}
    for i, face in enumerate(xf):
        target = face | {new} if face in (frozenset(A), frozenset(B)) else face
        old_to_new[i] = yi[target]
    jx, jy = K(xf), K(yf)
    if not jy.has_edge(ai, bi):
        raise AssertionError("The ear facets must intersect at the added vertex")
    if any(
        t not in (ai, bi) and jy.has_edge(t, ai) and jy.has_edge(t, bi)
        for t in jy
    ):
        raise AssertionError("Distinguished ear edge has a common old neighbor")

    jxf, jyf = max_facets(jx), max_facets(jy)
    bridge = frozenset((ai, bi))
    if bridge not in jyf:
        raise AssertionError("Designated ear edge is not maximal in K(Y)")
    bridge_idx = jyf.index(bridge)
    k2x, k2y = K(jxf), K(jyf)
    side_a = [
        i for i, facet in enumerate(jyf)
        if i != bridge_idx and ai in facet
    ]
    side_b = [
        i for i, facet in enumerate(jyf)
        if i != bridge_idx and bi in facet
    ]
    if (
        not side_a or not side_b
        or set(side_a) & set(side_b)
        or set(k2y.neighbors(bridge_idx)) != set(side_a) | set(side_b)
        or any(not k2y.has_edge(i, j)
               for side in (side_a, side_b)
               for i, j in combinations(side, 2))
        or any(k2y.has_edge(i, j) for i in side_a for j in side_b)
    ):
        raise AssertionError("K² bridge link fails two-complete-components test")

    PA = {i for i, face in enumerate(xf) if face & A}
    PB = {i for i, face in enumerate(xf) if face & B}
    source_to_dest = []
    for facet in jxf:
        old_image = frozenset(old_to_new[v] for v in facet)
        if not bothmax[0] and facet <= PA:
            extended = old_image | {ai}
        elif not bothmax[1] and facet <= PB:
            extended = old_image | {bi}
        else:
            extended = old_image
        if extended not in jyf:
            raise AssertionError("Old K² maximal-clique extension missing")
        source_to_dest.append(jyf.index(extended))
    if len(source_to_dest) != len(set(source_to_dest)):
        raise AssertionError("Old K² embedding is not injective")
    for i, j in combinations(range(len(jxf)), 2):
        if k2x.has_edge(i, j) != k2y.has_edge(
            source_to_dest[i], source_to_dest[j]
        ):
            raise AssertionError("The older K² graph is not induced")

    # Remove bridge. Extra facets have exact old dominators;
    # deletion is checked against CLOSED neighborhoods.
    work = k2y.copy()
    work.remove_node(bridge_idx)
    old_indices = set(source_to_dest)
    extras = [i for i in work if i not in old_indices]
    for i in extras:
        dominators = [
            d for d in source_to_dest
            if (set(work.neighbors(i)) | {i})
            <= (set(work.neighbors(d)) | {d})
        ]
        if not dominators:
            raise AssertionError("An extra second-iterate clique is not dominated")
        work.remove_node(i)
    if set(work) != old_indices:
        raise AssertionError("K²-ear deletion does not recover exactly the old K² graph")

    return {
        "case_maximal_sides": sum(bothmax),
        "old_k2_order": len(jxf),
        "new_k2_order": len(jyf),
        "bridge_vertex": bridge_idx,
        "bridge_link_component_orders": [len(side_a), len(side_b)],
        "extra_dominated_vertices": len(extras),
        "induced_old_k2": True,
        "deleted_bridge_folds_to_old_k2": True,
    }


def verify_six_all_iterates() -> list[dict]:
    if blob_sha(PREVIOUS_SOURCE.read_bytes()) != PREVIOUS_GIT_BLOB:
        raise ValueError("Merged PR #32 K7 theorem and fold verifier was modified")
    older = previous.verify_six_symbolic_applications()
    if (
        tuple(row["core_id"] for row in older) != EXPECTED_IDS
        or tuple(row["original_order10_members"] for row in older)
        != EXPECTED_MEMBERS
    ):
        raise ValueError("Historical six-core research population changed")

    raw = INITIAL_CERT.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PINNED_INITIAL_SHA256:
        raise ValueError("Merged PR #29 initial-complete-ear certificate changed")
    certificates = json.loads(raw)
    if [r["core_id"] for r in certificates["records"]] != list(EXPECTED_IDS):
        raise ValueError("Earlier initial ear classification changed")

    snub = early.graph("GQyuzw")
    rows = []
    for record, old in zip(certificates["records"], older):
        level0 = record["levels"][0]
        g = early.graph(record["core_graph6"])
        phi = level0["snub_to_core_vertex_map"]
        extra = level0["extra_core_vertices"]
        if (
            len(g) != 9 or len(snub) != 8
            or len(phi) != 8 or len(set(phi)) != 8 or len(extra) != 1
            or level0["link_certificate"]["kind"] != "two_clique_cone_bridge"
        ):
            raise ValueError("The original nine-core is not an eight-vertex ear")
        inverse = {label: i for i, label in enumerate(phi)}
        a, b = (
            {inverse[v] for v in component}
            for component in level0["link_certificate"]["components"]
        )
        x = extra[0]
        if (
            not a or not b or a & b
            or not previous.complete(snub, a)
            or not previous.complete(snub, b)
            or any(snub.has_edge(u, v) for u in a for v in b)
            or {inverse[v] for v in g.neighbors(x)}
            != a | b
        ):
            raise ValueError("Initial ear is not attached along two anticomplete completes")
        for i, j in combinations(range(8), 2):
            if snub.has_edge(i, j) != g.has_edge(phi[i], phi[j]):
                raise ValueError("Snub-to-ninecore base is not induced")

        concrete = verify_marked_ear_two_step(snub, a, b)
        rows.append({
            "core_id": record["core_id"],
            "original_order10_members": old["original_order10_members"],
            "initial_attachment_component_orders": [len(a), len(b)],
            "two_step_induced_and_dismantled_certificate": concrete,
            "relative_all_iterates_homotopy":
                "For all j>=0: Delta(K^j(G)) ~= Delta(K^j(S)) wedge S1",
            "induction_invariant": "marked complete-ear over a dismantling",
            "not_a_clique_divergence_proof": True,
        })
    if sum(row["original_order10_members"] for row in rows) != 710:
        raise ValueError("Wrong original ten-vertex class cohort")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("verify", "json"))
    args = parser.parse_args()
    rows = verify_six_all_iterates()
    if args.action == "json":
        print(json.dumps(rows, sort_keys=True, indent=2))
    else:
        print(
            "VERIFIED all-iterate homotopy theorem for six snub-related "
            "nine-vertex cores (710 represented original ten-vertex graphs): "
            "for every integer j>=0, Delta(K^j(G)) ~= Delta(K^j(S)) wedge S1. "
            "This is NOT a clique convergence/divergence verdict."
        )


if __name__ == "__main__":
    main()
