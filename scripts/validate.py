"""Streaming verification of a connected-graph census, orders 1--10.

The graph6 source is independently read again while comparing the original
index with each recorded verdict. This avoids loading millions of graph
records or a giant graph index into memory for order ten.
"""

from __future__ import annotations

import argparse
import collections
import csv
import gzip
import json
import os
import sys
from collections.abc import Iterator
from pathlib import Path

from graph_sources import EXPECTED_COUNTS, connected_graphs, graph6

STATUSES = {"CONVERGENT", "DIVERGENT", "INDETERMINATE"}
# The expected *baseline* result is checked only for orders <=8 in this run.
SNUB = {"order": 8, "index": 10829, "graph6": "GQyuzw"}


def iter_verdicts(path: Path) -> Iterator[tuple[int, str, str]]:
    if not path.is_file():
        raise ValueError(f"missing completed verdict file: {path}")
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.reader(
            (line for line in handle if line.strip() and not line.startswith("#")),
            delimiter="\t",
        )
        for row in reader:
            if len(row) != 3 or row[1] not in STATUSES:
                raise ValueError(f"invalid verdict row in {path}: {row!r}")
            yield int(row[0]), row[1], row[2]


def iter_chunks(directory: Path, n: int, batch_size: int) -> Iterator[tuple[int, str, str]]:
    expected = set()
    total = EXPECTED_COUNTS[n]
    for start in range(0, total, batch_size):
        end = min(total - 1, start + batch_size - 1)
        name = f"{start:08d}-{end:08d}.tsv.gz"
        expected.add(name)
        path = directory / "chunks" / name
        if n >= 9:
            mark = directory / "completed" / f"{start:08d}-{end:08d}.done"
            sidecar = directory / "unresolved_chunks" / name
            if not mark.is_file() or not sidecar.is_file():
                raise ValueError(f"order {n}: chunk completion marker or sidecar missing for {name}")
        count = 0
        for index, verdict, reason in iter_verdicts(path):
            if index != start + count or index > end:
                raise ValueError(f"order {n}: incomplete, duplicate or out-of-order chunk {name}")
            count += 1
            yield index, verdict, reason
        if count != end - start + 1:
            raise ValueError(f"order {n}: wrong number of records in {name}: {count}")
    extra = {p.name for p in (directory / "chunks").glob("*.tsv.gz")} - expected
    if extra:
        raise ValueError(f"order {n}: unexpected chunk files: {sorted(extra)[:10]}")


def read_unresolved_file(path: Path) -> dict[int, str]:
    if not path.is_file():
        return {}
    rows: dict[int, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        fields = line.split()
        if len(fields) < 3:
            raise ValueError(f"malformed unresolved row: {line!r}")
        idx = int(fields[0])
        if idx in rows:
            raise ValueError(f"duplicate unresolved index {idx} in {path}")
        rows[idx] = fields[2]  # pared graph6, NOT necessarily original graph6
    return rows


def verify_order(directory: Path, n: int, batch_size: int) -> tuple[dict, list[dict]]:
    verdicts = iter_verdicts(directory / "verdicts.tsv") if n <= 5 else iter_chunks(directory, n, batch_size)
    inventory = None
    # For small orders, retain an independently verified original graph6 inventory.
    if n <= 8:
        inventory_path = directory / "graph_index.tsv"
        if not inventory_path.is_file():
            raise ValueError(f"order {n}: missing source inventory {inventory_path}")
        inventory_handle = inventory_path.open(encoding="utf-8", newline="")
        inventory = csv.DictReader(inventory_handle, delimiter="\t")
        if inventory.fieldnames != ["index", "graph6", "vertices", "edges"]:
            inventory_handle.close()
            raise ValueError(f"order {n}: malformed source inventory header")
    counts = collections.Counter()
    unresolved: list[dict] = []
    seen = 0
    try:
        for index, graph in enumerate(connected_graphs(n)):
            try:
                verdict_index, status, reason = next(verdicts)
            except StopIteration as exc:
                raise ValueError(f"order {n}: missing verdict for index {index}") from exc
            if verdict_index != index:
                raise ValueError(f"order {n}: expected index {index}, got {verdict_index}")
            original = graph6(graph)
            if inventory is not None:
                row = next(inventory, None)
                if (row is None or int(row["index"]) != index
                    or row["graph6"] != original or int(row["vertices"]) != n
                    or int(row["edges"]) != graph.number_of_edges()):
                    raise ValueError(f"order {n}: source inventory mismatch at {index}")
            counts[status] += 1
            seen += 1
            if status == "INDETERMINATE":
                unresolved.append({"order": n, "index": index, "graph6": original, "reason": reason})
        if seen != EXPECTED_COUNTS[n]:
            raise ValueError(f"order {n}: dataset has {seen} connected graphs, expected {EXPECTED_COUNTS[n]}")
        if next(verdicts, None) is not None:
            raise ValueError(f"order {n}: verdict records beyond source dataset")
        if inventory is not None and next(inventory, None) is not None:
            raise ValueError(f"order {n}: source inventory has extra rows")
    finally:
        if inventory is not None:
            inventory_handle.close()

    if n >= 6:
        saved = read_unresolved_file(directory / f"indeterminate_order_{n}.txt")
        if set(saved) != {x["index"] for x in unresolved}:
            raise ValueError(f"order {n}: saved unresolved cohort differs from verdicts")
    return {
        "order": n, "connected_total": seen,
        "convergent": counts["CONVERGENT"], "divergent": counts["DIVERGENT"],
        "indeterminate": counts["INDETERMINATE"],
    }, unresolved


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--no-expect-snub", action="store_true")
    args = ap.parse_args()
    manifest = json.loads((args.run_dir / "manifest.json").read_text(encoding="utf-8"))
    minimum = manifest["min_order"]
    maximum = manifest["max_order"]
    batch_size = manifest["batch_size"]
    summaries: list[dict] = []
    unresolved: list[dict] = []
    for n in range(minimum, maximum + 1):
        summary, rest = verify_order(args.run_dir / f"order{n}", n, batch_size)
        summaries.append(summary)
        unresolved.extend(rest)
        print(f"n={n}: {summary['connected_total']} connected types; "
              f"{summary['convergent']} convergent; {summary['divergent']} divergent; "
              f"{summary['indeterminate']} indeterminate", flush=True)

    # For >8, classifications remain open; do not demand the snub-only pattern.
    baseline_observed = [
        {key: item[key] for key in ("order", "index", "graph6")}
        for item in unresolved if item["order"] <= 8
    ]
    baseline_expected = [SNUB] if minimum <= 8 <= maximum else []
    expectation_met = baseline_observed == baseline_expected
    result = {
        "manifest": manifest,
        "scope": "connected unlabeled simple graphs only",
        "orders": summaries,
        "unresolved": unresolved,
        "expected_unresolved_through_8": baseline_expected,
        "baseline_expectation_met": expectation_met,
    }
    destination = args.run_dir / "summary.json"
    tmp = destination.with_suffix(".partial")
    tmp.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, destination)
    print("Validated census summary:", destination)
    if unresolved:
        print("Unresolved connected graphs:")
        for row in unresolved[:30]:
            print(f"  n={row['order']} i={row['index']} graph6={row['graph6']}: {row['reason']}")
        if len(unresolved) > 30:
            print(f"  ... {len(unresolved)-30} more (see summary.json)")
    if not expectation_met:
        print("WARNING: orders through 8 differ from historical snub-only expectation", file=sys.stderr)
        if not args.no_expect_snub:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
