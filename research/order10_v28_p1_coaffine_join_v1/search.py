"""Recognize expansive coaffine joins already in the first pared clique graph.

Uses the exact existing independent double-enumerator P1 builder for
ALL 613 still-indeterminate stiff ten-originals. Structural targets
are joins of complements of paths/cycles? Here only verified components
of the *complement* that are K2 or C_n (n>=3) are recognized; their
factor coaffinations are explicitly constructed and checked on every
pair. Applies [LNP09, Theorem 3.6] or Theorem 4.6, and Theorem 5.4
when P1 itself is complement(C_n), n>=8.

No coaffine assumption is inferred merely from connectedness.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("Cannot optimize away positive first-iterate join proofs")

import networkx as nx

from research.order10_p4_crossdepth_o15_v25.verify import git_blob, source_rows
from research.order10_p3_global_v23_index.independent_verify import (
    independent_clique_graph, independent_pare,
)

ROOT = Path(__file__).resolve().parents[2]
TEN_V28 = ROOT / "indeterminate_order_10_v28.txt"
TEN_V28_BLOB = "35bb83b56bb8b4fd453b0ba272d354dc6b42e68c"


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise AssertionError(reason)


def current_stiff_sources() -> dict[int, str]:
    need(git_blob(TEN_V28.read_bytes()) == TEN_V28_BLOB,
         "Immutable ten-v28 source Git blob changed")
    rows = source_rows(TEN_V28)
    need(len(rows) == 1043, "Wrong authoritative ten-v28 population")
    stiff = {i: row.split()[2] for i, row in rows.items()
             if row.split()[1] == "10"}
    need(len(stiff) == 613 and list(stiff) == sorted(stiff),
         "Wrong stiff ten-original source cohort")
    return stiff


def reconstruct_P1(original_graph6: str) -> nx.Graph:
    G = nx.from_graph6_bytes(original_graph6.encode("ascii"))
    need(len(G) == 10, "Wrong original order")
    G0 = independent_pare(G)
    need(len(G0) == 10, "Stiff original was unexpectedly dominated")
    K = independent_clique_graph(G0, stage=1, orders=[len(G0)])
    return independent_pare(K)


def component_certificate(H: nx.Graph) -> dict | None:
    """Find explicit complement-component coaffinations on K2 and C_n."""
    n = len(H)
    if n == 2 and H.number_of_edges() == 1:
        vertices = sorted(H)
        alpha = {vertices[0]: vertices[1], vertices[1]: vertices[0]}
        kind = "K2"
    elif n >= 3 and H.number_of_edges() == n and nx.is_connected(H)
            and all(H.degree(v) == 2 for v in H):
        vertices = sorted(H)
        order = [min(vertices)]
        previous = None
        while len(order) < n:
            neighbors = [v for v in H[order[-1]]
                         if v != previous]
            need(neighbors, "Cycle continuation failed")
            next_vertex = min(neighbors)
            need(next_vertex not in order, "Cycle repeated before completion")
            previous = order[-1]
            order.append(next_vertex)
        need(H.has_edge(order[-1], order[0]),
             "Claimed cycle order fails closing edge")
        alpha = {order[j]: order[(j+1)%n] for j in range(n)}
        kind = f"C{n}"
    else:
        return None
    F = nx.complement(H)
    need(set(alpha) == set(H) and set(alpha.values()) == set(H)
         and all(v != alpha[v] and not F.has_edge(v, alpha[v])
                 for v in H)
         and all(F.has_edge(u,v) == F.has_edge(alpha[u],alpha[v])
                 for u in H for v in H),
         "Explicit component symmetry is not a coaffination")
    return {
        "order": n,
        "kind": kind,
        "vertices": sorted(H),
        "coaffination": [alpha[v] for v in sorted(H)],
        "factor_connected": nx.is_connected(F),
    }


def classify_P1(P1: nx.Graph) -> dict | None:
    H = nx.complement(P1)
    factors = []
    for cc in nx.connected_components(H):
        factor = component_certificate(H.subgraph(cc))
        if factor is None:
            return None
        factors.append(factor)
    factors.sort(key=lambda x: (x["order"], x["kind"], x["vertices"]))
    theorem = None
    if len(factors) >= 3:
        theorem = "Larrión--Neumann-Lara--Pizaña 2009, Theorem 3.6"
    elif len(factors) >= 2 and any(x["factor_connected"] for x in factors):
        theorem = "Larrión--Neumann-Lara--Pizaña 2009, Theorem 4.6"
    elif len(factors) == 1 and factors[0]["kind"].startswith("C")
            and factors[0]["order"] >= 8:
        theorem = "Larrión--Neumann-Lara--Pizaña 2009, Theorem 5.4"
    if theorem is None:
        return None

    # Different complement components have no missing cross-edge in P1:
    # the source P1 is exactly the join of all certified coaffine factors.
    for i, a in enumerate(factors):
        for b in factors[i+1:]:
            need(all(P1.has_edge(u,v)
                     for u in a["vertices"] for v in b["vertices"]),
                 "Proposed Zykov sum lacks a cross-edge")
    return {
        "P1_order": len(P1),
        "P1_edges": P1.number_of_edges(),
        "P1_graph6_sha256": hashlib.sha256(
            nx.to_graph6_bytes(P1, header=False).strip()
        ).hexdigest(),
        "complement_components": factors,
        "theorem": theorem,
        "whole_first_pared_clique_graph_expansive": True,
        "original_K_divergent": True,
    }


def scan_all() -> dict:
    sources = current_stiff_sources()
    tested = 0
    positives = []
    for index, original_graph6 in sources.items():
        P1 = reconstruct_P1(original_graph6)
        found = classify_P1(P1)
        tested += 1
        if found is not None:
            positives.append({
                "original_index": index,
                "original_graph6": original_graph6,
                **found,
            })
            print(f"POSITIVE P1 original={index}"
                  f" target={len(P1)}"
                  f" factors={[x['kind'] for x in found['complement_components']]}",
                  flush=True)
    need(tested == 613 and len({x["original_index"] for x in positives})
         == len(positives),
         "Exact first-iterate population is incomplete")
    return {
        "schema": 1,
        "kind": "exact_all_613_stiff_ten_v28_first_iterate_coaffine_join_survey",
        "source_git_blob": TEN_V28_BLOB,
        "originals_checked": tested,
        "positive_count": len(positives),
        "positive_originals": [x["original_index"] for x in positives],
        "positive_theorems": dict(Counter(x["theorem"] for x in positives)),
        "positive_full_structures": positives,
        "all_other_originals_indeterminate": True,
        "not_a_census_promotion": True,
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    proof = scan_all()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(proof, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print("PASS: all 613 stiff ten-v28 first iterates checked for "
          "explicit expansive connected-coaffine joins", flush=True)


if __name__ == "__main__":
    main()
