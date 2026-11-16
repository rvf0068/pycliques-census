"""Versioned post-PR14 nine-core double-cover comparison.

The isolated post-PR14 pin is reused without touching existing experiments.
For eight historically unresolved nine-vertex cores, reconstruct and verify
their saved completely pared first and second clique iterates, then run one
bounded covering search on each of these 16 graphs. Any positive result is
certified for the PARED ITERATE, not automatically for the initial core or
the represented ten-vertex graphs; negative finite-family results establish
neither convergence nor nondivergence.
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

import core9iterate_v1_worker as worker
from pycliques.small import CliqueSequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "postpasses"))
from s1_divergence import verify_cover_witness  # noqa: E402
SOURCE = ROOT / "runs/order10/core9-structure-v1"
CROSSREF = ROOT / "reports/order10_core9_crossref_v1/unclassified.tsv"
OUTPUT = ROOT / "runs/order10/core9-cover-iterates-v1"
PIN_FILE = ROOT / "config/pycliques_commit_core9cover_v2.txt"
DEPENDENCY = ROOT / ".deps/pycliques-project-core9cover-v2"
PIN = "005f6cc06a3bf1332bf6e729af73eea8ff26a40d"
EXPECTED_IDS = (
    2317843, 3148541, 3505942, 4952669,
    4953338, 5601875, 6938156, 7315343,
)
MODES = ("g1", "g2")
BATCH_SIZE = 4
TIMEOUT_SECONDS = 120
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
    dirty = subprocess.check_output(
        ["git", "-C", str(DEPENDENCY), "status", "--porcelain"],
        text=True,
    )
    if dirty.strip():
        raise ValueError("Pinned pycliques dependency working tree is dirty")


def cohort() -> dict[int, dict]:
    """Verify eight frozen core histories, including the pared K-iteration."""
    historical = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))
    if (
        historical.get("stage") != "core9-structure-v1"
        or historical.get("v3_upstream_commit")
            != "d6753ac445b57740d90997008aa96830d4fc117c"
        or not set(EXPECTED_IDS).issubset(set(historical.get("core_ids", [])))
    ):
        raise ValueError("Unexpected historical structural-investigation source")
    lines = CROSSREF.read_text(encoding="utf-8").splitlines()
    expected_header = (
        "core_id\tcore_graph6\toriginal_members\torder9_index\t"
        "order9_graph6\tlast_stage_examined"
    )
    if not lines or lines[0] != expected_header:
        raise ValueError("Unexpected frozen historical cross-reference schema")
    ref = {}
    for line in lines[1:]:
        items = line.split("\t")
        if len(items) != 6:
            raise ValueError("Malformed cross-reference")
        i = int(items[0])
        if i in EXPECTED_IDS:
            if i in ref:
                raise ValueError("Duplicated core index in cross-reference")
            ref[i] = (items[1], int(items[2]))
    if set(ref) != set(EXPECTED_IDS):
        raise ValueError("Missing nine-core cross-reference inputs")

    selected = {}
    for i in EXPECTED_IDS:
        path = SOURCE / "records" / f"{i:08d}.json"
        old = json.loads(path.read_text(encoding="utf-8"))
        if (
            old.get("core_id") != i
            or old.get("input_graph6") != ref[i][0]
            or old.get("scope") != "structural_diagnostics_only"
            or old.get("failure_iterate") != 4
        ):
            raise ValueError(f"Corrupted historical core {i}")
        rows = old.get("iterates")
        if not isinstance(rows, list) or len(rows) < 3:
            raise ValueError(f"Missing saved pared clique iterates for {i}")
        g0 = nx.from_graph6_bytes(ref[i][0].encode("ascii"))
        if len(g0) != 9 or not nx.is_connected(g0):
            raise ValueError(f"Invalid initial core graph6 for {i}")
        # Crucial: CliqueSequence constructs COMPLETELY PARED iterates.
        # They are not the raw unpared K^j(G), so do not infer initial-core
        # or original-ten-vertex divergence from an iterate certificate.
        seq = CliqueSequence(g0, bound=120)
        graphs = {}
        for j in range(3):
            row = rows[j]
            graph6 = row.get("graph6")
            if not isinstance(graph6, str) or row.get("index") != j:
                raise ValueError(f"Bad saved iterate {i}:G{j}")
            graph = nx.from_graph6_bytes(graph6.encode("ascii"))
            comparison = seq[j]
            if (
                comparison is None
                or not nx.is_isomorphic(comparison, graph)
                or row.get("order") != len(graph)
                or row.get("edges") != graph.number_of_edges()
                or row.get("betti1_mod2") != 1
                or not nx.is_connected(graph)
            ):
                raise ValueError(f"Unverified pared iterate {i}:G{j}")
            if j in (1, 2):
                expected_orders = {1: {13, 14}, 2: {21}}
                if len(graph) not in expected_orders[j]:
                    raise ValueError("Unexpected pared iterate size")
                if 2 * graph.number_of_edges() > worker.LIMITS[f"g{j}"]["max_cover_edges"]:
                    raise ValueError("Bound excludes the historical lifted graph")
                graphs[f"g{j}"] = graph6
        selected[i] = {
            "graph6": graphs,
            "member_count": ref[i][1],
            "source_sha256": sha(path),
        }
    if sum(row["member_count"] for row in selected.values()) != 881:
        raise ValueError("Historical represented-member counts changed")
    return selected

def tasks() -> list[tuple[str, int]]:
    # Baseline first, for a reproducible paired comparison with the old pin.
    return [(mode, i) for mode in MODES for i in EXPECTED_IDS]


def manifest(selected: dict[int, dict]) -> dict:
    dependencies = {
        "pin_file_sha256": PIN_FILE,
        "runner_sha256": ROOT / "scripts/core9iterate_v1.py",
        "worker_sha256": ROOT / "scripts/core9iterate_v1_worker.py",
        "launcher_sha256": ROOT / "scripts/core9iterate_v1.sh",
        "tests_sha256": ROOT / "tests/test_core9iterate_v1.py",
        "workflow_sha256": ROOT / ".github/workflows/core9-cover-iterates-v1.yml",
        "existing_worker_sha256": ROOT / "scripts/core9cover_v2_worker.py",
        "existing_pin_guard_sha256": ROOT / "scripts/core9cover_v2.py",
        "source_manifest_sha256": SOURCE / "manifest.json",
        "crossref_sha256": CROSSREF,
        "certificate_verifier_sha256": ROOT / "postpasses/s1_divergence.py",
    }
    return {
        "schema": 1,
        "stage": "core9-cover-iterates-v1",
        "scope": "pared_iterates_only",
        "upstream_commit": PIN,
        "source_core_ids": list(EXPECTED_IDS),
        "source_original_member_total": sum(x["member_count"] for x in selected.values()),
        "source_iterates": [1, 2],
        "tasks": [{"mode": mode, "core_id": i} for mode, i in tasks()],
        "source_records_sha256": {str(i): selected[i]["source_sha256"] for i in EXPECTED_IDS},
        "input_graph6": {str(i): selected[i]["graph6"] for i in EXPECTED_IDS},
        "limits_by_iterate": worker.LIMITS,
        "batch_size": BATCH_SIZE,
        "timeout_seconds": TIMEOUT_SECONDS,
        "memory_mib": MEMORY_MIB,
        "negative_scope": "finite triangular double-cover / clockwork family only",
        "positive_scope": "certificate for the saved pared iterate only",
        **{key: sha(path) for key, path in dependencies.items()},
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
        or entry.get("scope") != "pared_iterate_only"
        or entry.get("input_graph6") != selected[i]["graph6"][mode]
        or entry.get("status") not in VALID
    ):
        raise ValueError(f"Invalid iterate record identity for {mode}:{i}")
    status = entry["status"]
    if status in {"ERROR", "TIMEOUT"}:
        if entry.get("witness") is not None or entry.get("proof_status") == "verified":
            raise ValueError("Resource failures cannot carry proof")
        return
    limits = worker.LIMITS[mode]
    search = entry.get("search", {})
    eligible = entry.get("eligible", {})
    g = nx.from_graph6_bytes(selected[i]["graph6"][mode].encode("ascii"))
    actual_eligible = worker.previous.eligible_sources(g, limits)
    expected_parameters = [
        [m, n] for m in range(2, limits["max_m"] + 1)
        for n in range(limits["max_n"] + 1)
    ]
    # The finite family is a multiset; ordering is not part of a witness.
    # Counter preserves the multiplicity check (unlike a bare set).
    configured = search.get("configured_source_parameters")
    parameters_valid = (
        isinstance(configured, list)
        and all(
            isinstance(pair, list)
            and len(pair) == 2
            and all(type(x) is int for x in pair)
            for pair in configured
        )
        and Counter(map(tuple, configured)) == Counter(map(tuple, expected_parameters))
    )
    if (
        eligible != actual_eligible
        or search.get("limits") != limits
        or search.get("cover_classes_total") != 1
        or search.get("cover_classes_checked") != 1
        or search.get("cover_candidates_checked") != 1
        or not parameters_valid
        or not all(
            isinstance(search.get(k), int) and 0 <= search[k] <= limits[cap]
            for k, cap in (
                ("morphism_states", "max_morphism_states"),
                ("morphism_assignments", "max_morphism_assignments"),
            )
        )
    ):
        raise ValueError("Search does not match the frozen finite family")
    if status == "EXHAUSTED":
        if (
            search.get("search_status") != status
            or search.get("cover_classes_complete") is not True
            or search.get("morphisms_complete") is not True
            or entry.get("witness") is not None
            or entry.get("proof_status") != "none"
            or search.get("morphism_searches_exhausted")
                != sum(len(x["source_parameters_eligible"]) for x in eligible["covers"])
        ):
            raise ValueError("False complete-exhaustion claim")
    elif status == "LIMIT_REACHED":
        if (
            search.get("search_status") != status
            or entry.get("witness") is not None
            or entry.get("proof_status") != "none"
        ):
            raise ValueError("Invalid truncated bounded search")
    else:
        witness = entry.get("witness")
        if (
            status != "DIVERGENT"
            or entry.get("proof_status") != "verified"
            or search.get("search_status") != "FOUND"
            or not isinstance(witness, dict)
            or not isinstance(witness.get("m"), int)
            or witness["m"] not in range(2, limits["max_m"]+1)
            or not isinstance(witness.get("n"), int)
            or witness["n"] not in range(limits["max_n"]+1)
            or 2*witness["m"]*(witness["n"]+3) > limits["max_source_order"]
            or [witness["m"], witness["n"]]
                not in [p for c in eligible["covers"] for p in c["source_parameters_eligible"]]
            or witness.get("deck_radius") != witness["m"] + 1
            or witness.get("clique_bound") != limits["max_clique_vertices"]
            or witness.get("clique_max_edges") != limits["max_clique_edges"]
            or not verify_cover_witness(g, witness)
        ):
            raise ValueError("Positive iterate certificate failed independent replay")

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
    fd, raw = tempfile.mkstemp(prefix="iterate_", suffix=".partial", dir=OUTPUT)
    os.close(fd)
    started = time.monotonic()
    env = os.environ.copy()
    for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[key] = "1"
    try:
        with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as err:
            child = subprocess.Popen(
                [sys.executable, str(ROOT / "scripts/core9iterate_v1_worker.py"),
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
    lines = [
        "# Triangular-cover searches on pared first and second clique iterates",
        "",
        "These are eight historically unresolved nine-vertex cores. G1 and G2 are",
        "the *completely pared* clique iterates verified against the pinned",
        "CliqueSequence, not raw iterates. The 881 original ten-vertex graphs",
        "are represented only as historical metadata, not newly classified.",
        "EXHAUSTED is a finite-family negative result, not a proof of convergence.",
        "",
        "| Core ID | Represented ten-graphs | G1 | G1 assignments | G2 | G2 assignments |",
        "|---:|---:|---|---:|---|---:|",
    ]
    for i in EXPECTED_IDS:
        a = saved.get(f"g1_{i:08d}.json", {})
        b = saved.get(f"g2_{i:08d}.json", {})
        lines.append(
            f"| {i} | {selected[i]['member_count']} "
            f"| {a.get('status', '-')} | {a.get('search',{}).get('morphism_assignments','-')} "
            f"| {b.get('status', '-')} | {b.get('search',{}).get('morphism_assignments','-')} |"
        )
    lines += [
        "",
        "## Scope and provenance",
        "",
        "- New, isolated pinned-AC-3 experiment; all historical stages are read-only.",
        "- The complete configured family is m=2..3, n=0..2, with actual",
        "  eligible pairs recorded for each lifted graph and source-order limits.",
        "- Every positive iterate certificate is independently checked against",
        "  that iterate. No inference about earlier pared or original graphs is",
        "  promoted by this program without a separate transfer justification.",
        "- TIMEOUT, ERROR and LIMIT_REACHED are inconclusive. EXHAUSTED means",
        "  exhaustion solely of the recorded finite family, not nondivergence.",
        "",
    ]
    return "\n".join(lines)

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
    lockpath = ROOT / ".deps/core9iterate-v1.lock"
    lockpath.parent.mkdir(exist_ok=True)
    with lockpath.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise SystemExit(
                f"Another core9iterate-v1 run is in progress ({lockpath})"
            ) from error
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
            print(f"All {len(saved)} pared-iterate covering tasks are complete.", flush=True)
            return False
        for mode, i in chunks[index]:
            name = f"{mode}_{i:08d}.json"
            if name in saved:
                continue
            print(f"Core {i}, pared iterate {mode}", flush=True)
            entry = {
                "core_id": i, "mode": mode, "kind": mode,
                "input_graph6": selected[i]["graph6"][mode],
                "scope": "pared_iterate_only",
                **run_worker(mode, selected[i]["graph6"][mode]),
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
            fresh = run_worker(mode, selected[i]["graph6"][mode])
            if fresh["status"] in {"TIMEOUT", "ERROR"}:
                raise ValueError(f"Bounded replay failed for {mode}:{i}: {fresh['status']}")
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
    print(f"Validated {len(saved)}/{len(tasks())} pared-iterate records.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", default="next")
    cmd = parser.parse_args().command
    if cmd == "plan":
        require_pin()
        selected = cohort()
        print(
            f"Pin {PIN}: {len(selected)} cores, "
            f"{sum(row['member_count'] for row in selected.values())} represented "
            f"ten-vertex graphs, 16 searches (G1 and G2), four batches. "
            f"Maximum {TIMEOUT_SECONDS}s/{MEMORY_MIB}MiB per search."
        )
        print("The sources are completely pared iterates; core divergence is not asserted.")
        print("Clockworks: m=2..3, n=0..2, source order <=42; exact eligibility recorded.")
    elif cmd in ("verify", "replay"):
        verify(replay=(cmd == "replay"))
    elif cmd == "all":
        while run("next"):
            pass
    elif cmd == "next" or cmd.isdecimal():
        run(cmd)
    else:
        parser.error("Use plan, next, all, verify, replay, or batch number")


if __name__ == "__main__":
    main()

