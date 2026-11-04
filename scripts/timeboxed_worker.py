"""One bounded clique-behavior classification, invoked in an isolated process.

Conjectured references are *hints*, never facts. This worker temporarily
omits them from the classifier's internal reference registry so the normal
proof-producing criteria can run even for conjecture-dependent inputs.
The change affects only this subprocess, never the installed dependency.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import networkx as nx

from surface_refs import load_surface_references
from pycliques import small


def classify(graph6: str) -> dict:
    graph = nx.from_graph6_bytes(graph6.encode("ascii"))
    if graph.number_of_nodes() != 10:
        raise ValueError("Timeboxed stage requires an original ten-vertex graph")
    from pycliques.dominated import find_dominated_vertex
    if find_dominated_vertex(graph) is not None:
        raise ValueError("Timeboxed stage excludes originals with dominated vertices")

    load_surface_references()
    saved_references = small._REFERENCE_GRAPHS
    small._REFERENCE_GRAPHS = {
        key: value for key, value in saved_references.items()
        if value[1] is small.ReferenceStatus.PROVEN
    }
    try:
        result = small.classify_clique_behavior(graph, bound=120)
    finally:
        small._REFERENCE_GRAPHS = saved_references

    cert = result.certificate
    if (
        result.verdict.name in ("CONVERGENT", "DIVERGENT")
        and cert is not None
        and cert.target_status == "conjectured_divergent"
    ):
        raise ValueError("An unproved reference must never justify a definite verdict")

    pared = nx.convert_node_labels_to_integers(result.pared_graph)
    if result.bound_exceeded and result.verdict.name == "INDETERMINATE":
        status = "BOUND_EXCEEDED"
    else:
        status = result.verdict.name
    return {
        "status": status,
        "verdict": result.verdict.name,
        "bound": 120,
        "iterations_checked": result.iterations_checked,
        "bound_exceeded": bool(result.bound_exceeded),
        "reason": result.reason,
        "pared_order": pared.order(),
        "pared_graph6": nx.to_graph6_bytes(
            pared, header=False
        ).decode("ascii").strip(),
        "certificate_rule": cert.rule if cert is not None else "-",
        "certificate_target_status": (cert.target_status or "-") if cert is not None else "-",
        "certificate_target_label": (cert.target_label or "-") if cert is not None else "-",
        "conjectured_references_ignored": True,
    }


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: timeboxed_worker.py GRAPH6 RESULT_PATH")
    graph6, filename = sys.argv[1:]
    record = classify(graph6)
    Path(filename).write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
