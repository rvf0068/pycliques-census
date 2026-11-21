"""Reproducible positive-only fourth-iterate octahedral retract screen.

The immutable v11 unclassified stiff population has 1,043 sources.
We select those with completely pared K^3 of order <= --max-k3-order,
then build and pare K^4 using the pinned public pycliques API.
Every source is subprocess-timeboxed; absence of a found map is inconclusive.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from research.order10_nonlocal_oct_stiff_v1.sweep import (  # noqa: E402
    SOURCE, entries, iterate, verify_record,
)


def inspect(index: int, g6: str, *, bound: int, max_k3_order: int,
            dims: tuple[int, ...], restarts: int, states: int) -> dict:
    import pycliques

    k3 = iterate(g6, 3, bound)
    if k3 is None:
        return {"index": index, "source_graph6": g6,
                "status": "INCONCLUSIVE", "reason": "K3_ITERATE_BOUND"}
    report = {"index": index, "source_graph6": g6,
              "status": "INCONCLUSIVE", "k3_order": len(k3),
              "k3_edges": k3.number_of_edges()}
    if len(k3) > max_k3_order:
        report["reason"] = "K3_ORDER_EXCLUDED"
        return report
    k4_unpared = pycliques.clique_graph(k3, bound=bound)
    if k4_unpared is None:
        report["reason"] = "K4_ITERATE_BOUND"
        return report
    host = nx.convert_node_labels_to_integers(
        pycliques.completely_pared_graph(k4_unpared)
    )
    report.update({
        "k4_raw_order": len(k4_unpared),
        "k4_order": len(host),
        "k4_edges": host.number_of_edges(),
        "reason": "BOUNDED_SEARCH",
        "trials": [],
    })
    for dimension in dims:
        if 2 * dimension > len(host):
            continue
        seed = (index * 1_000_003 + dimension * 97 + 4 * 10_007) % (2**32)
        finder = pycliques.find_induced_octahedron_amplified(
            host, target_dimension=dimension, max_restarts=restarts,
            seed=seed, require_dominating=True,
        )
        trial = {"dimension": dimension, "finder_status": finder.status.value,
                 "best_dimension": finder.best_dimension,
                 "restarts": finder.restarts}
        report["trials"].append(trial)
        pairs = finder.antipodal_pairs
        if pairs is None:
            continue
        projection = pycliques.find_octahedral_retraction(
            host, pairs, max_states=states, seed=seed,
        )
        trial["retraction_status"] = projection.status.name
        trial["retraction_states"] = projection.states_explored
        if projection.status is not pycliques.RetractionSearchStatus.FOUND:
            continue
        assert projection.retraction is not None
        assert projection.inclusion is not None
        target = host.subgraph([v for pair in pairs for v in pair])
        assert pycliques.verify_retraction_witness(
            host, target, (projection.retraction, projection.inclusion)
        )
        report["status"] = "CERTIFIED_DIVERGENT"
        report["reason"] = "VERIFIED_OCTAHEDRAL_RETRACTION"
        report["certificate"] = {
            "depth": 4,
            "host_graph6": nx.to_graph6_bytes(
                host, header=False).decode("ascii").strip(),
            "antipodal_pairs": [list(pair) for pair in pairs],
            "images": [projection.retraction[v] for v in range(len(host))],
        }
        return report
    return report


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("plan", "one", "run", "verify"))
    p.add_argument("--index", type=int)
    p.add_argument("--shard", type=int, default=0)
    p.add_argument("--shards", type=int, default=8)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--max-k3-order", type=int, default=40)
    p.add_argument("--bound", type=int, default=1500)
    p.add_argument("--dimensions", default="3,4,5,6,8,10,12,16,24,32")
    p.add_argument("--restarts", type=int, default=200)
    p.add_argument("--states", type=int, default=2500)
    p.add_argument("--timeout-sec", type=int, default=16)
    p.add_argument("--output", type=Path)
    p.add_argument("--input-results", type=Path)
    a = p.parse_args()
    if (a.shards < 1 or not 0 <= a.shard < a.shards or a.limit < 0
            or a.max_k3_order < 1 or a.bound < 3 or a.restarts < 1
            or a.states < 1 or a.timeout_sec < 1):
        p.error("Invalid bounds or shard settings")
    dims = tuple(int(x) for x in a.dimensions.split(","))
    if not dims or any(d < 3 for d in dims) or len(set(dims)) != len(dims):
        p.error("Dimensions must be distinct integers at least three")
    cases = entries()
    chosen = cases[a.shard::a.shards]
    if a.limit:
        chosen = chosen[:a.limit]
    if a.action == "plan":
        print(json.dumps({"total": len(cases), "selected": len(chosen),
                          "indices": [row[0] for row in chosen]}))
        return
    if a.action == "verify":
        if a.input_results is None:
            p.error("--input-results required")
        result = json.loads(a.input_results.read_text(encoding="utf-8"))
        if result.get("schema") != 1 or result.get("source") != SOURCE.name:
            raise ValueError("Unexpected schema or source")
        opts = result["settings"]
        if opts["shards"] < 1 or not 0 <= opts["shard"] < opts["shards"] or opts["limit"] < 0:
            raise ValueError("Invalid recorded shard settings")
        expected_rows = cases[opts["shard"]::opts["shards"]]
        if opts["limit"]:
            expected_rows = expected_rows[:opts["limit"]]
        saved = result["records"]
        if (len(saved) != len(expected_rows) or
                [(r["index"], r["source_graph6"]) for r in saved] != expected_rows):
            raise ValueError("Source identities or coverage differ from pinned v11")
        counts = {}
        for record in saved:
            status = record["status"]
            if status not in ("INCONCLUSIVE", "TIMEOUT", "ERROR", "CERTIFIED_DIVERGENT"):
                raise ValueError("Unknown record status")
            counts[status] = counts.get(status, 0) + 1
            if status == "CERTIFIED_DIVERGENT":
                if record["certificate"]["depth"] != 4:
                    raise ValueError("Wrong witness depth")
                verify_record(record, opts["bound"])
        print("Verified", len(saved), "indexed records;", counts)
        return
    if a.action == "one":
        case = next((r for r in cases if r[0] == a.index), None)
        if case is None:
            p.error("--index must be a source McKay index in v11")
        result = inspect(*case, bound=a.bound, max_k3_order=a.max_k3_order,
                         dims=dims, restarts=a.restarts, states=a.states)
        print(json.dumps(result, separators=(",", ":")))
        return
    if a.output is None:
        p.error("--output required for run")
    records = []
    for index, g6 in chosen:
        cmd = [sys.executable, str(Path(__file__)), "one", "--index", str(index),
               "--max-k3-order", str(a.max_k3_order), "--bound", str(a.bound),
               "--dimensions", a.dimensions, "--restarts", str(a.restarts),
               "--states", str(a.states)]
        try:
            child = subprocess.run(cmd, capture_output=True, text=True,
                                   check=True, timeout=a.timeout_sec)
            record = json.loads(child.stdout)
        except subprocess.TimeoutExpired:
            record = {"index": index, "source_graph6": g6, "status": "TIMEOUT"}
        except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
            record = {"index": index, "source_graph6": g6, "status": "ERROR",
                      "message": str(exc),
                      "stderr": getattr(exc, "stderr", "")}
        records.append(record)
        print(index, record["status"], record.get("reason", ""), flush=True)
    payload = {"schema": 1, "source": SOURCE.name,
               "settings": {"shard": a.shard, "shards": a.shards, "limit": a.limit,
                            "max_k3_order": a.max_k3_order, "bound": a.bound,
                            "dimensions": dims, "restarts": a.restarts,
                            "states": a.states, "timeout_sec": a.timeout_sec},
               "records": records}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("Saved", a.output)


if __name__ == "__main__":
    main()
