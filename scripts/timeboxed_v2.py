"""Resumable, five-graph chunks of order-10 classification at bound 120.

Only unresolved original ten-vertex graphs with NO dominated vertex qualify,
including those whose previous status was conjecture-dependent.

Each classification runs in an isolated worker with a 600-second wall-clock
timeout and a 6144 MiB address-space limit (Linux). Results are immutable
JSON records; a time limit or resource failure proves no clique behavior.
Run 'bash scripts/stage.sh 10 bound120-timeboxed-v2' repeatedly for successive
five-graph batches, or append a zero-based batch index.
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

import networkx as nx

from pycliques.dominated import find_dominated_vertex

from timeboxed_trace_v2 import summarize_events
import staged


ROOT = Path(__file__).resolve().parents[1]
STAGE = "bound120-timeboxed-v2"
ORDER = 10
BATCH_SIZE = 5
TIMEOUT_SECONDS = 600
CLIQUE_BOUND = 120
MEMORY_MIB = 6144
FINAL_STATUSES = {
    "CONVERGENT", "DIVERGENT", "INDETERMINATE",
    "BOUND_EXCEEDED", "TIMEOUT", "ERROR",
}
PROVEN = {"CONVERGENT", "DIVERGENT"}


def cohort() -> tuple[dict[int, dict], dict[int, dict]]:
    """Freeze the original source-index cohort, ignoring this stage's records."""
    remaining, origins, source = staged.active(ORDER, include_timeboxed=False)
    eligible = {}
    for index, row in sorted(remaining.items()):
        graph = nx.from_graph6_bytes(row["graph6"].encode("ascii"))
        if len(graph) != 10:
            raise ValueError(f"Original source graph is not order 10: {index}")
        if find_dominated_vertex(graph) is None:
            # Defense in depth: the historical paring count must agree too.
            if origins[index].split()[1] != "10":
                raise ValueError(f"Original dominated-vertex mismatch at {index}")
            eligible[index] = row
    return eligible, source


def predecessor_hashes() -> dict[str, str]:
    names = ("c10", "homotopy", "s1divergence",
             "bound70", "bound120", "easycovers")
    checksums = {}
    for name in names:
        summary_path = staged.stage_dir(ORDER, name) / "summary.json"
        if not summary_path.is_file():
            raise ValueError(f"Complete and commit stage {name} first")
        checksums[name + "_summary_sha256"] = staged.filehash(summary_path)
    return checksums


def expected_manifest(eligible: dict[int, dict]) -> dict:
    return {
        "schema": 1,
        "order": ORDER,
        "stage": STAGE,
        "upstream_commit": staged.current_pin(),
        "initial_summary_sha256": staged.filehash(
            ROOT / "runs" / "order10" / "initial" / "summary.json"
        ),
        "surface_registry_sha256": staged.filehash(staged.reference_file()),
        "staged_script_sha256": staged.filehash(Path(staged.__file__)),
        "runner_sha256": staged.filehash(Path(__file__)),
        "worker_sha256": staged.filehash(ROOT / "scripts" / "timeboxed_worker_v2.py"),
        "trace_sha256": staged.filehash(ROOT / "scripts" / "timeboxed_trace_v2.py"),
        "bound": CLIQUE_BOUND,
        "timeout_seconds": TIMEOUT_SECONDS,
        "memory_mib": MEMORY_MIB,
        "batch_size": BATCH_SIZE,
        "indices": sorted(eligible),
        "selection": "Unresolved originals of order 10 with no dominated vertices; includes conjectured references",
        **predecessor_hashes(),
    }


def enforce_manifest(dest: Path, manifest: dict) -> None:
    """Never mix code versions, cohorts or limits within stage v2."""
    path = dest / "manifest.json"
    if path.exists():
        if json.loads(path.read_text(encoding="utf-8")) != manifest:
            raise ValueError(
                "Cannot resume v2 stage with changed dependency, code, "
                "cohort or resource settings"
            )
    else:
        if dest.exists() and any(dest.iterdir()):
            raise ValueError("v2 stage directory exists without provenance manifest")
        staged.write_atomic(path, manifest)


