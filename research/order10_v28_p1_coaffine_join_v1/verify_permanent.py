"""Permanent independent replay of two previously skipped-ten-P3 divergent P1 joins.

Does not rely on the expiring CI scan archive. Reconstructs every original
P1 using independent double clique enumerators, checks every target vertex,
full complement join structure, explicit coaffinations and exact theorem.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import networkx as nx

from research.order10_p4_crossdepth_o15_v25.verify import git_blob, source_rows
from research.order10_v28_p1_coaffine_join_v1.search import TEN_V28, TEN_V28_BLOB
from research.order10_v28_p1_coaffine_join_v1.verify import audit_positive

if sys.flags.optimize:
    raise RuntimeError("Cannot optimize away permanent P1 positive replays")

CERT = Path(__file__).with_name("positive_retractions.json")
EXPECTED_INDICES = (11715667, 11716441)


def need(ok: bool, why: str) -> None:
    if not ok:
        raise AssertionError(why)


def verify() -> dict:
    need(git_blob(TEN_V28.read_bytes()) == TEN_V28_BLOB,
         "Immutable ten-v28 input changed")
    rows = source_rows(TEN_V28)
    need(len(rows) == 1043, "Wrong current ten-v28 source population")
    archive = json.loads(CERT.read_text(encoding="utf-8"))
    need(archive.get("schema") == 1
         and archive.get("kind") ==
             "permanent_two_exact_P1_coaffine_join_divergences"
         and archive["ten_v28_git_blob"] == TEN_V28_BLOB
         and archive["originating_CI_run"] == 45746662585
         and archive["positive_count"] == 2
         and archive["positive_originals"] == list(EXPECTED_INDICES)
         and archive["requires_separate_v29_census_promotion"] is True
         and [z["original_index"] for z in archive["positive_full_structures"]]
             == list(EXPECTED_INDICES),
         "Permanent positive source identities or provenance changed")
    results = []
    for item in archive["positive_full_structures"]:
        i = item["original_index"]
        original = item["original_graph6"]
        need(rows[i] == f"{i} 10 {original} - - -",
             "Wrong frozen McKay original graph6")
        result = audit_positive(item, original)
        need(result["P1"] == [11,46]
             and result["target"] == ["K2","K2","C7"]
             and result["original_K_divergent"] is True,
             "The positive ordinary P1 target is not the expected join")
        results.append(result)

    # Reconstruct both P1 separately; an isomorphism is a mathematical
    # cross-check but not used as a substitute for either original proof.
    from research.order10_v28_p1_coaffine_join_v1.search import reconstruct_P1
    P1a = reconstruct_P1(archive["positive_full_structures"][0]["original_graph6"])
    P1b = reconstruct_P1(archive["positive_full_structures"][1]["original_graph6"])
    need(nx.is_isomorphic(P1a, P1b),
         "Two separately proved expansive P1 target graphs differ")
    return {
        "schema": 1,
        "kind": "two_permanent_11_vertex_C7_two_K2_positive_join_proofs",
        "originals_proven_K_divergent": list(EXPECTED_INDICES),
        "all_original_P1s_independently_reconstructed": True,
        "two_P1_targets_exactly_isomorphic": True,
        "complete_positive_proofs": results,
        "census_unchanged_pending_promotion": True,
    }


def main() -> None:
    import json
    print(json.dumps(verify(), indent=2, sort_keys=True))
    print("PASS: two complete P1-to-expansive-O2-join positive theorems "
          "independently certified", flush=True)


if __name__ == "__main__":
    main()
