"""Resumable local v3 benchmark of 153 order-10 graphs without an S^2 summand.

Only one 2-GiB worker runs at a time, for at most 120 seconds per graph.
The 120-clique bound and five-graph batch size are frozen in the manifest.
All original census results and the historical dependency pin remain intact.
"""
from __future__ import annotations

import argparse
from collections import Counter
import fcntl
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import tempfile
import time

import networkx as nx

import staged
from timeboxed_trace_v3 import summarize_events_v3

ROOT = Path(__file__).resolve().parents[1]
ORDER = 10
STAGE = "bound120-timeboxed-v3"
BATCH_SIZE = 5
TIMEOUT_SECONDS = 120
MEMORY_MIB = 2048
CLIQUE_BOUND = 120
PROVEN = {"CONVERGENT", "DIVERGENT"}
STATUSES = PROVEN | {"INDETERMINATE", "BOUND_EXCEEDED", "TIMEOUT", "ERROR"}
COHORT = ROOT / "config" / "homotopy_no_s2_order10.tsv"
V3_PIN = ROOT / "config" / "pycliques_commit_v3.txt"
V3_SOURCE = ROOT / ".deps" / "pycliques-project-v3"


def current_v3_pin() -> str:
    pin = V3_PIN.read_text(encoding="ascii").strip()
    head = subprocess.check_output(
        ["git", "-C", str(V3_SOURCE), "rev-parse", "HEAD"], text=True
    ).strip()
    if len(pin) != 40 or head != pin:
        raise ValueError("Separate v3 upstream checkout does not match its pinned SHA")
    expected = (V3_SOURCE / ".venv" / "bin" / "python").resolve()
    if Path(sys.executable).resolve() != expected:
        raise ValueError("Run with .venv-v3/bin/python, not the historical .venv")
    return head


def cohort() -> tuple[dict[int, dict], dict[int, dict]]:
    """Check the immutable 153-case table against the committed prior stages."""
    remaining, _origins, source = staged.active(ORDER)
    root_rows = {}
    for line in (ROOT / "indeterminate_order_10.txt").read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            words = line.split()
            root_rows[int(words[0])] = words[2]
    if len(remaining) != 8648 or set(root_rows) != set(remaining):
        raise ValueError("Historical unresolved baseline changed; review the frozen v3 cohort")
    rows = [x for x in COHORT.read_text(encoding="utf-8").splitlines()
            if x and not x.startswith("#")]
    if not rows or rows[0] != "index\tpared_graph6\ttype":
        raise ValueError("Invalid frozen cohort header")
    eligible = {}
    counts = Counter()
    for line in rows[1:]:
        index_s, pared_graph6, label = line.split("\t")
        index = int(index_s)
        if index in eligible or index not in remaining:
            raise ValueError(f"Duplicate or no longer unresolved source index: {index}")
        if root_rows[index] != pared_graph6:
            raise ValueError(f"Changed pared graph at original index {index}")
        if label not in {"S1", "S3", "S1+S3"}:
            raise ValueError(f"Unknown certified homotopy label {label}")
        if nx.from_graph6_bytes(remaining[index]["graph6"].encode("ascii")).order() != 10:
            raise ValueError(f"Incorrect source order at index {index}")
        eligible[index] = remaining[index]
        counts[label] += 1
    if len(eligible) != 153 or dict(counts) != {"S1": 115, "S3": 35, "S1+S3": 3}:
        raise ValueError(f"Incorrect frozen cohort: {counts}")
    return eligible, source


def manifest(eligible: dict[int, dict]) -> dict:
    previous = ROOT / "runs" / "order10"
    prerequisites = ("c10", "homotopy", "s1divergence",
                     "bound70", "bound120", "easycovers", "bound120-timeboxed-v2")
    hashes = {}
    for name in prerequisites:
        path = previous / name / "summary.json"
        if not path.is_file():
            raise ValueError(f"Missing completed historical stage: {name}")
        hashes[name + "_summary_sha256"] = staged.filehash(path)
    files = {
        "cohort_sha256": COHORT,
        "historical_working_list_sha256": ROOT / "indeterminate_order_10.txt",
        "historical_staged_sha256": ROOT / "scripts" / "staged.py",
        "runner_sha256": Path(__file__),
        "worker_sha256": ROOT / "scripts" / "timeboxed_worker_v3.py",
        "trace_sha256": ROOT / "scripts" / "timeboxed_trace_v3.py",
        "trace_base_sha256": ROOT / "scripts" / "timeboxed_trace_v2.py",
        "certificate_sha256": ROOT / "scripts" / "certificate_records_v3.py",
    }
    return {
        "schema": 3, "order": ORDER, "stage": STAGE,
        "upstream_commit": current_v3_pin(),
        "historical_upstream_commit": (ROOT / "config" / "pycliques_commit.txt")
            .read_text(encoding="ascii").strip(),
        "initial_summary_sha256": staged.filehash(previous / "initial" / "summary.json"),
        "batch_size": BATCH_SIZE,
        "timeout_seconds": TIMEOUT_SECONDS,
        "memory_mib": MEMORY_MIB,
        "bound": CLIQUE_BOUND,
        "retraction_depth": 2,
        "parallel_workers": 1,
        "indices": sorted(eligible),
        "selection": "Exactly the 153 still-unresolved order-10 original graphs with no S2 wedge summand",
        **{name: staged.filehash(path) for name, path in files.items()},
        **hashes,
    }


