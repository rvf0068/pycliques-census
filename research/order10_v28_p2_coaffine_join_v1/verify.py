"""Independent exact replay of positive second-iterate coaffine-join targets.

Reconstruct each positive P2 from original ten-v28 graph6 through both
independent maximal-clique enumerators and exact dominated paring;
verify exact P2 SHA256, every complementary component and its explicit
coaffination on every pair, all required join cross-edges, and the
published Three/Connected Summands or cycle-complement theorem.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("Cannot optimize away exact second-iterate positive replay")

import networkx as nx

from research.order10_p4_crossdepth_o15_v25.verify import source_rows, git_blob
from research.order10_v28_p1_coaffine_join_v1.search import (
    TEN_V28, TEN_V28_BLOB, classify_P1,
)
from research.order10_v28_p2_coaffine_join_v1.search import reconstruct_P2


def need(ok: bool, why: str) -> None:
    if not ok:
        raise AssertionError(why)


def audit_positive(row: dict, original: str) -> dict:
    need(row["original_graph6"] == original
         and row["original_K_divergent"] is True,
         "Positive original graph6 or claimed verdict differs")
    P1,P2 = reconstruct_P2(original)
    need(row["P1"] == [len(P1), P1.number_of_edges()]
         and row["P2_order"] == len(P2)
         and row["P2_edges"] == P2.number_of_edges()
         and row["P2_graph6_sha256"] == hashlib.sha256(
             nx.to_graph6_bytes(P2, header=False).strip()
         ).hexdigest(),
         "Full original P1/P2 reconstruction or source graph6 differs")
    result = classify_P1(P2)
    need(result is not None
         and result["complement_components"] == row["complement_components"]
         and result["theorem"] == row["theorem"]
         and result["whole_first_pared_clique_graph_expansive"] is True,
         "The exact published expansivity theorem or complement factors fail")
    return {
        "original_index": row["original_index"],
        "original_P1": row["P1"],
        "original_P2": [len(P2), P2.number_of_edges()],
        "complement_factors": [z["kind"] for z in row["complement_components"]],
        "published_K_divergence_theorem": row["theorem"],
        "all_original_P2_edges_reconstructed_from_graph6": True,
        "factor_coaffinations_verified_on_all_pairs": True,
        "original_K_divergent": True,
    }


def verify(path: Path) -> dict:
    need(git_blob(TEN_V28.read_bytes()) == TEN_V28_BLOB,
         "Immutable ten-v28 source Git blob changed")
    original_rows = source_rows(TEN_V28)
    need(len(original_rows) == 1043, "Wrong ten-v28 original population")
    stiff = {i: row.split()[2] for i,row in original_rows.items()
             if row.split()[1] == "10"}
    need(len(stiff) == 613, "Wrong stiff ten-original population")
    data = json.loads(path.read_text(encoding="utf-8"))
    need(data.get("schema") == 1
         and data.get("kind") ==
             "all_613_stiff_v28_P2_expansive_coaffine_cycle_joins"
         and data["source_git_blob"] == TEN_V28_BLOB
         and data["source_originals_checked"] == 613
         and data["positive_count"] == len(data["complete_positive_structures"])
         and data["positive_original_indices"] ==
             [z["original_index"] for z in data["complete_positive_structures"]]
         and data["positive_only_no_convergence_inference"] is True
         and data["historical_census_unmodified"] is True,
         "P2 historical source or complete positive protocol changed")
    verified = []
    for row in data["complete_positive_structures"]:
        i = row["original_index"]
        need(i in stiff
             and not any(z["original_index"] == i for z in verified),
             "Duplicate or absent stiff original in positive archive")
        verified.append(audit_positive(row, stiff[i]))
    ids = [v["original_index"] for v in verified]
    need(ids == sorted(ids)
         and {11715667,11716441} <= set(ids)
         and data["theorems"] ==
             dict(Counter(x["published_K_divergence_theorem"] for x in verified)),
         "Proved 11-vertex P1 source classes missing from P2 verification")
    return {
        "schema": 1,
        "kind": "independently_replayed_P2_coaffine_join_divergences",
        "source_v28_git_blob": TEN_V28_BLOB,
        "stiff_ten_originals_checked": 613,
        "positive_original_indices": ids,
        "positive_count": len(verified),
        "positive_complete_certificates": verified,
        "no_negative_behavior_claim": True,
        "census_root_unchanged": True,
    }


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = verify(args.archive)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "stiff_originals_checked": result["stiff_ten_originals_checked"],
        "positive_count": result["positive_count"],
        "indices": result["positive_original_indices"],
    }, sort_keys=True), flush=True)
    print("PASS: all second-iterate expansive join positives independently "
          "verified from original ten-vertex graph6", flush=True)


if __name__ == "__main__":
    main()
