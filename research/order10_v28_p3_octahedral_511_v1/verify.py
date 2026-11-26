"""Independent exact verification of 511-class native octahedral P3 pilot.

Replay all complete O_d projections against independently rebuilt P3
graphs from ORIGINAL ten-vertex graph6, not saved P3 adjacency.
For each FOUND, explicitly verify all antipodal pairs, all cross-edges,
pointwise fixation, and every source edge. O_d is K-divergent for d>=3.
Statuses EXHAUSTED and LIMIT_REACHED give no clique-behavior verdict.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("Cannot optimize away native octahedral replay checks")

import networkx as nx

from research.order10_p3_global_v23_index.independent_verify import independent_p3
from research.order10_p4_crossdepth_o15_v25.verify import git_blob, source_rows
from research.order10_overcap_p3_coaffine_v1.pilot import (
    independent_octahedral_retraction_check,
)
from research.order10_v28_p3_coaffine_all_v1.index import (
    TEN_V28, TEN_V28_BLOB, GLOBAL_INDEX, GLOBAL_INDEX_BLOB, SHARDS,
)
from research.order10_five_p3_native_v1.search import (
    MONOREPO_SHA, RUNTIME_VERSIONS,
)
from research.order10_v28_p3_octahedral_511_v1.search import (
    MAX_STATES, TIME_LIMIT, VALUE_ORDERS,
)


def need(ok: bool, explanation: str) -> None:
    if not ok:
        raise AssertionError(explanation)


def verify_positive(original: dict, result: dict) -> dict:
    """Independently rebuild original P3 and check every map coordinate."""
    i = original["index"]
    G = independent_p3(original["graph6"])
    encoded = nx.to_graph6_bytes(G, header=False).decode("ascii").strip()
    need(tuple(original["p3"]) == (len(G), G.number_of_edges())
         and hashlib.sha256(encoded.encode("ascii")).hexdigest()
         == original["p3_graph6_sha256"],
         "Positive P3 target was not independently reconstructed")
    pairs = result["target_pairs"]
    ret = result["complete_retraction_map"]
    need(isinstance(pairs, list) and
         len(pairs) == result["target_dimension"] >= 3
         and all(isinstance(q, list) and len(q) == 2 for q in pairs)
         and isinstance(ret, list) and len(ret) == len(G)
         and all(type(v) is int and 0 <= v < len(G) for v in ret),
         "Missing full native positive octahedral projection")
    independent_octahedral_retraction_check(
        G,
        tuple(tuple(q) for q in pairs),
        dict(enumerate(ret)),
    )
    need(result["originals_proven_divergent"] == original["members"],
         "Positive class transfer was altered")
    return {
        "representative": i,
        "originals": original["members"],
        "native_policy": result["value_order"],
        "target_O_dimension": len(pairs),
        "source_shape": original["p3"],
        "all_original_edges_verified": G.number_of_edges(),
        "ordinary_retraction_proven": True,
        "original_K_divergent": True,
    }


def verify_batch(index_path: Path, folder: Path) -> dict:
    need(git_blob(TEN_V28.read_bytes()) == TEN_V28_BLOB
         and git_blob(GLOBAL_INDEX.read_bytes()) == GLOBAL_INDEX_BLOB,
         "Canonical source or historical exact P3 archive changed")
    current = source_rows(TEN_V28)
    stiff = {i: row.split()[2] for i, row in current.items()
             if row.split()[1] == "10"}
    need(len(current) == 1043 and len(stiff) == 613,
         "Wrong current ten-v28 original cohort")
    idx = json.loads(index_path.read_text(encoding="utf-8"))
    need(idx["ten_v28_blob"] == TEN_V28_BLOB
         and idx["historical_P3_class_blob"] == GLOBAL_INDEX_BLOB
         and idx["pilot_classes"] == 511
         and idx["pilot_originals"] == 606
         and len(idx["records"]) == 511,
         "Historical 511-class coaffine source index corrupted")
    expected = idx["records"]
    seen = set()
    positives = []
    counts = Counter()
    paths = sorted(folder.glob("p3-octahedral-shard-*.json"))
    need(len(paths) == SHARDS, "Eight native octahedral shards must be present")
    seen_shards = set()
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        shard = data["shard"]
        need(data.get("schema") == 1
             and data.get("kind") == "public_native_Od_retraction_511_P3_classes"
             and type(shard) is int and shard in range(SHARDS)
             and shard not in seen_shards
             and data["shards"] == SHARDS
             and data["solver_commit"] == MONOREPO_SHA
             and data["pinned_solver_source_blobs_verified"] is True
             and data["pinned_dependency_versions"] == RUNTIME_VERSIONS
             and data["source_v28_git_blob"] == TEN_V28_BLOB
             and data["global_P3_class_blob"] == GLOBAL_INDEX_BLOB
             and data["max_states"] == MAX_STATES
             and data["seconds_per_order"] == TIME_LIMIT
             and data["limits_do_not_prove_convergence"] is True,
             "Wrong shard / native solver provenance / status limit policy")
        seen_shards.add(shard)
        scheduled = expected[shard::SHARDS]
        need(data["source_representatives"] == [z["index"] for z in scheduled]
             and data["source_originals"] ==
                 sorted(m for z in scheduled for m in z["members"])
             and len(data["results"]) == 2 * len(scheduled),
             "Native shard is missing original representatives")
        for offset, item in enumerate(scheduled):
            i = item["index"]
            need(i in stiff and stiff[i] == item["graph6"]
                 and i not in seen
                 and all(m in stiff for m in item["members"]),
                 "Unproved or duplicate source original")
            seen.add(i)
            for order, entry in zip(VALUE_ORDERS,
                                    data["results"][2*offset:2*offset+2],
                                    strict=True):
                need(entry["representative"] == i
                     and entry["members"] == item["members"]
                     and entry["p3"] == item["p3"]
                     and entry["p3_graph6_sha256"] == item["p3_graph6_sha256"]
                     and entry["value_order"] == order
                     and entry["status"] in ("FOUND", "EXHAUSTED", "LIMIT_REACHED")
                     and type(entry["states_explored"]) is int
                     and 0 <= entry["states_explored"] <= MAX_STATES
                     and type(entry["assignments_tried"]) is int
                     and entry["assignments_tried"] >= 0
                     and type(entry["arc_revisions"]) is int
                     and entry["arc_revisions"] >= 0,
                     "Native result provenance or P3 original mismatch")
                counts[entry["status"]] += 1
                if entry["status"] == "FOUND":
                    positives.append(verify_positive(item, entry))
                else:
                    need("target_pairs" not in entry
                         and "complete_retraction_map" not in entry
                         and "originals_proven_divergent" not in entry,
                         "A missing positive must not carry a retraction")
    need(seen_shards == set(range(SHARDS)) and len(seen) == 511
         and seen == {v["index"] for v in expected}
         and sum(counts.values()) == 1022,
         "Native octahedral search did not cover 511 classes twice")
    divergent = sorted(set(m for p in positives for m in p["originals"]))
    return {
        "schema": 1,
        "kind": "independently_verified_P3_Od_positive_only_511_class_pilot",
        "historical_input_v28_git_blob": TEN_V28_BLOB,
        "511_exact_P3_classes_covered": True,
        "stiff_originals_represented": 606,
        "native_searches_replayed": 1022,
        "status_counts": dict(counts),
        "all_full_positive_maps_reconstructed_from_original_graph6": True,
        "positive_Od_retractions": positives,
        "new_divergent_originals": divergent,
        "new_divergent_original_count": len(divergent),
        "requires_separate_positive_permanent_certificate_and_promotion": True,
        "no_convergence_inference_from_limit_or_exhaustion": True,
    }


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--index", type=Path, required=True)
    p.add_argument("--directory", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    report = verify_batch(args.index, args.directory)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "native_statuses": report["status_counts"],
        "positive_maps": len(report["positive_Od_retractions"]),
        "divergent_originals": report["new_divergent_original_count"],
        "original_indices": report["new_divergent_originals"],
    }, sort_keys=True), flush=True)
    print("PASS: all 511 P3 classes native O_d retraction statuses and "
          "complete positives independently verified", flush=True)


if __name__ == "__main__":
    main()
