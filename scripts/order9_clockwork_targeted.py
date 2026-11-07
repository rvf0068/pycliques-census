"""Target-library alternative to the slow exhaustive induced-clockwork scan.

Generate all clockwork templates of order 9 or 10 with three segments, crown
size 2 and nondecreasing core adjacency tables. Keep only isomorphism classes
whose divergence is certified by the *existing* clockwork theorem.

Then ask the improved pycliques.retractions.retracts for a first witness
onto each known-divergent template. Search is isolated per original graph and
time-bounded; exhaustion proves only absence of retractions to THIS library.
"""
from __future__ import annotations

import argparse
import itertools
import json
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

import networkx as nx

from order9_clockwork_pilot import CASES, betti_one_mod2


def library() -> list[dict]:
    from pycliques.clockwork import (
        ClockworkDivergenceStatus,
        clockwork_divergence_result,
        clockwork_graph,
    )

    targets: list[tuple[nx.Graph, dict]] = []
    for sizes in ((1, 1, 1), (2, 1, 1)):
        tables = [
            list(itertools.combinations_with_replacement(
                range(sizes[(i + 1) % 3] + 1), sizes[i]
            ))
            for i in range(3)
        ]
        for rows in itertools.product(*tables):
            for permutation in ((0, 1), (1, 0)):
                G = clockwork_graph(
                    list(sizes), [list(row) for row in rows], 2, list(permutation)
                )
                try:
                    status = clockwork_divergence_result(
                        G, fallback_enabled=False, fallback_max_order=10, fallback_max_candidates=2000
                    )
                except (ValueError, nx.NetworkXException):
                    continue
                if status.status is not ClockworkDivergenceStatus.DIVERGENT:
                    continue
                if any(nx.is_isomorphic(G, old) for old, _ in targets):
                    continue
                numbered = nx.convert_node_labels_to_integers(G)
                graph6 = nx.to_graph6_bytes(numbered, header=False).decode().strip()
                entry = {
                    "graph6": graph6,
                    "order": len(G),
                    "sizes": list(sizes),
                    "core_adjacencies": [list(row) for row in rows],
                    "permutation": list(permutation),
                }
                targets.append((G, entry))
    return [record for _, record in targets]


def solve_one(index: int, target_path: Path) -> dict:
    from pycliques.dominated import completely_pared_graph
    from pycliques.retractions import retracts, verify_retraction_witness
    from pycliques.small import CliqueSequence

    g6 = dict(CASES)[index]
    original = nx.from_graph6_bytes(g6.encode())
    seq = CliqueSequence(completely_pared_graph(original), bound=200)
    g2 = seq[2]
    if g2 is None:
        return {"index": index, "status": "CLIQUE_BOUND_EXCEEDED"}
    if betti_one_mod2(g2) != 1:
        return {"index": index, "status": "SKIPPED_BY_HOMOLOGY"}

    targets = json.loads(target_path.read_text())
    start = time.monotonic()
    checked = 0
    for target in targets:
        H = nx.from_graph6_bytes(target["graph6"].encode())
        checked += 1
        witness = retracts(g2, H)
        if not isinstance(witness, tuple):
            continue
        if not verify_retraction_witness(g2, H, witness):
            raise RuntimeError("Positive target retraction failed independent check")
        projection, inclusion = witness
        host_index = {v: i for i, v in enumerate(g2)}
        target_index = {v: i for i, v in enumerate(H)}
        return {
            "index": index, "graph6": g6, "status": "FOUND",
            "tested_targets": checked,
            "target_graph6": target["graph6"],
            "source_graph6": nx.to_graph6_bytes(
                nx.convert_node_labels_to_integers(g2), header=False
            ).decode().strip(),
            "source_iterate": 2,
            "target_proof": target,
            "projection_indices": [target_index[projection[v]] for v in g2],
            "inclusion_indices": [host_index[inclusion[v]] for v in H],
            "verified_retraction": True,
            "seconds": round(time.monotonic() - start, 3),
        }
    return {
        "index": index, "graph6": g6, "status": "EXHAUSTED_TARGET_LIBRARY",
        "tested_targets": checked,
        "source_order": len(g2),
        "seconds": round(time.monotonic() - start, 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--all", action="store_true")
    choice.add_argument("--case", type=int, choices=[i for i, _ in CASES])
    parser.add_argument("--targets", type=Path)
    parser.add_argument("--per-case-timeout", type=float, default=20.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.case is not None:
        if args.targets is None:
            parser.error("--case requires --targets")
        print(json.dumps(solve_one(args.case, args.targets), sort_keys=True))
        return
    if args.per_case_timeout <= 0:
        parser.error("timeout must be positive")
    target_rows = library()
    print(f"Certified divergent nonisomorphic target templates: {len(target_rows)}", flush=True)
    with tempfile.TemporaryDirectory() as folder:
        target_path = Path(folder) / "targets.json"
        target_path.write_text(json.dumps(target_rows))
        records = []
        for index, g6 in CASES:
            started = time.monotonic()
            try:
                p = subprocess.run(
                    [sys.executable, str(Path(__file__).resolve()),
                     "--case", str(index), "--targets", str(target_path)],
                    stdin=subprocess.DEVNULL, text=True, capture_output=True,
                    timeout=args.per_case_timeout, check=False,
                )
                if p.returncode:
                    row = {"index": index, "graph6": g6, "status": "ERROR",
                           "stderr": p.stderr[-1200:]}
                else:
                    row = json.loads(p.stdout)
            except subprocess.TimeoutExpired:
                row = {"index": index, "graph6": g6, "status": "TIMEOUT"}
            row["wall_seconds"] = round(time.monotonic() - started, 3)
            print(json.dumps(row, sort_keys=True), flush=True)
            records.append(row)
    summary = {
        "schema": 1,
        "target_library": target_rows,
        "target_scope": "three core/crown segments, sizes (1,1,1) and (2,1,1)",
        "proof_scope": "positive retraction onto a theorem-certified divergent clockwork",
        "per_case_timeout": args.per_case_timeout,
        "counts": dict(Counter(row["status"] for row in records)),
        "records": records,
    }
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n")
    print("SUMMARY", json.dumps(summary["counts"], sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
