"""Immutable targeted core9 follow-ups: 8 double covers, 5 bounds, 3 isomorphisms.

Only 13 selected nine-vertex pared-core tasks are run. The earlier 29-core
structural report and all historical census files are inputs, never changed.

    bash scripts/core9_followup.sh plan
    bash scripts/core9_followup.sh iso
    bash scripts/core9_followup.sh next
    bash scripts/core9_followup.sh all
    bash scripts/core9_followup.sh verify
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
from networkx.algorithms.isomorphism import GraphMatcher

import core9_structure
import core9_followup_worker as worker
from timeboxed_trace_v3 import summarize_events_v3
from timeboxed_v3 import current_v3_pin

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "runs/order10/core9-structure-v1"
OUTPUT = ROOT / "runs/order10/core9-followup-v1"
COINCIDENT = (4929602, 4972358, 5645085)
BATCH_SIZE = 4
TIMEOUT = 75
MEMORY_MIB = 2048
POSITIVE = {"DIVERGENT", "CONVERGENT"}
VALID_STATUSES = POSITIVE | {
    "BOUND_EXCEEDED", "INDETERMINATE", "EXHAUSTED", "LIMIT_REACHED", "TIMEOUT", "ERROR",
}


def sha(path: Path) -> str:
    return core9_structure.sha(path)


def atomic(path: Path, content: dict | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".partial")
    try:
        data = content if isinstance(content, str) else json.dumps(
            content, indent=2, sort_keys=True
        ) + "\n"
        temp.write_text(data, encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def cohort() -> tuple[dict[int, dict], dict[int, dict], list[tuple[str, int]]]:
    """Revalidate every saved structural record before making the task list."""
    previous = core9_structure.cohort()
    core9_structure.ensure_manifest(core9_structure.manifest(previous))
    prior = core9_structure.records(previous)
    if set(prior) != set(previous) or any(
        row["status"] != "OK" for row in prior.values()
    ):
        raise ValueError("The committed 29-core structural stage is not complete")
    summary = json.loads((SOURCE / "summary.json").read_text(encoding="utf-8"))
    if (
        summary.get("manifest") != core9_structure.manifest(previous)
        or summary.get("processed") != 29
        or summary.get("counts") != {"OK": 29}
    ):
        raise ValueError("Previous structural summary differs from frozen records")

    covers = sorted(i for i, row in prior.items()
                    if row["iterates"][0]["betti1_mod2"] == 1)
    larger = sorted(
        i for i, row in prior.items()
        if row["iterates"][-1]["maximal_cliques"]["maximal_cliques_exact"] is not None
        and row["iterates"][-1]["maximal_cliques"]["maximal_cliques_exact"] <= 300
    )
    if len(covers) != 8 or len(larger) != 5 or set(covers) & set(larger):
        raise ValueError("Expected eight b1=1 covers and five <=300-clique cores")
    if not set(COINCIDENT).issubset(prior):
        raise ValueError("Missing graph-isomorphism comparison cohort")
    for i in COINCIDENT:
        if len(prior[i]["iterates"]) < 3:
            raise ValueError(f"Missing G2 of matching-fingerprint core {i}")
    tasks = [("cover", i) for i in covers] + [("bound", i) for i in larger]
    return previous, prior, tasks


def manifest(previous: dict, tasks: list[tuple[str, int]]) -> dict:
    dependencies = {
        "runner_sha256": ROOT / "scripts/core9_followup.py",
        "worker_sha256": ROOT / "scripts/core9_followup_worker.py",
        "launcher_sha256": ROOT / "scripts/core9_followup.sh",
        "structure_runner_sha256": ROOT / "scripts/core9_structure.py",
        "structure_worker_sha256": ROOT / "scripts/core9_structure_worker.py",
        "source_manifest_sha256": SOURCE / "manifest.json",
        "source_summary_sha256": SOURCE / "summary.json",
        "source_report_sha256": SOURCE / "report.md",
        "certificate_sha256": ROOT / "scripts/certificate_records_v3.py",
        "cover_search_adapter_sha256": ROOT / "postpasses/s1_divergence.py",
        "trace_sha256": ROOT / "scripts/timeboxed_trace_v3.py",
        "trace_v2_sha256": ROOT / "scripts/timeboxed_trace_v2.py",
        "pin_checker_sha256": ROOT / "scripts/timeboxed_v3.py",
        "v3_pin_file_sha256": ROOT / "config/pycliques_commit_v3.txt",
        "bootstrap_sha256": ROOT / "scripts/bootstrap_v3.sh",
    }
    return {
        "schema": 1, "stage": "core9-followup-v1",
        "scope": "nine_vertex_pared_cores_only",
        "core_ids": sorted(previous),
        "iso_comparison_ids": list(COINCIDENT),
        "tasks": [{"kind": kind, "core_id": i} for kind, i in tasks],
        "source_record_sha256": {
            str(i): sha(SOURCE / "records" / f"{i:08d}.json") for i in previous
        },
        "upstream_commit": current_v3_pin(),
        "time_limit_per_task_seconds": TIMEOUT,
        "memory_mib": MEMORY_MIB, "parallel_workers": 1,
        "batch_size": BATCH_SIZE,
        "cover_limits": worker.COVER_LIMITS, "bound": worker.BOUND,
        "retraction_depth": worker.RETRACTION_DEPTH,
        "research_scope": "strictly bounded explorations; positive claims replayed",
        **{key: sha(path) for key, path in dependencies.items()},
    }


def ensure_manifest(meta: dict, *, create: bool) -> None:
    path = OUTPUT / "manifest.json"
    if path.is_file():
        if json.loads(path.read_text(encoding="utf-8")) != meta:
            raise ValueError("Targeted follow-up provenance changed; cannot resume")
        return
    if not create:
        raise ValueError("No targeted follow-up stage exists")
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise ValueError("Found partial targeted output without a manifest")
    atomic(path, meta)


def graph6_decode(data: str) -> nx.Graph:
    return nx.from_graph6_bytes(data.encode("ascii"))


def verify_mapping(left: nx.Graph, right: nx.Graph, mapping: list[int]) -> bool:
    """Explicit independent adjacency-and-nonadjacency check of an iso map."""
    if len(mapping) != len(left) or set(mapping) != set(right) or set(left) != set(range(len(left))):
        return False
    return all(
        left.has_edge(u, v) == right.has_edge(mapping[u], mapping[v])
        for u in left for v in left
    )


def compute_iso(prior: dict[int, dict]) -> dict:
    """Witness exact G2 isomorphisms, not just WL fingerprint collisions."""
    base = COINCIDENT[0]
    left = graph6_decode(prior[base]["iterates"][2]["graph6"])
    results = []
    for target in COINCIDENT[1:]:
        right = graph6_decode(prior[target]["iterates"][2]["graph6"])
        matcher = GraphMatcher(left, right)
        if matcher.is_isomorphic():
            mapping = [matcher.mapping[i] for i in range(len(left))]
            if not verify_mapping(left, right, mapping):
                raise ValueError("GraphMatcher produced an invalid isomorphism")
            record = {"right_core": target, "isomorphic": True, "mapping": mapping}
        else:
            record = {"right_core": target, "isomorphic": False, "mapping": None}
        results.append(record)
    return {
        "left_core": base, "iterate_index": 2,
        "left_graph6": prior[base]["iterates"][2]["graph6"],
        "comparisons": results,
        "scope": "exact_isomorphism_of_pared_second_clique_iterates",
        "proof_implication": "subsequent pared clique iterates are also isomorphic",
    }


def verify_iso(saved: dict, prior: dict[int, dict]) -> None:
    if (
        saved.get("left_core") != COINCIDENT[0] or saved.get("iterate_index") != 2
        or saved.get("left_graph6") != prior[COINCIDENT[0]]["iterates"][2]["graph6"]
        or saved.get("scope") != "exact_isomorphism_of_pared_second_clique_iterates"
        or len(saved.get("comparisons", [])) != len(COINCIDENT)-1
    ):
        raise ValueError("Malformed saved exact isomorphism comparison")
    left = graph6_decode(saved["left_graph6"])
    for index, row in enumerate(saved["comparisons"]):
        right_id = COINCIDENT[index+1]
        if row.get("right_core") != right_id:
            raise ValueError("Mismatched comparison core ID")
        right = graph6_decode(prior[right_id]["iterates"][2]["graph6"])
        found = row.get("isomorphic")
        if found is True:
            if not verify_mapping(left, right, row.get("mapping", [])):
                raise ValueError("Saved exact isomorphism mapping has failed replay")
        elif found is False:
            if row.get("mapping") is not None or nx.is_isomorphic(left, right):
                raise ValueError("Incorrect assertion of nonisomorphism")
        else:
            raise ValueError("Invalid isomorphism verdict")


def validate_record(row: dict, kind: str, core_id: int, previous: dict) -> None:
    if (
        row.get("kind") != kind or row.get("core_id") != core_id
        or row.get("scope") != "nine_vertex_core_only"
        or row.get("input_graph6") != previous[core_id]["graph6"]
        or row.get("status") not in VALID_STATUSES
    ):
        raise ValueError(f"Invalid targeted core record {kind}:{core_id}")
    state = row["status"]
    if state in {"TIMEOUT", "ERROR"}:
        if row.get("witness") is not None or row.get("proof_status") in {
            "verified", "verified_chain",
        }:
            raise ValueError("Resource failure cannot contain a positive certificate")
        return
    if kind == "cover":
        if state not in {"DIVERGENT", "EXHAUSTED", "LIMIT_REACHED"}:
            raise ValueError("Cover result has incompatible status")
        details = row.get("search", {})
        if details.get("limits") != worker.COVER_LIMITS:
            raise ValueError("Cover search limit metadata differs from stage manifest")
        expected_search_status = (
            "FOUND" if state == "DIVERGENT" else state
        )
        if details.get("search_status") != expected_search_status:
            raise ValueError("Cover search status and record disagree")
        if state == "DIVERGENT":
            if (
                row.get("proof_status") != "verified"
                or not isinstance(row.get("witness"), dict)
                or not worker.verify_cover_witness(
                    graph6_decode(previous[core_id]["graph6"]), row["witness"]
                )
            ):
                raise ValueError("Cover-based divergence claim failed witness replay")
        elif row.get("witness") is not None or row.get("proof_status") != "none":
            raise ValueError("Nonpositive cover result cannot carry a proof")
    else:
        if state not in POSITIVE | {"INDETERMINATE", "BOUND_EXCEEDED"}:
            raise ValueError("Unexpected higher-bound status")
        if row.get("clique_bound") != worker.BOUND:
            raise ValueError("Higher bound differs from manifest")
        if state in POSITIVE:
            if (
                row.get("verdict") != state
                or row.get("proof_status") != "verified_chain"
                or not isinstance(row.get("proof"), dict)
                or row["proof"].get("origin_graph6") != previous[core_id]["graph6"]
                or row["proof"].get("clique_bound") != worker.BOUND
                or not worker.verify_record(row, verify_iterate=True)
            ):
                raise ValueError("Higher-bound positive proof failed full replay")
        else:
            if row.get("proof_status") == "verified_chain" or row.get("proof") is not None:
                raise ValueError("Unsupported positive proof in nonpositive result")
            if state == "BOUND_EXCEEDED" and row.get("raw_verdict") != "INDETERMINATE":
                raise ValueError("Bound failure cannot be a positive verdict")
            if row.get("raw_verdict") not in POSITIVE | {"INDETERMINATE"}:
                raise ValueError("Invalid raw verdict")


def saved_records(tasks: list[tuple[str, int]], previous: dict) -> dict[str, dict]:
    expected = {f"{kind}_{i:08d}.json": (kind, i) for kind, i in tasks}
    saved = {}
    for path in sorted((OUTPUT / "records").glob("*.json")):
        if path.name not in expected:
            raise ValueError(f"Unrecognized targeted follow-up record {path}")
        kind, i = expected[path.name]
        row = json.loads(path.read_text(encoding="utf-8"))
        validate_record(row, kind, i, previous)
        saved[path.name] = row
    return saved


def worker_limit() -> None:
    amount = MEMORY_MIB * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (amount, amount))


def invoke_worker(kind: str, graph6: str) -> dict:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    result_fd, result_path = tempfile.mkstemp(prefix="followup_", suffix=".partial", dir=OUTPUT)
    trace_fd, trace_path = tempfile.mkstemp(prefix="followup_trace_", suffix=".partial", dir=OUTPUT)
    os.close(result_fd)
    os.close(trace_fd)
    begin = time.monotonic()
    env = os.environ.copy()
    for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[variable] = "1"
    try:
        with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as errors:
            process = subprocess.Popen(
                [sys.executable, str(ROOT / "scripts/core9_followup_worker.py"),
                 kind, graph6, result_path, trace_path],
                cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=errors,
                start_new_session=True, preexec_fn=worker_limit,
            )
            try:
                process.wait(timeout=TIMEOUT)
            except subprocess.TimeoutExpired:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                return {
                    "status": "TIMEOUT", "reason": f"Worker exceeded {TIMEOUT}s",
                    "elapsed_seconds": round(time.monotonic()-begin, 3),
                }
            except BaseException:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                raise
            duration = round(time.monotonic()-begin, 3)
            if process.returncode == 0:
                try:
                    payload = json.loads(Path(result_path).read_text(encoding="utf-8"))
                    if payload.get("status") not in VALID_STATUSES:
                        raise ValueError("Unexpected worker status")
                    if kind == "bound":
                        payload["trace"] = summarize_events_v3(trace_path)
                    payload["elapsed_seconds"] = duration
                    return payload
                except (OSError, TypeError, ValueError) as exc:
                    reason = f"Malformed successful worker output: {exc}"
            else:
                reason = f"Worker exit code {process.returncode}"
            errors.seek(0)
            return {
                "status": "ERROR", "reason": reason,
                "stderr_excerpt": errors.read(5000),
                "elapsed_seconds": duration,
            }
    finally:
        Path(result_path).unlink(missing_ok=True)
        Path(trace_path).unlink(missing_ok=True)


def summarize(tasks: list[tuple[str, int]], saved: dict[str, dict], previous: dict, prior: dict, meta: dict) -> None:
    counts = dict(sorted(Counter(
        f"{row['kind']}:{row['status']}" for row in saved.values()
    ).items()))
    progress = {
        "processed": len(saved), "total": len(tasks),
        "counts": counts,
        "iso_verified": (OUTPUT / "isomorphism.json").is_file(),
    }
    atomic(OUTPUT / "progress.json", progress)
    if len(saved) != len(tasks) or not progress["iso_verified"]:
        return
    iso = json.loads((OUTPUT / "isomorphism.json").read_text(encoding="utf-8"))
    verify_iso(iso, prior)
    atomic(OUTPUT / "summary.json", {"manifest": meta, **progress})
    lines = [
        "# Targeted follow-ups on unresolved order-nine pared cores", "",
        "All positive covering or larger-bound results below require independently",
        "replayed finite certificates. Nonpositive bounded search outcomes are",
        "inconclusive regarding clique convergence or divergence.", "",
        "## Exact second-iterate isomorphisms", "",
        f"- Reference core: {iso['left_core']}",
    ]
    for item in iso["comparisons"]:
        lines.append(
            f"- Core {item['right_core']}: "
            + ("**isomorphic**, explicit adjacency-preserving bijection saved"
               if item["isomorphic"] else "not isomorphic (exhaustive exact matcher)")
        )
    lines += ["", "## Covering and higher-bound experiments", "",
              "| Kind | Core | Original members | Status | Seconds | Detail |",
              "|---|---:|---:|---|---:|---|"]
    for kind, i in tasks:
        row = saved[f"{kind}_{i:08d}.json"]
        detail = (
            row.get("search", {}).get("search_status", "-")
            if kind == "cover"
            else f"raw={row.get('raw_verdict', '-')}, iterates={row.get('iterations_checked', '-')}"
        )
        lines.append(
            f"| {kind} | {i} | {previous[i]['member_count']} "
            f"| {row['status']} | {row.get('elapsed_seconds',0):.2f} | {detail} |"
        )
    lines += ["", "## Important limitations", "",
              "- The three second-iterate isomorphisms are about pared *nine-vertex cores*.",
              "- A cover search restricted to one cohomology class and small clockwork",
              "  parameters cannot disprove divergence; EXHAUSTED means only this finite family.",
              "- Positive core proofs do not transfer automatically to ten-vertex members.",
              "- Every core still lacking a positive certificate remains mathematically",
              "  unresolved by this stage.", ""]
    atomic(OUTPUT / "report.md", "\n".join(lines))


def execute(mode: str) -> bool:
    previous, prior, tasks = cohort()
    meta = manifest(previous, tasks)
    lockdir = ROOT / ".deps"
    lockdir.mkdir(exist_ok=True)
    with (lockdir / "core9-followup-v1.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ensure_manifest(meta, create=True)
        iso_path = OUTPUT / "isomorphism.json"
        if not iso_path.exists():
            iso_record = compute_iso(prior)
            verify_iso(iso_record, prior)
            atomic(iso_path, iso_record)
        else:
            verify_iso(json.loads(iso_path.read_text(encoding="utf-8")), prior)
        if mode == "iso":
            print("Saved and checked explicit G2 isomorphism mappings.")
            return False
        (OUTPUT / "records").mkdir(exist_ok=True)
        saved = saved_records(tasks, previous)
        blocks = [tasks[k:k+BATCH_SIZE] for k in range(0, len(tasks), BATCH_SIZE)]
        if mode == "next":
            batch = next((k for k, block in enumerate(blocks) if any(
                f"{kind}_{i:08d}.json" not in saved for kind, i in block
            )), None)
        else:
            batch = int(mode)
            if batch < 0 or batch >= len(blocks):
                raise ValueError(f"Batch index must be 0..{len(blocks)-1}")
        if batch is None:
            print("All 13 targeted tasks already processed.")
            summarize(tasks, saved, previous, prior, meta)
            return False
        print(f"Follow-up batch {batch}/{len(blocks)-1}", flush=True)
        for kind, i in blocks[batch]:
            key = f"{kind}_{i:08d}.json"
            if key in saved:
                continue
            print(f"  {kind} core {i}, {previous[i]['member_count']} members", flush=True)
            result = {
                "kind": kind, "core_id": i,
                "input_graph6": previous[i]["graph6"],
                "scope": "nine_vertex_core_only",
                **invoke_worker(kind, previous[i]["graph6"]),
            }
            validate_record(result, kind, i, previous)
            atomic(OUTPUT / "records" / key, result)
            saved[key] = result
            print(f"    {result['status']} in {result['elapsed_seconds']:.2f}s", flush=True)
        summarize(tasks, saved, previous, prior, meta)
        print(f"Checkpoint {len(saved)}/{len(tasks)}", flush=True)
        return len(saved) < len(tasks)


def verify() -> None:
    previous, prior, tasks = cohort()
    meta = manifest(previous, tasks)
    ensure_manifest(meta, create=False)
    iso_path = OUTPUT / "isomorphism.json"
    if not iso_path.is_file():
        raise ValueError("Missing exact isomorphism certificate")
    verify_iso(json.loads(iso_path.read_text(encoding="utf-8")), prior)
    saved = saved_records(tasks, previous)
    if len(saved) == len(tasks):
        progress = json.loads((OUTPUT / "progress.json").read_text(encoding="utf-8"))
        expected = {
            "processed": len(saved), "total": len(tasks),
            "counts": dict(sorted(Counter(
                f"{r['kind']}:{r['status']}" for r in saved.values()
            ).items())),
            "iso_verified": True,
        }
        if progress != expected:
            raise ValueError("Saved progress conflicts with task records")
        if json.loads((OUTPUT / "summary.json").read_text(encoding="utf-8")) != {
            "manifest": meta, **expected
        }:
            raise ValueError("Final summary conflicts with verified saved data")
    print(f"Verified 2 explicit G2 isomorphisms and {len(saved)}/{len(tasks)} core task records.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", default="next")
    mode = parser.parse_args().command
    if mode == "plan":
        previous, prior, tasks = cohort()
        print(
            f"8 covering tasks (b1=1 at G0), 5 higher-bound tasks (last count <=300), "
            f"3 G2-equivalent cores; 13 tasks in 4 batches; "
            f"{TIMEOUT}s, {MEMORY_MIB}MiB per task; pin {current_v3_pin()}"
        )
    elif mode == "verify":
        verify()
    elif mode == "all":
        while execute("next"):
            pass
    elif mode in {"iso", "next"} or mode.isdecimal():
        execute(mode)
    else:
        parser.error("Use plan, iso, next, all, verify, or a batch index")


if __name__ == "__main__":
    main()
