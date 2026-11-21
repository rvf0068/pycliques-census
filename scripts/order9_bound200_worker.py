"""One order-9 bound-200 classification; only invoked by a bounded supervisor.

This worker intentionally ignores conjectural divergent references. All
definite verdicts must be backed by a proven theorem or a verifiable witness.
Historical census dependency pins and records are never modified.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import networkx as nx

from certificate_records_v3 import serialize_result
from surface_refs import load_surface_references
from timeboxed_trace_v2 import ProgressTrace
from timeboxed_trace_v3 import trace_classifier_v3
from pycliques import small

BOUND = 200


def classify(graph6: str, trace_path: str) -> dict:
    original = nx.from_graph6_bytes(graph6.encode("ascii"))
    if len(original) != 9:
        raise ValueError("Order-9 stage only accepts nine-vertex originals")
    load_surface_references()
    old_registry = small._REFERENCE_GRAPHS
    small._REFERENCE_GRAPHS = {
        key: value for key, value in old_registry.items()
        if value[1] is small.ReferenceStatus.PROVEN
    }
    try:
        with ProgressTrace(trace_path) as diagnostic:
            with trace_classifier_v3(diagnostic):
                result = small.classify_clique_behavior(
                    original, bound=BOUND, tries=9, retraction_depth=2,
                )
    finally:
        small._REFERENCE_GRAPHS = old_registry

    cert = result.certificate
    if result.verdict.name in {"DIVERGENT", "CONVERGENT"}:
        if cert and cert.target_status == "conjectured_divergent":
            raise ValueError("Conditional reference cannot prove a definite verdict")
    status = (
        "BOUND_EXCEEDED"
        if result.verdict.name == "INDETERMINATE" and result.bound_exceeded
        else result.verdict.name
    )
    # Unsupported proof mechanisms remain explicitly 'not_serialized'.
    evidence = serialize_result(original, result, bound=BOUND)
    return {
        "status": status,
        "verdict": result.verdict.name,
        "bound": BOUND,
        "iterations_checked": result.iterations_checked,
        "bound_exceeded": bool(result.bound_exceeded),
        "reason": result.reason,
        "certificate_rule": cert.rule if cert is not None else None,
        "proof_status": evidence["proof_status"],
        "proof": evidence["proof"],
        "conjectured_references_ignored": True,
        "retraction_depth": 2,
    }


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("Usage: order9_bound200_worker.py GRAPH6 RESULT_PATH TRACE_PATH")
    record = classify(sys.argv[1], sys.argv[3])
    Path(sys.argv[2]).write_text(json.dumps(record, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
