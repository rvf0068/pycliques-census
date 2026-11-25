"""Classify one graph6 record and replay its schema-3 certificate."""

import argparse
import json
import sys
from contextlib import ExitStack
from pathlib import Path

import networkx as nx
from pycliques import small

# The historical scripts import each other as top-level modules.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import inspect_certificates_v3 as archived

try:
    import pycliques.certificate_records as certificate_records
except ModuleNotFoundError as error:
    if error.name != "pycliques.certificate_records":
        raise
    certificate_records = None


def inspect_graph(graph6, *, bound=120, proved_only=False, diagnostics=None):
    if certificate_records is None:
        if proved_only:
            raise ValueError(
                "--proved-only requires pycliques with per-call reference selection"
            )
        return archived.classify_example(graph6, bound=bound, trace_file=diagnostics)

    graph = nx.from_graph6_bytes(graph6.encode("ascii"))
    with ExitStack() as stack:
        if diagnostics is not None:
            trace = stack.enter_context(archived.ProgressTrace(diagnostics))
            stack.enter_context(archived.trace_classifier_v3(trace))
        result = small.classify_clique_behavior(
            graph,
            bound=bound,
            retraction_depth=2,
            references=small.select_reference_graphs(proved_only=proved_only),
        )
    record = certificate_records.serialize_result(graph, result, bound=bound)
    record.update(
        graph6=graph6,
        bound=bound,
        iterations_checked=result.iterations_checked,
        bound_exceeded=result.bound_exceeded,
    )
    if diagnostics is not None:
        record["diagnostics"] = archived.summarize_events_v3(diagnostics)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph6")
    parser.add_argument("--bound", type=int, default=120)
    parser.add_argument(
        "--proved-only", action="store_true", help="Use only proved reference graphs"
    )
    parser.add_argument(
        "--verify-chain", action="store_true", help="Replay the pared iterates"
    )
    parser.add_argument(
        "--require-proof", action="store_true", help="Fail unless a proof is verified"
    )
    parser.add_argument(
        "--diagnostics", type=Path, help="Write a JSONL trace of classification methods"
    )
    args = parser.parse_args()
    try:
        record = inspect_graph(
            args.graph6,
            bound=args.bound,
            proved_only=args.proved_only,
            diagnostics=args.diagnostics,
        )
    except ValueError as error:
        parser.error(str(error))
    if args.require_proof and record["proof_status"] != "verified_local":
        raise SystemExit("No independently verified proof is available")
    if args.verify_chain and record["proof"] is not None:
        verify = (
            archived.verify_record
            if certificate_records is None
            else certificate_records.verify_record
        )
        if not verify(record, verify_iterate=True):
            raise SystemExit("Full pared-iterate proof replay failed")
        record["iterate_chain_verified"] = True
    print(json.dumps(record, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
