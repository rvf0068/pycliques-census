"""Isolated 9-vertex pared-core classifier for the post-v3 representative benchmark.

This module deliberately does not classify all original 10-vertex members.
It checks a *representative core* only. Positive results require replayable
witnesses against this exact core, and all conjectural divergent references
are ignored. This is not a proof of the member-to-core transfer theorem.
"""
from __future__ import annotations

import json
import resource
import sys
from pathlib import Path

import networkx as nx

from pycliques import small
from pycliques.dominated import find_dominated_vertex
from certificate_records_v3 import serialize_result, verify_record
from timeboxed_trace_v2 import ProgressTrace
from timeboxed_trace_v3 import trace_classifier_v3

CLIQUE_BOUND = 120


def classify(graph6: str, diagnostic_path: str) -> dict:
    graph = nx.from_graph6_bytes(graph6.encode("ascii"))
    if len(graph) != 9 or not nx.is_connected(graph):
        raise ValueError("Expected a connected nine-vertex representative core")
    if find_dominated_vertex(graph) is not None:
        raise ValueError("Benchmark input is not a completely pared core")

    saved = small._REFERENCE_GRAPHS
    small._REFERENCE_GRAPHS = {
        key: value for key, value in saved.items()
        if value[1] is small.ReferenceStatus.PROVEN
    }
    try:
        with ProgressTrace(diagnostic_path) as trace:
            with trace_classifier_v3(trace):
                outcome = small.classify_clique_behavior(
                    graph, bound=CLIQUE_BOUND, retraction_depth=2
                )
    finally:
        small._REFERENCE_GRAPHS = saved

    record = serialize_result(graph, outcome, bound=CLIQUE_BOUND)
    verdict = outcome.verdict.name
    status = verdict
    if verdict == "INDETERMINATE" and outcome.bound_exceeded:
        status = "BOUND_EXCEEDED"
    elif verdict in {"CONVERGENT", "DIVERGENT"}:
        if record["proof_status"] == "verified_local":
            if not verify_record(record, verify_iterate=True):
                raise ValueError("Positive core certificate failed full iterate-chain replay")
            record["proof_status"] = "verified_chain"
        else:
            status = "INDETERMINATE"

    cert = outcome.certificate
    if (
        verdict in {"CONVERGENT", "DIVERGENT"}
        and cert is not None
        and cert.target_status == "conjectured_divergent"
    ):
        raise ValueError("A conjectured reference must not produce a positive verdict")

    return {
        **record,
        "status": status,
        "raw_verdict": verdict,
        "bound": CLIQUE_BOUND,
        "iterations_checked": outcome.iterations_checked,
        "bound_exceeded": bool(outcome.bound_exceeded),
        "retraction_depth": 2,
        "conjectured_references_ignored": True,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "scope": "pared_core_only",
    }


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("Usage: core9_worker.py GRAPH6 RESULT_PATH JOURNAL_PATH")
    graph6, result_file, journal_file = sys.argv[1:]
    record = classify(graph6, journal_file)
    Path(result_file).write_text(
        json.dumps(record, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
