"""Immutable, read-only isomorphism index for order-10 unresolved pared cores.

A structural fingerprint only filters candidates; graph equivalence is
established using NetworkX isomorphism. No new clique-behavior verdicts are
inferred. Neither historical files nor v3 certificates are modified.

Run:
    .venv/bin/python scripts/core_isomorphism_index.py build
    .venv/bin/python scripts/core_isomorphism_index.py verify
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = ROOT / "indeterminate_order_10.txt"
ACTIVE = ROOT / "indeterminate_order_10_v3.txt"
V3 = ROOT / "runs" / "order10" / "bound120-timeboxed-v3"
DEFAULT_OUTPUT = ROOT / "reports" / "order10_core_index_v1"


@dataclass(frozen=True)
class Row:
    index: int
    order: int
    graph6: str
    target_status: str


@dataclass
class CoreClass:
    rep: Row
    graph: nx.Graph
    members: list[Row] = field(default_factory=list)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hash(path: Path) -> str:
    return digest(path.read_bytes())


def decode(graph6: str) -> nx.Graph:
    return nx.from_graph6_bytes(graph6.encode("ascii"))


def load_rows(path: Path) -> dict[int, Row]:
    rows = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        if len(fields) != 6:
            raise ValueError(f"Malformed census row at {path}:{number}")
        index, order, g6 = int(fields[0]), int(fields[1]), fields[2]
        if index < 0 or index in rows or not 1 <= order <= 10:
            raise ValueError(f"Invalid source index/order at {path}:{number}")
        g = decode(g6)
        if g.number_of_nodes() != order or not nx.is_connected(g):
            raise ValueError(f"Bad pared graph at {path}:{number}")
        rows[index] = Row(index, order, g6, fields[4])
    return rows


def check_v3(historical: dict[int, Row], active: dict[int, Row], directory: Path) -> tuple[Counter, str]:
    """Cross-check the frozen v3 membership delta, without claiming proof replay.

    Replay mathematical proofs separately with scripts/timeboxed_v3.py verify.
    A status label here is evidence of consistency, not a new certificate.
    """
    meta = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
    if (meta.get("order"), meta.get("stage")) != (10, "bound120-timeboxed-v3"):
        raise ValueError("Not a completed order-10 v3 stage")
    if summary.get("manifest") != meta:
        raise ValueError("v3 summary and manifest disagree")
    for i, row in active.items():
        if i not in historical or historical[i] != row:
            raise ValueError(f"Active index {i} differs from historical list")

    indices = meta.get("indices")
    if not isinstance(indices, list) or len(set(indices)) != len(indices):
        raise ValueError("Malformed v3 manifest indices")
    paths = sorted((directory / "records").glob("*.json"))
    if len(paths) != len(indices) or summary.get("processed") != len(indices):
        raise ValueError("v3 records or summary are incomplete")
    counts = Counter()
    removed = set()
    seen = set()
    contents_hash = hashlib.sha256()
    for path in paths:
        data = path.read_bytes()
        contents_hash.update(path.name.encode("ascii") + b"\0" + data)
        r = json.loads(data)
        i = r.get("index")
        if (not isinstance(i, int) or i not in historical or i not in indices
                or i in seen or path.name != f"{i:08d}.json"):
            raise ValueError(f"Incorrect source identity in {path}")
        seen.add(i)
        status = r.get("status")
        if not isinstance(status, str):
            raise ValueError(f"Missing status for v3 index {i}")
        counts[status] += 1
        if status in {"CONVERGENT", "DIVERGENT"}:
            proof = r.get("proof")
            if (r.get("proof_status") != "verified_chain"
                    or not isinstance(proof, dict)
                    or proof.get("origin_graph6") != r.get("graph6")):
                raise ValueError(f"Unlinked positive v3 proof record at {i}")
            removed.add(i)
    if dict(counts) != summary.get("counts"):
        raise ValueError("v3 records disagree with summary counts")
    if set(historical) - set(active) != removed:
        raise ValueError("Active list is not exactly historical minus v3 positives")
    return counts, contents_hash.hexdigest()


def fingerprint(graph: nx.Graph) -> tuple:
    """Necessary isomorphism invariant, never a substitute for isomorphism."""
    d = dict(graph.degree())
    triangles = nx.triangles(graph)
    vertices = sorted(
        (d[v], triangles[v], tuple(sorted(d[u] for u in graph[v])))
        for v in graph
    )
    return (len(graph), graph.number_of_edges(), tuple(vertices))


def group_rows(rows: dict[int, Row]) -> list[CoreClass]:
    buckets: dict[tuple, list[CoreClass]] = defaultdict(list)
    classes = []
    for i in sorted(rows):
        row = rows[i]
        graph = decode(row.graph6)
        key = fingerprint(graph)
        group = next(
            (candidate for candidate in buckets[key]
             if nx.is_isomorphic(graph, candidate.graph)), None
        )
        if group is None:
            group = CoreClass(row, graph)
            buckets[key].append(group)
            classes.append(group)
        group.members.append(row)
    if sum(len(group.members) for group in classes) != len(rows):
        raise AssertionError("Core classes are not a partition")
    return classes


def prepare(historical_path: Path = HISTORICAL, active_path: Path = ACTIVE,
            v3_dir: Path = V3, script_path: Path | None = None) -> dict[str, bytes]:
    """Build deterministic outputs in memory before making any file changes."""
    historical = load_rows(historical_path)
    active = load_rows(active_path)
    v3_counts, records_sha = check_v3(historical, active, v3_dir)
    classes = group_rows(active)
    assignments = {r.index: group for group in classes for r in group.members}
    if set(assignments) != set(active):
        raise AssertionError("Missing/duplicated member assignment")

    assign_lines = [
        "index\tpared_order\tpared_graph6\tcore_id\tcore_order\tcore_graph6\tclass_size\toriginal_target_status"
    ]
    for i, row in sorted(active.items()):
        group = assignments[i]
        assign_lines.append("\t".join(map(str, (
            i, row.order, row.graph6, group.rep.index, group.rep.order,
            group.rep.graph6, len(group.members), row.target_status,
        ))))

    class_lines = [
        "core_id\tcore_order\tcore_graph6\tmembers\tconjectured_members\tmember_indices"
    ]
    for group in classes:
        class_lines.append("\t".join(map(str, (
            group.rep.index, group.rep.order, group.rep.graph6,
            len(group.members),
            sum(r.target_status == "conjectured_divergent" for r in group.members),
            ",".join(str(r.index) for r in group.members),
        ))))

    by_order = {}
    for order in sorted({g.rep.order for g in classes}):
        selected = [g for g in classes if g.rep.order == order]
        by_order[order] = {
            "originals": sum(len(g.members) for g in selected),
            "classes": len(selected),
        }
    largest = sorted(classes, key=lambda g: (-len(g.members), g.rep.index))[:25]
    report = [
        "# Order-10 post-v3 unresolved core-isomorphism index", "",
        "Each class contains all original census indices with isomorphic",
        "completely pared graphs. Representative core_id is the smallest",
        "original source index in the class. Graph6 equality is NOT required.",
        "An exact NetworkX isomorphism test verifies every merge.", "",
        "This is only an index: it supplies NO new clique-behavior proofs.",
        "Conjectured-divergent reference statuses remain conjectural.",
        "Independently replay v3 positives using the v3 verify command.", "",
        f"Original graphs remaining: {len(active):,}",
        f"Distinct pared cores: {len(classes):,}",
        f"Removed by completed v3: {len(historical) - len(active):,}", "",
        "## Classes by pared order", "",
        "| Pared order | Original graphs | Isomorphism classes |",
        "|---:|---:|---:|",
    ]
    for order, counts in by_order.items():
        report.append(f"| {order} | {counts['originals']:,} | {counts['classes']:,} |")
    report += [
        "", "## Largest classes", "",
        "| Representative index | Pared graph6 | Order | Members | Conjectured-reference entries |",
        "|---:|---|---:|---:|---:|",
    ]
    for group in largest:
        conjectured = sum(r.target_status == "conjectured_divergent" for r in group.members)
        report.append(f"| {group.rep.index} | {group.rep.graph6} | {group.rep.order} | {len(group.members):,} | {conjectured:,} |")
    report += [
        "", "## Files", "",
        "assignments.tsv maps every remaining original graph to a core class.",
        "classes.tsv lists all class representatives and complete memberships.",
        "manifest.json contains input and output digests plus the source revision.",
        "summary.md is this human-readable overview.", "",
        "Output is immutable. Changed inputs require a new versioned directory.", "",
    ]

    data = {
        "assignments.tsv": ("\n".join(assign_lines) + "\n").encode("utf-8"),
        "classes.tsv": ("\n".join(class_lines) + "\n").encode("utf-8"),
        "summary.md": ("\n".join(report)).encode("utf-8"),
    }
    metadata = {
        "schema": 1,
        "stage": "order10_core_index_v1",
        "method": "necessary degree/triangle/neighbor-degree filter, then exact NetworkX graph isomorphism",
        "representative_rule": "lowest original source index in class",
        "historical_sha256": file_hash(historical_path),
        "post_v3_sha256": file_hash(active_path),
        "v3_manifest_sha256": file_hash(v3_dir / "manifest.json"),
        "v3_summary_sha256": file_hash(v3_dir / "summary.json"),
        "v3_records_sha256": records_sha,
        "script_sha256": file_hash(script_path or Path(__file__)),
        "originals_before_v3": len(historical),
        "originals_remaining": len(active),
        "removed_by_v3": len(historical) - len(active),
        "distinct_cores": len(classes),
        "by_pared_order": {str(k): v for k, v in by_order.items()},
        "v3_counts": dict(sorted(v3_counts.items())),
        "output_sha256": {name: digest(blob) for name, blob in data.items()},
    }
    data["manifest.json"] = (json.dumps(metadata, sort_keys=True, indent=2) + "\n").encode("utf-8")
    return data


def check_saved(folder: Path, files: dict[str, bytes]) -> None:
    if not folder.is_dir():
        raise ValueError(f"Missing core index directory: {folder}")
    if {p.name for p in folder.iterdir()} != set(files):
        raise ValueError("Core index file set has changed")
    for name, data in files.items():
        if (folder / name).read_bytes() != data:
            raise ValueError(f"Core index is stale or modified: {name}")


def build(folder: Path, files: dict[str, bytes]) -> None:
    if folder.exists():
        check_saved(folder, files)
        print(f"Verified existing immutable index: {folder}")
        return
    folder.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".core-index-staging-", dir=folder.parent) as tmp:
        staging = Path(tmp) / "ready"
        staging.mkdir()
        for name, contents in files.items():
            (staging / name).write_bytes(contents)
        os.replace(staging, folder)
    print(f"Created immutable index: {folder}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("build", "verify"))
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = p.parse_args()
    files = prepare()
    if args.command == "build":
        build(args.output, files)
    else:
        check_saved(args.output, files)
        print(f"Verified index: {args.output}")
    report = json.loads(files["manifest.json"])
    print(f"{report['originals_remaining']} original graphs, {report['distinct_cores']} distinct cores")


if __name__ == "__main__":
    main()
