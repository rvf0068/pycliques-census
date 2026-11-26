"""Reproducible label-reordering pilot for existing public native coaffine solver.

The native general solver stops at its FIRST valid coaffine weak
endomorphism, commonly a four-vertex nonexpansive stable image. Changing
vertex insertion order is a legitimate deterministic search-policy
variation, not a new solver. Full FOUND maps are expressed in ORIGINAL
canonical P3 coordinates, independently verified and preserved.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import sys

if sys.flags.optimize:
    raise RuntimeError("Cannot optimize away relabeled coaffine proof checks")

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
from research.order10_v28_p3_coaffine_all_v1.index import (
    TEN_V28_BLOB, GLOBAL_INDEX_BLOB, SHARDS,
)

SEEDS = (1, 2, 3)
ORDERS = ("label", "fiber")
MAX_STATES = 150_000
SECONDS = 2.0


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise AssertionError(reason)


def canonical_permutation(n: int, index: int, seed: int) -> list[int]:
    need(type(index) is int and index > 0 and seed in SEEDS and n > 0,
         "Invalid deterministic native source relabeling")
    order = list(range(n))
    random.Random((index << 8) ^ seed).shuffle(order)
    need(sorted(order) == list(range(n)),
         "A search-order permutation is not a full bijection")
    return order


def search_shard(index_file: Path, shard: int) -> dict:
    need(type(shard) is int and 0 <= shard < SHARDS,
         "Wrong source partition number")
    from pycliques import find_coaffine_endomorphism
    versions = validate_runtime()
    idx = json.loads(index_file.read_text(encoding="utf-8"))
    need(idx.get("schema") == 1
         and idx.get("pilot_classes") == 511
         and idx.get("pilot_originals") == 606
         and idx.get("ten_v28_blob") == TEN_V28_BLOB
         and idx.get("historical_P3_class_blob") == GLOBAL_INDEX_BLOB
         and idx.get("shards") == SHARDS
         and len(idx.get("records", [])) == 511,
         "Historical exact P3 source index differs")
    scheduled = idx["records"][shard::SHARDS]
    rows = []
    for count, source in enumerate(scheduled):
        G = nx.from_graph6_bytes(source["p3_graph6"].encode("ascii"))
        n = len(G)
        need(set(G) == set(range(n))
             and [n, G.number_of_edges()] == source["p3"]
             and hashlib.sha256(
                 source["p3_graph6"].encode("ascii")
             ).hexdigest() == source["p3_graph6_sha256"],
             "Source canonical third-iterate graph6 is incorrect")
        for seed in SEEDS:
            perm = canonical_permutation(n, source["index"], seed)
            shuffled = nx.Graph()
            shuffled.add_nodes_from(perm)
            shuffled.add_edges_from(G.edges())
            need(set(shuffled) == set(G)
                 and len(shuffled) == n
                 and shuffled.number_of_edges() == G.number_of_edges()
                 and all(shuffled.has_edge(u,v) for u,v in G.edges()),
                 "Reordered graph changed its edge set")
            permutation_sha = hashlib.sha256(bytes(perm)).hexdigest()
            for policy in ORDERS:
                result = find_coaffine_endomorphism(
                    shuffled,
                    backend="native",
                    value_order=policy,
                    max_states=MAX_STATES,
                    time_limit=SECONDS,
                )
                status = result.status.name
                need(status in ("FOUND", "EXHAUSTED", "LIMIT_REACHED")
                     and type(result.states_explored) is int
                     and 0 <= result.states_explored <= MAX_STATES
                     and type(result.assignments_tried) is int
                     and result.assignments_tried >= 0
                     and type(result.arc_revisions) is int
                     and result.arc_revisions >= 0,
                     "Invalid pinned native search result")
                rec = {
                    "original_index": source["index"],
                    "members": source["members"],
                    "p3": source["p3"],
                    "p3_graph6_sha256": source["p3_graph6_sha256"],
                    "seed": seed,
                    "permutation_sha256": permutation_sha,
                    "policy": policy,
                    "status": status,
                    "states_explored": result.states_explored,
                    "assignments_tried": result.assignments_tried,
                    "arc_revisions": result.arc_revisions,
                }
                if status == "FOUND":
                    f = result.endomorphism
                    need(isinstance(f, dict) and set(f) == set(G),
                         "Native FOUND omitted the original full vertex map")
                    images = [f[i] for i in range(n)]
                    whole = audit_positive_map(G, images)
                    orbit = orbit_certificate(G, images)
                    positive = (whole["expansive_witness"]["proved"]
                                or orbit["expansive_coaffine_subgraph_proved"])
                    rec.update({
                        "full_map_on_canonical_original": images,
                        "stable_image": whole,
                        "invariant_orbit_witness": orbit,
                        "proved_divergent_originals":
                            source["members"] if positive else [],
                    })
                    if positive:
                        print(f"EXPANSIVE original={source['index']}"
                              f" class={len(source['members'])}"
                              f" seed={seed} policy={policy}"
                              f" image={whole['stable_order']}", flush=True)
                else:
                    need(result.endomorphism is None,
                         "Unexpected witness on negative/limited status")
                rows.append(rec)
        if (count + 1) % 10 == 0:
            print(f"PROGRESS shard={shard} {count+1}/{len(scheduled)}",
                  flush=True)
    return {
        "schema": 1,
        "kind": "reproducible_relabeling_public_coaffine_511_P3",
        "solver_commit": MONOREPO_SHA,
        "installed_solver_git_blobs_verified": True,
        "dependency_versions": versions,
        "ten_v28_blob": TEN_V28_BLOB,
        "historical_P3_class_blob": GLOBAL_INDEX_BLOB,
        "shard": shard,
        "shards": SHARDS,
        "seeds": list(SEEDS),
        "policies": list(ORDERS),
        "max_states": MAX_STATES,
        "time_limit": SECONDS,
        "source_representatives": [x["index"] for x in scheduled],
        "source_original_members": sorted(
            m for x in scheduled for m in x["members"]
        ),
        "results": rows,
        "no_negative_K_behavior_inference": True,
    }


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--index", type=Path, required=True)
    p.add_argument("--shard", type=int, choices=range(SHARDS), required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = search_shard(args.index, args.shard)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("PASS: deterministic relabeling shard "
          f"{args.shard} classes={len(result['source_representatives'])} "
          f"trials={len(result['results'])}", flush=True)


if __name__ == "__main__":
    main()
