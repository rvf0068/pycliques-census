"""Future-only (non-mutating) v3 classifier and certificate-replay example.

Requires a separate environment with pycliques >= the witness API revision;
it does not change config/pycliques_commit.txt or any v2 stage records.

Example:
  python scripts/inspect_certificates_v3.py 'ICvbvy}|g'
  python scripts/inspect_certificates_v3.py 'IEivrzm}o' --verify-chain
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import networkx as nx

from pycliques import small
from certificate_records_v3 import serialize_result, verify_record
from timeboxed_trace_v2 import ProgressTrace
from timeboxed_trace_v3 import summarize_events_v3, trace_classifier_v3


def classify_example(graph6: str, *, bound: int = 120, trace_file=None) -> dict:
    graph = nx.from_graph6_bytes(graph6.encode("ascii"))
    if trace_file is None:
        outcome = small.classify_clique_behavior(graph, bound=bound, retraction_depth=2)
    else:
        with ProgressTrace(trace_file) as journal:
            with trace_classifier_v3(journal):
                outcome = small.classify_clique_behavior(
                    graph, bound=bound, retraction_depth=2
                )
    record = serialize_result(graph, outcome, bound=bound)
    record.update(
        graph6=graph6,
        bound=bound,
        iterations_checked=outcome.iterations_checked,
        bound_exceeded=bool(outcome.bound_exceeded),
    )
    if trace_file is not None:
        record["diagnostics"] = summarize_events_v3(trace_file)
    return record


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("graph6")
    p.add_argument("--bound", type=int, default=120)
    p.add_argument("--diagnostics", type=Path)
    p.add_argument("--verify-chain", action="store_true")
    p.add_argument("--require-proof", action="store_true")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    result = classify_example(
        args.graph6, bound=args.bound, trace_file=args.diagnostics
    )
    if args.require_proof and result["proof_status"] != "verified_local":
        raise SystemExit("No independently verified positive proof was serialized")
    if args.verify_chain:
        if result["proof"] is None:
            if args.require_proof:
                raise SystemExit("A required proof is unavailable for full chain replay")
        else:
            result["iterate_chain_verified"] = verify_record(result, verify_iterate=True)
            if not result["iterate_chain_verified"]:
                raise SystemExit("Full pared-iterate proof replay failed")
    data = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(data, encoding="utf-8")
    else:
        print(data, end="")


if __name__ == "__main__":
    main()
