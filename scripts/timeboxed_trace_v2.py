"""Streaming, read-only diagnostics for the *root* pared clique sequence.

The pinned pycliques classifier is not changed. Temporary wrappers observe
its lazy CliqueSequence construction and its theorem-based tests. Each event
is appended and fsynced before the computation continues, so a forcibly
terminated worker still leaves verifiable partial *observations* (not proofs).
"""
from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from pathlib import Path

from pycliques import small

METHODS = (
    ("_classify_reference_graph", "registered_proven_reference"),
    ("_classify_suspension_2_coaffination", "suspension_coaffination"),
    ("_classify_reference_dependency", "reference_retraction"),
    ("_classify_local_bridge", "local_bridge_contraction"),
    ("_classify_non_triangle_edge", "non_triangle_edge_deletion"),
    ("_classify_inverse_cutpoint_extension", "inverse_cutpoint_extension"),
)
DEFAULT_METHODS = (
    "clockwork",
    "eventually_clique_helly",
    "retraction_suspension_C5_G0",
    "retraction_suspension_C6_G0",
    "retraction_suspension_C7_G0",
    "retraction_complement_C8_G0",
    "retraction_suspension_C5_G1",
    "retraction_suspension_C6_G1",
    "retraction_suspension_C7_G1",
    "retraction_complement_C8_G1",
    "eventually_special_octahedra",
)


class ProgressTrace:
    def __init__(self, filename):
        self.filename = Path(filename)
        self.started = time.monotonic()
        self.depth = 0
        self.root_sequence = None
        self.current_sequence = None
        self.stream = None

    def __enter__(self):
        self.stream = self.filename.open("w", encoding="utf-8")
        return self

    def __exit__(self, *_):
        if self.stream is not None:
            self.stream.close()
            self.stream = None

    def emit(self, event, **fields):
        row = {
            "event": event,
            "elapsed_seconds": round(time.monotonic() - self.started, 3),
            **fields,
        }
        self.stream.write(json.dumps(row, separators=(",", ":"), sort_keys=True) + "\n")
        self.stream.flush()
        os.fsync(self.stream.fileno())


def summarize_events(filename):
    """Return compact, honest diagnostics; an unfinished method is NOT a failure."""
    observations = {}
    methods = []
    pending = {}
    last_event = None
    try:
        lines = Path(filename).read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        lines = []
    for line in lines:
        try:
            row = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue  # Interrupted append: retain the preceding complete events.
        if not isinstance(row, dict):
            continue
        last_event = row
        event = row.get("event")
        step = row.get("iterate")
        if event == "initial_pared":
            observations[0] = {
                "index": 0,
                "pared_order": row["order"],
                "pared_edges": row["edges"],
            }
        elif event in {"iterate_start", "clique_graph_complete",
                       "pared_iterate_complete", "clique_bound_exceeded"}:
            item = observations.setdefault(step, {"index": step})
            if event == "iterate_start":
                item["status"] = "in_progress"
            if event == "clique_graph_complete":
                item.update({
                    "raw_order": row["order"],
                    "raw_edges": row["edges"],
                })
                item["status"] = "unpared_built"
            if event == "pared_iterate_complete":
                item.update({
                    "pared_order": row["order"],
                    "pared_edges": row["edges"],
                })
                item["status"] = "completed"
            if event == "clique_bound_exceeded":
                item["status"] = "clique_bound_exceeded"
        elif event == "method_start":
            m = {"method": row["method"], "outcome": "interrupted"}
            methods.append(m)
            pending[row["id"]] = m
        elif event == "method_end":
            m = pending.pop(row.get("id"), None)
            if m is not None:
                m["outcome"] = row["outcome"]
                m["seconds"] = row["seconds"]
    return {
        "diagnostic_schema": 1,
        "iterates": [observations[i] for i in sorted(observations)],
        "methods_tried": methods,
        "in_progress_method": (
            methods[-1]["method"] if methods and methods[-1]["outcome"] == "interrupted"
            else None
        ),
        "last_progress_event": last_event["event"] if last_event else None,
    }


