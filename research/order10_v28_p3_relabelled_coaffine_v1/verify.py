"""Independent proof-only replay of deterministic relabelled coaffine maps.

Use pinned original ten-v28 and global exact P3 classes. Reconstruct
all FOUND hosts from original ten-vertex McKay graph6, and check the
complete coaffine maps, stable-image retractions and published
expansivity hypotheses on every source edge. Solver statuses do not
establish K-convergence.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("Cannot optimize away seeded coaffine positive replay")

import networkx as nx

from research.order10_p3_global_v23_index.independent_verify import independent_p3
from research.order10_p4_crossdepth_o15_v25.verify import git_blob, source_rows
from research.order10_three_p3_coaffine_native_v1.verify import audit_positive_map
from research.order10_v28_p3_coaffine_all_v1.index import (
    TEN_V28, TEN_V28_BLOB, GLOBAL_INDEX, GLOBAL_INDEX_BLOB, SHARDS,
)
from research.order10_v28_p3_coaffine_all_v1.orbit_certificates import (
    orbit_certificate,
)
from research.order10_five_p3_native_v1.search import (
    MONOREPO_SHA, RUNTIME_VERSIONS,
)
from research.order10_v28_p3_relabelled_coaffine_v1.search import (
    SEEDS, ORDERS, MAX_STATES, SECONDS, canonical_permutation,
)


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise AssertionError(reason)


def audit_batch(index_path: Path, directory: Path) -> dict:
    need(git_blob(TEN_V28.read_bytes()) == TEN_V28_BLOB
         and git_blob(GLOBAL_INDEX.read_bytes()) == GLOBAL_INDEX_BLOB,
         "Historical frozen ten-v28 or P3 class certificates modified")
    current = source_rows(TEN_V28)
    stiff = {i: row.split()[2] for i, row in current.items()
             if row.split()[1] == "10"}
    need(len(current) == 1043 and len(stiff) == 613,
         "Wrong current ten-v28 original universe")
    idx = json.loads(index_path.read_text(encoding="utf-8"))
    need(idx.get("pilot_classes") == 511
         and idx.get("pilot_originals") == 606
         and idx.get("ten_v28_blob") == TEN_V28_BLOB
         and idx.get("historical_P3_class_blob") == GLOBAL_INDEX_BLOB
         and len(idx.get("records", [])) == 511,
         "Incorrect complete 511-class P3 source index")
    records = idx["records"]
    paths = sorted(directory.glob("p3-relabelled-coaffine-shard-*.json"))
    need(len(paths) == SHARDS, "Exactly eight source shards must be audited")
    shards = set()
    reps = set()
    counts = Counter()
    positive = []
    proved = set()
    perclass = {}
    for path in paths:
        shard_data = json.loads(path.read_text(encoding="utf-8"))
        shard = shard_data["shard"]
        need(shard_data.get("schema") == 1
             and shard_data.get("kind") ==
                 "reproducible_relabeling_public_coaffine_511_P3"
             and type(shard) is int and shard in range(SHARDS)
             and shard not in shards
             and shard_data.get("shards") == SHARDS
             and shard_data["solver_commit"] == MONOREPO_SHA
             and shard_data["installed_solver_git_blobs_verified"] is True
             and shard_data["dependency_versions"] == RUNTIME_VERSIONS
             and shard_data["ten_v28_blob"] == TEN_V28_BLOB
             and shard_data["historical_P3_class_blob"] == GLOBAL_INDEX_BLOB
             and shard_data["seeds"] == list(SEEDS)
             and shard_data["policies"] == list(ORDERS)
             and shard_data["max_states"] == MAX_STATES
             and shard_data["time_limit"] == SECONDS
             and shard_data["no_negative_K_behavior_inference"] is True,
             "Unproven native solver, permutation or budget provenance")
        shards.add(shard)
        assigned = records[shard::SHARDS]
        need(shard_data["source_representatives"] ==
             [a["index"] for a in assigned]
             and shard_data["source_original_members"] ==
             sorted(m for a in assigned for m in a["members"])
             and len(shard_data["results"]) ==
             len(assigned) * len(SEEDS) * len(ORDERS),
             "Missing source original or deterministic native seed")
        for pos, source in enumerate(assigned):
            index = source["index"]
            need(index not in reps and index in stiff
                 and stiff[index] == source["graph6"]
                 and all(m in stiff for m in source["members"]),
                 "Wrong current exact class representative or original")
            reps.add(index)
            subset = shard_data["results"][pos*6:(pos+1)*6]
            for offset, case in enumerate(subset):
                seed = SEEDS[offset//len(ORDERS)]
                policy = ORDERS[offset%len(ORDERS)]
                perm = canonical_permutation(
                    source["p3"][0], index, seed
                )
                need(case["original_index"] == index
                     and case["members"] == source["members"]
                     and case["p3"] == source["p3"]
                     and case["p3_graph6_sha256"] ==
                         source["p3_graph6_sha256"]
                     and case["seed"] == seed
                     and case["policy"] == policy
                     and case["permutation_sha256"] ==
                         hashlib.sha256(bytes(perm)).hexdigest()
                     and case["status"] in
                         ("FOUND", "EXHAUSTED", "LIMIT_REACHED")
                     and type(case["states_explored"]) is int
                     and 0 <= case["states_explored"] <= MAX_STATES
                     and type(case["assignments_tried"]) is int
                     and case["assignments_tried"] >= 0
                     and type(case["arc_revisions"]) is int
                     and case["arc_revisions"] >= 0,
                     "Malformed native search result or deterministic shuffle")
                counts[case["status"]] += 1
                if case["status"] == "FOUND":
                    G = perclass.get(index)
                    if G is None:
                        G = independent_p3(stiff[index])
                        g6 = nx.to_graph6_bytes(
                            G, header=False
                        ).decode("ascii").strip()
                        need((len(G), G.number_of_edges()) ==
                             tuple(source["p3"])
                             and hashlib.sha256(g6.encode("ascii")).hexdigest()
                                 == source["p3_graph6_sha256"],
                             "Found map was not replayed on the original P3")
                        perclass[index] = G
                    f = case["full_map_on_canonical_original"]
                    whole = audit_positive_map(G, f)
                    orbit = orbit_certificate(G, f)
                    need(whole == case["stable_image"]
                         and orbit == case["invariant_orbit_witness"],
                         "Full map, idempotent retraction or theorem changed")
                    good = whole["expansive_witness"]["proved"] or (
                        orbit["expansive_coaffine_subgraph_proved"]
                    )
                    need(case["proved_divergent_originals"] ==
                         (source["members"] if good else []),
                         "Solver claimed a divergent graph with no positive theorem")
                    positive.append({
                        "representative": index,
                        "seed": seed,
                        "policy": policy,
                        "stable_image_order": whole["stable_order"],
                        "expansive_target_proved": bool(good),
                        "theorem": (
                            whole["expansive_witness"]["theorem"]
                            or orbit["published_divergence_theorem"]
                        ),
                        "originals_proved": source["members"] if good else [],
                    })
                    if good:
                        proved.update(source["members"])
                else:
                    need("full_map_on_canonical_original" not in case
                         and "stable_image" not in case
                         and "invariant_orbit_witness" not in case
                         and "proved_divergent_originals" not in case,
                         "Limited or exhausted solver has an unexpected map")
    need(shards == set(range(SHARDS))
         and len(reps) == 511
         and reps == {a["index"] for a in records}
         and sum(counts.values()) == 3066,
         "Complete deterministic 511-class seeded survey is incomplete")
    return {
        "schema": 1,
        "kind": "independent_complete_relabelled_coaffine_P3_positive_audit",
        "exact_classes": len(reps),
        "stiff_ten_originals_represented": 606,
        "independent_native_trials": 3066,
        "statuses": dict(counts),
        "full_positive_maps_independently_replayed": len(positive),
        "divergent_original_indices": sorted(proved),
        "divergent_original_count": len(proved),
        "complete_positives": positive,
        "no_convergence_inference_from_exhausted_or_limited": True,
        "census_unchanged": True,
    }


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--index", type=Path, required=True)
    p.add_argument("--directory", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = audit_batch(args.index, args.directory)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "statuses": result["statuses"],
        "full_maps": result["full_positive_maps_independently_replayed"],
        "divergent_indices": result["divergent_original_indices"],
    }, sort_keys=True), flush=True)
    print("PASS: all 3066 seeded native P3 coaffine outcomes independently "
          "audited on exact original graph6", flush=True)


if __name__ == "__main__":
    main()
