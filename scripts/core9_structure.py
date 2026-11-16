"""Versioned structural investigation of 29 historically unresolved nine-cores.

New diagnostics ONLY; this stage never returns a convergence/divergence
verdict or edits a historical record. Distinguishes a certified homology
calculation from bounded exploratory searches. Uses the frozen v3 pin.

    bash scripts/core9_structure.sh plan
    bash scripts/core9_structure.sh next
    bash scripts/core9_structure.sh all
    bash scripts/core9_structure.sh verify

Worker scope: pared iterates that were *actually constructed* at bound
120 in the completed core9 benchmark; do not invent an unavailable G3.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
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
from pycliques.small import CliqueSequence

import core9_crossref
import core9_structure_worker as worker
from timeboxed_v3 import current_v3_pin

ROOT = Path(__file__).resolve().parents[1]
CROSSREF = ROOT / "reports/order10_core9_crossref_v1"
BENCH = ROOT / "runs/order10/core9-benchmark-v1"
FOLDER = ROOT / "runs/order10/core9-structure-v1"
BATCH_SIZE = 5
TIMEOUT = 45
MEMORY_MIB = 2048


def sha(path: Path) -> str:
    return core9_crossref.sha(path)


def atomic(path: Path, obj: dict | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".partial")
    try:
        payload = obj if isinstance(obj, str) else json.dumps(obj, sort_keys=True, indent=2) + "\n"
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def cohort() -> dict[int, dict]:
    """Require complete, byte-exact historical cross-reference and benchmark."""
    core9_crossref.verify_saved(CROSSREF, core9_crossref.prepare())
    lines = (CROSSREF / "unclassified.tsv").read_text(encoding="utf-8").splitlines()
    header = "core_id\tcore_graph6\toriginal_members\torder9_index\torder9_graph6\tlast_stage_examined"
    if not lines or lines[0] != header:
        raise ValueError("Malformed frozen unclassified core9 table")
    selected = {}
    original_total = 0
    for line in lines[1:]:
        fields = line.split("\t")
        if len(fields) != 6:
            raise ValueError("Malformed unclassified nine-core record")
        core_id, g6, members, index9, g9, stage = fields
        i = int(core_id)
        graph = nx.from_graph6_bytes(g6.encode("ascii"))
        if i in selected or graph.order() != 9 or not nx.is_connected(graph):
            raise ValueError(f"Corrupt nine-core source {i}")
        path = BENCH / "records" / f"{i:08d}.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        if (
            record.get("core_id") != i
            or record.get("graph6") != g6
            or record.get("member_count") != int(members)
            or record.get("status") != "BOUND_EXCEEDED"
            or record.get("bound") != 120
            or record.get("scope") != "pared_core_only"
            or len([r for r in record.get("iterates", [])
                    if r.get("status") == "clique_bound_exceeded"]) != 1
        ):
            raise ValueError(f"Frozen core9 benchmark does not support {i}")
        failure = next(
            r["index"] for r in record["iterates"]
            if r.get("status") == "clique_bound_exceeded"
        )
        if failure not in (3, 4):
            raise ValueError(f"Unexpected historical bound failure at {i}")
        selected[i] = {
            "graph6": g6, "member_count": int(members),
            "order9_index": int(index9), "order9_graph6": g9,
            "last_order9_stage": stage,
            "failure_iterate": failure,
            "expected_iterates": record["iterates"],
            "original_methods": record.get("methods_tried", []),
            "benchmark_record_sha256": sha(path),
        }
        original_total += int(members)
    if len(selected) != 29 or original_total != 3738:
        raise ValueError("Expected 29 unresolved nine-cores representing 3738 originals")
    return dict(sorted(selected.items()))


def manifest(selected: dict[int, dict]) -> dict:
    dependencies = {
        "runner_sha256": ROOT / "scripts/core9_structure.py",
        "worker_sha256": ROOT / "scripts/core9_structure_worker.py",
        "launcher_sha256": ROOT / "scripts/core9_structure.sh",
        "crossref_script_sha256": ROOT / "scripts/core9_crossref.py",
        "crossref_manifest_sha256": CROSSREF / "manifest.json",
        "crossref_unclassified_sha256": CROSSREF / "unclassified.tsv",
        "crossref_matches_sha256": CROSSREF / "matches.tsv",
        "benchmark_manifest_sha256": BENCH / "manifest.json",
        "benchmark_summary_sha256": BENCH / "summary.json",
        "pin_checker_sha256": ROOT / "scripts/timeboxed_v3.py",
        "bootstrap_sha256": ROOT / "scripts/bootstrap_v3.sh",
        "pin_file_sha256": ROOT / "config/pycliques_commit_v3.txt",
    }
    return {
        "schema": 1,
        "stage": "core9-structure-v1",
        "object": "29 historically unresolved nine-vertex completely pared cores",
        "core_ids": sorted(selected),
        "original_members": 3738,
        "benchmark_record_sha256": {
            str(i): row["benchmark_record_sha256"] for i, row in selected.items()
        },
        "v3_upstream_commit": current_v3_pin(),
        "parallel_workers": 1, "batch_size": BATCH_SIZE,
        "per_core_timeout_seconds": TIMEOUT, "per_worker_memory_mib": MEMORY_MIB,
        "clique_sequence_bound": worker.CLIQUE_BOUND,
        "max_clique_sample": worker.MAX_CLIQUES,
        "clockwork_candidates_per_iterate": worker.CLOCKWORK_CANDIDATES,
        "coaffinations_cap": worker.COAFFINATIONS_CAP,
        "claim_scope": "structural_exploration_only; no original-ten-graph verdict",
        **{name: sha(path) for name, path in dependencies.items()},
    }


def ensure_manifest(meta: dict) -> None:
    path = FOLDER / "manifest.json"
    if path.exists():
        if json.loads(path.read_text(encoding="utf-8")) != meta:
            raise ValueError("Refusing to resume: inputs, limits, scripts, or v3 pin changed")
        return
    if FOLDER.exists() and any(FOLDER.iterdir()):
        raise ValueError("Output exists without its frozen provenance manifest")
    atomic(path, meta)


def validate_record(record: dict, core_id: int, selected: dict) -> None:
    info = selected[core_id]
    if (
        record.get("core_id") != core_id
        or record.get("input_graph6") != info["graph6"]
        or record.get("member_count") != info["member_count"]
        or record.get("scope") != "structural_diagnostics_only"
        or record.get("failure_iterate") not in (info["failure_iterate"], None)
        or record.get("status") not in {"OK", "TIMEOUT", "ERROR"}
        or record.get("max_clique_sample") not in (None, worker.MAX_CLIQUES)
    ):
        raise ValueError(f"Invalid structure record for core {core_id}")
    if record["status"] == "OK":
        if record["failure_iterate"] != info["failure_iterate"]:
            raise ValueError(f"Incorrect structural diagnostic depth at {core_id}")
        iterates = record.get("iterates", [])
        if len(iterates) != info["failure_iterate"]:
            raise ValueError(f"Incorrect number of reconstructed iterates at {core_id}")
        # Saved intermediate graph6 is not trusted as an independent source.
        # Replay the pinned K-and-paring sequence from the nine-vertex core.
        # An unrelated graph with the *same* order and edge count must fail.
        origin = nx.from_graph6_bytes(info["graph6"].encode("ascii"))
        sequence = CliqueSequence(origin, bound=worker.CLIQUE_BOUND)
        for step, (row, old) in enumerate(zip(iterates, info["expected_iterates"])):
            if (
                row.get("index") != step
                or row.get("order") != old.get("pared_order")
                or row.get("edges") != old.get("pared_edges")
                or row.get("maximal_cliques", {}).get("maximal_cliques_at_least", 0) < 0
                or row.get("betti1_mod2", -1) < 0
            ):
                raise ValueError(f"Invalid core {core_id} iterate {step}")
            try:
                recorded = nx.from_graph6_bytes(row["graph6"].encode("ascii"))
            except (KeyError, AttributeError, TypeError, ValueError) as error:
                raise ValueError(f"Malformed saved iterate at core {core_id}") from error
            expected = sequence[step]
            if expected is None or not nx.is_isomorphic(recorded, expected):
                raise ValueError(
                    f"Saved G_{step} is not the actual clique iterate of core {core_id}"
                )


def records(selected: dict[int, dict]) -> dict[int, dict]:
    result = {}
    for path in sorted((FOLDER / "records").glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        i = record.get("core_id")
        if (
            not isinstance(i, int) or i in result or i not in selected
            or path.name != f"{i:08d}.json"
        ):
            raise ValueError(f"Unexpected/duplicate diagnostic record: {path}")
        validate_record(record, i, selected)
        result[i] = record
    return result


def limit_worker() -> None:
    bytes_limit = MEMORY_MIB * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (bytes_limit, bytes_limit))


def run_one(info: dict) -> dict:
    """Isolated worker. Timeouts, OOMs, and crashes are *unknown*, not negative."""
    FOLDER.mkdir(parents=True, exist_ok=True)
    fd_out, output = tempfile.mkstemp(prefix="core9_diags_", suffix=".partial", dir=FOLDER)
    fd_in, expected = tempfile.mkstemp(prefix="core9_baseline_", suffix=".partial", dir=FOLDER)
    os.close(fd_out)
    os.close(fd_in)
    Path(expected).write_text(json.dumps(info["expected_iterates"]), encoding="utf-8")
    env = os.environ.copy()
    for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[key] = "1"
    begin = time.monotonic()
    try:
        with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as errors:
            proc = subprocess.Popen(
                [sys.executable, str(ROOT / "scripts/core9_structure_worker.py"),
                 info["graph6"], expected, output],
                cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=errors,
                start_new_session=True, preexec_fn=limit_worker,
            )
            try:
                proc.wait(timeout=TIMEOUT)
            except subprocess.TimeoutExpired:
                if proc.poll() is None:
                    os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
                return {
                    "status": "TIMEOUT",
                    "reason": f"Worker exceeded {TIMEOUT} seconds",
                    "elapsed_seconds": round(time.monotonic()-begin, 3),
                    "scope": "structural_diagnostics_only",
                }
            except BaseException:
                if proc.poll() is None:
                    os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
                raise
            elapsed = round(time.monotonic() - begin, 3)
            if proc.returncode == 0:
                try:
                    data = json.loads(Path(output).read_text(encoding="utf-8"))
                    if data.get("scope") != "structural_diagnostics_only":
                        raise ValueError("Incorrect worker scope")
                    return {"status": "OK", "elapsed_seconds": elapsed, **data}
                except (OSError, ValueError, TypeError) as error:
                    problem = f"Invalid worker output: {error}"
            else:
                problem = f"Worker exited with code {proc.returncode}"
            errors.seek(0)
            return {
                "status": "ERROR", "reason": problem,
                "stderr_excerpt": errors.read(3000),
                "elapsed_seconds": elapsed,
                "scope": "structural_diagnostics_only",
            }
    finally:
        Path(output).unlink(missing_ok=True)
        Path(expected).unlink(missing_ok=True)


def report(saved: dict[int, dict]) -> str:
    lines = [
        "# Targeted structural investigation: 29 unresolved order-nine cores",
        "",
        "This report records **no new clique-behavior classification**.",
        "Mod-2 first Betti numbers are exact for each stored flag complex;",
        "zero rules out a *connected triangular double cover of that iterate*,",
        "but does not establish convergence. Induced clockworks are candidate",
        "subgraphs only, never divergence certificates for their hosts.",
        "Truncated maximal-clique counts give lower bounds, not estimates.",
        "",
        "| Core ID | Members | Built prefix | b1(F2), G0.. | G_last maximal cliques | Clockwork observations | Seconds | Status |",
        "|---:|---:|---|---|---|---:|---:|---|",
    ]
    by_b1 = Counter()
    wl = defaultdict(list)
    full = 0
    for i, row in sorted(saved.items()):
        if row["status"] != "OK":
            lines.append(
                f"| {i} | {row['member_count']} | - | - | - | - | "
                f"{row.get('elapsed_seconds', 0):.2f} | {row['status']} |"
            )
            continue
        full += 1
        data = row["iterates"]
        last = data[-1]
        b1 = [r["betti1_mod2"] for r in data]
        by_b1[tuple(b1)] += 1
        clique = last["maximal_cliques"]
        count = (
            str(clique["maximal_cliques_exact"])
            if clique["exact"] else
            f">={clique['maximal_cliques_at_least']}"
        )
        potential = sum(
            len(r.get("divergent_induced_clockwork", {}).get("witnesses", ()))
            for r in data
        )
        wl[(last["order"], last["edges"], last["wl3_hash"])].append(i)
        lines.append(
            f"| {i} | {row['member_count']} | G0..G{len(data)-1} "
            f"| {','.join(map(str, b1))} | {count} | {potential} "
            f"| {row.get('elapsed_seconds',0):.2f} | OK |"
        )
    lines += [
        "", "## Observations", "",
        f"- Fully probed cores: {full} of {len(saved)} recorded.",
        f"- Last-iterate WL/size signature collisions: "
        f"{sum(len(v) for v in wl.values() if len(v)>1)} core entries.",
        "- Matching WL hashes are only candidate pairs, not graph isomorphism.",
        "- An observed clockwork is not a verified retraction from the host.",
        "",
        "## Identical last-iterate fingerprints (not asserted isomorphic)", "",
    ]
    duplicate = sorted((v for v in wl.values() if len(v) > 1),
                       key=lambda ids: (-len(ids), ids))
    for core_ids in duplicate:
        lines.append("- " + ", ".join(map(str, core_ids)))
    if not duplicate:
        lines.append("No repeated last-iterate WL/size signatures.")
    lines += ["", "## First Betti number vectors", "",
              "| b1(G0),...,b1(Glast) | Cores |",
              "|---|---:|"]
    for vector, n in sorted(by_b1.items()):
        lines.append(f"| {vector} | {n} |")
    lines += [
        "", "## Next experiments", "",
        "Prioritize candidates by original membership, exact last-iterate",
        "clique count, and structural obstacles. Cover-based divergence",
        "search is relevant only at iterates with positive H^1(F2).",
        "Test specific verified retractions only when a candidate target",
        "is actually identified; avoid promoting bounded searches to proofs.",
        "",
    ]
    return "\n".join(lines)


def write_progress(selected: dict, saved: dict) -> None:
    chunks = [list(selected)[start:start+BATCH_SIZE]
              for start in range(0, len(selected), BATCH_SIZE)]
    progress = {
        "processed": len(saved), "total": len(selected),
        "counts": dict(sorted(Counter(r["status"] for r in saved.values()).items())),
        "completed_batches": sum(all(i in saved for i in chunk) for chunk in chunks),
        "total_batches": len(chunks),
    }
    atomic(FOLDER / "progress.json", progress)
    if len(saved) == len(selected):
        atomic(FOLDER / "summary.json", {"manifest": json.loads(
            (FOLDER / "manifest.json").read_text(encoding="utf-8")
        ), **progress})
        atomic(FOLDER / "report.md", report(saved))


def run(batch: str) -> bool:
    selected = cohort()
    meta = manifest(selected)
    lockdir = ROOT / ".deps"
    lockdir.mkdir(exist_ok=True)
    with (lockdir / "core9-structure-v1.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ensure_manifest(meta)
        (FOLDER / "records").mkdir(exist_ok=True)
        saved = records(selected)
        chunks = [list(selected)[start:start+BATCH_SIZE]
                  for start in range(0, len(selected), BATCH_SIZE)]
        if batch == "next":
            n = next((j for j, chunk in enumerate(chunks)
                      if any(i not in saved for i in chunk)), None)
        else:
            n = int(batch)
            if not 0 <= n < len(chunks):
                raise ValueError(f"Invalid batch number; must be 0..{len(chunks)-1}")
        if n is None:
            write_progress(selected, saved)
            print(f"All {len(saved)} structural probes complete.")
            return False
        for i in chunks[n]:
            if i in saved:
                continue
            info = selected[i]
            print(f"Core {i} ({info['member_count']} original graphs)", flush=True)
            entry = {
                "core_id": i, "input_graph6": info["graph6"],
                "member_count": info["member_count"],
                "scope": "structural_diagnostics_only",
                **run_one(info),
            }
            validate_record(entry, i, selected)
            atomic(FOLDER / "records" / f"{i:08d}.json", entry)
            saved[i] = entry
            print(f"  {entry['status']} in {entry['elapsed_seconds']:.2f}s",
                  flush=True)
        write_progress(selected, saved)
        print(f"Checkpoint {len(saved)}/{len(selected)}", flush=True)
        return len(saved) < len(selected)


def verify() -> None:
    selected = cohort()
    meta = manifest(selected)
    if not (FOLDER / "manifest.json").is_file():
        raise ValueError("No structural investigation has started")
    ensure_manifest(meta)
    saved = records(selected)
    for i, result in sorted(saved.items()):
        if result["status"] != "OK":
            continue
        # Recompute the exact finite structural invariants from each saved
        # graph, including clique counts and GF(2) Betti, without trusting
        # the first worker's numerical claims.
        for row in result["iterates"]:
            g = nx.from_graph6_bytes(row["graph6"].encode("ascii"))
            b1, tris, rank = worker.betti1_mod2(g)
            sample = worker.clique_sample(g)
            if (
                len(g) != row["order"]
                or g.number_of_edges() != row["edges"]
                or (b1, tris, rank) != (
                    row["betti1_mod2"], row["triangles"],
                    row["triangle_boundary_rank_mod2"]
                )
                or sample != row["maximal_cliques"]
            ):
                raise ValueError(f"Structural invariants failed replay: {i}")
    if len(saved) == len(selected):
        expected = {
            "manifest": meta,
            "processed": len(saved), "total": len(selected),
            "counts": dict(sorted(Counter(x["status"] for x in saved.values()).items())),
            "completed_batches": (len(selected) + BATCH_SIZE-1)//BATCH_SIZE,
            "total_batches": (len(selected) + BATCH_SIZE-1)//BATCH_SIZE,
        }
        if json.loads((FOLDER / "summary.json").read_text(encoding="utf-8")) != expected:
            raise ValueError("Structure summary disagrees with verified records")
    print(f"Independently checked {len(saved)} records ({sum(r['status']=='OK' for r in saved.values())} successful probes).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", default="next")
    args = parser.parse_args()
    if args.command == "plan":
        selected = cohort()
        pin = current_v3_pin()
        print(
            f"29 historically unresolved cores, 3738 original graph members; "
            f"6 batches, {TIMEOUT}s and {MEMORY_MIB} MiB per core, "
            f"clique cap {worker.MAX_CLIQUES}. V3 pin {pin}"
        )
    elif args.command == "verify":
        verify()
    elif args.command == "all":
        while run("next"):
            pass
    elif args.command == "next" or args.command.isdecimal():
        run(args.command)
    else:
        parser.error("Use plan, next, all, verify or a nonnegative batch number")


if __name__ == "__main__":
    main()
