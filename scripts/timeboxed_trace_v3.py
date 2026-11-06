"""Version-3 root-level diagnostic tracer for the composite clique classifier.

Unlike v2 this tracer does NOT rely on classifier callback positions. Named
criteria and root iterates are observed directly, and the historical v2
implementation/manifest remain immutable. The worker should pair these
diagnostics with certificate_records_v3.serialize_result.
"""
from __future__ import annotations

import json
import time
from contextlib import contextmanager
from pathlib import Path

from pycliques import small
from timeboxed_trace_v2 import ProgressTrace, summarize_events


NAMED_CRITERIA = (
    "_classify_reference_graph",
    "_classify_suspension_2_coaffination",
    "_test_clockwork",
    "_classify_reference_dependency",
    "_classify_local_bridge",
    "_classify_non_triangle_edge",
    "_classify_inverse_cutpoint_extension",
)

ITERATE_CRITERIA = {
    "is_clique_helly": "clique_helly",
    "retracts": "fixed_target_retraction",
    "special_octahedra_dimension": "special_octahedron_test",
    "find_special_octahedron_witness": "special_octahedron_witness",
}


def summarize_events_v3(filename: str) -> dict:
    """Reconstruct v2-compatible observations with explicit criterion/iterate."""
    result = summarize_events(filename)
    starts = []
    for line in Path(filename).read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if row.get("event") == "method_start":
            starts.append(row)
    for method, start in zip(result["methods_tried"], starts):
        for name in ("iterate", "target_order", "source_order"):
            if name in start:
                method[name] = start[name]
    result["diagnostic_schema"] = 3
    return result


@contextmanager
def trace_classifier_v3(trace: ProgressTrace):
    """Install instrumentation in one isolated worker, restoring on exit."""
    originals = {}
    names = (
        "CliqueSequence",
        "clique_graph",
        "completely_pared_graph",
        "classify_clique_behavior",
        "_test_iterate_certificates",
        *NAMED_CRITERIA,
        *ITERATE_CRITERIA,
    )
    for name in names:
        if hasattr(small, name):
            originals[name] = getattr(small, name)

    sequence_class = originals["CliqueSequence"]
    trace.depth = 0
    trace.root_sequence = None
    trace.current_sequence = None
    trace.in_iterate_pass = False
    counter = 0

    class TracedSequence(sequence_class):
        def __init__(self, graph, bound=30):
            super().__init__(graph, bound=bound)
            if trace.root_sequence is None and trace.depth == 1:
                trace.root_sequence = self
                trace.emit(
                    "initial_pared",
                    order=graph.number_of_nodes(),
                    edges=graph.number_of_edges(),
                )

        def __getitem__(self, index):
            old = trace.current_sequence
            trace.current_sequence = self
            try:
                return super().__getitem__(index)
            finally:
                trace.current_sequence = old

    def root_index(graph):
        sequence = trace.root_sequence
        if sequence is None:
            return None
        for index, candidate in enumerate(sequence._graphs):
            if graph is candidate:
                return index
        return None

    def observe_clique_graph(graph, *args, **kwargs):
        is_root = (
            trace.root_sequence is not None
            and trace.current_sequence is trace.root_sequence
        )
        if is_root:
            index = len(trace.root_sequence._graphs)
            trace.emit(
                "iterate_start",
                iterate=index,
                input_order=graph.number_of_nodes(),
                input_edges=graph.number_of_edges(),
            )
        result = originals["clique_graph"](graph, *args, **kwargs)
        if is_root:
            if result is None:
                trace.emit("clique_bound_exceeded", iterate=index)
            else:
                trace.emit(
                    "clique_graph_complete",
                    iterate=index,
                    order=result.number_of_nodes(),
                    edges=result.number_of_edges(),
                )
        return result

    def observe_pare(graph, *args, **kwargs):
        result = originals["completely_pared_graph"](graph, *args, **kwargs)
        if (
            trace.root_sequence is not None
            and trace.current_sequence is trace.root_sequence
        ):
            trace.emit(
                "pared_iterate_complete",
                iterate=len(trace.root_sequence._graphs),
                order=result.number_of_nodes(),
                edges=result.number_of_edges(),
            )
        return result

    def observe_classify(*args, **kwargs):
        trace.depth += 1
        try:
            return originals["classify_clique_behavior"](*args, **kwargs)
        finally:
            trace.depth -= 1

    def observe_iterate_pass(*args, **kwargs):
        original_flag = trace.in_iterate_pass
        if trace.depth == 1:
            trace.in_iterate_pass = True
        try:
            return originals["_test_iterate_certificates"](*args, **kwargs)
        finally:
            trace.in_iterate_pass = original_flag

    def method_wrapper(function, label, *, iterate_only=False):
        def wrapped(*args, **kwargs):
            nonlocal counter
            if trace.depth != 1 or (iterate_only and not trace.in_iterate_pass):
                return function(*args, **kwargs)
            counter += 1
            token = counter
            details = {}
            if iterate_only and args:
                index = root_index(args[0])
                if index is not None:
                    details["iterate"] = index
                    details["source_order"] = len(args[0])
                if label == "fixed_target_retraction" and len(args) > 1:
                    details["target_order"] = len(args[1])
            trace.emit("method_start", id=token, method=label, **details)
            start = time.monotonic()
            try:
                result = function(*args, **kwargs)
            except BaseException:
                trace.emit(
                    "method_end", id=token, outcome="exception",
                    seconds=round(time.monotonic() - start, 3),
                )
                raise
            if label == "fixed_target_retraction":
                outcome = "positive" if result else "no_certificate"
            elif isinstance(result, tuple) and result:
                verdict = result[0]
                outcome = getattr(verdict, "name", "no_certificate")
            elif result is True:
                outcome = "positive"
            elif result is False or result is None:
                outcome = "no_certificate"
            else:
                outcome = "positive"
            trace.emit(
                "method_end", id=token, outcome=outcome,
                seconds=round(time.monotonic() - start, 3),
            )
            return result
        return wrapped

    setattr(small, "CliqueSequence", TracedSequence)
    setattr(small, "clique_graph", observe_clique_graph)
    setattr(small, "completely_pared_graph", observe_pare)
    setattr(small, "classify_clique_behavior", observe_classify)
    setattr(small, "_test_iterate_certificates", observe_iterate_pass)
    for name in NAMED_CRITERIA:
        if name in originals:
            setattr(small, name, method_wrapper(originals[name], name.lstrip("_")))
    for name, label in ITERATE_CRITERIA.items():
        if name in originals:
            setattr(
                small,
                name,
                method_wrapper(originals[name], label, iterate_only=True),
            )
    try:
        yield
    finally:
        for name, original in originals.items():
            setattr(small, name, original)
