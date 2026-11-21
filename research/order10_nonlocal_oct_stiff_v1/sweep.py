"""Positive-only nonlocal octahedral retraction screen of stiff 10-vertex cores.

Uses the public pycliques-project API; never updates census indices or treats
bounded failure as a negative proof. A separate process limits each case's time.
Run in a Codespace with pycliques-project installed as in the census workflow.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "indeterminate_order_10_v11.txt"
SOURCE_GIT_BLOB = "34023e9323945c4a6e5e1249c37ba955ba62473f"


def entries() -> list[tuple[int, str]]:
    raw = SOURCE.read_bytes()
    digest = hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\\0" + raw
    ).hexdigest()
    if digest != SOURCE_GIT_BLOB:
        raise ValueError("Frozen v11 index changed")
    data = []
    for line in raw.decode("utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 6:
            raise ValueError("Malformed v11 census row")
        if parts[1] == "10" and parts[3:] == ["-", "-", "-"]:
            data.append((int(parts[0]), parts[2]))
    if len(data) != 1043 or [i for i, _ in data] != sorted(set(i for i, _ in data)):
        raise ValueError("Expected exactly 1043 sorted unclassified stiff ten-cores")
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
    if record["status"] != "CERTIFIED_DIVERGENT":
        return
    import pycliques
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
    p.add_argument("--shard", type=int, default=0)
    p.add_argument("--shards", type=int, default=8)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--output", type=Path)
    p.add_argument("--input-results", type=Path)
    p.add_argument("--max-depth", type=int, default=3)
    p.add_argument("--bound", type=int, default=450)
    p.add_argument("--dimensions", default="3,4,5,6,8,10")
    p.add_argument("--restarts", type=int, default=160)
    p.add_argument("--states", type=int, default=1200)
    p.add_argument("--timeout-sec", type=int, default=8)
    a = p.parse_args()
    candidates = entries()
    if a.shards < 1 or not 0 <= a.shard < a.shards or a.limit < 0:
        p.error("Invalid shard, shards, or limit")
    selected = candidates[a.shard::a.shards]
    if a.limit:
        selected = selected[:a.limit]
    if a.action == "plan":
        print(json.dumps({"total": len(candidates), "selected": len(selected),
                          "shard": a.shard, "shards": a.shards,
                          "indices": [i for i, _ in selected]}, indent=2))
        return
    if a.action == "verify":
        if a.input_results is None:
            p.error("--input-results is required for verify")
        result = json.loads(a.input_results.read_text())
        settings = result["settings"]
        if any(type(settings[k]) is not int for k in ("shard", "shards", "limit")):
            raise ValueError("Invalid saved shard settings")
        if settings["shards"] < 1 or not 0 <= settings["shard"] < settings["shards"] or settings["limit"] < 0:
            raise ValueError("Invalid saved shard selection")
        expected_rows = candidates[settings["shard"]::settings["shards"]]
        if settings["limit"]:
            expected_rows = expected_rows[:settings["limit"]]
        expected = dict(expected_rows)
        if result.get("schema") != 1 or result.get("source") != SOURCE.name:
            raise ValueError("Unexpected sweep report schema or source")
        records = result.get("records")
        if not isinstance(records, list):
            raise ValueError("Missing sweep records")
        indices = [record.get("index") for record in records]
        if len(indices) != len(expected) or set(indices) != set(expected):
            raise ValueError("Incomplete or duplicated McKay indices in sweep report")
        if len(set(indices)) != len(indices):
            raise ValueError("Duplicate McKay index in sweep report")
        settings = result["settings"]
        bound = settings["bound"]
        if type(bound) is not int or bound < 2:
            raise ValueError("Invalid saved clique bound")
        for record in records:
            if expected[record["index"]] != record.get("source_graph6"):
                raise ValueError("Incorrect indexed source graph6")
            if record.get("status") not in (
                "INCONCLUSIVE", "TIMEOUT", "CERTIFIED_DIVERGENT", "ERROR"
            ):
                raise ValueError("Unknown sweep result status")
            verify_record(record, bound)
        print("Verified", len(records), "records")
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
    if a.index is not None:
        p.error("Use action one --index for a single case; run writes complete reports")
    cases = selected
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
               "settings": {"shard": a.shard, "shards": a.shards, "limit": a.limit,
                            "max_depth": a.max_depth, "bound": a.bound,
                            "dimensions": dims, "restarts": a.restarts,
                            "states": a.states, "timeout_sec": a.timeout_sec},
               "records": records}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(payload, indent=2) + "\n")
    print("Saved", a.output)


if __name__ == "__main__":
    main()
