"""Bounded public native coaffine search on all 511 small P3 classes.

Eight independent shards and two built-in native value orderings. Each
FOUND map carries all source-to-source vertex coordinates and a complete
solver-independent ordinary stable-image retraction audit. Positive
expansivity uses either published LNP09 three/connected-summand theorem.
No LIMIT_REACHED or EXHAUSTED result is a K-convergence proof.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("Cannot optimize away exact P3 coaffine pilot checks")

import networkx as nx

from research.order10_five_p3_native_v1.search import (
    MONOREPO_SHA, validate_runtime,
)
from research.order10_three_p3_coaffine_native_v1.verify import (
    audit_positive_map,
)
from research.order10_v28_p3_coaffine_all_v1.orbit_certificates import (
    orbit_certificate,
)

SHARDS = 8
MAX_STATES = 250_000
TIME_LIMIT = 6.0
VALUE_ORDERS = ("label", "fiber")


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise AssertionError(reason)


def search_shard(index_file: Path, shard: int) -> dict:
    need(type(shard) is int and 0 <= shard < SHARDS,
         "Invalid shard number")
    from pycliques import find_coaffine_endomorphism

    versions = validate_runtime()
    data = json.loads(index_file.read_text(encoding="utf-8"))
    need(data.get("schema") == 1
         and data.get("kind") ==
             "current_ten_v28_511_reconstructed_P3_class_coaffine_pilot"
         and data.get("pilot_classes") == 511
         and data.get("pilot_originals") == 606
         and data.get("ten_v28_blob") ==
             "35bb83b56bb8b4fd453b0ba272d354dc6b42e68c"
         and data.get("shards") == SHARDS
         and len(data["records"]) == 511,
         "P3 source class index has invalid historical provenance")
    source_subset = data["records"][shard::SHARDS]
    rows = []
    for i, row in enumerate(source_subset):
        index = row["index"]
        graph = nx.from_graph6_bytes(row["p3_graph6"].encode("ascii"))
        need((len(graph), graph.number_of_edges()) == tuple(row["p3"])
             and hashlib.sha256(
                 row["p3_graph6"].encode("ascii")
             ).hexdigest() == row["p3_graph6_sha256"],
             "Third-iterate graph6 or source dimensions differ")
        for order in VALUE_ORDERS:
            result = find_coaffine_endomorphism(
                graph,
                backend="native",
                value_order=order,
                max_states=MAX_STATES,
                time_limit=TIME_LIMIT,
            )
            status = result.status.name
            need(status in ("FOUND", "EXHAUSTED", "LIMIT_REACHED")
                 and type(result.states_explored) is int
                 and 0 <= result.states_explored <= MAX_STATES
                 and type(result.assignments_tried) is int
                 and result.assignments_tried >= 0
                 and type(result.arc_revisions) is int
                 and result.arc_revisions >= 0,
                 "Malformed native coaffine result or counters")
            item = {
                "original_index": index,
                "members": row["members"],
                "p3": row["p3"],
                "p3_graph6_sha256": row["p3_graph6_sha256"],
                "value_order": order,
                "status": status,
                "states_explored": result.states_explored,
                "assignments_tried": result.assignments_tried,
                "arc_revisions": result.arc_revisions,
            }
            if status == "FOUND":
                need(result.endomorphism is not None,
                     "FOUND status without complete coaffine map")
                images = [result.endomorphism[v] for v in range(len(graph))]
                whole = audit_positive_map(graph, images)
                orbit = orbit_certificate(graph, images)
                item.update({
                    "complete_coaffine_map": images,
                    "whole_stable_image": whole,
                    "invariant_orbit_subgraph": orbit,
                    "proved_divergent_originals": (
                        row["members"] if (
                            whole["expansive_witness"]["proved"]
                            or orbit["expansive_coaffine_subgraph_proved"]
                        ) else []
                    ),
                })
                print(f"FOUND original={index} class={len(row['members'])}"
                      f" stable={whole['stable_order']}"
                      f" divergent={bool(item['proved_divergent_originals'])}"
                      f" order={order}", flush=True)
            else:
                need(result.endomorphism is None,
                     "A negative or limited result cannot contain a map")
            rows.append(item)
        if (i + 1) % 10 == 0:
            print(f"PROGRESS shard={shard} checked={i+1}/"
                  f"{len(source_subset)}", flush=True)

    return {
        "schema": 1,
        "kind": "bounded_native_coaffine_511_p3_class_pilot",
        "pinned_solver_revision": MONOREPO_SHA,
        "installed_solver_source_blobs_verified": True,
        "dependency_versions": versions,
        "ten_v28_blob": data["ten_v28_blob"],
        "historical_P3_class_blob": data["historical_P3_class_blob"],
        "shards": SHARDS,
        "shard": shard,
        "max_states": MAX_STATES,
        "time_limit_seconds_each_order": TIME_LIMIT,
        "source_class_representatives": [row["index"] for row in source_subset],
        "source_original_members": sorted(
            m for row in source_subset for m in row["members"]
        ),
        "results": rows,
        "no_convergence_inference_from_native_negative": True,
    }


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--index", type=Path, required=True)
    p.add_argument("--shard", type=int, choices=range(SHARDS), required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    item = search_shard(args.index, args.shard)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(item, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"PASS: bounded P3 coaffine shard {args.shard} "
          f"classes={len(item['source_class_representatives'])} "
          f"positives={sum(x['status']=='FOUND' for x in item['results'])}",
          flush=True)


if __name__ == "__main__":
    main()