def child_memory_limit() -> None:
    """Linux process-address-space cap, applied before imports in the worker."""
    limit = MEMORY_MIB * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))


def terminate_group(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        os.killpg(proc.pid, signal.SIGKILL)
    proc.wait()


def run_one(graph6: str, dest: Path) -> dict:
    """Wall-time-bounded classification; no subprocess is left on timeout."""
    fd, temp_path = tempfile.mkstemp(prefix="worker_", suffix=".partial", dir=dest)
    os.close(fd)
    fd_diag, diagnostic_path = tempfile.mkstemp(
        prefix="worker_progress_", suffix=".partial", dir=dest
    )
    os.close(fd_diag)
    start = time.monotonic()
    env = os.environ.copy()
    env.update({"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1",
                "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"})
    command = [sys.executable, str(ROOT / "scripts" / "timeboxed_worker_v2.py"),
               graph6, temp_path, diagnostic_path]
    try:
        with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as log:
            proc = subprocess.Popen(
                command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=log, cwd=ROOT, env=env,
                start_new_session=True, preexec_fn=child_memory_limit,
            )
            try:
                proc.wait(timeout=TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                terminate_group(proc)
                return {
                    "status": "TIMEOUT", "verdict": "INDETERMINATE",
                    "reason": f"Worker exceeded {TIMEOUT_SECONDS} seconds of wall time",
                    "bound": CLIQUE_BOUND,
                    "elapsed_seconds": round(time.monotonic() - start, 3),
                    **summarize_events(diagnostic_path),
                }
            except BaseException:
                terminate_group(proc)
                raise
            elapsed = round(time.monotonic() - start, 3)
            if proc.returncode == 0:
                try:
                    result = json.loads(Path(temp_path).read_text(encoding="utf-8"))
                    if result.get("status") not in FINAL_STATUSES - {"TIMEOUT", "ERROR"}:
                        raise ValueError("Worker produced an invalid verdict")
                    if result.get("bound") != CLIQUE_BOUND:
                        raise ValueError("Worker used an unexpected bound")
                    result["elapsed_seconds"] = elapsed
                    result.update(summarize_events(diagnostic_path))
                    return result
                except (ValueError, OSError, TypeError) as exc:
                    failure = f"Invalid worker record: {exc}"
            else:
                failure = f"Worker exit status {proc.returncode}"
            log.seek(0)
            excerpt = log.read(4096)
            return {
                "status": "ERROR", "verdict": "INDETERMINATE",
                "bound": CLIQUE_BOUND, "elapsed_seconds": elapsed,
                "reason": failure,
                "stderr_excerpt": excerpt,
                **summarize_events(diagnostic_path),
            }
    finally:
        Path(temp_path).unlink(missing_ok=True)
        Path(diagnostic_path).unlink(missing_ok=True)


def verify_saved(source: dict[int, dict], eligible: dict[int, dict]) -> dict[int, dict]:
    records = staged.checked_records(ORDER, STAGE, source)
    if set(records) - set(eligible):
        raise ValueError("Timeboxed results contain non-eligible graph indices")
    return records


def write_progress(dest: Path, eligible: dict[int, dict], records: dict[int, dict]) -> None:
    counts = Counter(row["status"] for row in records.values())
    progress = {
        "processed": len(records),
        "total": len(eligible),
        "counts": dict(sorted(counts.items())),
        "batches_total": (len(eligible) + BATCH_SIZE - 1) // BATCH_SIZE,
        "batches_complete": sum(
            all(index in records for index in list(sorted(eligible))[a:a+BATCH_SIZE])
            for a in range(0, len(eligible), BATCH_SIZE)
        ),
    }
    staged.write_atomic(dest / "progress.json", progress)
    if len(records) == len(eligible):
        staged.write_atomic(dest / "summary.json", {
            "manifest": json.loads((dest / "manifest.json").read_text(encoding="utf-8")),
            "processed": len(records),
            "counts": dict(sorted(counts.items())),
        })


def run(batch_arg: str = "next") -> None:
    if not staged.reference_file().is_file():
        raise ValueError("Missing order-9 conjectured surface registry")
    # Every classification worker registers the same pinned reference registry.
    from surface_refs import load_surface_references
    load_surface_references()

    eligible, source = cohort()
    dest = staged.stage_dir(ORDER, STAGE)
    manifest = expected_manifest(eligible)

    # Prevent two Codespace processes claiming the same batch simultaneously.
    lock_dir = ROOT / ".deps"
    lock_dir.mkdir(exist_ok=True)
    with (lock_dir / "bound120-timeboxed-v2.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Another bound120-timeboxed run is active") from exc
        enforce_manifest(dest, manifest)
        (dest / "records").mkdir(exist_ok=True)
        (dest / "batches").mkdir(exist_ok=True)
        saved = verify_saved(source, eligible)
        indices = manifest["indices"]
        batches = [
            indices[pos:pos + BATCH_SIZE]
            for pos in range(0, len(indices), BATCH_SIZE)
        ]
        if batch_arg == "next":
            batch_number = next(
                (i for i, b in enumerate(batches) if any(j not in saved for j in b)),
                None
            )
        else:
            batch_number = int(batch_arg)
            if not 0 <= batch_number < len(batches):
                raise ValueError(f"Batch must be between 0 and {len(batches)-1}")
        if batch_number is None:
            write_progress(dest, eligible, saved)
            print(f"All {len(indices)} eligible graphs have been processed.")
            staged.refresh(ORDER)
            return
        selected = batches[batch_number]
        print(
            f"Stage {STAGE}: batch {batch_number}/{len(batches)-1}, "
            f"source indices {selected}, budget {TIMEOUT_SECONDS}s per graph",
            flush=True,
        )
        for position, index in enumerate(selected, start=1):
            if index in saved:
                continue
            graph6 = eligible[index]["graph6"]
            print(f"[{position}/{len(selected)}] index={index}", flush=True)
            record = {
                "index": index,
                "graph6": graph6,
                "batch": batch_number,
                "implementation_sha256": {
                    "runner": staged.filehash(Path(__file__)),
                    "worker": staged.filehash(ROOT / "scripts" / "timeboxed_worker_v2.py")
                        if (ROOT / "scripts" / "timeboxed_worker_v2.py").is_file() else None,
                    "trace": staged.filehash(ROOT / "scripts" / "timeboxed_trace_v2.py")
                        if (ROOT / "scripts" / "timeboxed_trace_v2.py").is_file() else None,
                },
                **run_one(graph6, dest),
            }
            staged.write_atomic(dest / "records" / f"{index:08d}.json", record)
            saved[index] = record
            print(f"  result: {record['status']} ({record['elapsed_seconds']:.2f}s)",
                  flush=True)
        batch_rows = {i: saved[i]["status"] for i in selected}
        staged.write_atomic(dest / "batches" / f"{batch_number:05d}.json", {
            "batch": batch_number,
            "indices": selected,
            "statuses": batch_rows,
            "counts": dict(sorted(Counter(batch_rows.values()).items())),
        })
        write_progress(dest, eligible, saved)
        outcome = staged.refresh(ORDER)
        print(
            f"Batch complete: {len(saved)}/{len(indices)} processed, "
            f"{outcome['remaining']} order-10 graphs still indeterminate",
            flush=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", nargs="?", default="next",
                        help="next (default) or zero-based batch number")
    args = parser.parse_args()
    if args.batch != "next" and (
        not args.batch.isascii() or not args.batch.isdecimal()
    ):
        parser.error("Batch must be 'next' or a nonnegative integer")
    run(args.batch)


if __name__ == "__main__":
    main()
