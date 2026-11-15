"""Isolated single-graph v3 classifier; positive results require replayable certificates.

Unlike v2, this stage admits originals with dominated vertices. It never
treats a conjectured surface reference or an unverified candidate as proof.
"""
from __future__ import annotations

import json
import resource
import sys
from pathlib import Path

import networkx as nx

from pycliques import small
from certificate_records_v3 import serialize_result, verify_record
from timeboxed_trace_v2 import ProgressTrace
from timeboxed_trace_v3 import trace_classifier_v3

CLIQUE_BOUND = 120


def classify(graph6: str, diagnostic_path: str) -> dict:
    graph = nx.from_graph6_bytes(graph6.encode("ascii"))
    if graph.number_of_nodes() != 10:
        raise ValueError("Expected original connected order-10 graph")
    if not nx.is_connected(graph):
        raise ValueError("Source graph must be connected")

    # Do not register the conjectured order-9 surface list in this process.
    # Also filter any conjectured references bundled upstream. The worker is
    # isolated, so the restored registry cannot affect other classifications.
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

    serialized = serialize_result(graph, outcome, bound=CLIQUE_BOUND)
    verdict = outcome.verdict.name
    status = verdict
    if verdict == "INDETERMINATE" and outcome.bound_exceeded:
        status = "BOUND_EXCEEDED"
    elif verdict in {"CONVERGENT", "DIVERGENT"}:
        # A local witness alone is not enough. Rebuild the full pared iterate
        # sequence and check its terminal proof before recording a positive.
        if serialized["proof_status"] == "verified_local":
            if not verify_record(serialized, verify_iterate=True):
                raise ValueError("Positive witness failed full iterate-chain verification")
            serialized["proof_status"] = "verified_chain"
        else:
            # Some sound upstream criteria lack a portable proof serializer.
            # They remain candidates, not new independent census results.
            status = "INDETERMINATE"

    cert = outcome.certificate
    if (
        verdict in {"CONVERGENT", "DIVERGENT"} and cert is not None
        and cert.target_status == "conjectured_divergent"
    ):
        raise ValueError("Conjectured reference must not yield a positive verdict")

    return {
        **serialized,
        "status": status,
        "raw_verdict": verdict,
        "bound": CLIQUE_BOUND,
        "iterations_checked": outcome.iterations_checked,
        "bound_exceeded": bool(outcome.bound_exceeded),
        "conjectured_references_ignored": True,
        "retraction_depth": 2,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("Usage: timeboxed_worker_v3.py GRAPH6 RESULT_PATH JOURNAL_PATH")
    graph6, filename, diagnostic_path = sys.argv[1:]
    record = classify(graph6, diagnostic_path)
    Path(filename).write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
