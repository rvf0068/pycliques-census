"""One isolated targeted core9 follow-up: cover search or larger-bound classification.

The only positive outputs accepted are independently replayable divergence
or convergence witnesses for the **nine-vertex pared core**. Absence of a
witness, exhausting one bounded search family, and exceeding a clique bound
are never proofs of nondivergence or convergence.
"""
from __future__ import annotations

import json
from pathlib import Path
import resource
import sys

import networkx as nx
from pycliques import small
from pycliques.dominated import find_dominated_vertex
from pycombtop.covering_divergence_search import (
    CoveringSearchStatus, search_covering_divergence,
)

from certificate_records_v3 import serialize_result, verify_record
from timeboxed_trace_v2 import ProgressTrace
from timeboxed_trace_v3 import trace_classifier_v3

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "postpasses"))
from s1_divergence import _cover_witness, verify_cover_witness  # noqa: E402

# Explicit, versioned limits: covering search is applied to core G0 only.
COVER_LIMITS = {
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
BOUND = 350
RETRACTION_DEPTH = 2


def analyze_cover(g: nx.Graph) -> dict:
    search = search_covering_divergence(g, **COVER_LIMITS)
    details = {
        "cover_classes_total": search.cover_classes_total,
        "cover_classes_checked": search.cover_classes_checked,
        "cover_candidates_checked": search.cover_candidates_checked,
        "morphism_states": search.morphism_states,
        "morphism_assignments": search.morphism_assignments,
        "morphism_searches_exhausted": search.morphism_searches_exhausted,
        "cover_classes_complete": search.cover_classes_complete,
        "morphisms_complete": search.morphisms_complete,
        "configured_source_parameters": [list(v) for v in search.configured_source_parameters],
        "limits": dict(search.limits),
        "reasons": list(search.reasons),
        "search_status": search.status.name,
    }
    if search.status is CoveringSearchStatus.FOUND:
        if search.certificate is None:
            raise AssertionError("FOUND without a covering divergence witness")
        witness = _cover_witness(search.certificate)
        if not verify_cover_witness(g, witness):
            raise ValueError("Discovered cover certificate failed independent replay")
        return {
            "status": "DIVERGENT",
            "proof_status": "verified",
            "witness": witness,
            "search": details,
        }
    if search.certificate is not None:
        raise AssertionError("Unproven cover search result with a certificate")
    return {
        "status": search.status.name,
        "proof_status": "none",
        "witness": None,
        "search": details,
    }


def analyze_bound(g: nx.Graph, journal: str) -> dict:
    # Conjectural references cannot certify any core.
    saved_refs = small._REFERENCE_GRAPHS
    small._REFERENCE_GRAPHS = {
        key: value for key, value in saved_refs.items()
        if value[1] is small.ReferenceStatus.PROVEN
    }
    try:
        with ProgressTrace(journal) as trace:
            with trace_classifier_v3(trace):
                outcome = small.classify_clique_behavior(
                    g, bound=BOUND, retraction_depth=RETRACTION_DEPTH
                )
    finally:
        small._REFERENCE_GRAPHS = saved_refs

    record = serialize_result(g, outcome, bound=BOUND)
    raw = outcome.verdict.name
    status = raw
    if raw == "INDETERMINATE" and outcome.bound_exceeded:
        status = "BOUND_EXCEEDED"
    elif raw in {"DIVERGENT", "CONVERGENT"}:
        if record["proof_status"] == "verified_local":
            if not verify_record(record, verify_iterate=True):
                raise ValueError("Higher-bound positive proof fails complete chain replay")
            record["proof_status"] = "verified_chain"
        else:
            status = "INDETERMINATE"
    if outcome.certificate is not None and (
        outcome.certificate.target_status == "conjectured_divergent"
        and status in {"DIVERGENT", "CONVERGENT"}
    ):
        raise AssertionError("Conjectural dependency promoted to a positive verdict")
    return {
        **record,
        "status": status,
        "raw_verdict": raw,
        "clique_bound": BOUND,
        "iterations_checked": outcome.iterations_checked,
        "bound_exceeded": bool(outcome.bound_exceeded),
        "retraction_depth": RETRACTION_DEPTH,
    }


def inspect(kind: str, graph6: str, journal: str) -> dict:
    g = nx.from_graph6_bytes(graph6.encode("ascii"))
    if len(g) != 9 or not nx.is_connected(g) or find_dominated_vertex(g) is not None:
        raise ValueError("Input must be a connected completely pared nine-vertex core")
    if kind == "cover":
        data = analyze_cover(g)
    elif kind == "bound":
        data = analyze_bound(g, journal)
    else:
        raise ValueError(f"Unknown follow-up kind {kind}")
    return {
        **data,
        "kind": kind, "scope": "nine_vertex_core_only",
        "input_graph6": graph6,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit("Usage: core9_followup_worker.py KIND GRAPH6 RESULT_PATH JOURNAL_PATH")
    kind, graph6, target, journal = sys.argv[1:]
    data = inspect(kind, graph6, journal)
    Path(target).write_text(
        json.dumps(data, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
