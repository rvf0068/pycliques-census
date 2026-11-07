"""Independent certified homotopy-type pilot for 54 unresolved order-9 graphs.

This is NOT the full 261080-graph homotopy census, which is already
implemented in rvf0068/pycliques-homotopy-census. It produces original-indexed
G and K(G) wedge-of-spheres certificates with explicit exact/limited flags.
Each case runs in a fresh process with a wall-clock timeout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import networkx as nx

import staged


def homotopy(graph: nx.Graph, graph6: str, tag: str) -> dict:
    from pycombtop.homotopy_type import homotopy_type_with_verdict

    random.seed(int.from_bytes(
        hashlib.sha256((graph6 + "\0" + tag).encode("ascii")).digest()[:8], "big"
    ))
    verdict = homotopy_type_with_verdict(
        graph, max_vertices=64, max_simplices=25000,
    )
    if verdict.is_limited:
        return {"status": "LIMITED", "spheres": None, "reason": verdict.reason}
    spheres = {
        str(k): int(v) for k, v in verdict.wedge.spheres.items() if v
    }
    return {
        "status": "EXACT" if verdict.is_exact else "BETTI_ONLY",
        "spheres": spheres,
        "reason": verdict.reason,
    }


def one(index: int) -> dict:
    from pycliques.cliques import clique_graph

    remaining, origins, _source = staged.active(9)
    row = remaining[index]
    graph6 = row["graph6"]
    graph = nx.from_graph6_bytes(graph6.encode())
    g = homotopy(graph, graph6, "G")
    kg = clique_graph(graph, bound=128, max_edges=5000)
    k = (
        homotopy(kg, graph6, "K(G)")
        if kg is not None
        else {"status": "LIMITED", "spheres": None, "reason": "K(G) bound reached"}
    )
    return {
        "index": index, "graph6": graph6,
        "group": ("conjectured" if origins[index].split()[4] == "conjectured_divergent"
                  else "nonconjectural"),
        "G": g, "KG": k,
        "comparison": (
            "EQUIVALENT_CERTIFIED_WEDGES"
            if g["status"] == k["status"] == "EXACT" and g["spheres"] == k["spheres"]
            else "DISTINCT_BETTI"
            if g["spheres"] is not None and k["spheres"] is not None
            and g["spheres"] != k["spheres"]
            else "UNRESOLVED"
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--all", action="store_true")
    mode.add_argument("--case", type=int)
    p.add_argument("--per-case-timeout", type=float, default=15.0)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    if args.case is not None:
        print(json.dumps(one(args.case), sort_keys=True))
        return
    if args.per_case_timeout <= 0:
        p.error("Timeout must be positive")

    remaining, origins, _source = staged.active(9)
    records = []
    for index in sorted(remaining):
        started = time.monotonic()
        try:
            child = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--case", str(index)],
                stdin=subprocess.DEVNULL, capture_output=True, text=True,
                timeout=args.per_case_timeout, check=False,
            )
            if child.returncode:
                entry = {"index": index, "status": "ERROR",
                         "stderr": child.stderr[-1200:]}
            else:
                entry = json.loads(child.stdout)
                entry["status"] = "COMPLETE"
        except subprocess.TimeoutExpired:
            entry = {"index": index, "status": "TIMEOUT"}
        entry["wall_seconds"] = round(time.monotonic() - started, 3)
        records.append(entry)
        if entry["status"] != "COMPLETE" or index in {208409, 260910, 180593}:
            print(json.dumps(entry, sort_keys=True), flush=True)

    grouped = {}
    for group in ("conjectured", "nonconjectural"):
        subset = [row for row in records
                  if row["index"] in remaining
                  and (origins[row["index"]].split()[4] == "conjectured_divergent")
                  == (group == "conjectured")]
        grouped[group] = {
            "total": len(subset),
            "status": dict(Counter(row["status"] for row in subset)),
            "types_G": dict(Counter(
                str(row.get("G", {}).get("spheres"))
                for row in subset if row["status"] == "COMPLETE"
            )),
            "comparison": dict(Counter(
                row.get("comparison")
                for row in subset if row["status"] == "COMPLETE"
            )),
        }
    report = {
        "schema": 1,
        "scope": "54 order-9 unresolved originals, not full 261080 census",
        "grouped": grouped, "records": records,
        "status_note": "EXACT only if pycombtop certifies a wedge-of-spheres type",
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print("GROUP_SUMMARY", json.dumps(grouped, sort_keys=True), flush=True)
    if any(r["status"] == "ERROR" for r in records):
        raise SystemExit("One or more homotopy workers returned an error")


if __name__ == "__main__":
    main()
