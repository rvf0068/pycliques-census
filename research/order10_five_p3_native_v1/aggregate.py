"""Replay ten distinct bounded octahedral searches and all positive witnesses.

A FOUND result is independently proven from the complete map, while
LIMIT_REACHED is only an attempt.  EXHAUSTED excludes O_d for that original
third-iterate graph.  The two branch orderings may return different maps.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("No optimized aggregate proof execution")

import networkx as nx

from research.order10_five_p3_native_v1.search import (
    MONOREPO_SHA, MAX_STATES, SECONDS, REMAINING, VALUE_ORDERS, require,
    RUNTIME_VERSIONS, PYCLIQUES_SOURCE_GIT_BLOBS,
)
from research.order10_overcap_p3_coaffine_v1.pilot import (
    independent_octahedral_retraction_check, source_catalog,
)


def replay(files: list[Path]) -> dict:
    require(len(files) == len(REMAINING) * len(VALUE_ORDERS),
            "Expected exactly ten distinct bounded search reports")
    originals = source_catalog()
    seen = set()
    results = {}
    for path in files:
        rec = json.loads(path.read_text(encoding="utf-8"))
        i, order = rec["original_mckay"], rec["search_policy"]
        key = (i, order)
        require(i in REMAINING and order in VALUE_ORDERS
                and key not in seen, "Unexpected or duplicated P3 search assignment")
        seen.add(key)
        require(rec["solver_revision"] == MONOREPO_SHA
                and type(rec["max_states"]) is int
                and rec["max_states"] == MAX_STATES
                and type(rec["time_limit_seconds"]) in (int, float)
                and rec["time_limit_seconds"] == SECONDS,
                "Native monorepo revision, state or time budget altered")
        require(
            rec.get("installed_solver_source_blobs_verified") is True
            and rec.get("dependency_versions") == RUNTIME_VERSIONS
            and len(PYCLIQUES_SOURCE_GIT_BLOBS) == 7,
            "The native pilot lacked exact runtime distribution and source "
            "blob verification",
        )
        src = originals[i]
        graph = nx.from_graph6_bytes(src["p3_graph6"].encode("ascii"))
        H = nx.complement(graph)
        require(
            rec["original_graph6"] == src["graph6"]
            and rec["p3_dimensions"] == list(src["p3"])
            and rec["p3_graph6_sha256"] ==
                hashlib.sha256(src["p3_graph6"].encode("ascii")).hexdigest()
            and rec["complement_edges"] == H.number_of_edges()
            and rec["complement_triangle_count"] ==
                sum(nx.triangles(H).values()) // 3
            and rec["complement_connected"] == nx.is_connected(H),
            "Source graph6, adjacency, or complement structure changed",
        )
        status = rec["status"]
        require(status in ("FOUND", "EXHAUSTED", "LIMIT_REACHED"),
                "Invented native search status")
        require(all(
            type(rec[k]) is int and rec[k] >= 0
            for k in ("states_explored", "assignments_tried", "arc_revisions")
        ) and rec["states_explored"] <= MAX_STATES,
                "Corrupted native solver counters")
        if status == "FOUND":
            pairs = tuple(tuple(pair) for pair in rec["antipodal_pairs"])
            mapping = dict(enumerate(rec["retraction_map"]))
            independent_octahedral_retraction_check(graph, pairs, mapping)
            require(rec["target_dimension"] == len(pairs) >= 3
                    and rec["complete_retraction_verified_on_every_source_edge"] is True,
                    "Positive certificate is incomplete or wrong")
        else:
            require("retraction_map" not in rec
                    and "antipodal_pairs" not in rec
                    and "target_dimension" not in rec,
                    "A limited or negative search pretends to have a witness")
        results[key] = rec
    require(
        seen == {(i, order) for i in REMAINING for order in VALUE_ORDERS},
        "Missing one or more original and search-order combinations",
    )
    for i in REMAINING:
        statuses = {results[(i, v)]["status"] for v in VALUE_ORDERS}
        require(not ("EXHAUSTED" in statuses and "FOUND" in statuses),
                "Two complete native solvers return contradictory positive/negative")
    successes = sorted(
        {(i, order, results[(i, order)]["target_dimension"])
         for i, order in seen if results[(i, order)]["status"] == "FOUND"}
    )
    from research.order10_five_p3_native_v1.verify_positive import (
        verify_positive,
    )
    permanent = verify_positive()
    check_success = [(i, order, d) for i, order, d in successes]
    require(
        check_success == [(permanent["original_mckay"], "label", 11)]
        and permanent["original_K_divergent"] is True,
        "The native positive set differs from the complete permanent O11 map",
    )
    exhausted = sorted(
        i for i in REMAINING
        if any(results[(i, order)]["status"] == "EXHAUSTED"
               for order in VALUE_ORDERS)
    )
    unresolved = sorted(
        i for i in REMAINING
        if i not in exhausted
        and not any(results[(i, order)]["status"] == "FOUND"
                    for order in VALUE_ORDERS)
    )
    return {
        "schema": 1,
        "kind": "dual_order_native_public_mono56_octahedral_p3_probe",
        "monorepo_commit": MONOREPO_SHA,
        "pinned_dependency_versions": RUNTIME_VERSIONS,
        "installed_solver_source_blobs_verified": True,
        "search_budget": {
            "max_states": MAX_STATES,
            "time_limit_seconds": SECONDS,
        },
        "originals": list(REMAINING),
        "search_orders": list(VALUE_ORDERS),
        "permanent_O11_retraction_certificate_replayed": True,
        "new_original_divergent_but_not_yet_promoted": 11656793,
        "found_p3_octahedral_retractions": [
            {"index":i, "order":order, "dimension":d}
            for i, order, d in successes
        ],
        "exhaustively_excluded_octahedral_retractions": exhausted,
        "still_resource_limited_without_positive_witness": unresolved,
        "census_classifications_modified": False,
        "complete_results": [
            results[(i, order)] for i in REMAINING for order in VALUE_ORDERS
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    reports = sorted(args.directory.glob("*.json"))
    result = replay(reports)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2)
                           + "\n", encoding="utf-8")
    print(json.dumps({
        k: v for k, v in result.items() if k != "complete_results"
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
