"""Read-only bounded nonlocal octahedral sweep for the 13 unresolved 9-vertex cases.

Uses the public pycliques-project API; never updates census indices or treats
bounded failure as a negative proof. A separate process limits each case's time.
Run in a Codespace with pycliques-project installed as in the census workflow.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "indeterminate_order_9_v3.txt"


def entries() -> list[tuple[int, str]]:
    data = []
    for line in SOURCE.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 6 or parts[4:] != ["-", "-"]:
            raise ValueError("Unexpected unresolved v3 row")
        data.append((int(parts[0]), parts[2]))
    if len(data) != 13 or [i for i, _ in data] != sorted(set(i for i, _ in data)):
        raise ValueError("Expected exactly 13 sorted unresolved nine-vertex graphs")
    return data


def iterate(graph6: str, depth: int, bound: int):
    import pycliques

    g = pycliques.completely_pared_graph(
        nx.from_graph6_bytes(graph6.encode("ascii")))
    for _ in range(depth):
        k = pycliques.clique_graph(g, bound=bound)
        if k is None:
            return None
        g = pycliques.completely_pared_graph(k)
    return nx.convert_node_labels_to_integers(g)


def inspect(index: int, graph6: str, *, max_depth: int, bound: int,
            dimensions: tuple[int, ...], restarts: int, states: int) -> dict:
    import pycliques

    steps = []
    for depth in range(max_depth + 1):
        g = iterate(graph6, depth, bound)
        if g is None:
            steps.append({"depth": depth, "status": "ITERATE_BOUND"})
            break
        stage = {"depth": depth, "order": len(g),
                 "size": g.number_of_edges(), "trials": []}
        steps.append(stage)
        for d in dimensions:
            if 2 * d > len(g):
                continue
            seed = (index * 1000003 + depth * 10007 + d * 97) % (2 ** 32)
            finder = pycliques.find_induced_octahedron_amplified(
                g, target_dimension=d, max_restarts=restarts,
                seed=seed, require_dominating=True)
            trial = {"dimension": d, "status": finder.status.value,
                     "restarts": finder.restarts,
                     "best_dimension": finder.best_dimension}
            stage["trials"].append(trial)
            pairs = finder.antipodal_pairs
            if pairs is None:
                continue
            projection = pycliques.find_octahedral_retraction(
                g, pairs, max_states=states, seed=seed)
            trial["retraction_status"] = projection.status.value
            trial["retraction_states"] = projection.states_explored
            if projection.status is not pycliques.RetractionSearchStatus.FOUND:
                continue
            assert projection.retraction is not None
            assert projection.inclusion is not None
            target = g.subgraph([v for pair in pairs for v in pair])
            assert pycliques.verify_retraction_witness(
                g, target, (projection.retraction, projection.inclusion))
            return {"index": index, "source_graph6": graph6,
                    "status": "CERTIFIED_DIVERGENT", "steps": steps,
                    "certificate": {
                        "depth": depth,
                        "host_graph6": nx.to_graph6_bytes(
                            g, header=False).decode().strip(),
                        "antipodal_pairs": [list(p) for p in pairs],
                        "images": [projection.retraction[v] for v in range(len(g))],
                    }}
    return {"index": index, "source_graph6": graph6,
            "status": "INCONCLUSIVE", "steps": steps}


def verify_record(record: dict, bound: int) -> None:
    import pycliques

    if record["status"] != "CERTIFIED_DIVERGENT":
        return
    c = record["certificate"]
    host = iterate(record["source_graph6"], c["depth"], bound)
    if host is None or nx.to_graph6_bytes(host, header=False).decode().strip() != c["host_graph6"]:
        raise ValueError("Saved host does not equal reconstructed pared iterate")
    pairs = [tuple(p) for p in c["antipodal_pairs"]]
    if not pycliques.verify_induced_octahedron(host, pairs):
        raise ValueError("Invalid induced octahedron")
    images = c["images"]
    if len(images) != len(host):
        raise ValueError("Incomplete projection")
    target = host.subgraph([v for pair in pairs for v in pair])
    if not pycliques.verify_retraction_witness(
        host, target, ({v: images[v] for v in host}, {v: v for v in target})
    ):
        raise ValueError("Invalid graph retraction certificate")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("plan", "run", "one", "verify"))
    p.add_argument("--index", type=int)
    p.add_argument("--output", type=Path)
    p.add_argument("--input-results", type=Path)
    p.add_argument("--max-depth", type=int, default=4)
    p.add_argument("--bound", type=int, default=1600)
    p.add_argument("--dimensions", default="4,5,6,8,10,12")
    p.add_argument("--restarts", type=int, default=150)
    p.add_argument("--states", type=int, default=2000)
    p.add_argument("--timeout-sec", type=int, default=90)
    a = p.parse_args()
    candidates = entries()
    if a.action == "plan":
        print(json.dumps({"count": len(candidates),
                          "indices": [i for i, _ in candidates]}, indent=2))
        return
    if a.action == "verify":
        if a.input_results is None:
            p.error("--input-results is required for verify")
        result = json.loads(a.input_results.read_text())
        expected = dict(candidates)
        for record in result["records"]:
            if expected.get(record["index"]) != record["source_graph6"]:
                raise ValueError("Incorrect indexed source graph6")
            verify_record(record, result["settings"]["bound"])
        print("Verified", len(result["records"]), "records")
        return
    if a.max_depth < 0 or a.bound < 2 or a.restarts < 1 or a.states < 1:
        p.error("Invalid search budget")
    dims = tuple(int(v) for v in a.dimensions.split(","))
    if not dims or any(d < 3 for d in dims):
        p.error("Octahedral dimensions must be at least three")
    if a.action == "one":
        case = next((row for row in candidates if row[0] == a.index), None)
        if case is None:
            p.error("Unknown McKay index")
        print(json.dumps(inspect(*case, max_depth=a.max_depth, bound=a.bound,
                                 dimensions=dims, restarts=a.restarts,
                                 states=a.states)))
        return
    if a.output is None:
        p.error("--output is required for run")
    cases = [row for row in candidates if a.index is None or row[0] == a.index]
    records = []
    for index, graph6 in cases:
        cmd = [sys.executable, str(Path(__file__)), "one", "--index", str(index),
               "--max-depth", str(a.max_depth), "--bound", str(a.bound),
               "--dimensions", a.dimensions, "--restarts", str(a.restarts),
               "--states", str(a.states)]
        try:
            child = subprocess.run(cmd, capture_output=True, text=True,
                                   timeout=a.timeout_sec, check=True)
            record = json.loads(child.stdout)
        except subprocess.TimeoutExpired:
            record = {"index": index, "source_graph6": graph6,
                      "status": "TIMEOUT"}
        except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
            record = {"index": index, "source_graph6": graph6,
                      "status": "ERROR", "message": str(exc)}
        records.append(record)
        print(index, record["status"], flush=True)
    payload = {"schema": 1, "source": SOURCE.name,
               "settings": {"max_depth": a.max_depth, "bound": a.bound,
                            "dimensions": dims, "restarts": a.restarts,
                            "states": a.states, "timeout_sec": a.timeout_sec},
               "records": records}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(payload, indent=2) + "\n")
    print("Saved", a.output)


if __name__ == "__main__":
    main()
