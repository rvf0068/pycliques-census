"""Staged, resumable connected-graph census post-processing.

Stages operate on original-indexed graph6 from a validated initial census.
Conjectural dependence is not a proof, and resource-limited computations do
not establish negative results. Each graph's JSON record is written atomically.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "postpasses"))
from clique_retract_comp_c10 import search_retraction  # noqa: E402
from s1_divergence import scan as scan_s1_divergence  # noqa: E402

from pycliques.small import classify_clique_behavior
from pycliques.surfaces import is_surface
from surface_refs import load_surface_references
from pycombtop.homotopy_type import homotopy_type_with_verdict


def filehash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_atomic(path: Path, value: dict | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".partial")
    try:
        if isinstance(value, str):
            temp.write_text(value, encoding="utf-8")
        else:
            temp.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def current_pin() -> str:
    source = ROOT / ".deps" / "pycliques-project"
    head = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    pin = (ROOT / "config" / "pycliques_commit.txt").read_text().strip()
    if head != pin:
        raise ValueError("Installed pycliques revision is not the pinned revision")
    return head


def reference_file() -> Path:
    return ROOT / "config" / "conjectured_surfaces_order9.tsv"



def census(order: int) -> tuple[Path, dict[int, dict], dict[int, str]]:
    run = ROOT / "runs" / f"order{order}" / "initial"
    summary = json.loads((run / "summary.json").read_text(encoding="utf-8"))
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    expected = 261080 if order == 9 else 11716571
    if (
        summary.get("manifest") != manifest
        or manifest.get("min_order") != order
        or manifest.get("max_order") != order
        or len(summary.get("orders", [])) != 1
        or summary["orders"][0].get("connected_total") != expected
    ):
        raise ValueError(f"Order-{order} initial census not complete or not validated")
    # The validated initial census is a frozen historical result. Its
    # manifest must agree with its summary, but subsequent stages may use a
    # different pinned pycliques-project revision. The new revision is checked
    # separately by current_pin() and recorded in each *new* stage manifest.
    original_revision = manifest.get("upstream_commit")
    if (
        not isinstance(original_revision, str)
        or len(original_revision) != 40
        or any(digit not in "0123456789abcdef" for digit in original_revision)
    ):
        raise ValueError("Initial census does not record a valid upstream revision")
    entries = summary["unresolved"]
    if len(entries) != summary["orders"][0]["indeterminate"]:
        raise ValueError("Original indeterminate count differs from summary")
    by_index: dict[int, dict] = {}
    for entry in entries:
        i = entry["index"]
        if entry["order"] != order or i in by_index:
            raise ValueError("Bad or duplicated original source index")
        by_index[i] = entry
    origins: dict[int, str] = {}
    lines = (run / f"order{order}" / f"indeterminate_order_{order}.txt").read_text().splitlines()
    for line in lines:
        if not line or line.startswith("#"):
            continue
        items = line.split()
        if len(items) != 6:
            raise ValueError(f"Malformed initial unresolved row: {line}")
        i = int(items[0])
        if i not in by_index or i in origins:
            raise ValueError("Unresolved source index not present in summary")
        conditional = "conjectur" in by_index[i]["reason"].lower()
        if (items[4] == "conjectured_divergent") != conditional:
            raise ValueError(f"Contradictory conjectural status at {i}")
        origins[i] = line
    if set(origins) != set(by_index):
        raise ValueError("Source unresolved cohort differs from original summary")
    return run, by_index, origins


def stage_dir(order: int, stage: str) -> Path:
    return ROOT / "runs" / f"order{order}" / stage


def checked_records(order: int, stage: str, source: dict[int, dict]) -> dict[int, dict]:
    folder = stage_dir(order, stage)
    if not folder.exists():
        return {}
    meta_path = folder / "manifest.json"
    if not meta_path.is_file():
        raise ValueError(f"Stage directory exists without manifest: {folder}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("stage") != stage or meta.get("order") != order:
        raise ValueError(f"Wrong stage manifest: {folder}")
    stage_revision = meta.get("upstream_commit")
    if (
        not isinstance(stage_revision, str)
        or len(stage_revision) != 40
        or any(digit not in "0123456789abcdef" for digit in stage_revision)
    ):
        raise ValueError(f"Stage has an invalid historical upstream revision: {folder}")
    summary_path = folder / "summary.json"
    if summary_path.is_file():
        saved_summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if saved_summary.get("manifest") != meta:
            raise ValueError(f"Stage summary disagrees with its manifest: {folder}")
    rows: dict[int, dict] = {}
    for file in sorted((folder / "records").glob("*.json")):
        row = json.loads(file.read_text(encoding="utf-8"))
        idx = row.get("index")
        if (
            not isinstance(idx, int) or idx not in source
            or row.get("graph6") != source[idx]["graph6"]
            or file.name != f"{idx:08d}.json"
            or idx in rows
        ):
            raise ValueError(f"Malformed or wrong graph source in {file}")
        if stage == "c10":
            if row.get("status") not in {"RETRACTION_FOUND", "NO_RETRACTION", "INCONCLUSIVE"}:
                raise ValueError(f"Bad retraction status in {file}")
            if row["status"] == "RETRACTION_FOUND" and not isinstance(row.get("witness"), dict):
                raise ValueError(f"Missing positive retraction witness in {file}")
        elif stage in ("bound60", "bound70"):
            if row.get("verdict") not in {"CONVERGENT", "DIVERGENT", "INDETERMINATE"}:
                raise ValueError(f"Bad classification in {file}")
        elif stage == "homotopy":
            if not isinstance(row.get("is_exact"), bool):
                raise ValueError(f"Bad homotopy result in {file}")
        elif stage == "s1divergence":
            if row.get("status") not in {"DIVERGENT", "INDETERMINATE"}:
                raise ValueError(f"Bad S^1 divergence status in {file}")
            if row["status"] == "DIVERGENT" and (
                row.get("rule") not in {"clockwork_iterate", "triangular_cover_pair"}
                or not isinstance(row.get("witness"), dict)
                or row["witness"].get("kind") not in {
                    "divergent_clockwork_iterate", "triangular_cover_pair"
                }
            ):
                raise ValueError(f"Missing positive divergence witness in {file}")
        rows[idx] = row
    return rows


def active(order: int) -> tuple[dict[int, dict], dict[int, str], dict[int, dict]]:
    _, source, origins = census(order)
    c10 = checked_records(order, "c10", source)
    bound60 = checked_records(9, "bound60", source) if order == 9 else {}
    bound70 = checked_records(order, "bound70", source)
    s1 = checked_records(10, "s1divergence", source) if order == 10 else {}
    active_rows: dict[int, dict] = {}
    for i, row in source.items():
        if c10.get(i, {}).get("status") == "RETRACTION_FOUND":
            continue
        if s1.get(i, {}).get("status") == "DIVERGENT":
            continue
        if any(
            results.get(i, {}).get("verdict") in {"CONVERGENT", "DIVERGENT"}
            for results in (bound60, bound70)
        ):
            continue
        active_rows[i] = row
    return active_rows, origins, source


def stage_selection(order: int, stage: str) -> tuple[dict[int, dict], dict[int, dict]]:
    """Select a fixed cohort from *preceding* stages, never this stage.

    This remains unchanged as successful records accumulate, permitting
    deterministic resumption after an interruption.
    """
    if (order, stage) not in {
        (9, "c10"), (9, "bound60"), (9, "bound70"),
        (10, "c10"), (10, "homotopy"), (10, "s1divergence"), (10, "bound70"),
    }:
        raise ValueError(f"Unsupported stage: order={order}, stage={stage}")
    _, source, origins = census(order)
    c10 = checked_records(order, "c10", source) if stage != "c10" else {}
    resolved_c10 = {
        i for i, result in c10.items()
        if result["status"] == "RETRACTION_FOUND"
    }
    # Post-C10 order-10 stages retain the original nonconjectural
    # full-pared-order cohort. The extra divergence stage examines only S^1.
    require_full_pared_order = order == 10 and stage in (
        "homotopy", "s1divergence", "bound70"
    )
    prior_bound60 = (
        checked_records(9, "bound60", source)
        if order == 9 and stage == "bound70"
        else {}
    )
    homotopy = (
        checked_records(10, "homotopy", source)
        if order == 10 and stage in ("s1divergence", "bound70")
        else {}
    )
    resolved_s1 = (
        {
            i for i, result in checked_records(10, "s1divergence", source).items()
            if result["status"] == "DIVERGENT"
        }
        if order == 10 and stage == "bound70" else set()
    )
    eligible = {
        i: row for i, row in source.items()
        if i not in resolved_c10
        and i not in resolved_s1
        and origins[i].split()[4] != "conjectured_divergent"
        and (not require_full_pared_order or origins[i].split()[1] == "10")
        and prior_bound60.get(i, {}).get("verdict") not in {"CONVERGENT", "DIVERGENT"}
        and prior_bound60.get(i, {}).get("certificate_target_status") != "conjectured_divergent"
        and (
            stage != "s1divergence"
            or (
                homotopy.get(i, {}).get("is_exact") is True
                and homotopy[i].get("is_limited") is False
                and homotopy[i].get("spheres") == {"1": 1}
            )
        )
        and (
            order != 10 or stage != "bound70"
            or (
                homotopy.get(i, {}).get("is_exact") is True
                and homotopy[i].get("is_limited") is False
                and isinstance(homotopy[i].get("spheres"), dict)
                and all(
                    dimension == "1"
                    and isinstance(multiplicity, int)
                    and not isinstance(multiplicity, bool)
                    and multiplicity > 0
                    for dimension, multiplicity in homotopy[i]["spheres"].items()
                )
            )
        )
    }
    return eligible, source


def refresh(order: int) -> dict:
    remaining, origins, source = active(order)
    c10 = checked_records(order, "c10", source)
    bound60 = checked_records(9, "bound60", source) if order == 9 else {}
    bound70 = checked_records(order, "bound70", source)
    h = checked_records(order, "homotopy", source) if order == 10 else {}
    s1 = checked_records(order, "s1divergence", source) if order == 10 else {}
    conditional = 0
    data: list[str] = []
    for i in sorted(remaining):
        fields = origins[i].split()
        new = bound70.get(i) or bound60.get(i)
        if new and new["verdict"] == "INDETERMINATE":
            fields = [
                str(i), str(new["pared_order"]), new["pared_graph6"],
                new["certificate_rule"], new["certificate_target_status"],
                new["certificate_target_label"],
            ]
        if fields[4] == "conjectured_divergent":
            conditional += 1
        data.append(" ".join(fields))
    out = ROOT / f"indeterminate_order_{order}.txt"
    header = [
        f"# Current indeterminate connected graphs of order {order}",
        "# Derived from certified stage records; raw initial census remains unchanged.",
        f"# Remaining={len(data)} conjectured_divergent={conditional}",
        f"# C10_checked={len(c10)} bound60_checked={len(bound60)} "
        f"bound70_checked={len(bound70)} homotopy_checked={len(h)} "
        f"s1divergence_checked={len(s1)} "
        f"s1divergence_proven={sum(r['status'] == 'DIVERGENT' for r in s1.values())}",
        "# Format: original_index pared_order pared_graph6 certificate_rule certificate_target_status certificate_target_label",
    ]
    write_atomic(out, "\n".join(header + data) + "\n")
    return {
        "original_indeterminate": len(source),
        "remaining": len(data),
        "conjectured_divergent": conditional,
        "C10_checked": len(c10),
        "bound60_checked": len(bound60),
        "bound70_checked": len(bound70),
        "homotopy_checked": len(h),
        "s1divergence_checked": len(s1),
        "s1divergence_proven": sum(r["status"] == "DIVERGENT" for r in s1.values()),
    }


def surface_registry(order: int) -> int:
    if order != 9:
        raise ValueError("Surface registration is the final stage of order 9")
    remaining, _, source = active(9)
    registered: list[tuple[int, str]] = []
    for i, row in sorted(remaining.items()):
        graph6 = row["graph6"]
        graph = nx.from_graph6_bytes(graph6.encode("ascii"))
        if is_surface(graph):
            registered.append((i, graph6))
    lines = [
        "# Conjectured divergent surfaces: original order-9 source-index graph6",
        "# Generated from remaining indeterminate graphs after stages c10, bound60 and bound70",
        "# Each graph is registered as ReferenceStatus.CONJECTURED, never PROVEN.",
    ]
    lines.extend(f"{i} {g6}" for i, g6 in registered)
    write_atomic(reference_file(), "\n".join(lines) + "\n")
    return len(registered)


def compute(order: int, stage: str, graph: nx.Graph) -> dict:
    if stage == "c10":
        return search_retraction(graph)
    if stage in ("bound60", "bound70"):
        bound = 60 if stage == "bound60" else 70
        r = classify_clique_behavior(graph, bound=bound)
        c = r.certificate
        pared = nx.convert_node_labels_to_integers(r.pared_graph)
        return {
            "bound": bound,
            "verdict": r.verdict.name,
            "reason": r.reason,
            "pared_order": pared.number_of_nodes(),
            "pared_graph6": nx.to_graph6_bytes(pared, header=False).decode("ascii").strip(),
            "certificate_rule": c.rule if c is not None else "-",
            "certificate_target_status": (c.target_status or "-") if c is not None else "-",
            "certificate_target_label": (c.target_label or "-") if c is not None else "-",
        }
    if stage == "s1divergence":
        return scan_s1_divergence(graph)
    if stage == "homotopy":
        v = homotopy_type_with_verdict(graph)
        return {
            "is_exact": bool(v.is_exact),
            "is_limited": bool(v.is_limited),
            "verdict": v.verdict,
            "reason": v.reason,
            "spheres": {str(k): count for k, count in v.wedge.spheres.items()} if v.is_exact else None,
        }
    raise ValueError(stage)


def run_stage(order: int, stage: str) -> None:
    if (order, stage) not in {
        (9, "c10"), (9, "bound60"), (9, "bound70"),
        (10, "c10"), (10, "homotopy"), (10, "s1divergence"), (10, "bound70"),
    }:
        raise ValueError(f"Unsupported stage: order={order}, stage={stage}")
    if order == 9 and stage == "bound70":
        # Replacing references after an order-10 initial census has started
        # would invalidate that census's surface-registry provenance.
        if (ROOT / "runs" / "order10" / "initial" / "manifest.json").exists():
            raise ValueError(
                "Order-10 initial census already exists: do not change its "
                "surface references. Preserve or restart that census first."
            )
    if order == 10:
        if not reference_file().is_file():
            raise ValueError("Run order-9 bound70 to finalize surface references first")
        load_surface_references()
    current = current_pin()
    selection, source = stage_selection(order, stage)
    initial = ROOT / "runs" / f"order{order}" / "initial"
    meta = {
        "schema": 1,
        "stage": stage,
        "order": order,
        # Each post-stage records the dependency revision used *now*.
        # The initial census and earlier completed post-stages retain their
        # original revisions and are never retroactively relabeled.
        "upstream_commit": current,
        "initial_summary_sha256": filehash(initial / "summary.json"),
        "script_sha256": filehash(Path(__file__)),
        "surface_registry_sha256": filehash(reference_file()) if order == 10 else None,
        "indices": sorted(selection),
    }
    # Hash the complete preceding stage metadata to prevent stale cohort reuse.
    prerequisites = {
        "c10": [],
        "bound60": ["c10"],
        "bound70": ["c10", "bound60"] if order == 9 else ["c10", "homotopy", "s1divergence"],
        "homotopy": ["c10"],
        "s1divergence": ["c10", "homotopy"],
    }[stage]
    for name in prerequisites:
        path = stage_dir(order, name) / "summary.json"
        if not path.is_file():
            raise ValueError(f"Finish order-{order} stage {name} before {stage}")
        meta[f"{name}_summary_sha256"] = filehash(path)
    dest = stage_dir(order, stage)
    manifest_path = dest / "manifest.json"
    if manifest_path.exists():
        if json.loads(manifest_path.read_text(encoding="utf-8")) != meta:
            raise ValueError(f"Cannot resume stage with changed inputs: {dest}")
    else:
        if dest.exists() and any(dest.iterdir()):
            raise ValueError(f"Stage has files but no provenance manifest: {dest}")
        write_atomic(manifest_path, meta)
    folder = dest / "records"
    folder.mkdir(exist_ok=True)
    prev = checked_records(order, stage, source)
    if set(prev) - set(selection):
        raise ValueError("Saved results no longer belong to current cohort")

    for n, (i, row) in enumerate(sorted(selection.items()), start=1):
        if i in prev:
            continue
        graph6 = row["graph6"]
        graph = nx.from_graph6_bytes(graph6.encode("ascii"))
        print(f"order={order} stage={stage} [{n}/{len(selection)}] index={i}", flush=True)
        record = {"index": i, "graph6": graph6, **compute(order, stage, graph)}
        write_atomic(folder / f"{i:08d}.json", record)
    # No stage is complete until ALL records are present. The wrapper can
    # refresh a partial root list after interruption.
    results = checked_records(order, stage, source)
    if set(results) != set(selection):
        raise ValueError("Post-stage results incomplete")
    counts = Counter(
        result.get("status", result.get("verdict", "HOMOTOPY_CHECKED"))
        for result in results.values()
    )
    write_atomic(dest / "summary.json", {
        "manifest": meta,
        "processed": len(results),
        "counts": dict(sorted(counts.items())),
    })
    if order == 9 and stage == "bound70":
        surfaces = surface_registry(9)
        print(f"Registered {surfaces} remaining order-9 surface references (conjectural)", flush=True)
    result = refresh(order)
    print(f"Completed order {order} stage {stage}: {counts}; working cohort={result['remaining']}", flush=True)


def check_baseline() -> None:
    """Verify the saved through-eight baseline has only the snub exception."""
    run = ROOT / "runs" / "baseline-through8-bound30"
    summary = json.loads((run / "summary.json").read_text(encoding="utf-8"))
    orders = summary.get("orders", [])
    expected_counts = {1: 1, 2: 1, 3: 2, 4: 6, 5: 21, 6: 112, 7: 853, 8: 11117}
    if (
        {x["order"]: x["connected_total"] for x in orders} != expected_counts
        or not summary.get("baseline_expectation_met")
        or len(summary.get("unresolved", [])) != 1
    ):
        raise ValueError("Baseline census through order 8 is not verified")
    case = summary["unresolved"][0]
    if (case["order"], case["index"], case["graph6"]) != (8, 10829, "GQyuzw"):
        raise ValueError("The sole historical exception is not the snub disphenoid")
    print("Baseline verified: all connected graphs through order 8; snub disphenoid is the only indeterminate.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("order", type=int, choices=(9, 10))
    parser.add_argument("stage", choices=("refresh", "c10", "bound60", "bound70", "homotopy", "s1divergence"))
    args = parser.parse_args()
    if args.stage == "refresh":
        print(refresh(args.order))
    else:
        run_stage(args.order, args.stage)


if __name__ == "__main__":
    main()