def ensure_manifest(folder: Path, meta: dict) -> None:
    path = folder / "manifest.json"
    if path.exists():
        if json.loads(path.read_text(encoding="utf-8")) != meta:
            raise ValueError("v3 resume refused: changed input, code, pin, or resource parameters")
    else:
        if folder.exists() and any(folder.iterdir()):
            raise ValueError("Existing v3 directory lacks a provenance manifest")
        staged.write_atomic(path, meta)


def saved_records(source: dict[int, dict], eligible: dict[int, dict]) -> dict[int, dict]:
    records = staged.checked_records(ORDER, STAGE, source)
    if set(records) - set(eligible):
        raise ValueError("v3 contains a record outside its frozen cohort")
    for index, row in records.items():
        if row.get("status") not in STATUSES or row.get("bound") != CLIQUE_BOUND:
            raise ValueError(f"Bad v3 result record at {index}")
        if row["status"] in PROVEN and (
            row.get("verdict") != row["status"]
            or row.get("proof_status") != "verified_chain"
            or not isinstance(row.get("proof"), dict)
        ):
            raise ValueError(f"Unverified positive result at {index}")
    return records


def worker_memory_limit() -> None:
    limit = MEMORY_MIB * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))


def kill_group(process: subprocess.Popen) -> None:
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGKILL)
    process.wait()


