"""Four elementary target-screening certificates on oversized P3 cores.

For a hypothetical ordinary retraction X -> O_d, with H=complement(X),
the target endpoints S induce exactly d independent edges in H and
totally dominate H.  If an H-vertex v has a unique neighbor s in S,
its image is forced to be the antipode of s.  If two such forced images
are antipodes but their preimages are NOT adjacent in H, this specified
target S is impossible.

These are four *candidate-specific obstructions*. They do NOT rule
out other target octahedra or establish K-convergence.
"""
from __future__ import annotations

import hashlib
import json
import sys

if sys.flags.optimize:
    raise RuntimeError("Proof assertions must not be optimized away")

import networkx as nx

from research.order10_overcap_p3_coaffine_v1.pilot import source_catalog


# Each candidate S is a total dominating induced matching in H, but
# is NOT the image of an octahedral retraction: check the forced pair.
# Format: index -> (induced antipodal H-edges, (u,v,a,b)).
# This means N_H(u) cap S={b}, N_H(v) cap S={a}, uv not in E(H).
CANDIDATE_CERTIFICATES = {
    11505012: (
        ((117, 155), (23, 64), (54, 198), (136, 182),
         (94, 206), (119, 162), (0, 225), (28, 211)),
        (56, 154, 117, 155),
    ),
    11595632: (
        ((14, 119), (58, 156), (61, 71), (20, 180),
         (115, 131), (24, 168), (13, 143)),
        (12, 86, 14, 119),
    ),
    11709142: (
        ((99, 15), (37, 109), (11, 56),
         (46, 127), (48, 82), (53, 95)),
        (91, 2, 99, 15),
    ),
    11713984: (
        ((0, 156), (99, 55), (36, 26), (39, 122),
         (8, 141), (135, 48), (108, 127), (148, 63)),
        (24, 160, 0, 156),
    ),
}


def require(value: bool, explanation: str) -> None:
    if not value:
        raise AssertionError(explanation)


def verify_candidate(
    graph: nx.Graph,
    matching: tuple[tuple[int, int], ...],
    conflict: tuple[int, int, int, int],
) -> dict:
    """Recompute the exact necessary conditions, not merely a signature."""
    n = len(graph)
    require(set(graph) == set(range(n)), "Expected canonical P3 labels")
    H = nx.complement(graph)
    S = [v for pair in matching for v in pair]
    endpoints = set(S)
    require(len(matching) >= 3 and len(S) == len(endpoints)
            and all(v in H for v in S), "Malformed target endpoint set")

    target_H = H.subgraph(endpoints)
    require(target_H.number_of_edges() == len(matching)
            and all(target_H.has_edge(a, b) for a, b in matching)
            and all(degree == 1 for _, degree in target_H.degree()),
            "Target endpoints are not an induced matching in H")

    # Every v (including selected vertices) has an H-neighbor in S.
    neighbor_sets = {
        v: set(H[v]) & endpoints for v in H
    }
    require(all(neighbor_sets.values()),
            "Target matching does not totally dominate complement H")

    u, v, a, b = conflict
    require((a, b) in matching or (b, a) in matching,
            "Conflict is not associated with a selected antipodal pair")
    require(u != v and u in H and v in H
            and neighbor_sets[u] == {b}
            and neighbor_sets[v] == {a}
            and not H.has_edge(u, v),
            "Proposed unique-neighbor contradiction is not exact")

    # If a retraction fixed S, u would have to map to a and
    # v to b, contradicting that uv is an edge of X.
    forced = sum(len(s) == 1 for s in neighbor_sets.values())
    return {
        "p3_vertices": n,
        "p3_edges": graph.number_of_edges(),
        "matching_edges": len(matching),
        "complement_edges": H.number_of_edges(),
        "complement_triangles": sum(nx.triangles(H).values()) // 3,
        "all_complement_vertices_totally_dominated": True,
        "vertices_with_forced_image": forced,
        "forced_conflict": {"u": u, "v": v,
                            "would_map_u_to": a, "would_map_v_to": b},
        "specified_target_cannot_be_a_retract": True,
    }


def verify_all() -> dict:
    sources = source_catalog()
    expected = (11505012, 11595632, 11709142, 11713984)
    require(tuple(sorted(CANDIDATE_CERTIFICATES)) == expected,
            "Missing or unexpected proof-only candidate")
    report = {}
    for index in expected:
        entry = sources[index]
        graph6 = entry["p3_graph6"]
        graph = nx.from_graph6_bytes(graph6.encode("ascii"))
        require([len(graph), graph.number_of_edges()] == list(entry["p3"]),
                "Source P3 graph6 does not match frozen dimensions")
        matching, conflict = CANDIDATE_CERTIFICATES[index]
        data = verify_candidate(graph, matching, conflict)
        data["p3_graph6_sha256"] = hashlib.sha256(
            graph6.encode("ascii")).hexdigest()
        data["original_mckay_index"] = index
        report[index] = data
    return {
        "schema": 1,
        "kind": "four_proved_specific_matching_target_obstructions",
        "all_four_H_have_total_dominating_induced_matchings": True,
        "all_four_display_implicit_forced_nonedge_conflicts": True,
        "proof_scope": "only the four specified induced matchings",
        "cannot_promote_any_census_classification": True,
        "records": [report[i] for i in expected],
    }


if __name__ == "__main__":
    print(json.dumps(verify_all(), sort_keys=True, indent=2))
    print("PASS: four exact total-dominating-matchings and four "
          "candidate-specific forced-image conflicts", flush=True)
