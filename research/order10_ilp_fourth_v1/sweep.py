"""Positive-only MILP/fixed-target-CSP screen of unresolved order-ten P4 cores.

Every potential mathematical positive is checked with public pycliques
routines and saved as a complete pointwise-fixed graph retraction. This
experimental *consumer* of pycliques does not implement private solvers.
Bounded failures and excluded large iterates are always inconclusive.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
import sys
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "indeterminate_order_10_v13.txt"
CURRENT_BLOB = "deca07f54c885d41011e266a03868341c054bdf6"

sys.path.insert(0, str(ROOT))
from research.order10_nonlocal_oct_stiff_v1.sweep import (  # noqa: E402
    entries as older_stiff_cases,
    iterate,
)


def cases() -> list[tuple[int, str]]:
    raw = CURRENT.read_bytes()
    actual = hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()
    if actual != CURRENT_BLOB:
        raise ValueError("Immutable v13 census index has been modified")
    if (ROOT / "indeterminate_order_10.txt").read_bytes() != raw:
        raise ValueError("The authoritative current index is not v13")
    active = {}
    for line in CURRENT.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        row = line.split()
        if len(row) != 6:
            raise ValueError("Malformed current unresolved row")
        if row[1] == "10" and row[3:] == ["-", "-", "-"]:
            active[int(row[0])] = row[2]
    result = [(index, g6) for index, g6 in older_stiff_cases()
              if active.get(index) == g6]
    if len(result) < 200:
        raise ValueError("Unexpected shrinkage of original stiff cohort")
    return result


def search_one(
    index: int, graph6: str, *, bound: int, max_k3: int, max_k4: int,
    ilp_seconds: float, restarts: int, max_states: int,
) -> dict:
    import pycliques
    from pycliques.octahedral_ilp import (
        OctahedronILPStatus, find_induced_octahedron_ilp,
    )
    k3 = iterate(graph6, 3, bound)
    report = {"index": index, "source_graph6": graph6,
              "status": "INCONCLUSIVE", "trials": []}
    if k3 is None:
        report["reason"] = "THIRD_ITERATE_BOUND"
        return report
    report["k3_order"] = len(k3)
    if len(k3) > max_k3:
        report["reason"] = "THIRD_ORDER_EXCLUDED"
        return report
    raw = pycliques.clique_graph(k3, bound=bound)
    if raw is None:
        report["reason"] = "FOURTH_ITERATE_BOUND"
        return report
    host = nx.convert_node_labels_to_integers(pycliques.completely_pared_graph(raw))
    n = len(host)
    report.update({"k4_order": n, "k4_edges": host.number_of_edges()})
    if n > max_k4:
        report["reason"] = "FOURTH_ORDER_EXCLUDED"
        return report
    if n < 6:
        report["reason"] = "TOO_SMALL"
        return report

    for trial in range(restarts):
        # Deterministic vertex relabeling diversifies solutions without
        # changing the graph, mathematical ILP or retraction constraints.
        labels = list(host)
        rng = random.Random((index * 1000003 + trial * 9871) % (2**32))
        order = rng.sample(labels, len(labels))
        f = {old: new for new, old in enumerate(order)}
        finv = {new: old for old, new in f.items()}
        relabeled = nx.relabel_nodes(host, f, copy=True)
        # First try maximal target; alternate pure-feasibility targets.
        maximize = trial % 3 == 0
        minimum = 3 if trial == 0 else (
            6 if n >= 100 and trial % 3 == 1 else
            8 if n >= 100 else
            4 if trial % 3 == 1 else 3
        )
        result = find_induced_octahedron_ilp(
            relabeled, min_dimension=minimum,
            maximize_dimension=maximize, require_dominating=True,
            time_limit=ilp_seconds,
        )
        record = {"trial": trial, "milp": result.status.value,
                  "dimension": result.dimension, "maximize": maximize}
        report["trials"].append(record)
        if result.antipodal_pairs is None:
            continue
        if result.status not in (
            OctahedronILPStatus.OPTIMAL,
            OctahedronILPStatus.FOUND,
            OctahedronILPStatus.FEASIBLE_LIMIT,
        ):
            continue
        pairs = [(finv[a], finv[b]) for a, b in result.antipodal_pairs]
        if not pycliques.verify_induced_octahedron(
            host, pairs, require_dominating=True
        ):
            raise AssertionError("Returned ILP target failed validation")
        if len(pairs) < 3:
            continue
        found = pycliques.find_octahedral_retraction(
            host, pairs, max_states=max_states,
            seed=(index + trial * 97) % (2**32),
        )
        record["csp"] = found.status.name
        record["states"] = found.states_explored
        if found.status is not pycliques.RetractionSearchStatus.FOUND:
            continue
        if found.retraction is None or found.inclusion is None:
            raise AssertionError("Missing alleged complete witness")
        target = host.subgraph([v for pair in pairs for v in pair])
        if not pycliques.verify_retraction_witness(
            host, target, (found.retraction, found.inclusion)
        ):
            raise AssertionError("False-positive fixed-target retraction")
        report["status"] = "CERTIFIED_DIVERGENT"
        report["reason"] = "VERIFIED_ILP_OCTAHEDRAL_RETRACTION"
        report["certificate"] = {
            "depth": 4,
            "host_graph6": nx.to_graph6_bytes(
                host, header=False).decode("ascii").strip(),
            "antipodal_pairs": [list(pair) for pair in pairs],
            "images": [found.retraction[v] for v in range(n)],
        }
        return report
    report["reason"] = "BOUNDED_SEARCH"
    return report


def verify_positive(record: dict, bound: int) -> None:
    import pycliques

    cert = record["certificate"]
    if cert["depth"] != 4:
        raise AssertionError("Wrong depth")
    k3 = iterate(record["source_graph6"], 3, bound)
    if k3 is None:
        raise AssertionError("Could not reconstruct third iterate")
    raw = pycliques.clique_graph(k3, bound=bound)
    if raw is None:
        raise AssertionError("Could not reconstruct fourth iterate")
    host = nx.convert_node_labels_to_integers(
        pycliques.completely_pared_graph(raw)
    )
    expected = nx.to_graph6_bytes(host, header=False).decode("ascii").strip()
    if expected != cert["host_graph6"]:
        raise AssertionError("Host graph6 differs")
    pairs = [tuple(pair) for pair in cert["antipodal_pairs"]]
    if not pycliques.verify_induced_octahedron(
        host, pairs, require_dominating=True
    ):
            raise AssertionError("Bad induced target")
    images = cert["images"]
    if len(images) != len(host) or any(v not in host for v in images):
        raise AssertionError("Malformed projection")
    target = host.subgraph([v for pair in pairs for v in pair])
    if not pycliques.verify_retraction_witness(
        host, target,
        ({v: images[v] for v in host}, {v: v for v in target}),
    ):
        raise AssertionError("Invalid full graph retraction")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("plan", "one", "run", "verify"))
    p.add_argument("--index", type=int, default=0)
    p.add_argument("--shard", type=int, default=0)
    p.add_argument("--shards", type=int, default=8)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--bound", type=int, default=1500)
    p.add_argument("--max-k3", type=int, default=40)
    p.add_argument("--max-k4", type=int, default=180)
    p.add_argument("--ilp-seconds", type=float, default=3.0)
    p.add_argument("--restarts", type=int, default=4)
    p.add_argument("--max-states", type=int, default=5000)
    p.add_argument("--timeout", type=int, default=24)
    p.add_argument("--output", type=Path)
    p.add_argument("--input-results", type=Path)
    args = p.parse_args()

    if (args.shards < 1 or not 0 <= args.shard < args.shards
            or args.limit < 0 or args.restarts < 1 or args.max_k4 < 6
            or args.max_k3 < 1 or args.bound < 3 or args.timeout < 1
            or args.ilp_seconds <= 0 or args.max_states < 1):
        p.error("Invalid resource or shard settings")
    population = cases()
    selected = population[args.shard::args.shards]
    if args.limit:
        selected = selected[:args.limit]
    if args.action == "plan":
        print(json.dumps({"population": len(population), "selected": len(selected),
                          "first_indices": [x[0] for x in selected[:20]]}))
        return
    if args.action == "one":
        candidate = next((x for x in population if x[0] == args.index), None)
        if candidate is None:
            p.error("Unknown active source index")
        print(json.dumps(search_one(
            *candidate, bound=args.bound, max_k3=args.max_k3,
            max_k4=args.max_k4, ilp_seconds=args.ilp_seconds,
            restarts=args.restarts, max_states=args.max_states,
        ), separators=(",", ":")))
        return
    if args.action == "verify":
        if args.input_results is None:
            p.error("--input-results is required")
        data = json.loads(args.input_results.read_text())
        if data.get("schema") != 1 or data.get("source") != CURRENT.name:
            raise ValueError("Incorrect sweep schema")
        opts = data["settings"]
        selected = population[opts["shard"]::opts["shards"]]
        if opts["limit"]:
            selected = selected[:opts["limit"]]
        recs = data["records"]
        if [(r["index"], r["source_graph6"]) for r in recs] != selected:
            raise AssertionError("Missing, duplicate or displaced records")
        for r in recs:
            if r["status"] == "CERTIFIED_DIVERGENT":
                verify_positive(r, opts["bound"])
        print("REPLAYED", len(recs), "cases",
              sum(r["status"] == "CERTIFIED_DIVERGENT" for r in recs),
              "complete positive certificates")
        return
    if args.output is None:
        p.error("--output is required for run")
    records = []
    for index, g6 in selected:
        command = [sys.executable, str(Path(__file__)), "one", "--index",
                   str(index), "--bound", str(args.bound), "--max-k3",
                   str(args.max_k3), "--max-k4", str(args.max_k4),
                   "--ilp-seconds", str(args.ilp_seconds),
                   "--restarts", str(args.restarts),
                   "--max-states", str(args.max_states)]
        try:
            process = subprocess.run(command, check=True, capture_output=True,
                                     text=True, timeout=args.timeout)
            record = json.loads(process.stdout)
        except subprocess.TimeoutExpired:
            record = {"index": index, "source_graph6": g6, "status": "TIMEOUT"}
        except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
            record = {"index": index, "source_graph6": g6, "status": "ERROR",
                      "message": str(exc),
                      "stderr": getattr(exc, "stderr", "")}
        records.append(record)
        print("SCREEN", index, record["status"], record.get("reason", ""),
              "K3", record.get("k3_order"), "K4", record.get("k4_order"),
              flush=True)
        if record["status"] == "CERTIFIED_DIVERGENT":
            print("POSITIVE_CERT", json.dumps(record, separators=(",", ":")),
                  flush=True)
    data = {"schema": 1, "source": CURRENT.name,
            "settings": {"shard": args.shard, "shards": args.shards,
                         "limit": args.limit, "bound": args.bound,
                         "max_k3": args.max_k3, "max_k4": args.max_k4,
                         "ilp_seconds": args.ilp_seconds,
                         "restarts": args.restarts,
                         "max_states": args.max_states},
            "records": records}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n")
    print("SWEEP_SUMMARY", json.dumps({
        "shard": args.shard,
        "counts": {s: sum(r["status"] == s for r in records)
                   for s in ("CERTIFIED_DIVERGENT", "INCONCLUSIVE", "TIMEOUT",
                             "ERROR")},
        "k4_built": sum("k4_order" in r for r in records),
        "k4_screened": sum(r.get("reason") == "BOUNDED_SEARCH" for r in records),
        "positives": [r["index"] for r in records
                      if r["status"] == "CERTIFIED_DIVERGENT"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
