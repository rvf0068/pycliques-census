"""Isolated one-core covering search on the post-PR14 pinned pycombtop.

Usage: core9cover_v2_worker.py MODE GRAPH6 PATH
No original order-ten graph classification is performed.
"""
from __future__ import annotations

import json
from pathlib import Path
import resource
import sys

import networkx as nx
from pycombtop.covering_divergence_search import (
    CoveringSearchStatus,
    _all_nonzero_cocycles,
    _double_cover,
    search_covering_divergence,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "postpasses"))
from s1_divergence import _cover_witness, verify_cover_witness  # noqa: E402

BASELINE = {
    "max_cover_classes": 1,
    "max_cover_vertices": 18,
    "max_cover_edges": 62,
    "max_clique_vertices": 350,
    "max_clique_edges": 6000,
    "max_source_order": 18,
    "max_m": 3,
    "max_n": 0,
    "max_morphism_states": 25000,
    "max_morphism_assignments": 100000,
}
EXPANDED = {
    **BASELINE,
    # The new dimensions here are the source *family* (not merely budgets):
    # R_(2m)^n for n=1,2 in addition to the historical n=0 family.
    "max_source_order": 42,
    "max_m": 4,
    "max_n": 2,
    "max_morphism_states": 100000,
    "max_morphism_assignments": 500000,
}
LIMITS = {"baseline": BASELINE, "expanded": EXPANDED}


def eligible_sources(graph: nx.Graph, limits: dict[str, int]) -> dict:
    """State exactly which clockwork parameters the cover radius permits."""
    classes = _all_nonzero_cocycles(
        graph, max_classes=limits["max_cover_classes"]
    )
    data = []
    for cocycle in classes:
        cover, _ = _double_cover(graph, cocycle)
        deck_distances = [
            nx.shortest_path_length(cover, (v, 0), (v, 1))
            for v in graph
        ]
        radius = min(deck_distances)
        candidates = [
            [m, n]
            for m in range(2, limits["max_m"] + 1)
            for n in range(limits["max_n"] + 1)
            if 2 * m * (n + 3) <= limits["max_source_order"]
            and m + 1 <= radius
        ]
        data.append({
            "deck_radius": radius,
            "source_parameters_eligible": candidates,
            "cover_order": len(cover),
            "cover_edges": cover.number_of_edges(),
        })
    return {
        "checked_cover_classes": len(classes),
        "covers": data,
    }


def investigate(mode: str, graph6: str) -> dict:
    if mode not in LIMITS:
        raise ValueError(f"Unknown covering family: {mode}")
    graph = nx.from_graph6_bytes(graph6.encode("ascii"))
    if len(graph) != 9 or not nx.is_connected(graph):
        raise ValueError("Expected a connected nine-vertex pared representative")
    limits = LIMITS[mode]
    eligible = eligible_sources(graph, limits)
    result = search_covering_divergence(graph, **limits)
    if dict(result.limits) != limits:
        raise AssertionError("Search did not use declared limits")

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
        "configured_source_parameters": [list(pair) for pair in result.configured_source_parameters],
        "reasons": list(result.reasons),
        "limits": dict(result.limits),
    }
    witness = None
    status = result.status.name
    if result.status is CoveringSearchStatus.FOUND:
        if result.certificate is None:
            raise AssertionError("FOUND without a certificate")
        witness = _cover_witness(result.certificate)
        if (
            witness["m"] > limits["max_m"]
            or witness["n"] > limits["max_n"]
            or 2 * witness["m"] * (witness["n"] + 3) > limits["max_source_order"]
            or [witness["m"], witness["n"]] not in [
                pair for item in eligible["covers"] for pair in item["source_parameters_eligible"]
            ]
            or not verify_cover_witness(graph, witness)
        ):
            raise ValueError("Found an invalid or out-of-family covering witness")
        status = "DIVERGENT"
    elif result.certificate is not None:
        raise AssertionError("Unverified certificate accompanied a negative search")
    return {
        "kind": mode,
        "status": status,
        "scope": "nine_vertex_core_only",
        "input_graph6": graph6,
        "eligible": eligible,
        "search": details,
        "proof_status": "verified" if witness is not None else "none",
        "witness": witness,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("Usage: core9cover_v2_worker.py MODE GRAPH6 OUTPUT_PATH")
    mode, graph6, output_path = sys.argv[1:]
    payload = investigate(mode, graph6)
    Path(output_path).write_text(
        json.dumps(payload, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
