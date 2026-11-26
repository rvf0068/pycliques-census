"""Independent aggregate of all 511-class native third-stage coaffine pilots.

Every FOUND map is replayed on independently reconstructed P3 graphs
and all source edges, re-verifying the finite-image retraction, the
coaffine automorphism, and every orbit-summand theorem hypothesis.
The historical complete exact P3 class isomorphisms transfer any
positive to each member, not to nine-core dependents.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("Cannot optimize away exact positive P3 replay")

import networkx as nx

from research.order10_p3_global_v23_index.independent_verify import independent_p3
from research.order10_p4_crossdepth_o15_v25.verify import git_blob, source_rows
from research.order10_three_p3_coaffine_native_v1.verify import audit_positive_map
from research.order10_v28_p3_coaffine_all_v1.orbit_certificates import orbit_certificate
from research.order10_v28_p3_coaffine_all_v1.index import (
    GLOBAL_INDEX, GLOBAL_INDEX_BLOB, TEN_V28, TEN_V28_BLOB,
    P3_UNRECONSTRUCTED, P3_OVERSIZED, SHARDS,
)
from research.order10_v28_p3_coaffine_all_v1.search import (
    MAX_STATES, TIME_LIMIT, VALUE_ORDERS,
)
from research.order10_five_p3_native_v1.search import (
    MONOREPO_SHA, RUNTIME_VERSIONS,
)


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise AssertionError(reason)


def audit_batch(index_path: Path, directory: Path) -> dict:
    need(git_blob(TEN_V28.read_bytes()) == TEN_V28_BLOB
         and git_blob(GLOBAL_INDEX.read_bytes()) == GLOBAL_INDEX_BLOB,
         "Immutable historical source or global P3 class index changed")
    live_rows = source_rows(TEN_V28)
    stiff = {i: row.split()[2] for i, row in live_rows.items()
             if row.split()[1] == "10"}
    need(len(stiff) == 613, "Wrong current stiff ten-original universe")

    idx = json.loads(index_path.read_text(encoding="utf-8"))
    need(idx.get("schema") == 1
         and idx["ten_v28_blob"] == TEN_V28_BLOB
         and idx["historical_P3_class_blob"] == GLOBAL_INDEX_BLOB
         and idx["pilot_classes"] == 511
         and idx["pilot_originals"] == 606
         and len(idx["records"]) == 511,
         "P3 discovery index provenance or total differs")
    old = json.loads(GLOBAL_INDEX.read_text(encoding="utf-8"))
    old_classes = {i: [i] for i in old["singleton_indices"]}
    old_classes.update({
        q["representative"]: [r["index"] for r in q["members"]]
        for q in old["nontrivial_classes"]
    })
    byrep = {}
    for row in idx["records"]:
        i = row["index"]
        need(i not in byrep and i in stiff
             and row["members"] == old_classes[i]
             and all(m in stiff for m in row["members"])
             and row["graph6"] == stiff[i],
             "A pilot class was forged, duplicated or fragmented")
        byrep[i] = row
    need(sum(len(x["members"]) for x in byrep.values()) == 606
         and len(set(m for row in byrep.values()
                     for m in row["members"])) == 606,
         "511 current P3 classes must represent 606 distinct original graphs")
    other_reconstructed = {
        k: v for k, v in old_classes.items() if k in stiff and k not in byrep
    }
    need(set(other_reconstructed) == P3_OVERSIZED
         and sum(len(v) for v in other_reconstructed.values()) == 4,
         "Wrong explicitly excluded three large P3 representatives")
    covered = {m for row in byrep.values() for m in row["members"]}
    covered.update(m for v in other_reconstructed.values() for m in v)
    need(set(stiff) - covered == P3_UNRECONSTRUCTED,
         "Wrong three historically unbuilt P3 original graphs")

    paths = sorted(directory.glob("p3-coaffine-shard-*.json"))
    need(len(paths) == SHARDS, "Exactly eight native search shards required")
    seen_shards = set()
    classes = set()
    status = Counter()
    positives = []
    divergent = set()
    outcomes = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        shard = data["shard"]
        need(data.get("schema") == 1
             and data.get("kind") == "bounded_native_coaffine_511_p3_class_pilot"
             and type(shard) is int and 0 <= shard < SHARDS
             and shard not in seen_shards
             and data.get("shards") == SHARDS
             and data["pinned_solver_revision"] == MONOREPO_SHA
             and data["installed_solver_source_blobs_verified"] is True
             and data["dependency_versions"] == RUNTIME_VERSIONS
             and data["ten_v28_blob"] == TEN_V28_BLOB
             and data["historical_P3_class_blob"] == GLOBAL_INDEX_BLOB
             and data["max_states"] == MAX_STATES
             and data["time_limit_seconds_each_order"] == TIME_LIMIT
             and data["no_convergence_inference_from_native_negative"] is True,
             "Wrong native solver run provenance or search status")
        seen_shards.add(shard)
        scheduled = idx["records"][shard::SHARDS]
        need(data["source_class_representatives"] ==
             [x["index"] for x in scheduled]
             and data["source_original_members"] ==
             sorted(m for x in scheduled for m in x["members"]),
             "Native shard has unexpected or missing P3 host sources")
        need(len(data["results"]) == 2 * len(scheduled),
             "Some required native search ordering was omitted")
        for k, src in enumerate(scheduled):
            i = src["index"]
            need(i not in classes, "Duplicate P3 class representative")
            classes.add(i)
            per_source = data["results"][2*k:2*k+2]
            need([x["value_order"] for x in per_source] == list(VALUE_ORDERS),
                 "The two exact value orderings were not both searched")
            for item in per_source:
                need(item["original_index"] == i
                     and item["members"] == src["members"]
                     and item["p3"] == src["p3"]
                     and item["p3_graph6_sha256"] ==
                         src["p3_graph6_sha256"]
                     and item["status"] in ("FOUND", "EXHAUSTED", "LIMIT_REACHED")
                     and type(item["states_explored"]) is int
                     and 0 <= item["states_explored"] <= MAX_STATES
                     and type(item["assignments_tried"]) is int
                     and item["assignments_tried"] >= 0
                     and type(item["arc_revisions"]) is int
                     and item["arc_revisions"] >= 0,
                     "Malformed claimed native result or original identity")
                status[item["status"]] += 1
                if item["status"] == "FOUND":
                    original = nx.from_graph6_bytes(
                        stiff[i].encode("ascii")
                    )
                    G = independent_p3(stiff[i])
                    computed = nx.to_graph6_bytes(
                        G, header=False
                    ).decode("ascii").strip()
                    need((len(G), G.number_of_edges()) == tuple(src["p3"])
                         and hashlib.sha256(computed.encode("ascii")).hexdigest()
                             == src["p3_graph6_sha256"]
                         and nx.is_connected(original),
                         "Found map was not replayed on authentic independent P3")
                    f = item["complete_coaffine_map"]
                    whole = audit_positive_map(G, f)
                    orbit = orbit_certificate(G, f)
                    need(whole == item["whole_stable_image"]
                         and orbit == item["invariant_orbit_subgraph"],
                         "Native positive P3 map or expansivity logic changed")
                    good = (whole["expansive_witness"]["proved"]
                            or orbit["expansive_coaffine_subgraph_proved"])
                    need(item["proved_divergent_originals"] ==
                         (src["members"] if good else []),
                         "The native claim overstates transferred divergence")
                    positives.append({
                        "representative": i,
                        "value_order": item["value_order"],
                        "stable_image_order": whole["stable_order"],
                        "coaffine_expansive_subgraph_proved": good,
                        "whole_target_theorem": whole["expansive_witness"]["theorem"],
                        "orbit_target_theorem": orbit["published_divergence_theorem"],
                        "originals_if_proved": src["members"] if good else [],
                        "complete_source_edges_checked": G.number_of_edges(),
                    })
                    if good:
                        divergent.update(src["members"])
                else:
                    need("complete_coaffine_map" not in item
                         and "whole_stable_image" not in item
                         and "invariant_orbit_subgraph" not in item
                         and "proved_divergent_originals" not in item,
                         "A negative or limited case must not contain a positive map")
                outcomes.append({
                    "index": i, "order": item["value_order"],
                    "status": item["status"],
                })

    need(seen_shards == set(range(SHARDS))
         and len(classes) == 511
         and classes == set(byrep)
         and sum(status.values()) == 1022,
         "Eight-shard P3 native pilot is not complete")
    return {
        "schema": 1,
        "kind": "independently_verified_511_class_P3_native_coaffine_pilot",
        "stiff_originals_in_ten_v28": 613,
        "exact_P3_class_representatives": 511,
        "originals_represented": 606,
        "oversized_P3_class_representatives_excluded": sorted(P3_OVERSIZED),
        "historical_P3_unreconstructed_originals_excluded":
            sorted(P3_UNRECONSTRUCTED),
        "search_cases_audited": 1022,
        "status_counts": dict(status),
        "positive_coaffine_endomorphisms_replayed": len(positives),
        "proved_K_divergent_originals": sorted(divergent),
        "proved_K_divergent_original_count": len(divergent),
        "positives": positives,
        "complete_source_class_and_value_order_coverage": True,
        "no_convergence_or_nondivergence_inference_from_limits": True,
        "census_remains_v28_pending_separate_positive_promotion": True,
    }


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--index", type=Path, required=True)
    p.add_argument("--directory", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    report = audit_batch(args.index, args.directory)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "native_statuses": report["status_counts"],
        "positive_maps": report["positive_coaffine_endomorphisms_replayed"],
        "divergent_originals": report["proved_K_divergent_original_count"],
        "divergent_indices": report["proved_K_divergent_originals"],
    }, sort_keys=True), flush=True)
    print("PASS: complete 511-class positive P3 coaffine maps and full "
          "historical source coverage independently audited", flush=True)


if __name__ == "__main__":
    main()
