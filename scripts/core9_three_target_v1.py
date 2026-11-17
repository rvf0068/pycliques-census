"""Versioned targeted experiment for three unresolved nine-vertex stiff cores.

Search ONLY reproducible positive divergence witnesses, in raw and
completely pared iterates 0..3; test special octahedra independently
and bounded retractions to proven divergent target families. Never
promote bounded failure to convergence or nondivergence, and do not
modify historical census verdicts, results or previous reports.

Run after: bash scripts/bootstrap_core9_three_target_v1.sh
  .venv-core9-three-v1/bin/python scripts/core9_three_target_v1.py run
  .venv-core9-three-v1/bin/python scripts/core9_three_target_v1.py verify
  .venv-core9-three-v1/bin/python scripts/core9_three_target_v1.py report
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile

import networkx as nx
from pycliques.small import CliqueSequence
from pycliques.dominated import find_dominated_vertex
from pycliques.retractions import (
    find_special_octahedron_witness,
    verify_special_octahedron_witness,
    SpecialOctahedronWitness,
)
from pycliques.targeted_retractions import (
    search_targeted_retractions,
    verify_targeted_retraction,
    TargetRetractionResult,
    TargetSearchStatus,
)

import core9_structure_worker
import special_octahedron_class_lift_v1 as previous

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "runs/order10/core9-three-target-v1"
SOURCE = ROOT / "runs/order10/core9-structure-v1/records"
PIN = ROOT / "config/pycliques_commit_core9_three_target_v1.txt"
CORE = {
    6914104: ("HEhev^{", 219),
    6962151: ("HEhvfzm", 242),
    6974529: ("HEh~dzm", 235),
}
MAX_LEVEL = 3
CLIQUE_BOUND = 120
WORKER_SECONDS = 80
MEMORY_MIB = 2048
TARGET_LIMITS = {
    "max_target_order": 12,
    "max_patterns": 120,
    "max_states": 15000,
    "max_assignments": 30000,
}
FAMILIES = ("octahedra", "suspensions", "cycle_complements")
SCHEMA = 1


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def number(graph: nx.Graph) -> nx.Graph:
    return nx.convert_node_labels_to_integers(graph)


def decode(graph6: str) -> nx.Graph:
    return nx.from_graph6_bytes(graph6.encode("ascii"))


def check_sources() -> dict:
    """Independent prior-core-index reconstruction plus frozen-iterate checks."""
    classes, _ = previous.saved_core_index()
    if PIN.read_text(encoding="utf-8").strip() != (
        "a78e4d979c70b0a242fa89efd2fcf3e058c318b1"
    ):
        raise ValueError("Unexpected optimized library pin")
    for core_id, (g6, size) in CORE.items():
        row = classes.get(core_id)
        if (
            row is None or row["core_graph6"] != g6
            or int(row["members"]) != size or int(row["core_order"]) != 9
        ):
            raise ValueError(f"Frozen class index disagrees with core {core_id}")
        historical = historic(core_id)
        if (
            historical.get("input_graph6") != g6
            or historical.get("member_count") != size
            or historical.get("status") != "OK"
            or historical.get("failure_iterate") != 4
            or len(historical.get("iterates", ())) != MAX_LEVEL + 1
        ):
            raise ValueError(f"Frozen structural records inconsistent at {core_id}")
    return classes


def historic(core_id: int) -> dict:
    return json.loads((SOURCE / f"{core_id:08d}.json").read_text(encoding="utf-8"))


def pared_iterates(core_id: int) -> list[nx.Graph]:
    graph = decode(CORE[core_id][0])
    if len(graph) != 9 or not nx.is_connected(graph) or find_dominated_vertex(graph) is not None:
        raise ValueError("Invalid stiff nine-vertex input")
    frozen = historic(core_id)["iterates"]
    seq = CliqueSequence(graph, bound=CLIQUE_BOUND)
    answer = []
    for i in range(MAX_LEVEL + 1):
        raw = seq[i]
        if raw is None:
            raise ValueError(f"Cannot reconstruct frozen pared K^{i} for {core_id}")
        g = number(raw)
        known = decode(frozen[i]["graph6"])
        betti, _, _ = core9_structure_worker.betti1_mod2(g)
        if (
            frozen[i]["index"] != i
            or len(g) != frozen[i]["order"]
            or g.number_of_edges() != frozen[i]["edges"]
            or betti != frozen[i]["betti1_mod2"]
            or not nx.is_isomorphic(g, known)
        ):
            raise ValueError(f"Fresh pinned pared K^{i} disagrees with frozen record")
        answer.append(g)
    return answer


def clique_graph_independent(graph: nx.Graph) -> nx.Graph:
    """Raw K, deliberately no dominated-vertex deletions."""
    facets = sorted(tuple(sorted(q)) for q in nx.find_cliques(graph))
    sets = [set(q) for q in facets]
    result = nx.Graph()
    result.add_nodes_from(range(len(sets)))
    result.add_edges_from(
        (i, j) for i in range(len(sets))
        for j in range(i + 1, len(sets)) if sets[i] & sets[j]
    )
    return result


def raw_iterates(graph6: str) -> list[nx.Graph]:
    graphs = [decode(graph6)]
    for _ in range(MAX_LEVEL):
        graphs.append(clique_graph_independent(graphs[-1]))
    return graphs


def independent_special(graph: nx.Graph) -> tuple[list[int], list[int]] | None:
    """Exhaustive facet-antipode search independent of the pinned library.

    A negative return exhausts ALL maximal privileged facets and antipode
    assignments; this is not a clique-convergence certificate.
    """
    verts = set(graph)
    for facet in nx.find_cliques(graph):
        clique = sorted(facet)
        if len(clique) < 3:
            continue
        cset = set(clique)
        domains = []
        for v in clique:
            candidates = verts - cset - set(graph[v])
            for u in clique:
                if u != v:
                    candidates.intersection_update(graph[u])
            if not candidates:
                break
            domains.append(sorted(candidates))
        if len(domains) != len(clique):
            continue

        def extend(i: int, picked: list[int]) -> list[int] | None:
            if i == len(clique):
                return picked
            for v in domains[i]:
                if v not in picked and all(graph.has_edge(v, u) for u in picked):
                    found = extend(i + 1, picked + [v])
                    if found is not None:
                        return found
            return None

        antipodes = extend(0, [])
        if antipodes is not None:
            return clique, antipodes
    return None


def special_result(graph: nx.Graph) -> dict:
    direct = independent_special(graph)
    library = find_special_octahedron_witness(graph)
    if (direct is None) != (library is None):
        raise AssertionError("Independent special-O_d search disagrees with library")
    if direct is None:
        return {"status": "ABSENT_EXHAUSTIVE", "facet": None, "antipodes": None}
    witness = SpecialOctahedronWitness(tuple(direct[0]), tuple(direct[1]))
    if not verify_special_octahedron_witness(graph, witness):
        raise AssertionError("Independent positive special witness failed library verification")
    return {
        "status": "FOUND",
        "facet": direct[0],
        "antipodes": direct[1],
        "dimension": len(direct[0]),
    }


def targeted_result(graph: nx.Graph, b1: int) -> list[dict]:
    matches = search_targeted_retractions(
        graph, families=FAMILIES, betti_numbers={1: b1}, **TARGET_LIMITS
    )
    result = []
    for family in FAMILIES:
        match = matches[family]
        row = {
            "family": family, "status": match.status.name,
            "patterns": match.patterns_checked,
            "induced_targets": match.induced_targets_checked,
            "states": match.states_explored,
            "assignments": match.assignments_tried,
            "reason": match.reason,
            "target_kind": None, "vertices": None, "projection": None,
        }
        if match.status is TargetSearchStatus.FOUND:
            if not verify_targeted_retraction(graph, match):
                raise AssertionError("Library found an invalid retraction certificate")
            row.update({
                "target_kind": match.target_kind,
                "vertices": [int(v) for v in match.target_vertices],
                "projection": [[int(u), int(v)] for u, v in
                               sorted(match.projection.items())],
            })
        result.append(row)
    return result


def replay_target(graph: nx.Graph, row: dict) -> None:
    if row.get("family") not in FAMILIES:
        raise ValueError("Unknown target family in saved record")
    if row["status"] != "FOUND":
        if row["status"] not in {"EXHAUSTED", "LIMIT_REACHED", "HOMOLOGY_EXCLUDED"}:
            raise ValueError("Unsupported bounded-search status")
        if any(row.get(k) is not None for k in ("vertices", "projection", "target_kind")):
            raise ValueError("Nonpositive result cannot contain a positive certificate")
        return
    target = TargetRetractionResult(
        family=row["family"],
        status=TargetSearchStatus.FOUND,
        target_kind=row["target_kind"],
        target_vertices=tuple(row["vertices"]),
        projection=dict(row["projection"]),
    )
    if not verify_targeted_retraction(graph, target):
        raise ValueError("Saved positive retraction does not replay")


def probe(core_id: int) -> dict:
    """Never infer a positive verdict from a failed/limited search."""
    pared = pared_iterates(core_id)
    raw = raw_iterates(CORE[core_id][0])
    results = []
    raw_results = []
    positives = []
    for level in range(MAX_LEVEL + 1):
        for mode, graph, rows in (
            ("raw", raw[level], raw_results),
            ("pared", pared[level], results),
        ):
            special = special_result(graph)
            record = {
                "level": level, "order": len(graph),
                "edges": graph.number_of_edges(), "special": special,
            }
            if special["status"] == "FOUND":
                positives.append({"level": level, "mode": mode,
                                  "rule": "special_octahedron",
                                  "dimension": special["dimension"]})
            if mode == "pared":
                b1, triangles, rank = core9_structure_worker.betti1_mod2(graph)
                diameter = nx.diameter(graph)
                record.update({
                    "b1_mod2": b1,
                    "diameter": diameter,
                    "cover_search": (
                        "SKIPPED_H1_ZERO" if b1 == 0 else "NOT_RUN_IN_THIS_STAGE"
                    ),
                    "direct_radius3_coaffination": (
                        "IMPOSSIBLE_DIAMETER_LT3" if diameter < 3 else "NOT_RUN"
                    ),
                    "targeted": targeted_result(graph, b1),
                })
                for hit in record["targeted"]:
                    if hit["status"] == "FOUND":
                        positives.append({
                            "level": level, "mode": mode,
                            "rule": "targeted_retraction", "family": hit["family"],
                            "target_kind": hit["target_kind"],
                        })
            rows.append(record)
    return {
        "schema": SCHEMA, "status": "COMPLETED",
        "core_id": core_id, "core_graph6": CORE[core_id][0],
        "original_members": CORE[core_id][1],
        "raw_levels": raw_results, "pared_levels": results,
        "positive_certificates": sorted(
            positives, key=lambda row: (row["level"], row["mode"], row["rule"])
        ),
        "interpretation": (
            "Only independently replayed positive witnesses certify K-divergence; "
            "negative targeted-search results are scoped to configured budgets"
        ),
    }


def validate_record(record: dict, core_id: int) -> None:
    if (
        record.get("core_id") != core_id
        or record.get("core_graph6") != CORE[core_id][0]
        or record.get("original_members") != CORE[core_id][1]
        or record.get("schema") != SCHEMA
    ):
        raise ValueError("Incorrect source identity in saved core record")
    if record.get("status") == "TIMEOUT":
        if record.get("positive_certificates") or record.get("pared_levels"):
            raise ValueError("Timed-out record must not claim positive proofs")
        return
    if record.get("status") != "COMPLETED":
        raise ValueError("Invalid worker status")
    pared = pared_iterates(core_id)
    raw = raw_iterates(CORE[core_id][0])
    discovered = []
    for mode, graphs, key in (
        ("raw", raw, "raw_levels"), ("pared", pared, "pared_levels")
    ):
        rows = record.get(key)
        if not isinstance(rows, list) or len(rows) != MAX_LEVEL + 1:
            raise ValueError("Missing saved iterate records")
        for level, (graph, row) in enumerate(zip(graphs, rows)):
            if (row.get("level"), row.get("order"), row.get("edges")) != (
                level, len(graph), graph.number_of_edges()
            ):
                raise ValueError("Saved iterate graph metrics differ")
            expected = special_result(graph)
            if row["special"] != expected:
                raise ValueError("Special-octahedron witness or exhaustive absence differs")
            if expected["status"] == "FOUND":
                discovered.append({"level": level, "mode": mode,
                                   "rule": "special_octahedron",
                                   "dimension": expected["dimension"]})
            if mode == "pared":
                b1, _, _ = core9_structure_worker.betti1_mod2(graph)
                diameter = nx.diameter(graph)
                if (
                    row.get("b1_mod2") != b1
                    or row.get("diameter") != diameter
                    or row.get("cover_search") != (
                        "SKIPPED_H1_ZERO" if b1 == 0 else "NOT_RUN_IN_THIS_STAGE"
                    )
                    or row.get("direct_radius3_coaffination") != (
                        "IMPOSSIBLE_DIAMETER_LT3" if diameter < 3 else "NOT_RUN"
                    )
                    or [r.get("family") for r in row.get("targeted", [])] != list(FAMILIES)
                ):
                    raise ValueError("Saved topology, coaffination or search scope differs")
                for hit in row["targeted"]:
                    replay_target(graph, hit)
                    if hit["status"] == "FOUND":
                        discovered.append({
                            "level": level, "mode": mode,
                            "rule": "targeted_retraction", "family": hit["family"],
                            "target_kind": hit["target_kind"],
                        })
    if record["positive_certificates"] != (
        sorted(discovered, key=lambda x:(x["level"], x["mode"], x["rule"]))
    ):
        raise ValueError("Saved positive claims disagree with replayed witnesses")


def manifest() -> dict:
    check_sources()
    paths = [
        Path(__file__), PIN,
        ROOT / "scripts/bootstrap_core9_three_target_v1.sh",
        ROOT / "scripts/core9_structure_worker.py",
        ROOT / "scripts/special_octahedron_class_lift_v1.py",
        ROOT / "reports/order10_core_index_v1/manifest.json",
    ] + [SOURCE / f"{core_id:08d}.json" for core_id in CORE]
    return {
        "schema": SCHEMA, "stage": "order10_core9_three_target_v1",
        "core_ids": list(CORE),
        "represented_originals": sum(x[1] for x in CORE.values()),
        "upstream_pin": PIN.read_text().strip(),
        "max_level": MAX_LEVEL, "pared_clique_bound": CLIQUE_BOUND,
        "target_families": list(FAMILIES), "target_limits": TARGET_LIMITS,
        "per_core_timeout_seconds": WORKER_SECONDS, "memory_mib": MEMORY_MIB,
        "source_sha256": {
            str(path.relative_to(ROOT)): sha(path) for path in paths
        },
        "scope": "exploratory; positive proof replay only; no historical verdict modifications",
    }


def atomic_json(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(row, indent=2, sort_keys=True) + "\n"
    temp = path.with_name(path.name + ".partial")
    try:
        temp.write_text(payload, encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def limit_worker() -> None:
    memory = MEMORY_MIB * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory, memory))


def run(destination: Path) -> None:
    meta = manifest()
    destination.mkdir(parents=True, exist_ok=True)
    header = destination / "manifest.json"
    if header.exists():
        if json.loads(header.read_text()) != meta:
            raise ValueError("Refusing to reuse a stage with different provenance")
    else:
        if any(destination.iterdir()):
            raise ValueError("Stage directory exists without a matching manifest")
        atomic_json(header, meta)
    for core_id in CORE:
        path = destination / "records" / f"{core_id:08d}.json"
        if path.exists():
            validate_record(json.loads(path.read_text()), core_id)
            print(f"Verified existing core {core_id}", flush=True)
            continue
        with tempfile.TemporaryDirectory(prefix="core9-three-worker-") as tmp:
            result = Path(tmp) / "result.json"
            args = [sys.executable, str(Path(__file__)),
                    "worker", "--core-id", str(core_id), "--output", str(result)]
            try:
                child = subprocess.run(
                    args, timeout=WORKER_SECONDS, preexec_fn=limit_worker,
                    capture_output=True, text=True,
                )
            except subprocess.TimeoutExpired:
                atomic_json(path, {
                    "schema": SCHEMA, "core_id": core_id,
                    "core_graph6": CORE[core_id][0],
                    "original_members": CORE[core_id][1],
                    "status": "TIMEOUT",
                    "limit_seconds": WORKER_SECONDS,
                })
                print(f"Core {core_id}: TIMEOUT; no mathematical negative claim", flush=True)
                continue
            if child.returncode:
                raise RuntimeError(f"Worker {core_id} failed:\n{child.stderr[-4000:]}")
            row = json.loads(result.read_text())
            validate_record(row, core_id)
            atomic_json(path, row)
            print(f"Core {core_id}: {len(row['positive_certificates'])} certificates", flush=True)
    verify(destination)


def verify(destination: Path) -> None:
    meta = manifest()
    path = destination / "manifest.json"
    if json.loads(path.read_text()) != meta:
        raise ValueError("Saved stage manifest differs from fresh source/code provenance")
    record_dir = destination / "records"
    expected = {f"{i:08d}.json" for i in CORE}
    if not record_dir.is_dir() or {p.name for p in record_dir.iterdir()} != expected:
        raise ValueError("The three-core stage is missing records or contains extras")
    for core_id in CORE:
        row = json.loads((record_dir / f"{core_id:08d}.json").read_text())
        validate_record(row, core_id)
    print("Verified three-core targeted stage and all available positive witnesses")


def report(destination: Path) -> None:
    verify(destination)
    for core_id in CORE:
        record = json.loads(
            (destination / "records" / f"{core_id:08d}.json").read_text()
        )
        if record["status"] == "TIMEOUT":
            print(f"{core_id}: TIMEOUT; no divergence/convergence inference")
            continue
        positives = record["positive_certificates"]
        counts = {}
        for row in record["pared_levels"]:
            counts[row["level"]] = {
                result["family"]: result["status"] for result in row["targeted"]
            }
        print(json.dumps({
            "core_id": core_id, "members": CORE[core_id][1],
            "positives": positives, "targeted": counts,
            "raw_specials": [r["special"]["status"] for r in record["raw_levels"]],
            "pared_specials": [r["special"]["status"] for r in record["pared_levels"]],
        }, sort_keys=True))
    print("A completed bounded search without a positive certificate remains inconclusive.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "worker", "run", "verify", "report"))
    parser.add_argument("--core-id", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.action == "worker":
        if args.core_id not in CORE or args.output is None:
            parser.error("worker requires an allowed --core-id and --output file")
        atomic_json(args.output, probe(args.core_id))
        return
    if args.action == "plan":
        print(json.dumps(manifest(), sort_keys=True, indent=2))
        return
    target = OUTPUT if args.output is None else args.output
    if args.action == "run":
        run(target)
    elif args.action == "verify":
        verify(target)
    else:
        report(target)


if __name__ == "__main__":
    main()
