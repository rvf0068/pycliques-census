"""Bounded native coaffine-endomorphism pilot on three unresolved oversized P3.

Calls only the official public pycliques native solver pinned to the
unchanged merged PR #56 implementation; it does not reimplement a CSP.
A FOUND map is independently checked and saved IN FULL. A resource-limit
status is always inconclusive and never changes a census classification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("Optimized proof execution is forbidden")

import networkx as nx

from research.order10_five_p3_native_v1.search import (
    MONOREPO_SHA, source_graph, validate_runtime,
)
from research.order10_overcap_p3_coaffine_v1.pilot import (
    independent_coaffine_check,
)
from research.order10_three_p3_coaffine_native_v1.verify import (
    audit_positive_map, audit_source,
)

ORIGINALS = (11505012, 11595632, 11709142)
VALUE_ORDERS = ("label", "fiber")
MAX_STATES = 3_000_000
SECONDS = 150


def require(ok: bool, explanation: str) -> None:
    if not ok:
        raise AssertionError(explanation)


def investigate(index: int, value_order: str) -> dict:
    require(index in ORIGINALS and value_order in VALUE_ORDERS,
            "Unrecognized original or native value ordering")
    versions = validate_runtime()
    from pycliques import find_coaffine_endomorphism

    source, graph = source_graph(index)
    audit_source(index, source, graph)
    result = find_coaffine_endomorphism(
        graph,
        backend="native",
        value_order=value_order,
        max_states=MAX_STATES,
        time_limit=SECONDS,
    )
    status = result.status.name
    require(status in ("FOUND", "EXHAUSTED", "LIMIT_REACHED"),
            "Unrecognized native solver status")
    require(
        type(result.states_explored) is int
        and 0 <= result.states_explored <= MAX_STATES
        and type(result.assignments_tried) is int
        and result.assignments_tried >= 0
        and type(result.arc_revisions) is int
        and result.arc_revisions >= 0,
        "Malformed native search counters",
    )
    row = {
        "schema": 1,
        "kind": "bounded_native_three_oversized_p3_coaffine_pilot",
        "original_index": index,
        "original_graph6": source["graph6"],
        "p3_graph6_sha256": hashlib.sha256(
            source["p3_graph6"].encode("ascii")
        ).hexdigest(),
        "p3_dimensions": list(source["p3"]),
        "monorepo_pinned_revision": MONOREPO_SHA,
        "installed_solver_source_blobs_verified": True,
        "dependency_versions": versions,
        "value_order": value_order,
        "max_states": MAX_STATES,
        "time_limit_seconds": SECONDS,
        "coaffine_status": status,
        "states_explored": result.states_explored,
        "assignments_tried": result.assignments_tried,
        "arc_revisions": result.arc_revisions,
        "bounded_search_does_not_certify_nondivergence": True,
    }
    if status == "FOUND":
        require(result.endomorphism is not None,
                "A native FOUND status lacks a complete map")
        f = result.endomorphism
        independent_coaffine_check(graph, f)
        images = [f[v] for v in range(len(graph))]
        row["complete_coaffine_map"] = images
        row["positive_analysis"] = audit_positive_map(graph, images)
    else:
        require(result.endomorphism is None,
                "Limited or exhausted result unexpectedly contains a map")
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=int, required=True, choices=ORIGINALS)
    parser.add_argument("--value-order", choices=VALUE_ORDERS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    item = investigate(args.index, args.value_order)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(item, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print("P3 original=" + str(args.index)
          + " order=" + args.value_order
          + " coaffine=" + item["coaffine_status"]
          + " states=" + str(item["states_explored"]), flush=True)
    if "positive_analysis" in item:
        print("POSITIVE COMPLETE COAFFINE MAP; "
              "stable_retract=" + str(item["positive_analysis"]["stable_order"])
              + " K_divergent_certificate="
              + str(item["positive_analysis"]["expansive_witness"]["proved"]),
              flush=True)


if __name__ == "__main__":
    main()
