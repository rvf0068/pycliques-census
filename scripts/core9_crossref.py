"""Read-only order-9 historical cross-reference for order-10 pared nine-cores.

Match all 35 order-9 representatives in the frozen post-v3 core index to
the *original zero-based* connected-nine-graph McKay/pyg6data inventory.
Inspect the COMPLETE historical order-9 verdict history (initial chunks,
c10, bound60, bound70), not merely the initial indeterminate list.

This module makes no mathematical transfer claim from a pared core to its
ten-vertex members and never modifies past stages or working lists.

Usage (after the existing separate v3 environment is prepared):
    .venv-v3/bin/python scripts/core9_crossref.py build
    .venv-v3/bin/python scripts/core9_crossref.py verify
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import tempfile
from collections import Counter, defaultdict
from importlib import resources
from pathlib import Path

import networkx as nx
from pyg6data.lists import graph_generator

import core_isomorphism_index as indexer

ROOT = Path(__file__).resolve().parents[1]
CORE_INDEX = ROOT / "reports" / "order10_core_index_v1"
ORDER9 = ROOT / "runs" / "order9"
FINAL9 = ROOT / "indeterminate_order_9.txt"
OUTPUT = ROOT / "reports" / "order10_core9_crossref_v1"
STAGES = ("c10", "bound60", "bound70")
POSITIVE = {"CONVERGENT", "DIVERGENT"}
TOTAL_ORDER9 = 261080


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return digest(path.read_bytes())


def graph6(graph: nx.Graph) -> str:
    return nx.to_graph6_bytes(
        nx.convert_node_labels_to_integers(graph), header=False
    ).decode("ascii").strip()


def frozen_cores(index_folder: Path = CORE_INDEX) -> dict[int, dict]:
    """Require a byte-exact reconstruction of the committed core index."""
    indexer.check_saved(index_folder, indexer.prepare())
    path = index_folder / "classes.tsv"
    rows = path.read_text(encoding="utf-8").splitlines()
    required = (
        "core_id\tcore_order\tcore_graph6\tmembers\tconjectured_members\tmember_indices"
    )
    if not rows or rows[0] != required:
        raise ValueError("Frozen core index class header changed")
    selected = {}
    count = 0
    for line in rows[1:]:
        parts = line.split("\t")
        if len(parts) != 6:
            raise ValueError("Malformed frozen class entry")
        core_id, order, encoded, members, _, _ = parts
        if int(order) != 9:
            continue
        i = int(core_id)
        if i in selected:
            raise ValueError(f"Duplicate core representative {i}")
        graph = nx.from_graph6_bytes(encoded.encode("ascii"))
        if graph.order() != 9 or not nx.is_connected(graph):
            raise ValueError(f"Invalid order-nine core graph: {i}")
        selected[i] = {
            "graph6": encoded,
            "graph": graph,
            "members": int(members),
        }
        count += int(members)
    if len(selected) != 35 or count != 4038:
        raise ValueError("Expected exactly 35 pared nine-cores with 4038 members")
    return dict(sorted(selected.items()))


def coarse_key(graph: nx.Graph) -> tuple:
    """Isomorphism-invariant filter; matches still require exact isomorphism."""
    return (
        graph.number_of_nodes(),
        graph.number_of_edges(),
        tuple(sorted(degree for _, degree in graph.degree())),
    )


def match_source(cores: dict[int, dict], graphs, *, expected_count: int) -> dict[int, dict]:
    """Exact, bijective matches in source order; reject missing/duplicate matches.

    The iterator's enumeration index is the historical zero-based index.
    No graph6 string is presumed canonical across vertex relabelings.
    """
    buckets = defaultdict(list)
    for core_id, record in cores.items():
        buckets[coarse_key(record["graph"])].append((core_id, record["graph"]))
    matched = {}
    scanned = 0
    for source_index, original in enumerate(graphs):
        scanned += 1
        for core_id, core in buckets.get(coarse_key(original), ()):
            if nx.is_isomorphic(original, core):
                if core_id in matched:
                    raise ValueError(
                        f"Core {core_id} matches multiple source entries: "
                        f"{matched[core_id]['order9_index']} and {source_index}"
                    )
                matched[core_id] = {
                    "order9_index": source_index,
                    "order9_graph6": graph6(original),
                }
    if scanned != expected_count:
        raise ValueError(f"Connected order-nine source count changed: {scanned}")
    if set(matched) != set(cores):
        raise ValueError(f"Unmatched order-nine core IDs: {sorted(set(cores)-set(matched))}")
    if len({r["order9_index"] for r in matched.values()}) != len(matched):
        raise ValueError("Distinct core classes map to one source graph")
    return dict(sorted(matched.items()))


def validate_dataset(initial_meta: dict) -> str:
    """Hash the original compressed source as the initial census did."""
    source = resources.files("pyg6data.data").joinpath("graph9c.g6.gz")
    archive_sha = digest(source.read_bytes())
    expected = initial_meta.get("bundled_connected_graph6_sha256", {}).get("9")
    if archive_sha != expected:
        raise ValueError("Installed connected nine-graph6 data differ from the frozen census")
    return archive_sha


def initial_data(root: Path = ROOT) -> tuple[dict, dict, dict[int, dict]]:
    run = root / "runs" / "order9" / "initial"
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((run / "summary.json").read_text(encoding="utf-8"))
    orders = summary.get("orders")
    if (
        summary.get("manifest") != manifest
        or manifest.get("min_order") != 9
        or manifest.get("max_order") != 9
        or not isinstance(orders, list) or len(orders) != 1
        or orders[0].get("connected_total") != TOTAL_ORDER9
    ):
        raise ValueError("Order-nine initial census has inconsistent provenance")
    unresolved = {}
    for entry in summary.get("unresolved", []):
        i = entry["index"]
        if i in unresolved or entry.get("order") != 9:
            raise ValueError("Bad original unresolved index in order-nine summary")
        unresolved[i] = entry
    if len(unresolved) != orders[0]["indeterminate"]:
        raise ValueError("Order-nine initial unresolved total differs from summary")
    return manifest, summary, unresolved


def read_initial_verdicts(indices: dict[int, str], initial_meta: dict,
                          unresolved: dict[int, dict],
                          root: Path = ROOT) -> tuple[dict[int, dict], dict[str, str]]:
    """Retrieve genuine initial verdicts for matched indices from frozen chunks."""
    batch = initial_meta["batch_size"]
    if not isinstance(batch, int) or batch < 1:
        raise ValueError("Invalid historical initial batch size")
    run = root / "runs" / "order9" / "initial" / "order9" / "chunks"
    found = {}
    hashes = {}
    by_chunk = defaultdict(set)
    for i in indices:
        by_chunk[(i // batch) * batch].add(i)
    for start, desired in sorted(by_chunk.items()):
        end = min(TOTAL_ORDER9 - 1, start + batch - 1)
        path = run / f"{start:08d}-{end:08d}.tsv.gz"
        hashes[str(path.relative_to(root))] = sha(path)
        with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
            for line in stream:
                if line.startswith("#") or not line.strip():
                    continue
                parts = next(csv.reader([line], delimiter="\t"))
                if len(parts) != 3:
                    raise ValueError(f"Malformed frozen initial verdict in {path}")
                i = int(parts[0])
                if i not in desired:
                    continue
                if i in found:
                    raise ValueError(f"Repeated source index {i} in initial chunk")
                status, reason = parts[1:]
                if status not in POSITIVE | {"INDETERMINATE"}:
                    raise ValueError(f"Invalid original verdict at index {i}")
                if status == "INDETERMINATE":
                    if (
                        i not in unresolved
                        or unresolved[i]["graph6"] != indices[i]
                    ):
                        raise ValueError(f"Initial indeterminate source graph mismatch at {i}")
                elif i in unresolved:
                    raise ValueError(f"Original source {i} simultaneously classified and unresolved")
                found[i] = {
                    "verdict": status, "reason": reason,
                    "stage": "initial", "rule": reason,
                    "record_path": str(path.relative_to(root)),
                }
        if set(found) & desired != desired:
            raise ValueError(f"Missing source indices in initial chunk {path}")
    if set(found) != set(indices):
        raise ValueError("Some matched nine-vertex graphs lack initial verdicts")
    return found, hashes


def load_stage_records(stage: str, original_unresolved: dict[int, dict],
                       root: Path = ROOT) -> tuple[dict[int, dict], dict[str, str]]:
    """Validate entire completed historical stage and bind records to originals."""
    folder = root / "runs" / "order9" / stage
    summary_path = folder / "summary.json"
    manifest_path = folder / "manifest.json"
    meta = json.loads(manifest_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if (meta.get("order"), meta.get("stage")) != (9, stage) or summary.get("manifest") != meta:
        raise ValueError(f"Historical stage provenance mismatch: {stage}")
    indices = meta.get("indices")
    if not isinstance(indices, list) or len(set(indices)) != len(indices):
        raise ValueError(f"Malformed cohort indices for stage {stage}")
    if summary.get("processed") != len(indices):
        raise ValueError(f"Incomplete historical stage {stage}")
    saved = {}
    hashes = {
        str(manifest_path.relative_to(root)): sha(manifest_path),
        str(summary_path.relative_to(root)): sha(summary_path),
    }
    for path in sorted((folder / "records").glob("*.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        i = row.get("index")
        if (
            not isinstance(i, int) or i not in original_unresolved
            or i not in indices or i in saved
            or path.name != f"{i:08d}.json"
            or row.get("graph6") != original_unresolved[i]["graph6"]
        ):
            raise ValueError(f"Bad original source identity in {path}")
        if stage == "c10":
            status = row.get("status")
            if status not in {"RETRACTION_FOUND", "NO_RETRACTION", "INCONCLUSIVE"}:
                raise ValueError(f"Bad historical c10 status at {i}")
            if status == "RETRACTION_FOUND" and not isinstance(row.get("witness"), dict):
                raise ValueError(f"Missing historical retraction witness at {i}")
        else:
            if row.get("verdict") not in POSITIVE | {"INDETERMINATE"}:
                raise ValueError(f"Bad historical {stage} verdict at {i}")
            if row.get("bound") != int(stage.removeprefix("bound")):
                raise ValueError(f"Incorrect historical {stage} bound at {i}")
        hashes[str(path.relative_to(root))] = sha(path)
        saved[i] = row
    if set(saved) != set(indices):
        raise ValueError(f"Historical {stage} records do not match cohort indices")
    return saved, hashes


def final_unresolved(root: Path = ROOT) -> set[int]:
    path = root / "indeterminate_order_9.txt"
    indices = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        if len(fields) != 6:
            raise ValueError("Malformed frozen final order-nine unresolved list")
        i = int(fields[0])
        if i in indices:
            raise ValueError(f"Repeated order-nine unresolved index {i}")
        indices.add(i)
    if len(indices) != 54:
        raise ValueError("Unexpected size of historical final order-nine list")
    return indices


def historical_verdict(initial: dict, stages: dict[str, dict | None],
                       still_unresolved: bool) -> dict:
    """First positive event in the chronological, immutable stage history."""
    verdict = initial["verdict"]
    earliest = initial["stage"] if verdict in POSITIVE else ""
    reason = initial["reason"] if earliest else ""
    rule = initial["rule"] if earliest else ""
    last = "initial"
    path = initial["record_path"] if earliest else ""
    for stage in STAGES:
        row = stages.get(stage)
        if row is None:
            continue
        last = stage
        if stage == "c10":
            candidate = "DIVERGENT" if row["status"] == "RETRACTION_FOUND" else None
            candidate_reason = row.get("reason", "")
            candidate_rule = "c10_retraction" if candidate else ""
        else:
            candidate = row["verdict"] if row["verdict"] in POSITIVE else None
            candidate_reason = row.get("reason", "")
            candidate_rule = row.get("certificate_rule", "") or candidate_reason
            if candidate_rule == "-":
                candidate_rule = candidate_reason
        if candidate:
            if verdict in POSITIVE and verdict != candidate:
                raise ValueError(f"Contradictory historical verdicts: {verdict} vs {candidate}")
            if not earliest:
                earliest = stage
                verdict = candidate
                reason = candidate_reason
                rule = candidate_rule
                path = row["_record_path"]
    if (verdict == "INDETERMINATE") != still_unresolved:
        raise ValueError("Historical stage results disagree with final order-nine list")
    return {
        "verdict": verdict, "first_positive_stage": earliest or "-",
        "positive_reason": reason or "-",
        "positive_rule": rule or "-",
        "evidence_path": path or "-",
        "last_stage_examined": last,
        "still_unresolved": still_unresolved,
    }


def prepare(root: Path = ROOT, output_script: Path | None = None) -> dict[str, bytes]:
    """Create complete deterministic cross-reference, without modifying sources."""
    core_folder = root / "reports" / "order10_core_index_v1"
    # The source index validator checks the complete post-v3 frozen input and
    # all original-ten census links before accepting the representative list.
    cores = frozen_cores(core_folder)
    initial_meta, _initial_summary, initial_unresolved = initial_data(root)
    archive_hash = validate_dataset(initial_meta)
    matched = match_source(
        cores, graph_generator(9, connected=True), expected_count=TOTAL_ORDER9
    )
    indexed = {record["order9_index"]: record["order9_graph6"] for record in matched.values()}
    initial, initial_hashes = read_initial_verdicts(
        indexed, initial_meta, initial_unresolved, root
    )
    stages = {}
    dependency_hashes = initial_hashes
    for stage in STAGES:
        stages[stage], hashed = load_stage_records(stage, initial_unresolved, root)
        dependency_hashes.update(hashed)
    unresolved = final_unresolved(root)
    if not unresolved.issubset(initial_unresolved):
        raise ValueError("Final order-nine unresolved list contains new source indices")
    dependency_hashes.update({
        "reports/order10_core_index_v1/manifest.json": sha(core_folder / "manifest.json"),
        "reports/order10_core_index_v1/classes.tsv": sha(core_folder / "classes.tsv"),
        "reports/order10_core_index_v1/assignments.tsv": sha(core_folder / "assignments.tsv"),
        "runs/order9/initial/manifest.json": sha(root / "runs/order9/initial/manifest.json"),
        "runs/order9/initial/summary.json": sha(root / "runs/order9/initial/summary.json"),
        "indeterminate_order_9.txt": sha(root / "indeterminate_order_9.txt"),
    })

    header = (
        "core_id\tcore_graph6\toriginal_members\torder9_index\torder9_graph6"
        "\thistorical_verdict\tfirst_positive_stage\tpositive_rule"
        "\tpositive_reason\tlast_stage_examined\torder9_still_unresolved\tevidence_path"
    )
    lines = [header]
    pending = [
        "core_id\tcore_graph6\toriginal_members\torder9_index\torder9_graph6\tlast_stage_examined"
    ]
    summary_count = Counter()
    stage_counts = Counter()
    originals_by_verdict = Counter()
    for i, item in cores.items():
        match = matched[i]
        nine = match["order9_index"]
        old_records = {}
        for stage in STAGES:
            record = stages[stage].get(nine)
            if record is not None:
                old_records[stage] = {
                    **record,
                    "_record_path": f"runs/order9/{stage}/records/{nine:08d}.json"
                }
        verdict = historical_verdict(initial[nine], old_records, nine in unresolved)
        summary_count[verdict["verdict"]] += 1
        stage_counts[verdict["first_positive_stage"]] += 1
        originals_by_verdict[verdict["verdict"]] += item["members"]
        lines.append("\t".join(map(str, (
            i, item["graph6"], item["members"], nine, match["order9_graph6"],
            verdict["verdict"], verdict["first_positive_stage"],
            verdict["positive_rule"], verdict["positive_reason"],
            verdict["last_stage_examined"], str(verdict["still_unresolved"]).lower(),
            verdict["evidence_path"],
        ))))
        if verdict["still_unresolved"]:
            pending.append("\t".join(map(str, (
                i, item["graph6"], item["members"], nine,
                match["order9_graph6"], verdict["last_stage_examined"],
            ))))

    doc = [
        "# Historical order-nine cross-reference for the order-ten pared cores", "",
        "The 35 distinct completely pared nine-vertex representatives were",
        "matched by actual graph isomorphism to the full 261,080-entry",
        "McKay/pyg6data connected-nine-graph source, using its zero-based order.",
        "No canonical identity of differently labeled graph6 encodings is assumed.", "",
        "**Historical classification is about the nine-vertex core only.**",
        "It is not a new certificate for any original ten-vertex member graph.",
        "A positive historical verdict is recorded with its original stage",
        "and reason; it is not upgraded to a newly replayable certificate.", "",
        "## Historical status of the 35 core classes", "",
        "| Historical verdict | Distinct 9-cores | Original order-10 members |",
        "|---|---:|---:|",
    ]
    for verdict in ("DIVERGENT", "CONVERGENT", "INDETERMINATE"):
        doc.append(
            f"| {verdict} | {summary_count[verdict]} "
            f"| {originals_by_verdict[verdict]:,} |"
        )
    doc.extend([
        "", "## First positive historical stage", "",
        "| Stage | Cores |", "|---|---:|",
    ])
    for stage in ("initial", *STAGES, "-"):
        doc.append(f"| {stage} | {stage_counts[stage]} |")
    doc.extend([
        "", "## The four rediscovered divergent nine-cores", "",
        "| Order-10 core ID | Order-9 index | First positive stage | Witness description |",
        "|---:|---:|---|---|",
    ])
    for i in (6938923, 6939350, 7454135, 9678187):
        record = next((line.split("\t") for line in lines[1:]
                       if line.startswith(f"{i}\t")), None)
        if record is not None:
            doc.append(
                f"| {i} | {record[3]} | {record[6]} | {record[8]} |"
            )
    doc.extend([
        "", "## Cores already divergent in the initial order-nine census", "",
        "| Order-10 core ID | Order-9 index | Original members | Initial reason |",
        "|---:|---:|---:|---|",
    ])
    for line in lines[1:]:
        fields = line.split("\t")
        if fields[6] == "initial" and fields[5] == "DIVERGENT":
            doc.append(
                f"| {fields[0]} | {fields[3]} | {fields[2]} | {fields[8]} |"
            )
    doc.extend([
        "", "## Outputs", "",
        "- matches.tsv: all 35 isomorphism matches, historical verdicts, and evidence paths",
        "- unclassified.tsv: representatives still unresolved after all historical stages",
        "- manifest.json: frozen dataset and historical source/output SHA-256 digests",
        "",
        "Results are reproducible and immutable. Repeated build verifies rather",
        "than overwrites. The source census and all completed stages are read-only.", "",
    ])

    payload = {
        "matches.tsv": ("\n".join(lines) + "\n").encode("utf-8"),
        "unclassified.tsv": ("\n".join(pending) + "\n").encode("utf-8"),
        "summary.md": ("\n".join(doc)).encode("utf-8"),
    }
    meta = {
        "schema": 1,
        "stage": "order10_core9_historical_crossref_v1",
        "method": "full connected order-nine graph6 stream, coarse invariant then verified NetworkX isomorphism",
        "source": "pyg6data.data/graph9c.g6.gz",
        "source_sha256": archive_hash,
        "source_total": TOTAL_ORDER9,
        "input_sha256": dict(sorted(dependency_hashes.items())),
        "script_sha256": sha(output_script or Path(__file__)),
        "cores": len(cores),
        "original_members": sum(row["members"] for row in cores.values()),
        "historical_verdict_counts": dict(sorted(summary_count.items())),
        "original_members_by_verdict": dict(sorted(originals_by_verdict.items())),
        "first_positive_stage_counts": dict(sorted(stage_counts.items())),
        "output_sha256": {name: digest(data) for name, data in payload.items()},
    }
    payload["manifest.json"] = (json.dumps(meta, sort_keys=True, indent=2) + "\n").encode("utf-8")
    return payload


def verify_saved(folder: Path, expected: dict[str, bytes]) -> None:
    if not folder.is_dir() or {x.name for x in folder.iterdir()} != set(expected):
        raise ValueError("Missing or unexpected cross-reference output files")
    for name, blob in expected.items():
        if (folder / name).read_bytes() != blob:
            raise ValueError(f"Cross-reference output changed: {name}")


def build(folder: Path, expected: dict[str, bytes]) -> None:
    if folder.exists():
        verify_saved(folder, expected)
        print(f"Existing cross-reference verified unchanged: {folder}")
        return
    folder.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".core9-crossref-", dir=folder.parent) as temp:
        stage = Path(temp) / "ready"
        stage.mkdir()
        for name, blob in expected.items():
            (stage / name).write_bytes(blob)
        os.replace(stage, folder)
    print(f"Created immutable cross-reference: {folder}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify"))
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    expected = prepare()
    if args.command == "build":
        build(args.output, expected)
    else:
        verify_saved(args.output, expected)
        print(f"Verified cross-reference: {args.output}")
    report = json.loads(expected["manifest.json"])
    print(
        f"{report['cores']} nine-cores matched to {report['source_total']:,} "
        f"connected nine-vertex graphs: {report['historical_verdict_counts']}"
    )


if __name__ == "__main__":
    main()
