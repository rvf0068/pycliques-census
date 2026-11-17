"""Deduplicated, provenance-verified order-10 divergent-target postpass (v3).

Census orchestration only. The general search and exact homology algorithms
remain pinned in pycliques-project; v2 is an immutable reference implementation.

One result is stored per EXACT graph6 encoding (not merely graph isomorphism).
v2 records may be imported only after full iterate-chain, cache and positive
witness verification. Identical graph6 strings then share a verified result.
Unannotated inputs are processed before conjectured-divergent inputs.
No behavior verdict is inferred from a negative search.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import resource
import subprocess
import sys
from pathlib import Path

import targeted_retractions_v2 as v2

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "indeterminate_order_10.txt"
SCRIPT = Path(__file__).resolve()
PIN = ROOT / "config/pycliques_commit_targeted_v3.txt"
STAGE = ROOT / "runs/order10/targeted-retractions-v3"
V2_STAGE = v2.root_dir(10)
SCHEMA = 3
ALGORITHM = "pinned-v2-exact-graph6-dedup-v1"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def source_groups() -> list[dict]:
    """Stable deterministic order; each index appears once and each graph6 once."""
    validated = v2.input_rows(10)
    groups: dict[str, dict] = {}
    observed: set[int] = set()
    for line in SOURCE.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        if len(fields) != 6:
            raise ValueError("Malformed frozen v3 source row")
        index, encoded = int(fields[0]), fields[2]
        if index in observed or validated.get(index) != encoded:
            raise ValueError("Source row disagreement with frozen v2 inputs")
        observed.add(index)
        group = groups.setdefault(
            encoded, {"graph6": encoded, "indices": [], "unclassified": False}
        )
        group["indices"].append(index)
        group["unclassified"] |= fields[4] == "-"
    if observed != set(validated):
        raise ValueError("Missing source rows in v3 census")
    return sorted(groups.values(), key=lambda row: not row["unclassified"])


def manifest() -> dict:
    if PIN.read_text(encoding="utf-8").strip() != (
        v2.PIN_FILE.read_text(encoding="utf-8").strip()
    ):
        raise ValueError("v3 dependency must match the frozen v2 library pin")
    return {
        "schema": SCHEMA,
        "algorithm": ALGORITHM,
        "source_sha256": sha(SOURCE.read_bytes()),
        "code_sha256": sha(SCRIPT.read_bytes()),
        "v2_code_sha256": sha(v2.SCRIPT.read_bytes()),
        "dependency_pin": PIN.read_text(encoding="utf-8").strip(),
        "v2_schema": v2.SCHEMA,
        "v2_settings": v2.manifest(10)["settings"],
        "priority": "unclassified_first_stable_source_order",
        "key": "exact_graph6_sha256",
        "scope": "completely_pared_graph_and_first_two_pared_clique_iterates",
    }


def require_stage() -> Path:
    expected = manifest()
    path = STAGE / "manifest.json"
    if path.exists():
        if read(path) != expected:
            raise ValueError("Frozen v3 manifest/source/algorithm mismatch")
    else:
        if STAGE.exists() and any(STAGE.iterdir()):
            raise ValueError("Refusing to adopt v3 artifacts without a manifest")
        v2.atomic(path, expected)
    return STAGE


def record_path(encoded: str) -> Path:
    return STAGE / "records" / (sha(encoded.encode("ascii")) + ".json")


def v2_source_path(index: int) -> Path:
    return V2_STAGE / "records" / f"{index:08d}.json"


def source_manifest_sha() -> str:
    v2.require_manifest(10)
    return sha((V2_STAGE / "manifest.json").read_bytes())


def copy_verified_caches(record: dict) -> None:
    for level in record["levels"]:
        if level["status"] != "COMPLETED":
            continue
        key = level["homology_cache_key"]
        src = V2_STAGE / "homology_cache" / f"{key}.json"
        dst = STAGE / "homology_cache" / f"{key}.json"
        data = src.read_bytes()
        cached = json.loads(data)
        if sha(level["graph6"].encode("ascii")) != key:
            raise ValueError("Source homology cache graph key mismatch")
        v2.validate_homology_cache(cached, level["graph6"])
        if dst.exists():
            if dst.read_bytes() != data:
                raise ValueError("Conflicting cache payload for same graph6 key")
        else:
            v2.atomic(dst, cached)


def import_v2() -> dict:
    """Import each COMPLETED v2 record only after independent verification.

    Repeated v2 records with the same exact graph6 must agree in their
    normalized results, otherwise refuse unsafe reuse.
    """
    require_stage()
    manifest_hash = source_manifest_sha()
    by_index = v2.input_rows(10)
    by_encoding: dict[str, dict] = {}
    imported = 0
    for index, encoded in by_index.items():
        path = v2_source_path(index)
        if not path.exists():
            continue
        original = read(path)
        if original.get("status") != "COMPLETED":
            continue
        v2.verify_record(original, encoded, V2_STAGE, index=index)
        normalized = {k: v for k, v in original.items() if k != "index"}
        earlier = by_encoding.get(encoded)
        if earlier is not None:
            if normalized != earlier:
                raise ValueError(
                    f"Nonidentical completed v2 results for duplicated {encoded!r}"
                )
        else:
            by_encoding[encoded] = normalized
        imported += 1
        target = record_path(encoded)
        if target.exists():
            capsule = read(target)
            if capsule.get("graph6") != encoded:
                raise ValueError("Existing v3 record collides with source")
            continue
        copy_verified_caches(original)
        capsule = {
            "schema": SCHEMA,
            "graph6": encoded,
            "status": "COMPLETED",
            "origin": "verified_v2_import",
            "v2_source_index": index,
            "v2_source_sha256": sha(path.read_bytes()),
            "v2_manifest_sha256": manifest_hash,
            "record": original,
        }
        verify_capsule(capsule, encoded)
        v2.atomic(target, capsule)

    receipt = {
        "schema": SCHEMA,
        "v2_manifest_sha256": manifest_hash,
        "verified_v2_records": imported,
        "distinct_verified_v2_graph6": len(by_encoding),
    }
    v2.atomic(STAGE / "import_v2_receipt.json", receipt)
    return receipt


def verify_capsule(capsule: dict, encoded: str) -> None:
    if (
        not isinstance(capsule, dict)
        or capsule.get("schema") != SCHEMA
        or capsule.get("graph6") != encoded
        or capsule.get("origin") not in {"verified_v2_import", "v3_worker"}
    ):
        raise ValueError("Incorrect v3 result identity/provenance")
    if capsule.get("status") in {"TIMEOUT", "ERROR"}:
        if capsule["origin"] != "v3_worker" or "record" in capsule:
            raise ValueError("Malformed v3 terminal worker result")
        return
    if capsule.get("status") != "COMPLETED":
        raise ValueError("Invalid v3 result status")
    record = capsule.get("record")
    if not isinstance(record, dict):
        raise ValueError("Missing v3 graph computation record")
    source_index = record.get("index")
    if (
        type(source_index) is not int
        or v2.input_rows(10).get(source_index) != encoded
        or record.get("input_graph6") != encoded
    ):
        raise ValueError("V3 record cannot be tied to the original input")
    v2.verify_record(record, encoded, STAGE, index=source_index)
    if capsule["origin"] == "verified_v2_import":
        if capsule.get("v2_source_index") != source_index:
            raise ValueError("Imported v2 index provenance mismatch")
        source_path = v2_source_path(source_index)
        if source_path.exists():
            if capsule.get("v2_source_sha256") != sha(source_path.read_bytes()):
                raise ValueError("Imported v2 record source changed")
            if read(source_path) != record:
                raise ValueError("Imported record differs from original v2 record")
            if capsule.get("v2_manifest_sha256") != source_manifest_sha():
                raise ValueError("Imported record refers to another v2 manifest")
        else:
            # Embeds the original verified record and its cache, so archived
            # results remain independently replayable on another machine.
            if not isinstance(capsule.get("v2_source_sha256"), str):
                raise ValueError("Missing archived v2 source fingerprint")


def worker(index: int) -> None:
    require_stage()
    groups = {i: g for g in source_groups() for i in g["indices"]}
    if index not in groups:
        raise ValueError("Unknown order-10 source index")
    encoded = groups[index]["graph6"]
    path = record_path(encoded)
    if path.exists():
        raise ValueError("Refusing to overwrite completed graph6 result")
    record = v2.analyze(index, encoded, STAGE)
    capsule = {
        "schema": SCHEMA,
        "graph6": encoded,
        "status": "COMPLETED",
        "origin": "v3_worker",
        "record": record,
    }
    verify_capsule(capsule, encoded)
    v2.atomic(path, capsule)


def run_one(group: dict) -> None:
    encoded = group["graph6"]
    path = record_path(encoded)
    if path.exists():
        if read(path).get("graph6") != encoded:
            raise ValueError("Existing result hash collision or corrupt graph6")
        return
    index = group["indices"][0]
    cmd = [sys.executable, str(SCRIPT), "worker", "--index", str(index)]
    try:
        process = subprocess.run(
            cmd, capture_output=True, text=True, check=False,
            timeout=v2.TIMEOUT_SECONDS, preexec_fn=v2.resource_limit,
        )
        if process.returncode:
            v2.atomic(path, {
                "schema": SCHEMA, "graph6": encoded,
                "origin": "v3_worker", "status": "ERROR",
                "index": index, "error": process.stderr[-2000:],
            })
    except subprocess.TimeoutExpired:
        v2.atomic(path, {
            "schema": SCHEMA, "graph6": encoded,
            "origin": "v3_worker", "status": "TIMEOUT", "index": index,
        })


def summary(groups: list[dict], *, exhaustive_verify: bool = False) -> dict:
    counts = {
        "input_records": sum(len(g["indices"]) for g in groups),
        "distinct_graph6": len(groups),
        "completed_unique": 0,
        "covered_input_indices": 0,
        "pending_unique": 0,
        "unclassified_pending_unique": 0,
        "conjectured_pending_unique": 0,
        "imported_unique": 0,
        "found_families": 0,
        "timeouts": 0,
        "errors": 0,
    }
    for group in groups:
        encoded = group["graph6"]
        path = record_path(encoded)
        if not path.exists():
            counts["pending_unique"] += 1
            label = ("unclassified_pending_unique"
                     if group["unclassified"] else "conjectured_pending_unique")
            counts[label] += 1
            continue
        data = read(path)
        if data.get("graph6") != encoded or data.get("schema") != SCHEMA:
            raise ValueError("Malformed graph6-indexed v3 record")
        if exhaustive_verify:
            verify_capsule(data, encoded)
        if data["status"] == "COMPLETED":
            counts["completed_unique"] += 1
            counts["covered_input_indices"] += len(group["indices"])
            counts["imported_unique"] += data["origin"] == "verified_v2_import"
            counts["found_families"] += sum(
                result["status"] == "FOUND"
                for level in data["record"]["levels"]
                if level["status"] == "COMPLETED"
                for result in level["families"].values()
            )
        elif data["status"] in {"TIMEOUT", "ERROR"}:
            counts["timeouts" if data["status"] == "TIMEOUT" else "errors"] += 1
        else:
            raise ValueError("Unknown v3 graph6 result status")
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=("plan", "import-v2", "next", "all", "verify", "worker")
    )
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--index", type=int)
    args = parser.parse_args()
    if args.action == "worker":
        if args.index is None:
            parser.error("--index required for worker")
        worker(args.index)
        return
    if args.index is not None:
        parser.error("--index is reserved for the isolated worker")
    if args.batch_size < 1:
        parser.error("batch-size must be positive")
    require_stage()
    groups = source_groups()
    if args.action == "import-v2":
        print(json.dumps(import_v2(), sort_keys=True))
        print(json.dumps(summary(groups), sort_keys=True))
        return
    if args.action == "verify":
        print(json.dumps(summary(groups, exhaustive_verify=True), sort_keys=True))
        return
    if args.action == "plan":
        print(json.dumps(summary(groups), sort_keys=True))
        return
    if not (STAGE / "import_v2_receipt.json").exists():
        parser.error("Run import-v2 before new v3 searches")
    pending = [g for g in groups if not record_path(g["graph6"]).exists()]
    todo = pending if args.action == "all" else pending[:args.batch_size]
    for group in todo:
        run_one(group)
    print(json.dumps(summary(groups, exhaustive_verify=True), sort_keys=True))


if __name__ == "__main__":
    main()
