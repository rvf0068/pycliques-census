"""Resumable timeboxed order-9 stage, using an isolated new pycliques revision.

The historical stage files and the *existing* census pin remain unchanged.
The 54 still-undecided order-9 graphs are frozen from historical stages.
Each worker is process-isolated and gets 120 seconds/4096 MiB.
The 18 nonconjectural cases are scheduled first; 36 conditional cases can
then be processed separately. A result stopped by a bound, limit or timeout
is never interpreted as a proof.

Use:
  .deps/pycliques-project-order9/.venv/bin/python scripts/order9_bound200.py
  .deps/pycliques-project-order9/.venv/bin/python scripts/order9_bound200.py --all
  .deps/pycliques-project-order9/.venv/bin/python scripts/order9_bound200.py \
    --group conjectured --all
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import resource
import signal
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

import staged
from timeboxed_trace_v3 import summarize_events_v3

ROOT = Path(__file__).resolve().parents[1]
STAGE = "bound200-timeboxed"
DEPENDENCY = ROOT / ".deps" / "pycliques-project-order9"
UPSTREAM_SHA = "d6753ac445b57740d90997008aa96830d4fc117c"
ORDER = 9
BOUND = 200
TIMEOUT_SECONDS = 120
MEMORY_MIB = 4096
BATCH_SIZE = 3
STATUSES = {
    "CONVERGENT", "DIVERGENT", "INDETERMINATE",
    "BOUND_EXCEEDED", "TIMEOUT", "ERROR",
}
WORKER = ROOT / "scripts" / "order9_bound200_worker.py"
TRACE = ROOT / "scripts" / "timeboxed_trace_v3.py"
CERT = ROOT / "scripts" / "certificate_records_v3.py"


def check_dependency() -> None:
    revision = subprocess.check_output(
        ["git", "-C", str(DEPENDENCY), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    if revision != UPSTREAM_SHA:
        raise RuntimeError(
            f"Order-9 stage requires isolated pycliques {UPSTREAM_SHA}; "
            f"found {revision}. Do not update the historical dependency pin."
        )
    # Enforce the intended isolated environment, not the historical .venv.
    expected_python = DEPENDENCY / ".venv" / "bin" / "python"
    if Path(sys.executable).resolve() != expected_python.resolve():
        raise RuntimeError(f"Run with {expected_python}, not {sys.executable}")


def cohort() -> tuple[dict[int, dict], dict[int, dict], dict[int, str]]:
    remaining, origins, source = staged.active(ORDER)
    if len(remaining) != 54:
        raise ValueError(
            f"Expected 54 historical remaining order-9 graphs, found {len(remaining)}; "
            "inspect predecessor stages before starting a new manifest."
        )
    groups = {}
    for i, row in remaining.items():
        group = (
            "conjectured"
            if origins[i].split()[4] == "conjectured_divergent"
            else "nonconjectural"
        )
        groups[i] = group
        if len(row["graph6"]) == 0:
            raise ValueError(f"Empty source graph6 for index {i}")
    if Counter(groups.values()) != {"conjectured": 36, "nonconjectural": 18}:
        raise ValueError(f"Historical cohort differs from expected split: {Counter(groups.values())}")
    return remaining, source, groups


def manifest(remaining: dict, groups: dict) -> dict:
    files = {
        "runner": Path(__file__),
        "worker": WORKER,
        "trace": TRACE,
        "trace_v2_dependency": ROOT / "scripts" / "timeboxed_trace_v2.py",
        "certificate": CERT,
        "staged": Path(staged.__file__),
        "surface_refs": ROOT / "scripts" / "surface_refs.py",
        "initial_summary": ROOT / "runs" / "order9" / "initial" / "summary.json",
        "c10_summary": ROOT / "runs" / "order9" / "c10" / "summary.json",
        "bound60_summary": ROOT / "runs" / "order9" / "bound60" / "summary.json",
        "bound70_summary": ROOT / "runs" / "order9" / "bound70" / "summary.json",
        "dependency_lock": DEPENDENCY / "uv.lock",
    }
    return {
        "schema": 1, "order": ORDER, "stage": STAGE,
        "new_upstream_commit": UPSTREAM_SHA,
        "historical_pin_untouched": True,
        "source_sha256": {k: staged.filehash(p) for k, p in files.items()},
        "bound": BOUND, "tries": 9, "retraction_depth": 2,
        "timeout_seconds": TIMEOUT_SECONDS, "memory_mib": MEMORY_MIB,
        "batch_size": BATCH_SIZE,
        "indices": sorted(remaining),
        "group_by_index": {str(k): groups[k] for k in sorted(groups)},
        "selection": "All 54 historical order-9 active graphs, 18 nonconjectural then 36 conditional",
        "clockwork_retract_search": "separate optional pilot only",
    }


def saved_records(folder: Path, remaining: dict, manifest_data: dict) -> dict[int, dict]:
    if not (folder / "manifest.json").exists():
        if folder.exists() and any(folder.iterdir()):
            raise RuntimeError("Stage directory exists without an immutable manifest")
        staged.write_atomic(folder / "manifest.json", manifest_data)
    elif json.loads((folder / "manifest.json").read_text()) != manifest_data:
        raise RuntimeError("Stage manifest differs; use a NEW stage name for changed code/limits")
    result = {}
    for file in sorted((folder / "records").glob("*.json")):
        row = json.loads(file.read_text())
        index = row.get("index")
        if (index not in remaining or file.name != f"{index:08d}.json"
                or row.get("graph6") != remaining[index]["graph6"]
                or row.get("status") not in STATUSES
                or row.get("bound") != BOUND
                or index in result):
            raise ValueError(f"Invalid previously saved stage record: {file}")
        result[index] = row
    return result


def memory_limit() -> None:
    size = MEMORY_MIB * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (size, size))


def classify_one(graph6: str, destination: Path) -> dict:
    with tempfile.TemporaryDirectory(dir=destination, prefix="run_") as tmp:
        tmp_path = Path(tmp)
        output = tmp_path / "out.json"
        journal = tmp_path / "journal.jsonl"
        start = time.monotonic()
        env = os.environ.copy()
        env.update(
            OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1",
            MKL_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1",
        )
        with (tmp_path / "stderr.txt").open("w+") as log:
            proc = subprocess.Popen(
                [sys.executable, str(WORKER), graph6, str(output), str(journal)],
                cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=log, env=env,
                start_new_session=True, preexec_fn=memory_limit,
            )
            try:
                proc.wait(timeout=TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                if proc.poll() is None:
                    os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
                result = {
                    "status": "TIMEOUT", "verdict": "INDETERMINATE",
                    "reason": f"Wall-clock limit {TIMEOUT_SECONDS} seconds exceeded",
                }
            else:
                if proc.returncode == 0:
                    try:
                        result = json.loads(output.read_text())
                        if result.get("status") not in STATUSES - {"TIMEOUT", "ERROR"}:
                            raise ValueError("Malformed successful worker response")
                        if result.get("bound") != BOUND:
                            raise ValueError("Worker used a different bound")
                    except (OSError, ValueError, TypeError) as exc:
                        result = {
                            "status": "ERROR", "verdict": "INDETERMINATE",
                            "reason": f"Invalid worker result: {exc}",
                        }
                else:
                    result = {
                        "status": "ERROR", "verdict": "INDETERMINATE",
                        "reason": f"Worker failed with exit {proc.returncode}",
                    }
                if result["status"] == "ERROR":
                    log.seek(0)
                    result["stderr_excerpt"] = log.read(2000)
        result.update(
            bound=BOUND,
            elapsed_seconds=round(time.monotonic() - start, 3),
        )
        result.update(
            summarize_events_v3(str(journal)) if journal.exists()
            else {"diagnostic_schema": 3, "methods_tried": [], "iterates": []}
        )
        return result


def run(group: str, *, all_batches: bool = False) -> None:
    check_dependency()
    remaining, source, groups = cohort()
    folder = ROOT / "runs" / "order9" / STAGE
    expected = manifest(remaining, groups)
    folder.mkdir(parents=True, exist_ok=True)
    lock_dir = ROOT / ".deps"
    lock_dir.mkdir(exist_ok=True)
    with (lock_dir / "bound200-order9.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        saved = saved_records(folder, remaining, expected)
        (folder / "records").mkdir(exist_ok=True)
        indexed = sorted(i for i in remaining if groups[i] == group)
        batches = [indexed[x:x+BATCH_SIZE] for x in range(0, len(indexed), BATCH_SIZE)]
        while True:
            todo = next(
                (k for k, batch in enumerate(batches)
                 if any(i not in saved for i in batch)),
                None,
            )
            if todo is None:
                break
            print(f"order9 {STAGE} {group}: batch {todo+1}/{len(batches)}", flush=True)
            for index in batches[todo]:
                if index in saved:
                    continue
                row = {
                    "index": index,
                    "graph6": remaining[index]["graph6"],
                    "group": group,
                    **classify_one(remaining[index]["graph6"], folder),
                }
                staged.write_atomic(folder / "records" / f"{index:08d}.json", row)
                saved[index] = row
                print(f"  {index}: {row['status']} ({row['elapsed_seconds']} sec)",
                      flush=True)
            progress = {
                "processed": len(saved), "total": len(remaining),
                "counts": dict(sorted(Counter(x["status"] for x in saved.values()).items())),
                "nonconjectural_processed": sum(
                    i in saved for i in remaining if groups[i] == "nonconjectural"
                ),
                "conjectured_processed": sum(
                    i in saved for i in remaining if groups[i] == "conjectured"
                ),
            }
            staged.write_atomic(folder / "progress.json", progress)
            if len(saved) == len(remaining):
                staged.write_atomic(folder / "summary.json", {
                    "manifest": expected, **progress,
                })
            if not all_batches:
                break
        print(f"Completed group {group}: {sum(i in saved for i in indexed)}/{len(indexed)}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--group", choices=("nonconjectural", "conjectured"),
                   default="nonconjectural")
    p.add_argument("--all", action="store_true",
                   help="Complete all batches of chosen group (resumable)")
    args = p.parse_args()
    run(args.group, all_batches=args.all)


if __name__ == "__main__":
    main()
