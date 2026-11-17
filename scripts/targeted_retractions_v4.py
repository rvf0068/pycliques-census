"""V4: special-octahedron-first postpass through the third clique iterate.

The frozen v3 stage has already searched three divergent-target families on
the pared input and its first two pared clique iterates. V4 reuses those
independently verified exact-graph6 results and additionally searches for
special octahedra at levels 0, 1, 2, 3. At level 3, a negative special
search is followed by the existing bounded target retraction families.
Every positive special octahedron is a certified retraction onto O_d, d>=3,
and hence a divergence certificate. The converse is not assumed.

V4 does not change any earlier stage, and does not infer convergence from
a bounded negative search. Imported v3 records remain checked by v3's
existing iterate, homology and retraction-witness verifier.
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
from pycliques import (
    TargetRetractionResult,
    TargetSearchStatus,
    search_targeted_retractions,
    verify_targeted_retraction,
)
from pycliques.retractions import (
    SpecialOctahedronWitness,
    find_special_octahedron_witness,
    verify_special_octahedron_witness,
)
from pycliques.small import CliqueSequence

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(__file__).resolve()
PIN = ROOT / "config/pycliques_commit_targeted_v4.txt"
STAGE = ROOT / "runs/order10/targeted-retractions-v4"
SCHEMA = 4
MAX_LEVEL = 3
MAX_CLIQUE_BOUND = v2.MAX_CLIQUE_BOUND
MAX_TARGET_HOST_VERTICES = v2.MAX_HOST_VERTICES
MAX_SPECIAL_HOST_VERTICES = MAX_CLIQUE_BOUND
TIMEOUT_SECONDS = 180
MEMORY_MIB = v2.MEMORY_MIB
FAMILIES = frozenset(("octahedra", "suspensions", "cycle_complements"))
ALGORITHM = "special-first-k3-verified-v3-exact-graph6"


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def source_groups() -> list[dict]:
    """The frozen full census and deterministic unclassified-first ordering."""
    return v3.source_groups()


def manifest() -> dict:
    pin = PIN.read_text(encoding="utf-8").strip()
    if pin != v3.PIN.read_text(encoding="utf-8").strip():
        raise ValueError("V4 and V3 must use the identical pinned library revision")
    if pin != v2.PIN_FILE.read_text(encoding="utf-8").strip():
        raise ValueError("V4 library pin differs from the verified v2 library")
    return {
        "schema": SCHEMA,
        "algorithm": ALGORITHM,
        "source_sha256": digest(v3.SOURCE.read_bytes()),
        "code_sha256": digest(SCRIPT.read_bytes()),
        "v3_code_sha256": digest(v3.SCRIPT.read_bytes()),
        "v2_code_sha256": digest(v2.SCRIPT.read_bytes()),
        "dependency_pin": pin,
        "v3_dependency_schema": v3.SCHEMA,
        "v2_search_settings": v2.manifest(10)["settings"],
        "max_level": MAX_LEVEL,
        "clique_bound": MAX_CLIQUE_BOUND,
        "target_host_order_limit": MAX_TARGET_HOST_VERTICES,
        "special_host_order_limit": MAX_SPECIAL_HOST_VERTICES,
        "timeout_seconds": TIMEOUT_SECONDS,
        "memory_mib": MEMORY_MIB,
        "scope": "pared_G_and_pared_K_G_through_pared_K_cubed_G",
        "reuse": "complete_v3_graph6_results_only",
    }


def require_stage() -> Path:
    frozen = STAGE / "manifest.json"
    expected = manifest()
    if frozen.exists():
        if read(frozen) != expected:
            raise ValueError("Frozen v4 manifest/source/parameters mismatch")
    else:
        if STAGE.exists() and any(STAGE.iterdir()):
            raise ValueError("Refusing to adopt v4 outputs without their manifest")
        v2.atomic(frozen, expected)
    return STAGE


def key_path(encoded: str, folder: str) -> Path:
    return STAGE / folder / (digest(encoded.encode("ascii")) + ".json")


def imported_capsule(encoded: str) -> tuple[dict, dict]:
    """Reload v3 provenance and independently verify its complete record."""
    receipt = read(key_path(encoded, "imports"))
    if (
        receipt.get("schema") != SCHEMA
        or receipt.get("graph6") != encoded
    ):
        raise ValueError("Malformed v4 import identity")
    original_path = v3.record_path(encoded)
    if not original_path.exists():
        raise ValueError("Required v3 source result is missing")
    if digest(original_path.read_bytes()) != receipt.get("source_sha256"):
        raise ValueError("Imported v3 source result has changed")
    capsule = read(original_path)
    if capsule.get("status") != "COMPLETED":
        raise ValueError("V4 can reuse only completed v3 source results")
    v3.require_stage()
    if digest((v3.STAGE / "manifest.json").read_bytes()) != receipt.get(
        "v3_manifest_sha256"
    ):
        raise ValueError("Imported v3 manifest fingerprint has changed")
    v3.verify_capsule(capsule, encoded)
    if (
        type(receipt.get("source_index")) is not int
        or capsule["record"].get("index") != receipt["source_index"]
    ):
        raise ValueError("Imported v3 source index has changed")
    return receipt, capsule


def import_v3() -> dict:
    """Revalidate completed source records and register immutable fingerprints."""
    require_stage()
    v3.require_stage()
    groups = source_groups()
    imported = 0
    imported_indices = 0
    for group in groups:
        encoded = group["graph6"]
        original = v3.record_path(encoded)
        if not original.exists():
            continue
        capsule = read(original)
        if capsule.get("status") != "COMPLETED":
            continue
        v3.verify_capsule(capsule, encoded)
        receipt = {
            "schema": SCHEMA,
            "graph6": encoded,
            "source_index": capsule["record"]["index"],
            "source_sha256": digest(original.read_bytes()),
            "v3_manifest_sha256": digest((v3.STAGE / "manifest.json").read_bytes()),
        }
        target = key_path(encoded, "imports")
        if target.exists():
            if read(target) != receipt:
                raise ValueError("Previously imported v3 source was altered")
        else:
            v2.atomic(target, receipt)
        imported += 1
        imported_indices += len(group["indices"])
    return {
        "imported_unique_graph6": imported,
        "original_indices_covered_by_imports": imported_indices,
    }


def source_levels(record: dict) -> dict[int, dict]:
    """The already verified inner v3 computation record, not its capsule."""
    return {x["level"]: x for x in record["levels"]}


PROGRESS_PHASES = frozenset((
    "CONSTRUCT_CLIQUE_ITERATE",
    "SPECIAL_OCTAHEDRON_SEARCH",
    "K3_BETTI_AND_RETRACTIONS",
    "LEVEL_COMPLETED",
    "CERTIFIED_SPECIAL",
))


def progress_path(encoded: str) -> Path:
    return key_path(encoded, "progress")


def write_progress(index: int, encoded: str, level: int, phase: str) -> None:
    """Atomic worker diagnostics, not a mathematical or negative certificate."""
    if (
        type(index) is not int or v3.index_to_graph6().get(index) != encoded
        or type(level) is not int or not 0 <= level <= MAX_LEVEL
        or phase not in PROGRESS_PHASES
    ):
        raise ValueError("Invalid progress phase/index for v4 worker")
    v2.atomic(progress_path(encoded), {
        "schema": SCHEMA, "index": index, "graph6": encoded,
        "level": level, "phase": phase,
    })


def read_progress(index: int, encoded: str) -> dict | None:
    path = progress_path(encoded)
    if not path.exists():
        return None
    row = read(path)
    if (
        row.get("schema") != SCHEMA
        or row.get("graph6") != encoded
        or type(row.get("index")) is not int
        or row["index"] != index
        or v3.index_to_graph6().get(index) != encoded
        or type(row.get("level")) is not int
        or not 0 <= row["level"] <= MAX_LEVEL
        or row.get("phase") not in PROGRESS_PHASES
    ):
        raise ValueError("Corrupted v4 worker progress diagnostic")
    return row


def serialize_special(graph: nx.Graph, witness: SpecialOctahedronWitness) -> dict:
    if not verify_special_octahedron_witness(graph, witness):
        raise ValueError("Invalid special octahedron from upstream finder")
    labels = {vertex: i for i, vertex in enumerate(graph)}
    return {
        "status": "FOUND",
        "dimension": witness.dimension,
        "clique_indices": [labels[v] for v in witness.clique],
        "antipode_indices": [labels[v] for v in witness.antipodes],
    }


def verify_special(graph: nx.Graph, data: dict) -> bool:
    if (
        not isinstance(data, dict)
        or data.get("status") != "FOUND"
        or type(data.get("dimension")) is not int
    ):
        return False
    clique, antipodes = data.get("clique_indices"), data.get("antipode_indices")
    if not isinstance(clique, list) or not isinstance(antipodes, list):
        return False
    vertices = list(graph)
    if any(type(i) is not int or i < 0 or i >= len(vertices)
           for i in clique + antipodes):
        return False
    if data["dimension"] != len(clique):
        return False
    witness = SpecialOctahedronWitness(
        tuple(vertices[i] for i in clique),
        tuple(vertices[i] for i in antipodes),
    )
    return verify_special_octahedron_witness(graph, witness)


def serialize_level(
    index: int, graph: nx.Graph, level: int, inherited: dict[int, dict],
    *, diagnostic: bool = False,
) -> dict:
    encoded = v2.graph6(graph)
    row = {
        "level": level, "graph6": encoded,
        "order": len(graph), "edges": graph.number_of_edges(),
        "status": "COMPLETED",
    }

    # A special O_d is a sufficient divergence/retraction certificate.
    # Search it before starting ANY expensive retraction check at this level.
    if diagnostic:
        write_progress(index, v3.index_to_graph6()[index], level,
                       "SPECIAL_OCTAHEDRON_SEARCH")
    witness = find_special_octahedron_witness(graph)
    if witness is not None:
        row["special"] = serialize_special(graph, witness)
        row["retractions"] = {"mode": "SKIPPED_SPECIAL_CERTIFICATE"}
        return row
    row["special"] = {"status": "EXHAUSTED"}

    # Reuse full, already verified v3 searches on levels G, K(G), K^2(G).
    if level < MAX_LEVEL:
        saved = inherited.get(level)
        if saved is not None and saved.get("status") == "COMPLETED":
            if saved.get("graph6") != encoded:
                raise ValueError("V3 level mismatch before reusing search results")
            row["retractions"] = {
                "mode": "REUSED_VERIFIED_V3",
                "families": saved["families"],
            }
        else:
            row["retractions"] = {
                "mode": "NOT_AVAILABLE_FROM_V3",
                "reason": None if saved is None else saved.get("status"),
            }
        return row

    # Only K^3(G) needs a NEW bounded retraction search.
    if len(graph) > MAX_TARGET_HOST_VERTICES:
        row["retractions"] = {
            "mode": "SKIPPED_HOST_ORDER_LIMIT",
            "limit": MAX_TARGET_HOST_VERTICES,
        }
        return row

    if diagnostic:
        write_progress(index, v3.index_to_graph6()[index], level,
                       "K3_BETTI_AND_RETRACTIONS")
    known, cache_key = v2.cache_homology(graph, STAGE)
    candidates = search_targeted_retractions(
        graph, betti_numbers=known,
        max_target_order=v2.MAX_TARGET_ORDER,
        max_patterns=v2.MAX_PATTERNS,
        max_states=v2.MAX_STATES,
        max_assignments=v2.MAX_ASSIGNMENTS,
    )
    row["retractions"] = {
        "mode": "NEW_V4",
        "homology_cache_key": cache_key,
        "betti_known": (
            None if known is None else {str(d): rank for d, rank in known.items()}
        ),
        "families": {
            family: v2.serialize_family(graph, result)
            for family, result in candidates.items()
        },
    }
    return row


def analyze(
    index: int, encoded: str, source: dict, *, diagnostic: bool = False
) -> dict:
    graph = nx.from_graph6_bytes(encoded.encode("ascii"))
    seq = CliqueSequence(graph, bound=MAX_CLIQUE_BOUND)
    old_levels = source_levels(source)
    levels: list[dict] = []
    certificate: dict | None = None
    for i in range(MAX_LEVEL + 1):
        if diagnostic:
            write_progress(index, encoded, i, "CONSTRUCT_CLIQUE_ITERATE")
        current = seq[i]
        if current is None:
            levels.append({"level": i, "status": "CLIQUE_BOUND_EXCEEDED"})
            break
        if len(current) > MAX_SPECIAL_HOST_VERTICES:
            levels.append({
                "level": i, "status": "SPECIAL_HOST_ORDER_LIMIT",
                "order": len(current), "graph6": v2.graph6(current),
            })
            break
        row = serialize_level(index, current, i, old_levels,
                              diagnostic=diagnostic)
        levels.append(row)
        if diagnostic:
            write_progress(index, encoded, i, "LEVEL_COMPLETED")
        if row["special"]["status"] == "FOUND":
            if diagnostic:
                write_progress(index, encoded, i, "CERTIFIED_SPECIAL")
            certificate = {
                "rule": "special_octahedron",
                "iterate_index": i,
                "dimension": row["special"]["dimension"],
                "conclusion": "proven_divergent",
            }
            break
    return {
        "schema": SCHEMA,
        "status": "COMPLETED",
        "index": index,
        "graph6": encoded,
        "scope": "pared_iterates_0_through_3",
        "no_convergence_inference": True,
        "levels": levels,
        "divergence_certificate": certificate,
    }


def verify_families(graph: nx.Graph, families: dict) -> None:
    if not isinstance(families, dict) or set(families) != FAMILIES:
        raise ValueError("V4 target-family results are incomplete")
    for family, item in families.items():
        if (
            not isinstance(item, dict)
            or item.get("status") not in {
                "FOUND", "EXHAUSTED", "LIMIT_REACHED", "HOMOLOGY_EXCLUDED"
            }
            or any(
                type(item.get(key)) is not int or item[key] < 0
                for key in ("patterns", "induced_targets", "states", "assignments")
            )
        ):
            raise ValueError("Malformed v4 family result")
        if item["status"] != "FOUND":
            if any(k in item for k in ("kind", "projection_indices", "target_indices")):
                raise ValueError("Negative v4 family result carries an invalid witness")
            continue
        target = item.get("target_indices")
        projection = item.get("projection_indices")
        if (
            not isinstance(target, list)
            or not isinstance(projection, list)
            or not target
            or len(set(target)) != len(target)
            or len(projection) != len(graph)
            or any(type(i) is not int or i not in graph for i in target + projection)
        ):
            raise ValueError("Malformed v4 graph retraction witness indices")
        witness = TargetRetractionResult(
            family=family, status=TargetSearchStatus.FOUND,
            target_kind=item.get("kind"),
            target_vertices=tuple(target),
            projection={vertex: projection[vertex] for vertex in graph},
        )
        if not verify_targeted_retraction(graph, witness):
            raise ValueError("Positive v4 retraction certificate failed verification")


def verify_record(record: dict, encoded: str, source: dict) -> None:
    if (
        not isinstance(record, dict)
        or record.get("schema") != SCHEMA
        or record.get("status") != "COMPLETED"
        or record.get("graph6") != encoded
        or record.get("scope") != "pared_iterates_0_through_3"
        or record.get("no_convergence_inference") is not True
        or type(record.get("index")) is not int
        or v3.index_to_graph6().get(record["index"]) != encoded
    ):
        raise ValueError("Malformed v4 completed-record provenance")
    saved_levels = source_levels(source)
    seq = CliqueSequence(nx.from_graph6_bytes(encoded.encode("ascii")),
                         bound=MAX_CLIQUE_BOUND)
    levels = record.get("levels")
    if not isinstance(levels, list) or not levels or len(levels) > MAX_LEVEL + 1:
        raise ValueError("Malformed v4 iterate sequence")
    special_positive = None
    for i, row in enumerate(levels):
        if not isinstance(row, dict) or row.get("level") != i:
            raise ValueError("Noncontiguous v4 iterate record")
        graph = seq[i]
        if row.get("status") == "CLIQUE_BOUND_EXCEEDED":
            if graph is not None or i != len(levels) - 1:
                raise ValueError("False clique-bound limitation")
            break
        if row.get("status") == "SPECIAL_HOST_ORDER_LIMIT":
            if (
                graph is None or len(graph) <= MAX_SPECIAL_HOST_VERTICES
                or row.get("graph6") != v2.graph6(graph)
                or row.get("order") != len(graph)
                or i != len(levels) - 1
            ):
                raise ValueError("False special-host limitation")
            break
        if (
            row.get("status") != "COMPLETED"
            or graph is None
            or len(graph) > MAX_SPECIAL_HOST_VERTICES
            or row.get("graph6") != v2.graph6(graph)
            or row.get("order") != len(graph)
            or row.get("edges") != graph.number_of_edges()
        ):
            raise ValueError("Recorded v4 graph is not the correct pared iterate")
        special = row.get("special")
        retract = row.get("retractions")
        if not isinstance(special, dict) or not isinstance(retract, dict):
            raise ValueError("Missing v4 search status")
        if special.get("status") == "FOUND":
            if not verify_special(graph, special):
                raise ValueError("Special octahedron is not independently verified")
            if retract != {"mode": "SKIPPED_SPECIAL_CERTIFICATE"}:
                raise ValueError("Retraction search must follow special search")
            if i != len(levels) - 1:
                raise ValueError("Special positive must terminate v4 search")
            special_positive = {
                "rule": "special_octahedron", "iterate_index": i,
                "dimension": special["dimension"],
                "conclusion": "proven_divergent",
            }
            break
        if special != {"status": "EXHAUSTED"}:
            raise ValueError("Malformed negative special search status")
        mode = retract.get("mode")
        if i < MAX_LEVEL:
            old = saved_levels.get(i)
            if old is not None and old.get("status") == "COMPLETED":
                if (
                    mode != "REUSED_VERIFIED_V3"
                    or old.get("graph6") != v2.graph6(graph)
                    or retract.get("families") != old.get("families")
                ):
                    raise ValueError("V4 reused family results do not match verified v3")
            elif retract != {
                "mode": "NOT_AVAILABLE_FROM_V3",
                "reason": None if old is None else old.get("status"),
            }:
                raise ValueError("V4 claims unverified v3 source results")
            continue
        if len(graph) > MAX_TARGET_HOST_VERTICES:
            if retract != {
                "mode": "SKIPPED_HOST_ORDER_LIMIT",
                "limit": MAX_TARGET_HOST_VERTICES,
            }:
                raise ValueError("Missing K3 target host order limit")
            continue
        if mode != "NEW_V4" or set(retract.get("families", {})) != FAMILIES:
            raise ValueError("K3 bounded retraction search was not recorded")
        cache_key = digest(row["graph6"].encode("ascii"))
        if retract.get("homology_cache_key") != cache_key:
            raise ValueError("Invalid K3 homology key")
        cache = read(STAGE / "homology_cache" / (cache_key + ".json"))
        ranks = v2.validate_homology_cache(cache, row["graph6"])
        expected = (
            None if ranks is None else {str(d): rank for d, rank in ranks.items()}
        )
        if retract.get("betti_known") != expected:
            raise ValueError("K3 homology cache and recorded Betti ranks disagree")
        verify_families(graph, retract["families"])
    if (
        levels[-1]["status"] == "COMPLETED"
        and special_positive is None and len(levels) != MAX_LEVEL + 1
    ):
        raise ValueError("V4 record terminates before K3 without a certificate")
    if record.get("divergence_certificate") != special_positive:
        raise ValueError("Invalid v4 special-octahedron divergence certificate")


def record_path(encoded: str) -> Path:
    return key_path(encoded, "records")


def verify_terminal(data: dict, encoded: str) -> None:
    if (
        not isinstance(data, dict)
        or data.get("schema") != SCHEMA
        or data.get("status") not in {"TIMEOUT", "ERROR"}
        or data.get("graph6") != encoded
        or type(data.get("index")) is not int
        or v3.index_to_graph6().get(data["index"]) != encoded
    ):
        raise ValueError("Malformed v4 terminal worker provenance")
    progress = data.get("last_progress")
    if progress is not None and (
        not isinstance(progress, dict)
        or progress.get("schema") != SCHEMA
        or progress.get("graph6") != encoded
        or progress.get("index") != data["index"]
        or type(progress.get("level")) is not int
        or not 0 <= progress["level"] <= MAX_LEVEL
        or progress.get("phase") not in PROGRESS_PHASES
    ):
        raise ValueError("Malformed v4 terminal progress diagnostic")


def worker(index: int) -> None:
    require_stage()
    encoded = v3.index_to_graph6().get(index)
    if encoded is None:
        raise ValueError("Unknown source index")
    path = record_path(encoded)
    if path.exists():
        raise ValueError("V4 worker refuses to overwrite an existing result")
    _, source = imported_capsule(encoded)
    result = analyze(index, encoded, source["record"], diagnostic=True)
    verify_record(result, encoded, source["record"])
    v2.atomic(path, result)


def run_one(group: dict) -> None:
    encoded = group["graph6"]
    path = record_path(encoded)
    if path.exists():
        data = read(path)
        if data.get("graph6") != encoded:
            raise ValueError("Existing v4 record hash collision")
        return
    index = group["indices"][0]
    cmd = [sys.executable, str(SCRIPT), "worker", "--index", str(index)]
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, check=False,
            timeout=TIMEOUT_SECONDS, preexec_fn=v2.resource_limit,
        )
        if p.returncode:
            v2.atomic(path, {
                "schema": SCHEMA, "graph6": encoded,
                "status": "ERROR", "index": index,
                "error": p.stderr[-2000:],
                "last_progress": read_progress(index, encoded),
            })
    except subprocess.TimeoutExpired:
        v2.atomic(path, {
            "schema": SCHEMA, "graph6": encoded,
            "status": "TIMEOUT", "index": index,
            "last_progress": read_progress(index, encoded),
        })


def imported_groups() -> list[dict]:
    return [g for g in source_groups()
            if key_path(g["graph6"], "imports").exists()]


def summary(*, verify_all: bool = False) -> dict:
    groups = imported_groups()
    counts = {
        "distinct_v3_imports": len(groups),
        "input_indices_represented": sum(len(g["indices"]) for g in groups),
        "completed_unique": 0,
        "covered_input_indices": 0,
        "pending_unique": 0,
        "certified_special": 0,
        "certified_special_at_k3": 0,
        "timeouts": 0,
        "errors": 0,
        "target_family_found": 0,
        "family_statuses": {},
        "level_statuses": {},
        "terminal_phases": {},
    }
    families, levels, terminal_phases = Counter(), Counter(), Counter()
    for group in groups:
        encoded = group["graph6"]
        path = record_path(encoded)
        if not path.exists():
            counts["pending_unique"] += 1
            continue
        data = read(path)
        if data.get("schema") != SCHEMA or data.get("graph6") != encoded:
            raise ValueError("Invalid v4 result identity")
        if data["status"] in ("TIMEOUT", "ERROR"):
            verify_terminal(data, encoded)
            counts["timeouts" if data["status"] == "TIMEOUT" else "errors"] += 1
            progress = data.get("last_progress")
            key = ("unknown" if progress is None
                   else f"level{progress['level']}:{progress['phase']}")
            terminal_phases[key] += 1
            continue
        if data["status"] != "COMPLETED":
            raise ValueError("Unknown v4 result status")
        if verify_all:
            _, source = imported_capsule(encoded)
            verify_record(data, encoded, source["record"])
        counts["completed_unique"] += 1
        counts["covered_input_indices"] += len(group["indices"])
        cert = data.get("divergence_certificate")
        if cert is not None:
            counts["certified_special"] += 1
            if cert.get("iterate_index") == MAX_LEVEL:
                counts["certified_special_at_k3"] += 1
        for level in data["levels"]:
            levels[level["status"]] += 1
            if level["status"] != "COMPLETED":
                continue
            retractions = level["retractions"]
            for family, result in retractions.get("families", {}).items():
                families[family + ":" + result["status"]] += 1
                counts["target_family_found"] += result["status"] == "FOUND"
    counts["family_statuses"] = dict(sorted(families.items()))
    counts["level_statuses"] = dict(sorted(levels.items()))
    counts["terminal_phases"] = dict(sorted(terminal_phases.items()))
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=("import-v3", "plan", "next", "verify", "report", "worker")
    )
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--index", type=int)
    args = parser.parse_args()
    if args.action == "worker":
        if args.index is None:
            parser.error("worker requires --index")
        worker(args.index)
        return
    if args.index is not None:
        parser.error("--index is reserved for an isolated worker")
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    require_stage()
    if args.action == "import-v3":
        print(json.dumps(import_v3(), sort_keys=True))
    elif args.action == "next":
        pending = [
            g for g in imported_groups()
            if not record_path(g["graph6"]).exists()
        ]
        for group in pending[:args.batch_size]:
            run_one(group)
        print(json.dumps(summary(verify_all=True), sort_keys=True))
    elif args.action == "verify":
        print(json.dumps(summary(verify_all=True), sort_keys=True))
    elif args.action == "plan":
        print(json.dumps(summary(), sort_keys=True))
    elif args.action == "report":
        print(json.dumps(summary(verify_all=True), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
