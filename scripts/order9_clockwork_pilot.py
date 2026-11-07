"""Bounded order-9 clockwork-retraction pilot on the eight beta_1=1 cases.

This program is diagnostic, not a census stage. It searches the *second
completely pared* clique iterate and uses the existing pycliques certificate
validator. The candidate cap is NOT an exhaustive negative certificate.
Run under a witness-capable revision of pycliques-project.

    python scripts/order9_clockwork_pilot.py --all --output /tmp/clockwork.json

Each graph is isolated in a fresh process with an explicit wall-clock limit.
"""
from __future__ import annotations

import argparse
import itertools
import json
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import networkx as nx

# All order-9 remaining conjecture-dependent G with reduced mod-2 beta_1=1.
CASES = (
    (180593, "HCRSv\\}"),
    (220642, "HCpVUn{"),
    (220895, "HCpVVzu"),
    (232908, "HCpunV{"),
    (233406, "HCpvUzU"),
    (251414, "HEhvTn{"),
    (251445, "HEhvTyu"),
    (260038, "HQyvex{"),
)


def betti_one_mod2(graph: nx.Graph) -> int:
    """Compute H_1 over F_2 using the cycle-space and triangle boundary."""
    edge_index = {frozenset(e): i for i, e in enumerate(graph.edges())}
    basis: dict[int, int] = {}
    for a, b, c in itertools.combinations(graph.nodes(), 3):
        if not (graph.has_edge(a, b) and graph.has_edge(a, c)
                and graph.has_edge(b, c)):
            continue
        mask = sum(1 << edge_index[frozenset(e)]
                   for e in ((a, b), (b, c), (a, c)))
        while mask:
            pivot = mask.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = mask
                break
            mask ^= basis[pivot]
    return graph.number_of_edges() - graph.number_of_nodes() + (
        nx.number_connected_components(graph)
    ) - len(basis)


def evaluate(index: int, *, max_candidates: int) -> dict:
    from pycliques.clockwork_search import find_divergent_clockwork_retract
    from pycliques.dominated import completely_pared_graph
    from pycliques.small import CliqueSequence

    original = nx.from_graph6_bytes(dict(CASES)[index].encode("ascii"))
    seq = CliqueSequence(completely_pared_graph(original), bound=200)
    levels = [seq[i] for i in range(3)]
    if any(g is None for g in levels):
        return {"index": index, "status": "CLIQUE_BOUND_EXCEEDED"}
    source = levels[2]
    assert source is not None and levels[0] is not None
    b0, b2 = betti_one_mod2(original), betti_one_mod2(source)
    if (b0, b2) != (1, 1):
        return {"index": index, "status": "BETTI_FILTER_FAILED",
                "beta1_original": b0, "beta1_k2": b2}
    started = time.monotonic()
    found = find_divergent_clockwork_retract(
        source,
        max_target_order=10,
        max_candidates=max_candidates,
        max_retraction_attempts=8,
        max_retraction_states=20_000,
        max_retraction_assignments=100_000,
        iterate_index=2,
        origin_graph=levels[0],
        iterate_graphs=tuple(levels),
        replay_clique_bound=200,
    )
    return {
        "index": index,
        "graph6": dict(CASES)[index],
        "status": found.status.name,
        "reason": found.reason,
        "source_order": len(source),
        "source_edges": source.number_of_edges(),
        "beta1_original": b0,
        "beta1_k2": b2,
        "candidates_checked": found.candidates_checked,
        "retraction_attempts": found.retraction_attempts,
        "states_explored": found.states_explored,
        "assignments_tried": found.assignments_tried,
        "verified_certificate": found.certificate is not None,
        "seconds": round(time.monotonic() - started, 3),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--all", action="store_true")
    mode.add_argument("--case", type=int, choices=[i for i, _ in CASES])
    p.add_argument("--max-candidates", type=int, default=3000)
    p.add_argument("--per-case-timeout", type=int, default=20)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    if args.max_candidates < 1 or args.per_case_timeout < 1:
        p.error("Candidate and per-case limits must be positive")

    if args.case is not None:
        print(json.dumps(evaluate(args.case, max_candidates=args.max_candidates)))
        return
    records = []
    for index, graph6 in CASES:
        started = time.monotonic()
        try:
            result = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--case", str(index),
                 "--max-candidates", str(args.max_candidates)],
                stdin=subprocess.DEVNULL, text=True, capture_output=True,
                timeout=args.per_case_timeout, check=False,
            )
            if result.returncode:
                entry = {"index": index, "graph6": graph6, "status": "ERROR",
                         "stderr": result.stderr[-1200:]}
            else:
                entry = json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            entry = {"index": index, "graph6": graph6, "status": "TIMEOUT"}
        entry["wall_seconds"] = round(time.monotonic() - started, 3)
        records.append(entry)
        print(json.dumps(entry, sort_keys=True), flush=True)

    report = {
        "schema": 1,
        "scope": "eight order-9 conditional graphs with beta1(K2)=1",
        "parameters": {
            "iterate": 2, "max_target_order": 10,
            "max_candidates": args.max_candidates,
            "per_case_timeout": args.per_case_timeout,
            "max_retraction_attempts": 8,
            "max_retraction_states": 20_000,
            "max_retraction_assignments": 100_000,
        },
        "counts": dict(Counter(r["status"] for r in records)),
        "records": records,
        "note": "LIMIT_REACHED and TIMEOUT are unresolved, NOT negative proofs",
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("SUMMARY", json.dumps(report["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