def run_one(graph6: str, folder: Path) -> dict:
    fno, output = tempfile.mkstemp(prefix="worker_", suffix=".partial", dir=folder)
    os.close(fno)
    jno, journal = tempfile.mkstemp(prefix="journal_", suffix=".partial", dir=folder)
    os.close(jno)
    begin = time.monotonic()
    env = os.environ.copy()
    env.update({name: "1" for name in (
        "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"
    )})
    cmd = [sys.executable, str(ROOT / "scripts" / "timeboxed_worker_v3.py"),
           graph6, output, journal]
    try:
        with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as errors:
            process = subprocess.Popen(
                cmd, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=errors, env=env, start_new_session=True,
                preexec_fn=worker_memory_limit,
            )
            try:
                process.wait(timeout=TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                kill_group(process)
                return {
                    "status": "TIMEOUT", "verdict": "INDETERMINATE",
                    "bound": CLIQUE_BOUND, "elapsed_seconds": round(time.monotonic()-begin, 3),
                    "reason": f"Worker exceeded {TIMEOUT_SECONDS} seconds",
                    **summarize_events_v3(journal),
                }
            except BaseException:
                kill_group(process)
                raise
            elapsed = round(time.monotonic() - begin, 3)
            if process.returncode == 0:
                try:
                    result = json.loads(Path(output).read_text(encoding="utf-8"))
                    if result["status"] not in STATUSES - {"TIMEOUT", "ERROR"}:
                        raise ValueError("Invalid worker status")
                    if result["bound"] != CLIQUE_BOUND:
                        raise ValueError("Worker used wrong clique bound")
                    result["elapsed_seconds"] = elapsed
                    result.update(summarize_events_v3(journal))
                    return result
                except (KeyError, TypeError, ValueError, OSError) as error:
                    failure = f"Invalid worker output: {error}"
            else:
                failure = f"Worker exit status {process.returncode}"
            errors.seek(0)
            return {
                "status": "ERROR", "verdict": "INDETERMINATE",
                "bound": CLIQUE_BOUND, "elapsed_seconds": elapsed,
                "reason": failure,
                "stderr_excerpt": errors.read(4096),
                **summarize_events_v3(journal),
            }
    finally:
        Path(output).unlink(missing_ok=True)
        Path(journal).unlink(missing_ok=True)


def write_progress(folder: Path, meta: dict, records: dict[int, dict]) -> None:
    counts = dict(sorted(Counter(r["status"] for r in records.values()).items()))
    indices = meta["indices"]
    complete_batches = sum(
        all(index in records for index in indices[pos:pos+BATCH_SIZE])
        for pos in range(0, len(indices), BATCH_SIZE)
    )
    progress = {
        "processed": len(records),
        "total": len(indices),
        "counts": counts,
        "complete_batches": complete_batches,
        "total_batches": (len(indices) + BATCH_SIZE - 1) // BATCH_SIZE,
    }
    staged.write_atomic(folder / "progress.json", progress)
    if len(records) == len(indices):
        staged.write_atomic(folder / "summary.json", {
            "manifest": meta, "processed": len(records), "counts": counts,
        })


def refresh_v3(records: dict[int, dict]) -> int:
    """Produce a v3-aware list without overwriting the historical root list."""
    source = ROOT / "indeterminate_order_10.txt"
    resolved = {i for i, r in records.items() if r["status"] in PROVEN}
    lines = [s for s in source.read_text(encoding="utf-8").splitlines()
             if s and not s.startswith("#")]
    remaining = [s for s in lines if int(s.split()[0]) not in resolved]
    output = ROOT / "indeterminate_order_10_v3.txt"
    prefix = [
        "# Order-10 unresolved cases, after independently verified v3 positives",
        f"# Remaining={len(remaining)} v3_proven={len(resolved)}",
        "# Derived from indeterminate_order_10.txt; historical stages are unchanged.",
    ]
    staged.write_atomic(output, "\n".join(prefix + remaining) + "\n")
    return len(remaining)


def run(batch: str) -> bool:
    eligible, source = cohort()
    meta = manifest(eligible)
    folder = staged.stage_dir(ORDER, STAGE)
    lockfolder = ROOT / ".deps"
    lockfolder.mkdir(exist_ok=True)
    with (lockfolder / "bound120-timeboxed-v3.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as e:
            raise RuntimeError("Another v3 census process already holds the lock") from e
        ensure_manifest(folder, meta)
        (folder / "records").mkdir(exist_ok=True)
        (folder / "batches").mkdir(exist_ok=True)
        records = saved_records(source, eligible)
        chunks = [meta["indices"][i:i+BATCH_SIZE]
                  for i in range(0, len(eligible), BATCH_SIZE)]
        if batch == "next":
            number = next((i for i, chunk in enumerate(chunks)
                           if any(index not in records for index in chunk)), None)
        else:
            number = int(batch)
            if number < 0 or number >= len(chunks):
                raise ValueError(f"Batch index must be in 0..{len(chunks)-1}")
        if number is None:
            write_progress(folder, meta, records)
            remaining = refresh_v3(records)
            print(f"All {len(eligible)} graphs processed; {remaining} still unresolved overall.")
            return False
        selected = chunks[number]
        print(f"v3 batch {number}/{len(chunks)-1}: {selected}; "
              f"{TIMEOUT_SECONDS}s, {MEMORY_MIB} MiB, clique bound {CLIQUE_BOUND}", flush=True)
        for index in selected:
            if index in records:
                continue
            print(f"  classify original index {index}", flush=True)
            record = {
                "index": index,
                "graph6": eligible[index]["graph6"],
                "batch": number,
                **run_one(eligible[index]["graph6"], folder),
            }
            staged.write_atomic(folder / "records" / f"{index:08d}.json", record)
            records[index] = record
            print(f"    {record['status']} in {record['elapsed_seconds']:.1f}s", flush=True)
        staged.write_atomic(folder / "batches" / f"{number:05d}.json", {
            "batch": number,
            "indices": selected,
            "statuses": {str(i): records[i]["status"] for i in selected},
        })
        write_progress(folder, meta, records)
        remaining = refresh_v3(records)
        print(f"Checkpoint: {len(records)}/{len(eligible)}; {remaining} unresolved overall.", flush=True)
        return len(records) < len(eligible)


def verify() -> None:
    from certificate_records_v3 import verify_record

    eligible, source = cohort()
    meta = manifest(eligible)
    folder = staged.stage_dir(ORDER, STAGE)
    if not (folder / "manifest.json").exists():
        raise ValueError("No v3 stage has started yet")
    ensure_manifest(folder, meta)
    records = saved_records(source, eligible)
    positives = [(i, record) for i, record in sorted(records.items())
                 if record["status"] in PROVEN]
    for index, record in positives:
        if not verify_record(record, verify_iterate=True):
            raise ValueError(f"Independent v3 certificate replay FAILED for index {index}")
    print(f"Independently replayed {len(positives)} positive v3 certificates.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", nargs="?", default="next",
                        help="plan, next, all, verify, or zero-based batch index")
    args = parser.parse_args()
    if args.batch not in {"plan", "next", "all", "verify"} and not args.batch.isdecimal():
        parser.error("Use plan, next, all, verify, or a nonnegative batch index")
    if args.batch == "plan":
        eligible, _ = cohort()
        print(f"Selected {len(eligible)} unresolved graphs; "
              f"{(len(eligible)+BATCH_SIZE-1)//BATCH_SIZE} batches; "
              f"{MEMORY_MIB} MiB, {TIMEOUT_SECONDS}s, bound {CLIQUE_BOUND}, one worker")
        print(f"v3 upstream pin: {current_v3_pin()}")
    elif args.batch == "verify":
        verify()
    elif args.batch == "all":
        while run("next"):
            pass
    else:
        run(args.batch)


if __name__ == "__main__":
    main()
