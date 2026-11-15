"""Resumable core-only benchmark of 35 pared order-9 isomorphism classes.

It never modifies previous census stages or propagates a core verdict to
the original ten-vertex member graphs. Each successful core certificate
must independently replay its complete pared clique-iterate chain.

CLI: bash scripts/core9.sh [plan|next|all|verify|BATCH_INDEX]
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

import core_isomorphism_index as indexer
from timeboxed_trace_v3 import summarize_events_v3
from timeboxed_v3 import current_v3_pin

ROOT = Path(__file__).resolve().parents[1]
STAGE = "core9-benchmark-v1"
FOLDER = ROOT / "runs" / "order10" / STAGE
CORE_INDEX = ROOT / "reports" / "order10_core_index_v1"
BATCH_SIZE = 5
CLIQUE_BOUND = 120
TIMEOUT_SECONDS = 120
MEMORY_MIB = 2048
PROVEN = {"CONVERGENT", "DIVERGENT"}
STATUSES = PROVEN | {"INDETERMINATE", "BOUND_EXCEEDED", "TIMEOUT", "ERROR"}


def write_atomic(path: Path, value: dict | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".partial")
    try:
        text = value if isinstance(value, str) else json.dumps(value, sort_keys=True, indent=2) + "\n"
        temp.write_text(text, encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def cohort() -> dict[int, dict]:
    """Recompute and verify the full frozen index before selecting 9-cores."""
    indexer.check_saved(CORE_INDEX, indexer.prepare())
    lines = (CORE_INDEX / "classes.tsv").read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != (
        "core_id\tcore_order\tcore_graph6\tmembers\tconjectured_members\tmember_indices"
    ):
        raise ValueError("Invalid frozen core index header")
    classes = {}
    seen = set()
    for line in lines[1:]:
        fields = line.split("\t")
        if len(fields) != 6:
            raise ValueError("Malformed core class entry")
        label, order, graph6, count, conjectured, members = fields
        i = int(label)
        originals = [int(x) for x in members.split(",")]
        if (
            len(originals) != int(count) or len(originals) != len(set(originals))
            or min(originals) != i or set(originals) & seen
            or not 0 <= int(conjectured) <= int(count)
        ):
            raise ValueError(f"Bad class membership at {i}")
        seen.update(originals)
        if int(order) != 9:
            continue
        graph = nx.from_graph6_bytes(graph6.encode("ascii"))
        if graph.order() != 9 or not nx.is_connected(graph) or i in classes:
            raise ValueError(f"Bad 9-core at {i}")
        classes[i] = {
            "graph6": graph6, "member_count": int(count),
            "member_indices": originals, "conjectured_members": int(conjectured),
        }
    if len(classes) != 35 or sum(x["member_count"] for x in classes.values()) != 4038:
        raise ValueError("Expected 35 order-nine cores representing 4038 originals")
    if len(seen) != 8533:
        raise ValueError("Incomplete frozen core-index partition")
    return dict(sorted(classes.items()))


def manifest(selected: dict[int, dict]) -> dict:
    paths = {
        "runner_sha256": ROOT / "scripts" / "core9_benchmark.py",
        "worker_sha256": ROOT / "scripts" / "core9_worker.py",
        "certificate_sha256": ROOT / "scripts" / "certificate_records_v3.py",
        "trace_sha256": ROOT / "scripts" / "timeboxed_trace_v3.py",
        "trace_base_sha256": ROOT / "scripts" / "timeboxed_trace_v2.py",
        "index_script_sha256": ROOT / "scripts" / "core_isomorphism_index.py",
        "index_manifest_sha256": CORE_INDEX / "manifest.json",
        "index_classes_sha256": CORE_INDEX / "classes.tsv",
        "index_assignments_sha256": CORE_INDEX / "assignments.tsv",
        "v3_summary_sha256": ROOT / "runs" / "order10" / "bound120-timeboxed-v3" / "summary.json",
    }
    return {
        "schema": 1, "stage": STAGE, "order": 10,
        "object": "completely_pared_nine_vertex_core",
        "selection": "All 35 post-v3 order-9 core representatives (4038 original members)",
        "upstream_commit": current_v3_pin(), "core_ids": sorted(selected),
        "member_counts": {str(i): x["member_count"] for i, x in selected.items()},
        "batch_size": BATCH_SIZE, "bound": CLIQUE_BOUND,
        "timeout_seconds": TIMEOUT_SECONDS, "memory_mib": MEMORY_MIB,
        "parallel_workers": 1, "retraction_depth": 2,
        "proof_scope": "representative_core_only; no original-member claims",
        **{field: indexer.file_hash(path) for field, path in paths.items()},
    }


def ensure_manifest(folder: Path, meta: dict) -> None:
    path = folder / "manifest.json"
    if path.exists():
        if json.loads(path.read_text(encoding="utf-8")) != meta:
            raise ValueError("Core9 resume refused: inputs, implementation or limits changed")
    else:
        if folder.exists() and any(folder.iterdir()):
            raise ValueError("Core9 output exists without provenance manifest")
        write_atomic(path, meta)


def check_positive(core_id: int, row: dict, graph6: str) -> None:
    from certificate_records_v3 import verify_record

    if (
        row.get("status") not in PROVEN
        or row.get("verdict") != row["status"]
        or row.get("proof_status") != "verified_chain"
        or row.get("graph6") != graph6
        or row.get("bound") != CLIQUE_BOUND
        or not isinstance(row.get("proof"), dict)
        or row["proof"].get("origin_graph6") != graph6
        or row["proof"].get("clique_bound") != CLIQUE_BOUND
        or not verify_record(row, verify_iterate=True)
    ):
        raise ValueError(f"Nonreplayable core certificate for {core_id}")


def saved_records(folder: Path, selected: dict[int, dict]) -> dict[int, dict]:
    records = {}
    for path in sorted((folder / "records").glob("*.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        i = row.get("core_id")
        if (
            not isinstance(i, int) or i in records or i not in selected
            or path.name != f"{i:08d}.json"
            or row.get("graph6") != selected[i]["graph6"]
            or row.get("member_count") != selected[i]["member_count"]
            or row.get("scope") != "pared_core_only"
            or row.get("bound") != CLIQUE_BOUND or row.get("status") not in STATUSES
        ):
            raise ValueError(f"Malformed saved core9 record: {path}")
        if row["status"] in PROVEN:
            check_positive(i, row, selected[i]["graph6"])
        elif row.get("verdict") not in {"INDETERMINATE", "CONVERGENT", "DIVERGENT"}:
            raise ValueError(f"Malformed nonpositive core9 verdict for {i}")
        records[i] = row
    return records


def memory_limit() -> None:
    limit = MEMORY_MIB * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))


def kill_group(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        os.killpg(proc.pid, signal.SIGKILL)
    proc.wait()


def run_one(graph6: str, folder: Path) -> dict:
    """Subprocess with strict time/virtual-memory limits and trace recovery."""
    out_fd, out = tempfile.mkstemp(prefix="core9_", suffix=".partial", dir=folder)
    os.close(out_fd)
    log_fd, journal = tempfile.mkstemp(prefix="core9_trace_", suffix=".partial", dir=folder)
    os.close(log_fd)
    begin = time.monotonic()
    env = os.environ.copy()
    env.update({k: "1" for k in (
        "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"
    )})
    cmd = [sys.executable, str(ROOT / "scripts" / "core9_worker.py"), graph6, out, journal]
    try:
        with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as errors:
            proc = subprocess.Popen(
                cmd, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=errors, env=env, start_new_session=True, preexec_fn=memory_limit,
            )
            try:
                proc.wait(timeout=TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                kill_group(proc)
                return {
                    "status": "TIMEOUT", "verdict": "INDETERMINATE",
                    "bound": CLIQUE_BOUND, "scope": "pared_core_only",
                    "elapsed_seconds": round(time.monotonic() - begin, 3),
                    "reason": f"Worker exceeded {TIMEOUT_SECONDS} seconds",
                    **summarize_events_v3(journal),
                }
            except BaseException:
                kill_group(proc)
                raise
            seconds = round(time.monotonic() - begin, 3)
            if proc.returncode == 0:
                try:
                    result = json.loads(Path(out).read_text(encoding="utf-8"))
                    if (
                        result.get("status") not in STATUSES - {"TIMEOUT", "ERROR"}
                        or result.get("bound") != CLIQUE_BOUND
                        or result.get("scope") != "pared_core_only"
                    ):
                        raise ValueError("Invalid worker status/bound/scope")
                    result["elapsed_seconds"] = seconds
                    result.update(summarize_events_v3(journal))
                    return result
                except (ValueError, TypeError, OSError) as error:
                    failure = f"Invalid worker result: {error}"
            else:
                failure = f"Worker exited with status {proc.returncode}"
            errors.seek(0)
            return {
                "status": "ERROR", "verdict": "INDETERMINATE",
                "bound": CLIQUE_BOUND, "scope": "pared_core_only",
                "elapsed_seconds": seconds, "reason": failure,
                "stderr_excerpt": errors.read(4096),
                **summarize_events_v3(journal),
            }
    finally:
        Path(out).unlink(missing_ok=True)
        Path(journal).unlink(missing_ok=True)


def report(folder: Path, records: dict[int, dict]) -> None:
    lines = [
        "# Order-9 pared-core benchmark", "",
        "These verdicts apply only to representative cores; none is a",
        "proof about the original 10-vertex member graphs.", "",
        "| Core ID | Members | Verdict | Seconds | Peak MiB | Last root iterate | Last criterion | Proof |",
        "|---:|---:|---|---:|---:|---:|---|---|",
    ]
    for i, row in sorted(records.items()):
        iters = row.get("iterates") or []
        methods = row.get("methods_tried") or []
        last_iterate = iters[-1].get("index", "-") if iters else "-"
        last_method = methods[-1].get("method", "-") if methods else "-"
        memory = row.get("peak_rss_kib")
        peak = f"{memory/1024:.1f}" if isinstance(memory, (int, float)) else "-"
        seconds = row.get("elapsed_seconds")
        elapsed = f"{seconds:.2f}" if isinstance(seconds, (int, float)) else "-"
        lines.append(
            f"| {i} | {row['member_count']} | {row['status']} | {elapsed} | "
            f"{peak} | {last_iterate} | {last_method} | {row.get('proof_status', '-')} |"
        )
    lines.extend(["", "## Counts", ""])
    for status, n in sorted(Counter(r["status"] for r in records.values()).items()):
        lines.append(f"- {status}: {n} distinct cores")
    lines.append("")
    write_atomic(folder / "report.md", "\n".join(lines))


def write_progress(folder: Path, meta: dict, records: dict[int, dict]) -> None:
    ids = meta["core_ids"]
    progress = {
        "processed": len(records), "total": len(ids),
        "counts": dict(sorted(Counter(r["status"] for r in records.values()).items())),
        "complete_batches": sum(
            all(i in records for i in ids[start:start+BATCH_SIZE])
            for start in range(0, len(ids), BATCH_SIZE)
        ),
        "total_batches": (len(ids) + BATCH_SIZE - 1) // BATCH_SIZE,
    }
    write_atomic(folder / "progress.json", progress)
    if len(records) == len(ids):
        write_atomic(folder / "summary.json", {"manifest": meta, **progress})
        report(folder, records)


def run(batch: str) -> bool:
    selected = cohort()
    meta = manifest(selected)
    lockdir = ROOT / ".deps"
    lockdir.mkdir(exist_ok=True)
    with (lockdir / "core9-benchmark-v1.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("Another core9 benchmark holds the lock") from error
        ensure_manifest(FOLDER, meta)
        (FOLDER / "records").mkdir(exist_ok=True)
        (FOLDER / "batches").mkdir(exist_ok=True)
        saved = saved_records(FOLDER, selected)
        chunks = [
            meta["core_ids"][j:j+BATCH_SIZE]
            for j in range(0, len(selected), BATCH_SIZE)
        ]
        if batch == "next":
            number = next(
                (j for j, chunk in enumerate(chunks) if any(i not in saved for i in chunk)),
                None,
            )
        else:
            number = int(batch)
            if number < 0 or number >= len(chunks):
                raise ValueError(f"Batch number must be 0..{len(chunks)-1}")
        if number is None:
            write_progress(FOLDER, meta, saved)
            print(f"All {len(selected)} core representatives processed.")
            return False
        items = chunks[number]
        print(
            f"Core9 batch {number}/{len(chunks)-1}: {items}; "
            f"{TIMEOUT_SECONDS}s, {MEMORY_MIB} MiB, bound {CLIQUE_BOUND}",
            flush=True,
        )
        for i in items:
            if i in saved:
                continue
            print(f"  core {i}, {selected[i]['member_count']} members", flush=True)
            row = {
                "core_id": i, "graph6": selected[i]["graph6"],
                "member_count": selected[i]["member_count"], "batch": number,
                **run_one(selected[i]["graph6"], FOLDER),
            }
            if row["status"] in PROVEN:
                check_positive(i, row, selected[i]["graph6"])
            write_atomic(FOLDER / "records" / f"{i:08d}.json", row)
            saved[i] = row
            print(f"    {row['status']} in {row['elapsed_seconds']:.2f}s", flush=True)
        write_atomic(FOLDER / "batches" / f"{number:05d}.json", {
            "batch": number, "core_ids": items,
            "statuses": {str(i): saved[i]["status"] for i in items},
        })
        write_progress(FOLDER, meta, saved)
        print(f"Checkpoint: {len(saved)}/{len(selected)} cores.", flush=True)
        return len(saved) < len(selected)


def verify() -> None:
    selected = cohort()
    meta = manifest(selected)
    if not (FOLDER / "manifest.json").is_file():
        raise ValueError("Core9 benchmark has not started")
    ensure_manifest(FOLDER, meta)
    saved = saved_records(FOLDER, selected)
    if len(saved) == len(selected):
        expected = {
            "manifest": meta, "processed": len(saved), "total": len(selected),
            "counts": dict(sorted(Counter(r["status"] for r in saved.values()).items())),
            "complete_batches": (len(selected)+BATCH_SIZE-1)//BATCH_SIZE,
            "total_batches": (len(selected)+BATCH_SIZE-1)//BATCH_SIZE,
        }
        if json.loads((FOLDER / "summary.json").read_text(encoding="utf-8")) != expected:
            raise ValueError("Core9 summary disagrees with verified records")
    positives = sum(r["status"] in PROVEN for r in saved.values())
    print(
        f"Independently replayed {positives} core-only positive certificates; "
        f"validated {len(saved)}/{len(selected)} records."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", default="next")
    args = parser.parse_args()
    if args.command not in {"plan", "next", "all", "verify"} and not args.command.isdecimal():
        parser.error("Use plan, next, all, verify or a nonnegative batch index")
    if args.command == "plan":
        selected = cohort()
        print(
            f"Selected {len(selected)} distinct nine-vertex cores, "
            f"{sum(r['member_count'] for r in selected.values())} original members; "
            f"7 batches; bound {CLIQUE_BOUND}, {TIMEOUT_SECONDS}s, "
            f"{MEMORY_MIB} MiB, one worker"
        )
        print(f"Separate v3 upstream pin: {current_v3_pin()}")
    elif args.command == "verify":
        verify()
    elif args.command == "all":
        while run("next"):
            pass
    else:
        run(args.command)


if __name__ == "__main__":
    main()
