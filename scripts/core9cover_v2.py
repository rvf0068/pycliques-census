"""Versioned post-PR14 nine-core double-cover comparison.

A new PINNED pycombtop checkout executes two searches for each of eight
nine-vertex pared core classes, without touching historical census data.

    bash scripts/core9cover_v2.sh plan
    bash scripts/core9cover_v2.sh next
    bash scripts/core9cover_v2.sh all
    bash scripts/core9cover_v2.sh verify
    bash scripts/core9cover_v2.sh replay

Only complete, independently checked positive witnesses may certify
DIVERGENT for the *nine-core itself*. EXHAUSTED refers solely to the
configured finite cover/clockwork family. No original-ten-graph verdict.
"""
from __future__ import annotations

import argparse
from collections import Counter
import fcntl
import hashlib
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

import core9cover_v2_worker as worker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "postpasses"))
from s1_divergence import verify_cover_witness  # noqa: E402
OLD = ROOT / "runs/order10/core9-followup-v1"
OUTPUT = ROOT / "runs/order10/core9-cover-ac3-v2"
PIN_FILE = ROOT / "config/pycliques_commit_core9cover_v2.txt"
DEPENDENCY = ROOT / ".deps/pycliques-project-core9cover-v2"
PIN = "005f6cc06a3bf1332bf6e729af73eea8ff26a40d"
EXPECTED_IDS = (
    2317843, 3148541, 3505942, 4952669,
    4953338, 5601875, 6938156, 7315343,
)
MODES = ("baseline", "expanded")
BATCH_SIZE = 4
TIMEOUT_SECONDS = 90
MEMORY_MIB = 2048
VALID = {"DIVERGENT", "EXHAUSTED", "LIMIT_REACHED", "TIMEOUT", "ERROR"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path: Path, payload: dict | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".partial")
    try:
        text = payload if isinstance(payload, str) else json.dumps(
            payload, sort_keys=True, indent=2
        ) + "\n"
        temp.write_text(text, encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def require_pin() -> None:
    if PIN_FILE.read_text(encoding="utf-8").strip() != PIN:
        raise ValueError("Post-PR14 dependency pin differs from required merge")
    if not (DEPENDENCY / ".git").is_dir():
        raise ValueError("Run bash scripts/bootstrap_core9cover_v2.sh first")
    got = subprocess.check_output(
        ["git", "-C", str(DEPENDENCY), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    if got != PIN:
        raise ValueError("Loaded pycombtop checkout differs from frozen new pin")


def cohort() -> dict[int, dict]:
    """Select exactly the eight original inconclusive cover searches."""
    old_summary = json.loads((OLD / "summary.json").read_text(encoding="utf-8"))
    old_meta = json.loads((OLD / "manifest.json").read_text(encoding="utf-8"))
    if (
        old_summary.get("manifest") != old_meta
        or old_summary.get("processed") != 13
        or old_meta.get("stage") != "core9-followup-v1"
        or old_meta.get("scope") != "nine_vertex_pared_cores_only"
        or old_meta.get("upstream_commit") != "d6753ac445b57740d90997008aa96830d4fc117c"
    ):
        raise ValueError("Frozen core9-followup-v1 manifest/summary mismatch")
    ids = [
        item["core_id"]
        for item in old_meta["tasks"]
        if item.get("kind") == "cover"
    ]
    if sorted(ids) != sorted(EXPECTED_IDS):
        raise ValueError("The old covering cohort is not the eight known cores")
    selected = {}
    for i in EXPECTED_IDS:
        path = OLD / "records" / f"cover_{i:08d}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        graph6 = data.get("input_graph6")
        if (
            data.get("core_id") != i
            or data.get("kind") != "cover"
            or data.get("scope") != "nine_vertex_core_only"
            or data.get("status") != "LIMIT_REACHED"
            or data.get("witness") is not None
            or data.get("proof_status") != "none"
            or data.get("search", {}).get("limits") != worker.BASELINE
            or data["search"].get("morphism_assignments") != 100000
            or not isinstance(graph6, str)
        ):
            raise ValueError(f"Old core {i} does not support the new stage")
        graph = nx.from_graph6_bytes(graph6.encode("ascii"))
        if len(graph) != 9 or not nx.is_connected(graph):
            raise ValueError(f"Bad frozen graph6 for core {i}")
        selected[i] = {
            "graph6": graph6,
            "member_count": data["member_count"],
            "source_sha256": sha(path),
        }
    return selected


def tasks() -> list[tuple[str, int]]:
    # Baseline first, for a reproducible paired comparison with the old pin.
    return [(mode, i) for mode in MODES for i in EXPECTED_IDS]


def manifest(selected: dict[int, dict]) -> dict:
    deps = {
        "pin_file_sha256": PIN_FILE,
        "bootstrap_sha256": ROOT / "scripts/bootstrap_core9cover_v2.sh",
        "runner_sha256": ROOT / "scripts/core9cover_v2.py",
        "worker_sha256": ROOT / "scripts/core9cover_v2_worker.py",
        "launcher_sha256": ROOT / "scripts/core9cover_v2.sh",
        "witness_verifier_sha256": ROOT / "postpasses/s1_divergence.py",
        "old_manifest_sha256": OLD / "manifest.json",
        "old_summary_sha256": OLD / "summary.json",
    }
    return {
        "schema": 1,
        "stage": "core9-cover-ac3-v2",
        "scope": "nine_vertex_pared_cores_only",
        "upstream_commit": PIN,
        "source_core_ids": list(EXPECTED_IDS),
        "source_original_member_total": sum(x["member_count"] for x in selected.values()),
        "tasks": [{"mode": mode, "core_id": i} for mode, i in tasks()],
        "source_records_sha256": {str(i): selected[i]["source_sha256"] for i in EXPECTED_IDS},
        "limits_by_mode": worker.LIMITS,
        "batch_size": BATCH_SIZE,
        "timeout_seconds": TIMEOUT_SECONDS,
        "memory_mib": MEMORY_MIB,
        "negative_scope": "configured double-cover and clockwork family only",
        **{key: sha(path) for key, path in deps.items()},
    }


def ensure_manifest(meta: dict, create: bool) -> None:
    path = OUTPUT / "manifest.json"
    if path.is_file():
        if json.loads(path.read_text(encoding="utf-8")) != meta:
            raise ValueError("Cannot resume: source bytes, scripts, pin, or limits changed")
        return
    if not create:
        raise ValueError("Stage has not started; verify must be read-only")
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise ValueError("Found output without a valid provenance manifest")
    atomic(path, meta)


def validate_record(entry: dict, mode: str, i: int, selected: dict[int, dict]) -> None:
    if (
        entry.get("mode") != mode
        or entry.get("core_id") != i
        or entry.get("kind") != mode
        or entry.get("scope") != "nine_vertex_core_only"
        or entry.get("input_graph6") != selected[i]["graph6"]
        or entry.get("status") not in VALID
    ):
        raise ValueError(f"Invalid core9cover record identity for {mode}:{i}")
    status = entry["status"]
    if status in {"ERROR", "TIMEOUT"}:
        if entry.get("witness") is not None or entry.get("proof_status") == "verified":
            raise ValueError("Resource failure must never carry positive evidence")
        return
    search = entry.get("search", {})
    eligible = entry.get("eligible", {})
    if (
        search.get("limits") != worker.LIMITS[mode]
        or search.get("cover_classes_total") != 1
        or search.get("cover_classes_checked") != 1
        or search.get("cover_candidates_checked") != 1
        or search.get("configured_source_parameters") != [
            [m, n]
            for m in range(2, worker.LIMITS[mode]["max_m"] + 1)
            for n in range(worker.LIMITS[mode]["max_n"] + 1)
        ]
        or eligible.get("checked_cover_classes") != 1
        or len(eligible.get("covers", [])) != 1
        or any(
            not isinstance(search.get(key), int)
            or not 0 <= search[key] <= worker.LIMITS[mode][limit]
            for key, limit in (
                ("morphism_states", "max_morphism_states"),
                ("morphism_assignments", "max_morphism_assignments"),
            )
        )
    ):
        raise ValueError("Search output does not match frozen finite family")
    if status == "EXHAUSTED":
        if (
            search.get("search_status") != status
            or search.get("cover_classes_complete") is not True
            or search.get("morphisms_complete") is not True
            or entry.get("witness") is not None
            or entry.get("proof_status") != "none"
        ):
            raise ValueError("False complete-exhaustion claim")
    elif status == "LIMIT_REACHED":
        if (
            search.get("search_status") != status
            or entry.get("witness") is not None
            or entry.get("proof_status") != "none"
        ):
            raise ValueError("Invalid inconclusive search")
    else:
        witness = entry.get("witness")
        limits = worker.LIMITS[mode]
        if (
            status != "DIVERGENT"
            or entry.get("proof_status") != "verified"
            or search.get("search_status") != "FOUND"
            or not isinstance(witness, dict)
            or witness.get("m") not in range(2, limits["max_m"] + 1)
            or witness.get("n") not in range(limits["max_n"] + 1)
            or 2*witness["m"]*(witness["n"] + 3) > limits["max_source_order"]
            or witness.get("deck_radius") != witness["m"] + 1
            or witness.get("clique_bound") != limits["max_clique_vertices"]
            or witness.get("clique_max_edges") != limits["max_clique_edges"]
            or [witness["m"], witness["n"]]
                not in eligible["covers"][0]["source_parameters_eligible"]
            or not verify_cover_witness(
                nx.from_graph6_bytes(selected[i]["graph6"].encode("ascii")),
                witness,
            )
        ):
            raise ValueError("Positive divergence certificate failed independent replay")


def records(selected: dict[int, dict]) -> dict[str, dict]:
    valid_names = {f"{mode}_{i:08d}.json": (mode, i) for mode, i in tasks()}
    output = {}
    for path in sorted((OUTPUT / "records").glob("*.json")):
        if path.name not in valid_names:
            raise ValueError(f"Unknown result record {path}")
        mode, i = valid_names[path.name]
        row = json.loads(path.read_text(encoding="utf-8"))
        validate_record(row, mode, i, selected)
        output[path.name] = row
    return output


def resource_limit() -> None:
    cap = MEMORY_MIB * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (cap, cap))


def run_worker(mode: str, graph6: str) -> dict:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    fd, raw = tempfile.mkstemp(prefix="cover_", suffix=".partial", dir=OUTPUT)
    os.close(fd)
    started = time.monotonic()
    env = os.environ.copy()
    for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[key] = "1"
    try:
        with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as err:
            child = subprocess.Popen(
                [sys.executable, str(ROOT / "scripts/core9cover_v2_worker.py"),
                 mode, graph6, raw],
                cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=err,
                start_new_session=True, preexec_fn=resource_limit,
            )
            try:
                child.wait(timeout=TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGKILL)
                child.wait()
                return {
                    "status": "TIMEOUT",
                    "reason": f"Exceeded {TIMEOUT_SECONDS}s wall time",
                    "elapsed_seconds": round(time.monotonic()-started, 3),
                }
            except BaseException:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGKILL)
                child.wait()
                raise
            seconds = round(time.monotonic()-started, 3)
            if child.returncode == 0:
                try:
                    data = json.loads(Path(raw).read_text(encoding="utf-8"))
                    return {**data, "elapsed_seconds": seconds}
                except (OSError, ValueError, TypeError) as error:
                    failure = f"Invalid worker JSON: {error}"
            else:
                failure = f"Worker exited with code {child.returncode}"
            err.seek(0)
            return {
                "status": "ERROR",
                "reason": failure,
                "stderr_excerpt": err.read(4000),
                "elapsed_seconds": seconds,
            }
    finally:
        Path(raw).unlink(missing_ok=True)


def report(selected: dict, saved: dict) -> str:
    rows = [
        "# Post-PR14 AC-3 covering search on eight nine-vertex cores",
        "",
        "All claims are about *completely pared nine-vertex core graphs*;",
        "no conclusion is transferred automatically to the represented ten-vertex graphs.",
        "EXHAUSTED means precisely the finite double-cover / clockwork-source family",
        "recorded in the manifest, not absence of clique divergence.",
        "",
        "| Core ID | Original ten-graph members | Baseline | Expanded | New eligible clockwork pairs | Expanded assignments |",
        "|---:|---:|---|---|---|---:|",
    ]
    for i in EXPECTED_IDS:
        baseline = saved.get(f"baseline_{i:08d}.json", {})
        expanded = saved.get(f"expanded_{i:08d}.json", {})
        old_pairs = baseline.get("eligible", {}).get("covers", [{}])[0].get("source_parameters_eligible", [])
        new_pairs = expanded.get("eligible", {}).get("covers", [{}])[0].get("source_parameters_eligible", [])
        additional = [pair for pair in new_pairs if pair not in old_pairs]
        rows.append(
            f"| {i} | {selected[i]['member_count']} "
            f"| {baseline.get('status','-')} | {expanded.get('status','-')} "
            f"| {additional} "
            f"| {expanded.get('search',{}).get('morphism_assignments','-')} |"
        )
    rows += [
        "", "## Interpretation", "",
        "Both configurations use the same new pinned AC-3 implementation.",
        "The baseline reproduces the old finite family with the optimized search.",
        "The expanded configuration searches R_(2m)^n with additional n=1,2",
        "subject to actual cover radius and source-order restrictions.",
        "A configuration setting alone does not imply a family member was eligible.",
        "Certificates, if found, are rechecked independently against the base core.",
        "No positive certificate is inferred from a bounded negative search.",
        "",
    ]
    return "\n".join(rows)


def progress(selected: dict, saved: dict, meta: dict) -> None:
    counter = dict(sorted(Counter(
        f"{r['mode']}:{r['status']}" for r in saved.values()
    ).items()))
    details = {"processed": len(saved), "total": len(tasks()), "counts": counter}
    atomic(OUTPUT / "progress.json", details)
    if len(saved) == len(tasks()):
        atomic(OUTPUT / "summary.json", {"manifest": meta, **details})
        atomic(OUTPUT / "report.md", report(selected, saved))


def run(batch: str) -> bool:
    require_pin()
    selected = cohort()
    meta = manifest(selected)
    lockpath = ROOT / ".deps/core9cover-v2.lock"
    lockpath.parent.mkdir(exist_ok=True)
    with lockpath.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ensure_manifest(meta, create=True)
        (OUTPUT / "records").mkdir(exist_ok=True)
        saved = records(selected)
        all_tasks = tasks()
        chunks = [all_tasks[j:j+BATCH_SIZE] for j in range(0,len(all_tasks),BATCH_SIZE)]
        if batch == "next":
            index = next((
                j for j, chunk in enumerate(chunks)
                if any(f"{mode}_{i:08d}.json" not in saved for mode,i in chunk)
            ), None)
        else:
            index = int(batch)
            if not 0 <= index < len(chunks):
                raise ValueError(f"Batch must be 0..{len(chunks)-1}")
        if index is None:
            progress(selected, saved, meta)
            print(f"All {len(saved)} covering comparisons are complete.", flush=True)
            return False
        for mode, i in chunks[index]:
            name = f"{mode}_{i:08d}.json"
            if name in saved:
                continue
            print(f"Core {i}, {mode} family", flush=True)
            entry = {
                "core_id": i, "mode": mode,
                "input_graph6": selected[i]["graph6"],
                "scope": "nine_vertex_core_only",
                **run_worker(mode, selected[i]["graph6"]),
            }
            validate_record(entry, mode, i, selected)
            atomic(OUTPUT / "records" / name, entry)
            saved[name] = entry
            print(
                f"  {entry['status']}, assignments="
                f"{entry.get('search',{}).get('morphism_assignments','-')}, "
                f"{entry['elapsed_seconds']:.2f}s", flush=True
            )
        progress(selected, saved, meta)
        print(f"Checkpoint: {len(saved)}/{len(all_tasks)}", flush=True)
        return len(saved) < len(all_tasks)


def verify(*, replay: bool) -> None:
    require_pin()
    selected = cohort()
    meta = manifest(selected)
    ensure_manifest(meta, create=False)
    saved = records(selected)
    if replay:
        # A negative EXHAUSTED statement is a *computational observation*.
        # Replay the original deterministic search instead of trusting a
        # self-reported count or transforming it into a mathematical proof.
        for mode, i in tasks():
            key = f"{mode}_{i:08d}.json"
            if key not in saved or saved[key]["status"] in {"TIMEOUT", "ERROR"}:
                continue
            fresh = worker.investigate(mode, selected[i]["graph6"])
            old = saved[key]
            for field in ("kind", "status", "input_graph6", "eligible", "search", "witness", "proof_status"):
                if fresh[field] != old[field]:
                    raise ValueError(f"Replay mismatch in {field} for {mode}:{i}")
            print(f"Replayed {mode}:{i}", flush=True)
    if len(saved) == len(tasks()):
        expected = {
            "manifest": meta,
            "processed": len(saved), "total": len(tasks()),
            "counts": dict(sorted(Counter(
                f"{r['mode']}:{r['status']}" for r in saved.values()
            ).items())),
        }
        if json.loads((OUTPUT / "summary.json").read_text(encoding="utf-8")) != expected:
            raise ValueError("Saved full summary does not match verified records")
    print(f"Validated {len(saved)}/{len(tasks())} post-PR14 core-only records.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", default="next")
    cmd = parser.parse_args().command
    if cmd == "plan":
        require_pin()
        selected = cohort()
        print(
            f"Pin {PIN}; eight cores, {sum(row['member_count'] for row in selected.values())} "
            f"represented order-ten graphs; 16 tasks, four 4-task batches; "
            f"{TIMEOUT_SECONDS}s and {MEMORY_MIB}MiB per task."
        )
        print("Baseline source: m<=3,n=0; expanded source: m<=4,n<=2, order<=42.")
    elif cmd in ("verify","replay"):
        verify(replay=cmd=="replay")
    elif cmd == "all":
        while run("next"):
            pass
    elif cmd == "next" or cmd.isdecimal():
        run(cmd)
    else:
        parser.error("Use plan, next, all, verify, replay, or a batch number")


if __name__ == "__main__":
    main()