@contextmanager
def trace_classifier(trace):
    """Install temporary wrappers on a *worker-local* pycliques module."""
    originals = {}
    for name in ("CliqueSequence", "clique_graph", "completely_pared_graph",
                 "classify_clique_behavior", "_default_classifiers"):
        originals[name] = getattr(small, name)
    for name, _ in METHODS:
        if hasattr(small, name):
            originals[name] = getattr(small, name)

    seq_class = originals["CliqueSequence"]

    class TracedSequence(seq_class):
        def __init__(self, graph, bound=30):
            super().__init__(graph, bound=bound)
            if trace.root_sequence is None and trace.depth == 1:
                trace.root_sequence = self
                trace.emit("initial_pared", order=graph.number_of_nodes(),
                           edges=graph.number_of_edges())

        def __getitem__(self, index):
            prev = trace.current_sequence
            trace.current_sequence = self
            try:
                return super().__getitem__(index)
            finally:
                trace.current_sequence = prev

    def observed_clique_graph(graph, *args, **kwargs):
        is_root = (trace.root_sequence is not None and
                   trace.current_sequence is trace.root_sequence)
        if is_root:
            index = len(trace.root_sequence._graphs)
            trace.emit("iterate_start", iterate=index,
                       input_order=graph.number_of_nodes(),
                       input_edges=graph.number_of_edges())
        result = originals["clique_graph"](graph, *args, **kwargs)
        if is_root:
            if result is None:
                trace.emit("clique_bound_exceeded", iterate=index)
            else:
                trace.emit("clique_graph_complete", iterate=index,
                           order=result.number_of_nodes(), edges=result.number_of_edges())
        return result

    def observed_pare(graph, *args, **kwargs):
        result = originals["completely_pared_graph"](graph, *args, **kwargs)
        if trace.root_sequence is not None and trace.current_sequence is trace.root_sequence:
            trace.emit("pared_iterate_complete",
                       iterate=len(trace.root_sequence._graphs),
                       order=result.number_of_nodes(), edges=result.number_of_edges())
        return result

    def observed_classify(*args, **kwargs):
        trace.depth += 1
        try:
            return originals["classify_clique_behavior"](*args, **kwargs)
        finally:
            trace.depth -= 1

    sequence_number = 0

    def wrap_method(fn, label):
        def wrapper(*args, **kwargs):
            nonlocal sequence_number
            if trace.depth != 1:
                return fn(*args, **kwargs)
            sequence_number += 1
            token = sequence_number
            started = time.monotonic()
            trace.emit("method_start", id=token, method=label)
            try:
                result = fn(*args, **kwargs)
            except BaseException:
                trace.emit("method_end", id=token, outcome="exception",
                           seconds=round(time.monotonic()-started, 3))
                raise
            verdict = result[0] if result is not None else None
            outcome = (getattr(verdict, "name", "no_certificate")
                       if verdict is not None else "no_certificate")
            trace.emit("method_end", id=token, outcome=outcome,
                       seconds=round(time.monotonic()-started, 3))
            return result
        return wrapper

    def observed_default_methods(*args, **kwargs):
        callbacks = originals["_default_classifiers"](*args, **kwargs)
        return [
            wrap_method(callback, DEFAULT_METHODS[i] if i < len(DEFAULT_METHODS)
                        else f"classifier_rule_{i}")
            for i, callback in enumerate(callbacks)
        ]

    setattr(small, "CliqueSequence", TracedSequence)
    setattr(small, "clique_graph", observed_clique_graph)
    setattr(small, "completely_pared_graph", observed_pare)
    setattr(small, "classify_clique_behavior", observed_classify)
    setattr(small, "_default_classifiers", observed_default_methods)
    for name, label in METHODS:
        if name in originals:
            setattr(small, name, wrap_method(originals[name], label))
    try:
        yield
    finally:
        for name, value in originals.items():
            setattr(small, name, value)
