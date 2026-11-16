"""Bounded triangular-cover searches for the saved pared G1 and G2 cores.

The certificate establishes clique divergence ONLY for the selected pared
iterate. Original nine/ten-vertex classifications remain untouched.
"""
from __future__ import annotations

import json
from pathlib import Path
import resource
import sys

import networkx as nx
from pycombtop.covering_divergence_search import (
    CoveringSearchStatus,
    search_covering_divergence,
)

import core9cover_v2_worker as previous

# The saved G1 have 13-14 vertices and at most 59 edges; G2 have 21
# vertices and at most 144 edges. Limits permit their actual double covers.
# Only m=2,3 can be eligible for the observed radius-four covers.
COMMON = {
    "max_cover_classes": 1,
    "max_clique_vertices": 350,
    "max_clique_edges": 10000,
    "max_source_order": 42,
    "max_m": 3,
    "max_n": 2,
    "max_morphism_states": 100000,
    "max_morphism_assignments": 500000,
}
LIMITS = {
    "g1": {**COMMON, "max_cover_vertices": 28, "max_cover_edges": 118},
    "g2": {**COMMON, "max_cover_vertices": 42, "max_cover_edges": 288},
}


def investigate(iterate: str, graph6: str) -> dict:
    if iterate not in LIMITS:
        raise ValueError("Only pared iterates g1 and g2 are supported")
    graph = nx.from_graph6_bytes(graph6.encode("ascii"))
    expected_order = {"g1": {13, 14}, "g2": {21}}
    if len(graph) not in expected_order[iterate] or not nx.is_connected(graph):
        raise ValueError("Unexpected source order or disconnected pared iterate")
    limits = LIMITS[iterate]
    if graph.number_of_edges() * 2 > limits["max_cover_edges"]:
        raise ValueError("Frozen cover-edge limit excludes the input")
    eligible = previous.eligible_sources(graph, limits)
    result = search_covering_divergence(graph, **limits)
    if dict(result.limits) != limits:
        raise AssertionError("Solver limits differ from the frozen manifest")
    details = {
        "search_status": result.status.name,
        "cover_classes_total": result.cover_classes_total,
        "cover_classes_checked": result.cover_classes_checked,
        "cover_candidates_checked": result.cover_candidates_checked,
        "morphism_searches_exhausted": result.morphism_searches_exhausted,
        "morphism_states": result.morphism_states,
        "morphism_assignments": result.morphism_assignments,
        "cover_classes_complete": result.cover_classes_complete,
        "morphisms_complete": result.morphisms_complete,
        "configured_source_parameters": [list(p) for p in result.configured_source_parameters],
        "reasons": list(result.reasons),
        "limits": dict(result.limits),
    }
    witness = None
    status = result.status.name
    if result.status is CoveringSearchStatus.FOUND:
        if result.certificate is None:
            raise AssertionError("FOUND without a proof certificate")
        witness = previous._cover_witness(result.certificate)
        if (
            not isinstance(witness.get("m"), int)
            or not isinstance(witness.get("n"), int)
            or witness["m"] not in range(2, limits["max_m"] + 1)
            or witness["n"] not in range(limits["max_n"] + 1)
            or 2 * witness["m"] * (witness["n"] + 3) > limits["max_source_order"]
            or [witness["m"], witness["n"]] not in [
                pair for cover in eligible["covers"]
                for pair in cover["source_parameters_eligible"]
            ]
            or not previous.verify_cover_witness(graph, witness)
        ):
            raise ValueError("Out-of-family or invalid positive certificate")
        status = "DIVERGENT"
    elif result.certificate is not None:
        raise AssertionError("Negative status with a positive certificate")
    return {
        "kind": iterate,
        "status": status,
        "scope": "pared_iterate_only",
        "input_graph6": graph6,
        "eligible": eligible,
        "search": details,
        "proof_status": "verified" if witness is not None else "none",
        "witness": witness,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("Usage: core9iterate_v1_worker.py g1|g2 GRAPH6 RESULT_FILE")
    mode, graph6, path = sys.argv[1:]
    Path(path).write_text(
        json.dumps(investigate(mode, graph6), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
