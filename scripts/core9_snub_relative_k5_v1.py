"""Prove the RELATIVE fifth-iterate snub handle theorem without constructing K^5.

Depends only on the already completed and SHA-256-pinned K^0,...,K^4
induced-subgraph/attachment certificates from merged PR #29. Reconstruct
K^4(S) as the intersection graph of all K^3(S) maximal cliques (1,076
vertices) using bitsets, check the old graph is connected, and find
explicit outside common-neighbor witnesses showing that BOTH clique
components of the extra vertex's link are NOT maximal in K^4(S).

The general two-clique extension lemma then certifies
  K^5(G) = K^5(S) with exactly two additional adjacent clique-vertices,
  Delta(K^5(G)) ~ Delta(K^5(S)) wedge S^1,
without enumerating the potentially massive maximal cliques of K^4(S).
Neither statement implies K-divergence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import networkx as nx

import core9_snub_handle_iterates_v1 as prior

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "research/order9_snub_handle_iterates_v1/certificates.json"
INPUT_MANIFEST = ROOT / "research/order9_snub_handle_iterates_v1/manifest.json"
PINNED_INPUT_SHA256 = "16587a7997d377a2c2df9e23c656f9793992436c513e78b5e6e5a9526e385d3d"

# Maximal-clique indices use the stable sorting convention of merged PR #29.
# Each (size, extending_vertex) pair certifies one of the two link cliques.
# Each extending vertex lies outside its component and meets every member.
EXPECTED_WITNESSES: dict[int, tuple[tuple[int, int], tuple[int, int]]] = {
    2317843: ((1, 0), (1, 1)),
    3148541: ((1, 0), (1, 243)),
    3505942: ((1, 0), (82, 243)),
    4952669: ((1, 0), (1, 243)),
    4953338: ((1, 243), (62, 0)),
    5601875: ((1, 0), (34, 534)),
}


def frozen_input() -> list[dict]:
    data = INPUT.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if actual != PINNED_INPUT_SHA256:
        raise ValueError("Previous exact K0-K4 certificates changed")
    meta = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
    if meta["outputs_sha256"]["certificates.json"] != PINNED_INPUT_SHA256:
        raise ValueError("Previous source manifest does not authenticate certificates")
    cert = json.loads(data)
    if (
        cert["no_all_iterate_theorem"] is not True
        or cert["no_new_K_divergence_verdicts"] is not True
        or cert["original_ten_graphs_represented"] != 710
        or [r["core_id"] for r in cert["records"]] != list(EXPECTED_WITNESSES)
    ):
        raise ValueError("Unexpected previous finite theorem or six-core population")
    return cert["records"]


def snub_k4_facets() -> list[frozenset[int]]:
    """Label K^4(S) by the sorted maximal cliques of K^3(S)."""
    h = prior.graph("GQyuzw")
    for _ in range(3):
        h = prior.clique_graph_from_facets(prior.facets(h))
    f = prior.facets(h)
    if len(h) != 56 or len(f) != 1076:
        raise ValueError("Unexpected previous snub iterate and its maximal cliques")
    # The two-component gluing theorem needs the old complex connected.
    # Exact union-find over facet intersections checks this without K4.
    prior.require_connected_clique_graph_from_facets(f)
    return f


def verify_nonmaximal_components(
    f: list[frozenset[int]], components: list[list[int]]
) -> tuple[tuple[int, int], tuple[int, int]]:
    """Find concrete old K4 vertices extending each component clique.

    A clique C of X is not maximal iff some vertex outside C is
    adjacent to every vertex in C. At K4(S), vertices are K3 facets
    and adjacency is their NONEMPTY intersection.
    """
    if len(components) != 2 or any(not component for component in components):
        raise ValueError("Expected two nonempty components of the exact link")
    n = len(f)
    bits = [sum(1 << vertex for vertex in facet) for facet in f]
    all_labels = set(range(n))
    if any(
        len(set(comp)) != len(comp) or not set(comp) <= all_labels
        for comp in components
    ) or set(components[0]).intersection(components[1]):
        raise ValueError("Malformed or overlapping link components")
    if any(
        not (bits[i] & bits[j])
        for component in components
        for index, i in enumerate(component)
        for j in component[index + 1 :]
    ):
        raise ValueError("An alleged link component is not a complete graph")
    if any(
        bits[i] & bits[j]
        for i in components[0] for j in components[1]
    ):
        raise ValueError("The two link cliques are not graph-disjoint")
    answer = []
    for component in components:
        inside = set(component)
        candidates = [
            vertex for vertex in range(n)
            if vertex not in inside and all(
                bits[vertex] & bits[i] for i in component
            )
        ]
        if not candidates:
            raise ValueError("Attachment component may be a maximal clique")
        answer.append((len(component), candidates[0]))
    return answer[0], answer[1]


def verify() -> list[dict]:
    rows = frozen_input()
    f = snub_k4_facets()
    result = []
    for r in rows:
        level = r["levels"][4]
        if (
            level["iterate"] != 4
            or (level["snub_order"], level["core_order"]) != (1076, 1077)
            or level["link_certificate"]["kind"] != "two_clique_cone_bridge"
            or len(level["extra_core_vertices"]) != 1
            or len(level["snub_to_core_vertex_map"]) != 1076
            or len(set(level["snub_to_core_vertex_map"])) != 1076
        ):
            raise ValueError("Previous fourth-level induced embedding is incomplete")
        computed = verify_nonmaximal_components(
            f, level["link_certificate"]["components"]
        )
        expected = EXPECTED_WITNESSES[r["core_id"]]
        if computed != expected:
            raise ValueError(f"Incorrect maximal-clique extension witnesses for {r['core_id']}")
        result.append({
            "core_id": r["core_id"],
            "original_order10_members": r["original_order10_members"],
            "attachment_component_orders": [p[0] for p in computed],
            "strict_extension_vertices": [p[1] for p in computed],
            "exact_relative_K5_added_vertices": 2,
            "relative_K5_clique_complex": "Delta(K5(G)) ~= Delta(K5(S)) wedge S1",
        })
    if len(result) != 6 or sum(r["original_order10_members"] for r in result) != 710:
        raise ValueError("Six certified relative K5 classes do not cover 710 originals")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("verify", "json"))
    args = parser.parse_args()
    results = verify()
    if args.action == "json":
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        print(
            "VERIFIED six strict K4 link extensions: "
            "K5(G) has exactly two more vertices than K5(S), "
            "and the fifth clique complexes differ by a wedge S1. "
            "No K5(S) enumeration and no divergence claim."
        )


if __name__ == "__main__":
    main()
