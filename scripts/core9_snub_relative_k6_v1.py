"""Certify the relative SIXTH clique iterate of six snub-related nine-cores.

New structural theorem: if W=Z+a+b, a~b, N(a)\Z=P, N(b)\Z=Q
with P,Q disjoint nonempty induced cones in connected Z, then

  K(Z) is induced in K(W),
  K(W)-{c} dismantles onto K(Z), where c represents {a,b},
  N_K(W)(c) is the union of two anticomplete nonempty cliques,
  Delta(K(W)) ~= Delta(K(Z)) wedge S^1.

The extra vertices of K(W)-c arise from maximal cliques of Z[P]
or Z[Q] that are not maximal in Z; each has an EXPLICIT old
maximal-clique dominator. The program tests this generic lemma
on small graphs and authenticates the earlier exact K^4/K^5 source
before applying it symbolically to Z=K^5(S).

It DOES NOT materialize K^5(S) or K^6(S), estimate their orders,
or certify divergence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

import networkx as nx

import core9_snub_relative_k5_v1 as previous

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS_SOURCE = ROOT / "scripts/core9_snub_relative_k5_v1.py"
EXPECTED_PREVIOUS_GIT_BLOB = "fddc20451acbf211876883380928b0326b48e15d"
EXPECTED_IDS = (2317843, 3148541, 3505942, 4952669, 4953338, 5601875)
EXPECTED_MEMBERS = (70, 114, 133, 86, 196, 111)
EXPECTED_COMPONENT_ORDERS = (
    (1, 1), (1, 1), (1, 82), (1, 1), (1, 62), (1, 34),
)


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()


def maximal_cliques(g: nx.Graph) -> list[frozenset[int]]:
    return sorted(
        (frozenset(q) for q in nx.find_cliques(g)),
        key=lambda q: tuple(sorted(q)),
    )


def intersection_graph(cliques: list[frozenset[int]]) -> nx.Graph:
    h = nx.Graph()
    h.add_nodes_from(range(len(cliques)))
    h.add_edges_from(
        (i, j) for i, j in combinations(range(len(cliques)), 2)
        if cliques[i] & cliques[j]
    )
    return h


def is_cone(g: nx.Graph, vertices: set[int]) -> bool:
    return bool(vertices) and any(
        all(u == v or g.has_edge(u, v) for v in vertices)
        for u in vertices
    )


def verify_general_cone_bridge(
    z: nx.Graph, p: set[int], q: set[int]
) -> dict:
    """Independently enumerate the full ONE-STEP theorem on small graphs.

    This finite engine checks all maximal cliques, ALL adjacency pairs
    of the induced K(Z) map, the exact extra-clique formula and every
    dominated-vertex certificate after deleting the bridge {a,b}.
    It is a test fixture; no large snub iterate is constructed.
    """
    nodes = set(z)
    if (
        not nodes or not nx.is_connected(z)
        or not p or not q or p & q or not (p | q) <= nodes
        or not is_cone(z, p) or not is_cone(z, q)
    ):
        raise ValueError("Cone-bridge hypotheses invalid: connected Z, disjoint nonempty cone supports")

    zp = maximal_cliques(z.subgraph(p))
    zq = maximal_cliques(z.subgraph(q))
    old = maximal_cliques(z)
    old_set = set(old)
    a = max(nodes) + 1
    b = a + 1
    if a in nodes or b in nodes:
        raise ValueError("Fresh-vertex labels collide")
    w = z.copy()
    w.add_nodes_from((a, b))
    w.add_edge(a, b)
    w.add_edges_from((a, u) for u in p)
    w.add_edges_from((b, u) for u in q)

    full = maximal_cliques(w)
    full_idx = {face: i for i, face in enumerate(full)}
    bridge = frozenset((a, b))
    a_faces = {face | {a} for face in zp}
    b_faces = {face | {b} for face in zq}
    old_images = [
        face | {a} if face <= p else face | {b} if face <= q else face
        for face in old
    ]
    predicted = set(old_images) | a_faces | b_faces | {bridge}
    if predicted != set(full) or len(set(old_images)) != len(old):
        raise AssertionError("Full maximal-clique decomposition or old-facet lift failed")

    kz = intersection_graph(old)
    kw = intersection_graph(full)
    embedded = [full_idx[face] for face in old_images]
    for i, j in combinations(range(len(old)), 2):
        if kz.has_edge(i, j) != kw.has_edge(embedded[i], embedded[j]):
            raise AssertionError("Old clique graph is NOT an induced subgraph")

    bridge_idx = full_idx[bridge]
    side_a = [full_idx[face] for face in a_faces]
    side_b = [full_idx[face] for face in b_faces]
    if not side_a or not side_b:
        raise AssertionError("Bridge endpoints have empty link components")
    if (
        set(kw.neighbors(bridge_idx)) != set(side_a) | set(side_b)
        or set(side_a) & set(side_b)
        or any(not kw.has_edge(i, j) for i, j in combinations(side_a, 2))
        or any(not kw.has_edge(i, j) for i, j in combinations(side_b, 2))
        or any(kw.has_edge(i, j) for i in side_a for j in side_b)
    ):
        raise AssertionError("Bridge does not have two anticomplete clique link components")

    # Each strictly NEW side facet {a}+T with T maximal in Z[P] but
    # not in Z is dominated, after removing bridge c, by an OLD
    # maximal clique D of Z properly extending T. The cone apex in
    # P guarantees D meets every other a-side facet.
    extra = [
        face for face in sorted((a_faces | b_faces) - set(old_images),
                                key=lambda f: tuple(sorted(f)))
    ]
    current = kw.copy()
    current.remove_node(bridge_idx)
    dominations: list[tuple[int, int]] = []
    old_indices = set(embedded)
    for face in extra:
        i = full_idx[face]
        T = face - {a, b}
        candidates = [
            d for d in old
            if T < d and d not in (zp if a in face else zq)
        ]
        if not candidates:
            raise AssertionError("A strict side facet lacks its old maximal-clique extension")
        chosen = min(candidates, key=lambda f: tuple(sorted(f)))
        v = full_idx[chosen]
        if v not in old_indices or not (
            set(current.neighbors(i)) | {i}
        ) <= (set(current.neighbors(v)) | {v}):
            raise AssertionError("The claimed old-clique domination is invalid")
        dominations.append((i, v))
        current.remove_node(i)
    if set(current) != old_indices or not nx.is_connected(current):
        raise AssertionError("Bridge-deleted graph does not fold onto connected K(Z)")

    return {
        "old_cliques": len(old),
        "new_cliques": len(full),
        "bridge_vertex": bridge_idx,
        "extra_side_cliques": len(extra),
        "expected_increment": 1 + len(extra),
        "clique_component_orders": (len(side_a), len(side_b)),
        "domination_count": len(dominations),
        "old_graph_induced": True,
        "bridge_deleted_folds_to_old": True,
    }


def verify_six_symbolic_applications() -> list[dict]:
    # Source code and all earlier source-hash-checked research artifacts
    # are authenticated BEFORE any symbolic use of the general theorem.
    source = PREVIOUS_SOURCE.read_bytes()
    if git_blob_sha(source) != EXPECTED_PREVIOUS_GIT_BLOB:
        raise ValueError("Merged PR #30 K5 certificate verifier was modified")
    previous_result = previous.verify()
    if [r["core_id"] for r in previous_result] != list(EXPECTED_IDS):
        raise ValueError("Previous core cohort differs from the six proved cases")
    if tuple(r["original_order10_members"] for r in previous_result) != EXPECTED_MEMBERS:
        raise ValueError("Previously authenticated original class sizes changed")

    # PR #30 verifies K^4(G)=K^4(S)+x and N(x)=A disjoint_union B,
    # with A,B nonempty COMPLETE and each nonmaximal. Consequently,
    # K^5(G) has precisely two adjacent new vertices a,b. Their
    # supports in K^5(S) are sets of maximal cliques of K^4(S)
    # meeting A and B respectively. Each has a UNIVERSAL vertex:
    # any maximal clique R_A extending A intersects every such
    # maximal clique at A; likewise B. The supports are DISJOINT,
    # since a clique meeting both A and B would contain an edge
    # between the two anticomplete complete sets. K^5(S) is connected
    # because K^4(S) is (already verified in PR #30).
    #
    # These are EXACTLY the premises of the proved cone-bridge lemma.
    answer = []
    for record, component_orders in zip(previous_result, EXPECTED_COMPONENT_ORDERS):
        sizes = tuple(record["attachment_component_orders"])
        if sizes != component_orders:
            raise ValueError("Previous K4 attachment signature was altered")
        singleton_supports = all(size == 1 for size in sizes)
        answer.append({
            "core_id": record["core_id"],
            "original_order10_members": record["original_order10_members"],
            "k4_extra_link_component_orders": list(sizes),
            "k5_two_adjacent_extras": True,
            "k5_old_supports_are_disjoint_nonempty_cones": True,
            "k6_old_graph_induced": True,
            "k6_bridge_deleted_dismantles_to_snub_k6": True,
            "k6_bridge_link_two_anticomplete_cliques": True,
            "k6_homotopy": "Delta(K6(G)) ~= Delta(K6(S)) wedge S1",
            "k6_order_difference_lower_bound": 1,
            "k6_order_difference_upper_bound": 3 if singleton_supports else None,
            "no_divergence_certificate": True,
        })
    if len(answer) != 6 or sum(row["original_order10_members"] for row in answer) != 710:
        raise ValueError("Failed exact six-core transfer coverage")
    return answer


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("verify", "json"))
    args = parser.parse_args()
    results = verify_six_symbolic_applications()
    if args.action == "json":
        print(json.dumps(results, sort_keys=True, indent=2))
    else:
        print(
            "VERIFIED: for six cores (710 original ten-vertex graphs), "
            "Delta(K6(G)) ~= Delta(K6(S)) wedge S1; K6(S) induced in K6(G). "
            "The bridge-deleted graph folds to K6(S). "
            "No K5(S) or K6(S) enumeration; no divergence claim."
        )


if __name__ == "__main__":
    main()
