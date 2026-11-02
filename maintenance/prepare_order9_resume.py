#!/usr/bin/env python3
"""Import completed order-9 chunks into a NEW, explicitly mixed-provenance run.

Narrow, audited migration for a clockwork-recognizer correction which changes
only a path that previously raised, leaving successful classifications intact.
The old run is never modified, and only chunks with valid .done files are
copied. The new run's manifest will hash chunk_lineage.json, and its validator
checks every inherited file against its recorded digest.

Run after updating the pinned pycliques revision, before starting the new run.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate import iter_verdicts  # noqa: E402

OLD_COMMIT = "ce401a3e7c52d11392a8a5d04e39e48e9486328d"
FIXED_COMMIT = "da9ef9b0b76648d221b687487483da56603ccdff"
TOTAL = 261080


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def check_completed_chunk(folder: Path, start: int, end: int) -> dict[str, str]:
    name = f"{start:08d}-{end:08d}"
    paths = [
        Path("order9") / "chunks" / f"{name}.tsv.gz",
        Path("order9") / "unresolved_chunks" / f"{name}.tsv.gz",
        Path("order9") / "completed" / f"{name}.done",
    ]
    log = Path("order9") / "logs" / f"{name}.log"
    if (folder / log).is_file():
        paths.append(log)
    for path in paths:
        require((folder / path).is_file(), f"Missing complete chunk file: {path}")

    require(
        (folder / paths[2]).read_text(encoding="ascii") == f"{start}\t{end}\n",
        f"Incorrect completion marker for {name}",
    )
    status_by_index: dict[int, str] = {}
    for index, status, reason in iter_verdicts(folder / paths[0]):
        require(index == start + len(status_by_index), f"Invalid index in chunk {name}")
        require(index <= end, f"Chunk {name} extends beyond its boundary")
        status_by_index[index] = status
    require(len(status_by_index) == end - start + 1, f"Chunk {name} is incomplete")

    unresolved_indices: set[int] = set()
    with gzip.open(folder / paths[1], "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            fields = line.split()
            require(len(fields) >= 3, f"Malformed unresolved row in {name}")
            index = int(fields[0])
            require(index not in unresolved_indices, f"Duplicate unresolved row {index}")
            unresolved_indices.add(index)
    expected_unresolved = {i for i, status in status_by_index.items() if status == "INDETERMINATE"}
    require(
        unresolved_indices == expected_unresolved,
        f"Unresolved sidecar differs from verdicts in {name}",
    )
    return {path.as_posix(): sha256(folder / path) for path in paths}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old", type=Path, default=ROOT / "runs" / "order9-bound30")
    parser.add_argument(
        "--new", type=Path,
        default=ROOT / "runs" / "order9-bound30-after-clockwork-fix",
    )
    args = parser.parse_args()
    old, new = args.old.resolve(), args.new.resolve()
    require(old.is_dir(), f"Old run not found: {old}")
    require(not new.exists(), f"New run path must not exist: {new}")
    require(old != new, "Old and new run paths must differ")

    old_manifest_path = old / "manifest.json"
    old_manifest = json.loads(old_manifest_path.read_text(encoding="utf-8"))
    for key, value in (
        ("min_order", 9), ("max_order", 9), ("batch_size", 10000), ("bound", 30),
        ("upstream_commit", OLD_COMMIT),
    ):
        require(old_manifest.get(key) == value, f"Old manifest {key} is not {value!r}")
    require(
        old_manifest.get("scope") == "connected unlabeled simple graphs only",
        "Old run has unexpected graph scope",
    )

    source = ROOT / ".deps" / "pycliques-project"
    head = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    pinned = (ROOT / "config" / "pycliques_commit.txt").read_text().strip()
    require(head == FIXED_COMMIT == pinned, "Install the exact fixed commit first")

    from pyg6data.lists import _dict_connected, _get_data_file_path

    actual_dataset_sha = sha256(_get_data_file_path(_dict_connected[9]))
    require(
        old_manifest.get("bundled_connected_graph6_sha256", {}).get("9")
        == actual_dataset_sha,
        "The bundled connected order-9 graph6 dataset has changed",
    )
    uvlock_sha = sha256(source / "uv.lock")
    require(
        old_manifest.get("upstream_uv_lock_sha256") == uvlock_sha,
        "The upstream uv.lock differs; do not reuse old batches",
    )

    batch = 10000
    completed: list[dict] = []
    encountered_gap = False
    for start in range(0, TOTAL, batch):
        end = min(TOTAL - 1, start + batch - 1)
        name = f"{start:08d}-{end:08d}"
        marker = old / "order9" / "completed" / f"{name}.done"
        if not marker.is_file():
            encountered_gap = True
            continue
        require(not encountered_gap, "Completed source chunks are not consecutive from index zero")
        hashes = check_completed_chunk(old, start, end)
        completed.append({"start": start, "end": end, "sha256": hashes})

    require(completed, "There are no complete source chunks to import")
    require(completed[-1]["end"] < TOTAL - 1, "Old run is already complete")
    imported_count = sum(e["end"] - e["start"] + 1 for e in completed)
    lineage = {
        "schema": 1,
        "order": 9,
        "bound": 30,
        "batch_size": batch,
        "original_connected_dataset_sha256": actual_dataset_sha,
        "original_manifest_sha256": sha256(old_manifest_path),
        "old_upstream_commit": OLD_COMMIT,
        "new_upstream_commit": FIXED_COMMIT,
        "reason": (
            "The fixed fast clockwork recognizer rejects invalid cross-segment "
            "triangles before reporting a decomposition; earlier successful "
            "classifications were not changed. All inherited bytes are preserved."
        ),
        "imported_graph_count": imported_count,
        "imported": completed,
    }

    new.parent.mkdir(parents=True, exist_ok=True)
    partial = new.with_name(new.name + ".partial-migration")
    require(not partial.exists(), f"Remove or inspect incomplete migration: {partial}")
    try:
        partial.mkdir()
        for entry in completed:
            for name in entry["sha256"]:
                src = old / name
                dest = partial / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                require(sha256(dest) == entry["sha256"][name], f"Copy checksum mismatch: {name}")
        (partial / "chunk_lineage.json").write_text(
            json.dumps(lineage, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(partial, new)
    except Exception:
        shutil.rmtree(partial, ignore_errors=True)
        raise

    print(f"Copied and audited {len(completed)} completed chunks ({imported_count} graphs).")
    print(f"Original run left untouched: {old}")
    print(f"New run ready for remaining {TOTAL - imported_count} graphs: {new}")
    print("The new run's manifest will record the lineage-file SHA-256.")
    print("Now run MIN_ORDER=9 MAX_ORDER=9 BATCH_SIZE=10000 RUN_DIR=... bash scripts/run_census.sh")


if __name__ == "__main__":
    main()
