"""Exact first-two-iterate coaffine join recognizer for all stiff ten-v28.

Reuses the existing independently checked maximal-clique enumeration
and ordinary dominated-vertex paring, then the previously certified
explicit connected-coaffine-join recognizer. Reports only complete
positive witnesses to divergence; other sources remain indeterminate.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("Cannot optimize away first-two-iterate positive proofs")

import networkx as nx

from research.order10_v28_p1_coaffine_join_v1.search import (
    TEN_V28_BLOB, current_stiff_sources,
    reconstruct_P1, classify_P1,
)
from research.order10_p3_global_v23_index.independent_verify import (
    independent_clique_graph, independent_pare,
)


def need(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def reconstruct_P2(original_graph6: str) -> tuple[nx.Graph,nx.Graph]:
    P1 = reconstruct_P1(original_graph6)
    K2 = independent_clique_graph(
        P1, stage=2, orders=[10,len(P1)]
    )
    P2 = independent_pare(K2)
    return P1,P2


def scan_all() -> dict:
    sources = current_stiff_sources()
    positives = []
    computed = 0
    for index, original in sources.items():
        P1,P2 = reconstruct_P2(original)
        computed += 1
        certified = classify_P1(P2)
        if certified is not None:
            positives.append({
                "original_index": index,
                "original_graph6": original,
                "P1": [len(P1), P1.number_of_edges()],
                "P2_order": len(P2),
                "P2_edges": P2.number_of_edges(),
                "P2_graph6_sha256": hashlib.sha256(
                    nx.to_graph6_bytes(P2, header=False).strip()
                ).hexdigest(),
                "complement_components": certified["complement_components"],
                "theorem": certified["theorem"],
                "original_K_divergent": True,
            })
            print(f"POSITIVE P2 original={index} n={len(P2)} "
                  f"factors={[c['kind'] for c in certified['complement_components']]}",
                  flush=True)
    need(computed == len(sources) == 613
         and len(positives) == len(set(z["original_index"] for z in positives)),
         "The exact P2 source cohort was not completely processed")
    return {
        "schema": 1,
        "kind": "all_613_stiff_v28_P2_expansive_coaffine_cycle_joins",
        "source_git_blob": TEN_V28_BLOB,
        "source_originals_checked": len(sources),
        "positive_count": len(positives),
        "positive_original_indices": [z["original_index"] for z in positives],
        "theorems": dict(Counter(z["theorem"] for z in positives)),
        "complete_positive_structures": positives,
        "positive_only_no_convergence_inference": True,
        "historical_census_unmodified": True,
    }


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = scan_all()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "checked": result["source_originals_checked"],
        "positives": result["positive_count"],
        "indices": result["positive_original_indices"],
    }, sort_keys=True), flush=True)
    print("PASS: all 613 stiff original second pared iterates "
          "screened for exact expansive coaffine cycle joins", flush=True)


if __name__ == "__main__":
    main()
