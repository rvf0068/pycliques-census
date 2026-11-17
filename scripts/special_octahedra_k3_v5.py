"""V5: fast, independently replayable special-octahedron sweep through pared K³.

This is a separate frozen stage: unlike v4 it NEVER computes homology,
searches general retractions, or infers convergence from a negative.
It imports only COMPLETED, independently verified v3 exact-graph6 records,
reuses their recorded pared G, K(G), K²(G), and constructs only the missing
pared K³(G) using the same clique bound. Each positive special octahedron
certifies a retraction to O_d and hence K-divergence; the converse is false.

Computations are independently verifiable and are unique per exact graph6.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

import networkx as nx

import targeted_retractions_v2 as v2
import targeted_retractions_v3 as v3
from pycliques.cliques import clique_graph
from pycliques.dominated import completely_pared_graph
from pycliques.retractions import (
    SpecialOctahedronWitness,
    find_special_octahedron_witness,
    verify_special_octahedron_witness,
)

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(__file__).resolve()
PIN = ROOT / "config/pycliques_commit_special_k3_v5.txt"
STAGE = ROOT / "runs/order10/special-octahedra-k3-v5"
SCHEMA = 5
CLIQUE_BOUND = v2.MAX_CLIQUE_BOUND
MAX_LEVEL = 3
TIMEOUT_SECONDS = 120
MEMORY_MIB = v2.MEMORY_MIB
ALGORITHM = "exact-graph6-verified-v3-special-only-k3-v1"
PHASES = ("CHECK_LEVEL0", "CHECK_LEVEL1", "CHECK_LEVEL2", "CONSTRUCT_K3",
          "CHECK_LEVEL3", "COMPLETED")


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def groups() -> list[dict]:
    return v3.source_groups()


def manifest() -> dict:
    pin = PIN.read_text(encoding="utf-8").strip()
    if pin != v3.PIN.read_text(encoding="utf-8").strip():
        raise ValueError("V5 requires the same exact monorepo pin as frozen v3")
    return {
        "schema": SCHEMA, "algorithm": ALGORITHM,
        "source_sha256": digest(v3.SOURCE.read_bytes()),
        "code_sha256": digest(SCRIPT.read_bytes()),
        "v3_code_sha256": digest(v3.SCRIPT.read_bytes()),
        "v2_code_sha256": digest(v2.SCRIPT.read_bytes()),
        "dependency_pin": pin,
        "clique_bound": CLIQUE_BOUND,
        "max_level": MAX_LEVEL,
        "timeout_seconds": TIMEOUT_SECONDS, "memory_mib": MEMORY_MIB,
        "worker": "special_octahedron_only; no Betti or general retraction",
        "priority": "unclassified_first_stable_source_order",
    }


def require_stage() -> Path:
    current = manifest()
    path = STAGE / "manifest.json"
    if path.exists():
        if read(path) != current:
            raise ValueError("Frozen v5 manifest or sources have changed")
    else:
        if STAGE.exists() and any(STAGE.iterdir()):
            raise ValueError("V5 outputs exist without a frozen manifest")
        v2.atomic(path, current)
    return STAGE


def path_for(encoded: str, kind: str) -> Path:
    return STAGE / kind / (digest(encoded.encode("ascii")) + ".json")


def verify_import(encoded: str) -> dict:
    receipt = read(path_for(encoded, "imports"))
    original = v3.record_path(encoded)
    if (
        receipt.get("schema") != SCHEMA
        or receipt.get("graph6") != encoded
        or type(receipt.get("index")) is not int
        or v3.index_to_graph6().get(receipt["index"]) != encoded
        or not original.exists()
        or receipt.get("source_sha256") != digest(original.read_bytes())
    ):
        raise ValueError("V5 import identity or v3 source fingerprint mismatch")
    v3.require_stage()
    if (
        receipt.get("source_manifest_sha256") !=
        digest((v3.STAGE / "manifest.json").read_bytes())
    ):
        raise ValueError("V5 imported v3 manifest fingerprint mismatch")
    capsule = read(original)
    if capsule.get("status") != "COMPLETED":
        raise ValueError("V5 accepts only completed v3 source calculations")
    v3.verify_capsule(capsule, encoded)
    if receipt["index"] != capsule["record"]["index"]:
        raise ValueError("V5 import original-index mismatch")
    return capsule["record"]


def import_v3() -> dict:
    require_stage()
    v3.require_stage()
    count = 0
    represented = 0
    manifest_sha = digest((v3.STAGE / "manifest.json").read_bytes())
    for group in groups():
        encoded = group["graph6"]
        source = v3.record_path(encoded)
        if not source.exists():
            continue
        capsule = read(source)
        if capsule.get("status") != "COMPLETED":
            continue
        v3.verify_capsule(capsule, encoded)
        receipt = {
            "schema": SCHEMA, "graph6": encoded,
            "index": capsule["record"]["index"],
            "source_sha256": digest(source.read_bytes()),
            "source_manifest_sha256": manifest_sha,
        }
        target = path_for(encoded, "imports")
        if target.exists():
            if read(target) != receipt:
                raise ValueError("Previously imported v3 result has changed")
        else:
            v2.atomic(target, receipt)
        count += 1
        represented += len(group["indices"])
    return {"imported_unique": count, "original_indices_represented": represented}


def imported_groups() -> list[dict]:
    return [g for g in groups() if path_for(g["graph6"], "imports").exists()]


def serialize_special(graph: nx.Graph, witness: SpecialOctahedronWitness) -> dict:
    if not verify_special_octahedron_witness(graph, witness):
        raise ValueError("Invalid positive special-octahedron witness")
    lookup = {vertex: i for i, vertex in enumerate(graph)}
    return {
        "status": "FOUND", "dimension": witness.dimension,
        "clique_indices": [lookup[v] for v in witness.clique],
        "antipode_indices": [lookup[v] for v in witness.antipodes],
    }


def verify_special(graph: nx.Graph, data: dict) -> bool:
    if not isinstance(data, dict) or data.get("status") != "FOUND":
        return False
    clique = data.get("clique_indices")
    antipodes = data.get("antipode_indices")
    if not isinstance(clique, list) or not isinstance(antipodes, list):
        return False
    vertices = tuple(graph)
    if any(
        type(i) is not int or i < 0 or i >= len(vertices)
        for i in clique + antipodes
    ):
        return False
    return (
        data.get("dimension") == len(clique)
        and verify_special_octahedron_witness(
            graph,
            SpecialOctahedronWitness(
                tuple(vertices[i] for i in clique),
                tuple(vertices[i] for i in antipodes),
            ),
        )
    )


def reconstruct_k3(level_two: dict) -> nx.Graph | None:
    graph = nx.from_graph6_bytes(level_two["graph6"].encode("ascii"))
    result = clique_graph(graph, CLIQUE_BOUND)
    return None if result is None else completely_pared_graph(result)


def phase(index: int, encoded: str, value: str) -> None:
    if (
        type(index) is not int
        or v3.index_to_graph6().get(index) != encoded
        or value not in PHASES
    ):
        raise ValueError("Invalid V5 worker progress provenance")
    v2.atomic(path_for(encoded, "progress"), {
        "schema": SCHEMA, "index": index,
        "graph6": encoded, "phase": value,
    })


def read_phase(encoded: str, index: int) -> str | None:
    path = path_for(encoded, "progress")
    if not path.exists():
        return None
    data = read(path)
    if (
        data.get("schema") != SCHEMA
        or data.get("graph6") != encoded
        or type(data.get("index")) is not int or data["index"] != index
        or data.get("phase") not in PHASES
    ):
        raise ValueError("Malformed V5 worker progress record")
    return data["phase"]


def analyze(index: int, encoded: str, source: dict, *, journal: bool = False) -> dict:
    levels = []
    certificate = None
    originals = source.get("levels")
    if not isinstance(originals, list) or len(originals) != 3:
        raise ValueError("V5 requires all three completed v3 pared levels")
    for i in range(MAX_LEVEL + 1):
        if journal:
            phase(index, encoded, PHASES[i] if i < 3 else "CONSTRUCT_K3")
        if i < 3:
            level = originals[i]
            if level.get("status") != "COMPLETED" or level.get("level") != i:
                raise ValueError("V5 source level was not completed in v3")
            graph = nx.from_graph6_bytes(level["graph6"].encode("ascii"))
        else:
            graph = reconstruct_k3(originals[2])
            if graph is None:
                levels.append({"level": 3, "status": "CLIQUE_BOUND_EXCEEDED"})
                break
            if journal:
                phase(index, encoded, "CHECK_LEVEL3")
        result = find_special_octahedron_witness(graph)
        row = {
            "level": i, "status": "COMPLETED", "graph6": v2.graph6(graph),
            "order": len(graph), "edges": graph.number_of_edges(),
            "special": (
                {"status": "EXHAUSTED"} if result is None
                else serialize_special(graph, result)
            ),
        }
        levels.append(row)
        if result is not None:
            certificate = {
                "rule": "special_octahedron",
                "iterate_index": i,
                "dimension": result.dimension,
                "target_kind": f"octahedra:{result.dimension}",
                "conclusion": "proven_divergent",
            }
            break
    if journal:
        phase(index, encoded, "COMPLETED")
    return {
        "schema": SCHEMA, "status": "COMPLETED",
        "index": index, "graph6": encoded,
        "scope": "special_octahedron_only_pared_levels_0_to_3",
        "no_convergence_inference": True,
        "levels": levels, "divergence_certificate": certificate,
    }


def verify_record(data: dict, encoded: str, source: dict) -> None:
    if (
        not isinstance(data, dict) or data.get("schema") != SCHEMA
        or data.get("status") != "COMPLETED"
        or data.get("graph6") != encoded
        or type(data.get("index")) is not int
        or v3.index_to_graph6().get(data["index"]) != encoded
        or data.get("scope") != "special_octahedron_only_pared_levels_0_to_3"
        or data.get("no_convergence_inference") is not True
    ):
        raise ValueError("Malformed V5 computation provenance")
    levels = data.get("levels")
    if not isinstance(levels, list) or not 1 <= len(levels) <= 4:
        raise ValueError("Malformed V5 level count")
    expected = source.get("levels")
    if not isinstance(expected, list) or len(expected) != 3:
        raise ValueError("Missing three independently verified v3 levels")
    positive = None
    for i, row in enumerate(levels):
        if not isinstance(row, dict) or row.get("level") != i:
            raise ValueError("V5 level indices are not contiguous")
        if i < 3:
            saved = expected[i]
            if saved.get("level") != i or saved.get("status") != "COMPLETED":
                raise ValueError("V3 level was not completed")
            graph = nx.from_graph6_bytes(saved["graph6"].encode("ascii"))
        else:
            graph = reconstruct_k3(expected[2])
        if graph is None:
            if i != 3 or row != {"level": 3, "status": "CLIQUE_BOUND_EXCEEDED"}:
                raise ValueError("False or malformed K3 clique bound")
            if i != len(levels) - 1:
                raise ValueError("Bounded K3 must terminate level sequence")
            break
        if (
            row.get("status") != "COMPLETED"
            or row.get("graph6") != v2.graph6(graph)
            or row.get("order") != len(graph)
            or row.get("edges") != graph.number_of_edges()
        ):
            raise ValueError("V5 graph is not the actual pared iterate")
        item = row.get("special")
        if item == {"status": "EXHAUSTED"}:
            continue
        if not verify_special(graph, item):
            raise ValueError("Invalid special octahedron positive witness")
        if i != len(levels) - 1:
            raise ValueError("Positive special certificate must stop the search")
        positive = {
            "rule": "special_octahedron", "iterate_index": i,
            "dimension": item["dimension"],
            "target_kind": f"octahedra:{item['dimension']}",
            "conclusion": "proven_divergent",
        }
        break
    if (
        levels[-1]["status"] == "COMPLETED"
        and positive is None and len(levels) != 4
    ):
        raise ValueError("Negative V5 result did not reach K3")
    if data.get("divergence_certificate") != positive:
        raise ValueError("V5 claimed divergence certificate not replayed")


def verify_terminal(data: dict, encoded: str) -> None:
    if (
        not isinstance(data, dict) or data.get("schema") != SCHEMA
        or data.get("status") not in ("ERROR", "TIMEOUT")
        or data.get("graph6") != encoded
        or type(data.get("index")) is not int
        or v3.index_to_graph6().get(data["index"]) != encoded
        or data.get("last_phase") not in PHASES + (None,)
    ):
        raise ValueError("Malformed V5 terminal worker result")


def worker(index: int) -> None:
    require_stage()
    encoded = v3.index_to_graph6().get(index)
    if encoded is None:
        raise ValueError("Unknown V5 original index")
    if path_for(encoded, "records").exists():
        raise ValueError("Refusing to overwrite a v5 result")
    source = verify_import(encoded)
    result = analyze(index, encoded, source, journal=True)
    verify_record(result, encoded, source)
    v2.atomic(path_for(encoded, "records"), result)


def run_one(group: dict) -> None:
    encoded = group["graph6"]
    path = path_for(encoded, "records")
    if path.exists():
        record = read(path)
        if record.get("graph6") != encoded or record.get("schema") != SCHEMA:
            raise ValueError("V5 result collides with a different graph6")
        return
    index = group["indices"][0]
    command = [sys.executable, str(SCRIPT), "worker", "--index", str(index)]
    try:
        run = subprocess.run(
            command, timeout=TIMEOUT_SECONDS, capture_output=True,
            text=True, check=False, preexec_fn=v2.resource_limit,
        )
        if run.returncode:
            v2.atomic(path, {
                "schema": SCHEMA, "graph6": encoded, "index": index,
                "status": "ERROR", "last_phase": read_phase(encoded, index),
                "error": run.stderr[-2000:],
            })
    except subprocess.TimeoutExpired:
        v2.atomic(path, {
            "schema": SCHEMA, "graph6": encoded, "index": index,
            "status": "TIMEOUT", "last_phase": read_phase(encoded, index),
        })


def summary(*, strict: bool = False) -> dict:
    items = imported_groups()
    counts = {
        "imported_unique": len(items),
        "original_indices_represented": sum(len(g["indices"]) for g in items),
        "completed_unique": 0, "covered_input_indices": 0,
        "pending_unique": 0, "timeouts": 0, "errors": 0,
        "certified_divergent_unique": 0, "certified_divergent_indices": 0,
        "certified_by_level": {}, "negative_through_k3": 0,
        "clique_bound_exceeded": 0, "timeout_phases": {},
    }
    by_level, phases = Counter(), Counter()
    for group in items:
        encoded = group["graph6"]
        path = path_for(encoded, "records")
        if not path.exists():
            counts["pending_unique"] += 1
            continue
        data = read(path)
        if data.get("graph6") != encoded or data.get("schema") != SCHEMA:
            raise ValueError("Invalid V5 record identity")
        if data.get("status") in ("TIMEOUT", "ERROR"):
            verify_terminal(data, encoded)
            counts["timeouts" if data["status"] == "TIMEOUT" else "errors"] += 1
            if data["status"] == "TIMEOUT":
                phases[data.get("last_phase") or "unknown"] += 1
            continue
        if data.get("status") != "COMPLETED":
            raise ValueError("Unknown V5 record status")
        if strict:
            source = verify_import(encoded)
            verify_record(data, encoded, source)
        counts["completed_unique"] += 1
        counts["covered_input_indices"] += len(group["indices"])
        certificate = data["divergence_certificate"]
        if certificate is not None:
            counts["certified_divergent_unique"] += 1
            counts["certified_divergent_indices"] += len(group["indices"])
            by_level[str(certificate["iterate_index"])] += 1
        elif data["levels"][-1]["status"] == "CLIQUE_BOUND_EXCEEDED":
            counts["clique_bound_exceeded"] += 1
        else:
            counts["negative_through_k3"] += 1
    counts["certified_by_level"] = dict(sorted(by_level.items()))
    counts["timeout_phases"] = dict(sorted(phases.items()))
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("import-v3", "plan", "next",
                                           "verify", "report", "worker"))
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--index", type=int)
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    if args.action == "worker":
        if args.index is None:
            parser.error("worker requires --index")
        worker(args.index)
        return
    if args.index is not None and args.action != "next":
        parser.error("--index is only supported by next")
    require_stage()
    if args.action == "import-v3":
        print(json.dumps(import_v3(), sort_keys=True))
        return
    if args.action == "plan":
        print(json.dumps(summary(), sort_keys=True))
        return
    if args.action in ("verify", "report"):
        print(json.dumps(summary(strict=True), sort_keys=True,
                         indent=2 if args.action == "report" else None))
        return
    if not imported_groups():
        parser.error("Import verified completed v3 computations first")
    if args.index is None:
        pending = [g for g in imported_groups()
                   if not path_for(g["graph6"], "records").exists()]
        todo = pending[:args.batch_size]
    else:
        matched = [g for g in imported_groups() if args.index in g["indices"]]
        if not matched:
            parser.error("Requested --index has no imported v3 result")
        todo = matched
    for group in todo:
        run_one(group)
    print(json.dumps(summary(strict=True), sort_keys=True))


if __name__ == "__main__":
    main()
