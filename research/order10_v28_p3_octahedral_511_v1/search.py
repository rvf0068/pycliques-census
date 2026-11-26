"""Native octahedral retraction pilot across 511 surviving exact P3 classes.

Independently of the general coaffine first solution, use the existing
pycliques.find_octahedral_retraction_coaffine backend to demand a
*complete ordinary retraction* onto O_d (d>=3). Such a target is
K-divergent. No solver code is reimplemented. Full positive maps are
independently verified on all source edges before being stored.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("No optimized P3 octahedral proof search")

import networkx as nx

from research.order10_five_p3_native_v1.search import (
    MONOREPO_SHA, validate_runtime,
)
from research.order10_overcap_p3_coaffine_v1.pilot import (
    independent_octahedral_retraction_check,
)
from research.order10_v28_p3_coaffine_all_v1.index import (
    GLOBAL_INDEX_BLOB, TEN_V28_BLOB, SHARDS,
)

MAX_STATES = 250_000
TIME_LIMIT = 6.0
VALUE_ORDERS = ("label", "fiber")


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise AssertionError(reason)


def search_shard(index_file: Path, shard: int) -> dict:
    require(type(shard) is int and 0 <= shard < SHARDS,
            "Unexpected native search shard")
    from pycliques import find_octahedral_retraction_coaffine
    versions = validate_runtime()
    idx = json.loads(index_file.read_text(encoding="utf-8"))
    require(idx.get("schema") == 1
            and idx.get("kind") ==
                "current_ten_v28_511_reconstructed_P3_class_coaffine_pilot"
            and idx.get("pilot_classes") == 511
            and idx.get("pilot_originals") == 606
            and idx.get("ten_v28_blob") == TEN_V28_BLOB
            and idx.get("historical_P3_class_blob") == GLOBAL_INDEX_BLOB
            and idx.get("shards") == SHARDS
            and len(idx.get("records", [])) == 511,
            "Authenticated historical P3 source index is inconsistent")
    assigned = idx["records"][shard::SHARDS]
    records = []
    for n, original in enumerate(assigned):
        G = nx.from_graph6_bytes(original["p3_graph6"].encode("ascii"))
        require((len(G), G.number_of_edges()) == tuple(original["p3"])
                and hashlib.sha256(
                    original["p3_graph6"].encode("ascii")
                ).hexdigest() == original["p3_graph6_sha256"],
                "Wrong original third-iterate source")
        for order in VALUE_ORDERS:
            result = find_octahedral_retraction_coaffine(
                G,
                backend="native",
                value_order=order,
                min_dimension=3,
                max_states=MAX_STATES,
                time_limit=TIME_LIMIT,
            )
            status = result.status.name
            require(status in ("FOUND", "EXHAUSTED", "LIMIT_REACHED")
                    and type(result.states_explored) is int
                    and 0 <= result.states_explored <= MAX_STATES
                    and type(result.assignments_tried) is int
                    and result.assignments_tried >= 0
                    and type(result.arc_revisions) is int
                    and result.arc_revisions >= 0,
                    "Malformed original native solver status or state counters")
            row = {
                "representative": original["index"],
                "members": original["members"],
                "p3": original["p3"],
                "p3_graph6_sha256": original["p3_graph6_sha256"],
                "value_order": order,
                "status": status,
                "states_explored": result.states_explored,
                "assignments_tried": result.assignments_tried,
                "arc_revisions": result.arc_revisions,
            }
            if status == "FOUND":
                require(result.dimension is not None
                        and result.dimension >= 3
                        and result.retraction is not None
                        and result.antipodal_pairs is not None,
                        "FOUND native octahedral result lacks complete projection")
                pairs = [tuple(q) for q in result.antipodal_pairs]
                retraction = result.retraction
                independent_octahedral_retraction_check(G, pairs, retraction)
                require(result.dimension == len(pairs),
                        "Native target does not have exactly d antipodal pairs")
                row.update({
                    "target_dimension": result.dimension,
                    "target_pairs": [list(q) for q in pairs],
                    "complete_retraction_map":
                        [retraction[i] for i in range(len(G))],
                    "originals_proven_divergent": original["members"],
                })
                print(f"POSITIVE P3 O{result.dimension} rep={original['index']} "
                      f"members={len(original['members'])} order={order}",
                      flush=True)
            else:
                require(result.retraction is None
                        and result.antipodal_pairs is None,
                        "LIMIT/EXHAUSTED native result has a purported map")
            records.append(row)
        if (n + 1) % 10 == 0:
            print(f"PROGRESS octahedral shard={shard} "
                  f"classes={n+1}/{len(assigned)}", flush=True)
    return {
        "schema": 1,
        "kind": "public_native_Od_retraction_511_P3_classes",
        "solver_commit": MONOREPO_SHA,
        "pinned_solver_source_blobs_verified": True,
        "pinned_dependency_versions": versions,
        "source_v28_git_blob": TEN_V28_BLOB,
        "global_P3_class_blob": GLOBAL_INDEX_BLOB,
        "shards": SHARDS,
        "shard": shard,
        "max_states": MAX_STATES,
        "seconds_per_order": TIME_LIMIT,
        "source_representatives": [x["index"] for x in assigned],
        "source_originals": sorted(m for x in assigned for m in x["members"]),
        "results": records,
        "limits_do_not_prove_convergence": True,
    }


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--index", type=Path, required=True)
    p.add_argument("--shard", type=int, choices=range(SHARDS), required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    data = search_shard(args.index, args.shard)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"PASS: pinned native octahedral shard {args.shard} "
          f"classes={len(data['source_representatives'])} "
          f"found={sum(row['status']=='FOUND' for row in data['results'])}",
          flush=True)


if __name__ == "__main__":
    main()
