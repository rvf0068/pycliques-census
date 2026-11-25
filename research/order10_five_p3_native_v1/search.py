"""Independent bounded native search on the five remaining oversized P3 classes.

Uses the existing public pycliques octahedral-retraction algorithm, on the
current overhauled monorepo pinned to merged PR #56.  The two value-order
policies are searched separately, and *no* limit is called a negative proof.
Historical P3 graph6 and complete maps for positives are independently
verified. The canonical census remains untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("No optimized proof execution")

import networkx as nx

from research.order10_overcap_p3_coaffine_v1.pilot import (
    independent_octahedral_retraction_check, source_catalog,
)

MONOREPO_SHA = "e27649a6898b8c5b5bdbb4c6c64fd792672ae0ae"
MAX_STATES = 2_000_000
SECONDS = 90
REMAINING = (11505012, 11595632, 11656793, 11709142, 11713984)
VALUE_ORDERS = ("label", "fiber")


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError(reason)


def source_graph(index: int) -> tuple[dict, nx.Graph]:
    require(index in REMAINING, "Unrecognized unresolved original")
    entry = source_catalog()[index]
    graph = nx.from_graph6_bytes(entry["p3_graph6"].encode("ascii"))
    require([len(graph), graph.number_of_edges()] == list(entry["p3"]),
            "Authenticated P3 graph6 cannot be reconstructed")
    return entry, graph


def investigate(index: int, value_order: str) -> dict:
    require(value_order in VALUE_ORDERS, "Unknown source-order search policy")
    from pycliques import find_octahedral_retraction_coaffine

    source, graph = source_graph(index)
    comp = nx.complement(graph)
    result = find_octahedral_retraction_coaffine(
        graph, backend="native", value_order=value_order,
        min_dimension=3, max_states=MAX_STATES, time_limit=SECONDS,
    )
    status = result.status.name
    require(status in ("FOUND", "EXHAUSTED", "LIMIT_REACHED"),
            "Unknown native solver status")
    require(
        type(result.states_explored) is int
        and 0 <= result.states_explored <= MAX_STATES
        and type(result.assignments_tried) is int
        and result.assignments_tried >= 0,
        "Native counters are malformed",
    )
    entry = {
        "original_mckay": index,
        "original_graph6": source["graph6"],
        "p3_dimensions": list(source["p3"]),
        "p3_graph6_sha256": hashlib.sha256(
            source["p3_graph6"].encode("ascii")
        ).hexdigest(),
        "complement_edges": comp.number_of_edges(),
        "complement_triangle_count":
            sum(nx.triangles(comp).values()) // 3,
        "complement_connected": nx.is_connected(comp),
        "solver_revision": MONOREPO_SHA,
        "search_policy": value_order,
        "max_states": MAX_STATES,
        "time_limit_seconds": SECONDS,
        "status": status,
        "states_explored": result.states_explored,
        "assignments_tried": result.assignments_tried,
        "arc_revisions": result.arc_revisions,
    }
    if status == "FOUND":
        require(result.antipodal_pairs is not None
                and result.retraction is not None
                and result.dimension is not None,
                "Positive native return omitted its complete projection")
        independent_octahedral_retraction_check(
            graph, result.antipodal_pairs, result.retraction,
        )
        require(result.dimension == len(result.antipodal_pairs) >= 3,
                "Wrong octahedral dimension")
        entry.update({
            "target_dimension": result.dimension,
            "antipodal_pairs": [list(p) for p in result.antipodal_pairs],
            "retraction_map": [
                result.retraction[i] for i in range(len(graph))
            ],
            "complete_retraction_verified_on_every_source_edge": True,
        })
    else:
        require(result.retraction is None,
                "Limited/negative result contains an unverified retraction")
    return entry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=int, required=True)
    parser.add_argument("--value-order", required=True, choices=VALUE_ORDERS)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(os.environ.get("PYCLIQUES_PINNED_SHA") == MONOREPO_SHA,
            "Native solver must come from the specified PR56 merge commit")
    outcome = investigate(args.index, args.value_order)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(outcome, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"P3 original={args.index} order={args.value_order} "
        f"status={outcome['status']} states={outcome['states_explored']}"
    )
    if outcome["status"] == "FOUND":
        print(f"VALID P3 -> O_{outcome['target_dimension']} "
              f"retraction on {outcome['p3_dimensions'][0]} vertices "
              f"and {outcome['p3_dimensions'][1]} edges")


if __name__ == "__main__":
    main()
