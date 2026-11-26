"""Independent full-cohort P1 coaffine-join positive-certificate replay.

The original 10-vertex graph6 is read from immutable ten-v28. Both
Bron--Kerbosch and NetworkX maximal-clique sets are independently
compared by the existing historical canonical census code. For every
positive, check the ENTIRE reconstructed P1, each complement component
and each explicit coaffine automorphism, all join cross-edges, and the
exact hypothesis of published LNP09 Theorems 3.6, 4.6 or 5.4.

An unrecognized target is indeterminate, never convergence.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("Cannot optimize away exact first-iterate positive replay")

import networkx as nx

from research.order10_p4_crossdepth_o15_v25.verify import source_rows, git_blob
from research.order10_p3_global_v23_index.independent_verify import (
    independent_clique_graph, independent_pare,
)
from research.order10_v28_p1_coaffine_join_v1.search import (
    TEN_V28, TEN_V28_BLOB,
)

CONTROL_INDICES = (11715667, 11716441)


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise AssertionError(reason)


def audit_positive(row: dict, original: str) -> dict:
    need(row["original_graph6"] == original,
         "A positive source original graph6 differs")
    initial = nx.from_graph6_bytes(original.encode("ascii"))
    need(len(initial) == 10 and nx.is_connected(initial),
         "Source is not a connected ten-vertex graph")
    G0 = independent_pare(initial)
    need(len(G0) == 10,
         "The claimed stiff ten-original has a dominated vertex")
    K1 = independent_clique_graph(G0, stage=1, orders=[len(G0)])
    P1 = independent_pare(K1)
    g6 = nx.to_graph6_bytes(P1, header=False).strip()
    need((len(P1), P1.number_of_edges()) ==
         (row["P1_order"], row["P1_edges"])
         and hashlib.sha256(g6).hexdigest() ==
             row["P1_graph6_sha256"],
         "Original-first-iterate reconstruction fails pinned SHA256")
    H = nx.complement(P1)
    components = row["complement_components"]
    actual = sorted(
        (set(x) for x in nx.connected_components(H)),
        key=lambda x: (len(x), min(x)),
    )
    need(len(components) == len(actual)
         and row["whole_first_pared_clique_graph_expansive"] is True
         and row["original_K_divergent"] is True,
         "A claimed expansive target is not properly formed")
    connected_factors = 0
    for component, actual_vertices in zip(components, actual, strict=True):
        vertices = component["vertices"]
        n = component["order"]
        kind = component["kind"]
        need(vertices == sorted(actual_vertices) and n == len(vertices),
             "Complement-component vertices or order changed")
        Fbar = H.subgraph(vertices)
        F = P1.subgraph(vertices)
        if kind == "K2":
            need(n == 2 and Fbar.has_edge(*vertices),
                 "Alleged octahedral antipodes not an edge in complement")
        elif kind.startswith("C") and kind[1:].isdigit():
            need(n == int(kind[1:]) and n >= 3
                 and nx.is_connected(Fbar)
                 and Fbar.number_of_edges() == n
                 and all(Fbar.degree(u) == 2 for u in Fbar),
                 "Alleged complement component is not an induced cycle")
        else:
            raise AssertionError("Unproved coaffine complement factor kind")
        alpha = dict(zip(vertices, component["coaffination"], strict=True))
        need(set(alpha) == set(alpha.values()) == set(vertices)
             and all(u != alpha[u] and not F.has_edge(u,alpha[u])
                     for u in vertices)
             and all(F.has_edge(u,v) == F.has_edge(alpha[u],alpha[v])
                     for u in vertices for v in vertices),
             "Alleged factor coaffination is not a complete automorphism")
        connected = nx.is_connected(F)
        need(component["factor_connected"] is connected,
             "Published theorem's connectedness hypothesis altered")
        connected_factors += connected
    for i, C in enumerate(components):
        for D in components[i+1:]:
            need(all(P1.has_edge(u,v)
                     for u in C["vertices"] for v in D["vertices"]),
                 "Alleged graph join is missing a cross-edge")
    if len(components) >= 3:
        expected = "Larrión--Neumann-Lara--Pizaña 2009, Theorem 3.6"
    elif len(components) >= 2 and connected_factors:
        expected = "Larrión--Neumann-Lara--Pizaña 2009, Theorem 4.6"
    elif (len(components) == 1 and components[0]["kind"].startswith("C")
          and len(P1) >= 8):
        expected = "Larrión--Neumann-Lara--Pizaña 2009, Theorem 5.4"
    else:
        raise AssertionError("None of the cited divergence theorems applies")
    need(row["theorem"] == expected,
         "The cited K-divergence theorem is inappropriate for the target")
    return {
        "original_index": row["original_index"],
        "source_order": 10,
        "P1": [len(P1), P1.number_of_edges()],
        "target": [x["kind"] for x in components],
        "all_maximal_cliques_cross_checked": True,
        "every_factor_coaffination_checked_on_all_pairs": True,
        "all_join_edges_checked": True,
        "published_theorem": expected,
        "original_K_divergent": True,
    }


def verify(path: Path) -> dict:
    need(git_blob(TEN_V28.read_bytes()) == TEN_V28_BLOB,
         "Immutable authoritative ten-v28 source Git blob differs")
    rows = source_rows(TEN_V28)
    stiff = {i: row.split()[2] for i, row in rows.items()
             if row.split()[1] == "10"}
    need(len(rows) == 1043 and len(stiff) == 613,
         "The stiff ten-original cohort is not 613")
    data = json.loads(path.read_text(encoding="utf-8"))
    need(data.get("schema") == 1
         and data.get("kind") ==
             "exact_all_613_stiff_ten_v28_first_iterate_coaffine_join_survey"
         and data["source_git_blob"] == TEN_V28_BLOB
         and data["originals_checked"] == len(stiff)
         and data["positive_count"] == len(data["positive_full_structures"])
         and data["positive_originals"] ==
             [x["original_index"] for x in data["positive_full_structures"]]
         and data["all_other_originals_indeterminate"] is True
         and data["not_a_census_promotion"] is True,
         "Unproven source enumeration / positive archive provenance")
    found = []
    for row in data["positive_full_structures"]:
        i = row["original_index"]
        need(i in stiff and i not in {z["original_index"] for z in found},
             "Repeated or missing original source in positive archive")
        found.append(audit_positive(row, stiff[i]))
    ids = [x["original_index"] for x in found]
    need(list(ids) == sorted(ids) and
         set(CONTROL_INDICES) <= set(ids),
         "The two historical P3-unreconstructed positive originals disappeared")
    need(data["positive_theorems"] ==
         dict(Counter(z["published_theorem"] for z in found)),
         "The positive theorem composition changed")
    return {
        "schema": 1,
        "kind": "independently_certified_P1_coaffine_K_divergent_ten_originals",
        "ten_v28_immutable_git_blob": TEN_V28_BLOB,
        "stiff_ten_originals_scanned": len(stiff),
        "complete_positive_original_count": len(found),
        "originals_proven_K_divergent": ids,
        "complete_positive_proofs": found,
        "no_negative_K_behavior_from_other_originals": True,
        "no_authoritative_index_change": True,
    }


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = verify(args.archive)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "stiff_originals": result["stiff_ten_originals_scanned"],
        "positives": result["complete_positive_original_count"],
        "indices": result["originals_proven_K_divergent"],
    }, sort_keys=True), flush=True)
    print("PASS: exact all-stiff-ten P1 expansive joins and every positive "
          "original independently reconstructed", flush=True)


if __name__ == "__main__":
    main()
