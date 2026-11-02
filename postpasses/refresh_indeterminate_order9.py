#!/usr/bin/env python3
"""Refresh root indeterminate_order_9.txt from an immutable order-9 census.

The source census remains unchanged. A verified post-pass RETRACTION_FOUND
removes its graph from the *working* indeterminate list; NO_RETRACTION,
INCONCLUSIVE and untested graphs remain. The snub-dependent cohort remains
indeterminate, regardless of this post-pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_RUN = ROOT / "runs" / "order9-bound30-after-clockwork-fix"
DEFAULT_POSTPASS = SOURCE_RUN / "postpasses" / "clique_retract_comp_c10"
WORKING_FILE = ROOT / "indeterminate_order_9.txt"
VALID_STATUSES = {"RETRACTION_FOUND", "NO_RETRACTION", "INCONCLUSIVE"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_lines(run_dir: Path) -> tuple[list[str], dict[int, str]]:
    """Validate original six-column cohort against its census summary."""
    cohort_path = run_dir / "order9" / "indeterminate_order_9.txt"
    summary_path = run_dir / "summary.json"
    manifest_path = run_dir / "manifest.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if summary.get("manifest") != manifest:
        raise ValueError("Census summary does not match its original manifest")
    orders = summary.get("orders", [])
    if (
        manifest.get("min_order") != 9
        or manifest.get("max_order") != 9
        or len(orders) != 1
        or orders[0].get("connected_total") != 261080
        or orders[0].get("order") != 9
    ):
        raise ValueError("Expected a validated, completed order-9-only census")
    raw = [
        line
        for line in cohort_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    original = summary.get("unresolved", [])
    if len(raw) != len(original) or len(original) != orders[0]["indeterminate"]:
        raise ValueError("Original unresolved count differs from census summary")
    by_index: dict[int, dict] = {}
    for row in original:
        index = row["index"]
        if index in by_index or row.get("order") != 9:
            raise ValueError("Duplicate or invalid original index in census summary")
        by_index[index] = row
    result: dict[int, str] = {}
    previous = -1
    for line in raw:
        fields = line.split()
        if len(fields) != 6:
            raise ValueError(f"Expected six fields in original cohort: {line!r}")
        index = int(fields[0])
        if index <= previous or index not in by_index:
            raise ValueError("Source cohort has unordered or unknown original index")
        previous = index
        status = fields[4]
        if status not in {"-", "conjectured_divergent"}:
            raise ValueError(f"Unexpected original target status at index {index}")
        if ("conjectur" in by_index[index]["reason"].lower()) != (
            status == "conjectured_divergent"
        ):
            raise ValueError(f"Contradictory conjectural status at index {index}")
        result[index] = status
    if set(result) != set(by_index):
        raise ValueError("Source and summary indices disagree")
    return raw, result


def load_postpass_results(
    run_dir: Path, output_dir: Path, original_status: dict[int, str]
) -> dict[int, str]:
    """Accept only records from the current source run and experiment manifest."""
    manifest_file = output_dir / "manifest.json"
    records_dir = output_dir / "records"
    if not manifest_file.is_file():
        if output_dir.exists() and any(output_dir.iterdir()):
            raise ValueError("Post-pass results exist without a post-pass manifest")
        return {}
    meta = json.loads(manifest_file.read_text(encoding="utf-8"))
    if (
        meta.get("order") != 9
        or meta.get("target") != "complement_of_cycle(10)"
        or meta.get("graph_under_test") != "K(G)"
        or meta.get("source_run_manifest_sha256") != sha256(run_dir / "manifest.json")
        or meta.get("source_run_summary_sha256") != sha256(run_dir / "summary.json")
        or meta.get("unresolved_cohort_sha256")
        != sha256(run_dir / "order9" / "indeterminate_order_9.txt")
    ):
        raise ValueError("Post-pass manifest does not match this census or target")
    eligible = {i for i, status in original_status.items() if status == "-"}
    original_graph6 = {
        row["index"]: row["graph6"]
        for row in json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))["unresolved"]
    }
    if set(meta.get("eligible_indices", [])) != eligible:
        raise ValueError("Post-pass selected cohort differs from eligible graphs")
    if not records_dir.exists():
        return {}
    records: dict[int, str] = {}
    for path in sorted(records_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        index = data.get("index")
        status = data.get("status")
        if (
            index not in eligible
            or index in records
            or path.name != f"{index:06d}.json"
            or status not in VALID_STATUSES
            or data.get("graph6") != original_graph6.get(index)
            or (status == "RETRACTION_FOUND" and not isinstance(data.get("witness"), dict))
        ):
            raise ValueError(f"Invalid post-pass record: {path}")
        # Each record's source graph must agree with the original-indexed
        # graph6 in the independently validated census summary.
        records[index] = status
    return records


def refresh(
    run_dir: Path = SOURCE_RUN,
    output_dir: Path = DEFAULT_POSTPASS,
    destination: Path = WORKING_FILE,
) -> dict[str, int]:
    raw, original_status = load_lines(run_dir)
    records = load_postpass_results(run_dir, output_dir, original_status)
    resolved = {index for index, status in records.items() if status == "RETRACTION_FOUND"}
    conditional = sum(status == "conjectured_divergent" for status in original_status.values())
    remaining = [
        line for line in raw if int(line.split(maxsplit=1)[0]) not in resolved
    ]
    stats = {
        "original": len(raw),
        "conditional": conditional,
        "eligible": len(raw) - conditional,
        "checked": len(records),
        "resolved": len(resolved),
        "remaining": len(remaining),
    }
    display_run = run_dir.relative_to(ROOT) if run_dir.is_relative_to(ROOT) else run_dir
    heading = [
        "# Working indeterminate connected graphs of order 9",
        "# Original census is immutable; this file incorporates verified post-pass results.",
        f"# Source: {display_run}/order9/indeterminate_order_9.txt",
        "# Post-pass: retractions K(G) -> complement of C_10.",
        f"# Original={stats['original']} conditional_snub={conditional} eligible={stats['eligible']}",
        f"# Checked={stats['checked']} resolved_by_retraction={stats['resolved']} remaining={stats['remaining']}",
        "# NO_RETRACTION and INCONCLUSIVE still mean clique behavior INDETERMINATE.",
        "# Format: original_index pared_order pared_graph6 certificate_rule certificate_target_status certificate_target_label",
    ]
    output = "\n".join(heading + remaining) + "\n"
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_name(destination.name + ".partial")
    try:
        tmp.write_text(output, encoding="utf-8")
        os.replace(tmp, destination)
    finally:
        tmp.unlink(missing_ok=True)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=SOURCE_RUN)
    parser.add_argument("--postpass-dir", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=WORKING_FILE)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    output_dir = (
        args.postpass_dir.resolve() if args.postpass_dir is not None
        else run_dir / "postpasses" / "clique_retract_comp_c10"
    )
    stats = refresh(run_dir, output_dir, args.output.resolve())
    print(
        f"Updated {args.output}: {stats['remaining']} indeterminate "
        f"({stats['resolved']} resolved, {stats['checked']} tested, "
        f"{stats['conditional']} snub-conditional)"
    )


if __name__ == "__main__":
    main()
