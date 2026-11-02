#!/usr/bin/env python3
"""Check whether K(G) retracts onto the complement of C_10.

Process only INDETERMINATE order-9 graphs without a conjectured-divergent
reference dependency, as recorded by the completed connected census.

Positive results include explicit independently checked retraction witnesses.
NO_RETRACTION requires exhaustive search; budget exhaustion is INCONCLUSIVE.
Per-graph JSON files are written atomically, making this post-pass resumable.
No original census data is changed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

import networkx as nx
from networkx.algorithms import isomorphism
from pycliques.cliques import clique_graph
from pycliques.named import complement_of_cycle
from pycliques.retractions import RetractionSearchStatus, bounded_retraction


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".partial")
    tmp.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def load_candidates(run_dir: Path) -> tuple[dict, list[dict]]:
    """Check cohort consistency, using source indices and original graph6."""
    manifest_file = run_dir / "manifest.json"
    summary_file = run_dir / "summary.json"
    cohort_file = run_dir / "order9" / "indeterminate_order_9.txt"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    summary = json.loads(summary_file.read_text(encoding="utf-8"))
    if manifest.get("min_order") != 9 or manifest.get("max_order") != 9:
        raise ValueError("This post-pass requires a completed order-9-only census")
    if summary.get("manifest") != manifest:
        raise ValueError("Summary and run manifest disagree")
    orders = summary.get("orders", [])
    if (
        len(orders) != 1
        or orders[0].get("order") != 9
        or orders[0].get("connected_total") != 261080
    ):
        raise ValueError("Order-9 census is not complete and validated")
    unresolved = summary.get("unresolved", [])
    if len(unresolved) != orders[0].get("indeterminate"):
        raise ValueError("Unresolved count does not agree with census totals")
    by_index: dict[int, dict] = {}
    for row in unresolved:
        idx = row["index"]
        if row["order"] != 9 or idx in by_index:
            raise ValueError("Malformed or duplicate unresolved original index")
        by_index[idx] = row

    status_by_index: dict[int, str] = {}
    for line in cohort_file.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        fields = line.split()
        if len(fields) != 6:
            raise ValueError(f"Expected six fields in unresolved cohort: {line!r}")
        index = int(fields[0])
        if index in status_by_index:
            raise ValueError(f"Duplicate unresolved index {index}")
        if fields[4] not in ("-", "conjectured_divergent"):
            raise ValueError(
                f"Unexpected conditional target status at index {index}: {fields[4]}"
            )
        status_by_index[index] = fields[4]
    if set(status_by_index) != set(by_index):
        raise ValueError("Unresolved indices differ between cohort and summary")

    selected: list[dict] = []
    excluded = 0
    for index in sorted(by_index):
        item = by_index[index]
        conjectured = status_by_index[index] == "conjectured_divergent"
        # Never silently include a conditional verdict if metadata is missing.
        reason_conditional = "conjectur" in item["reason"].lower()
        if reason_conditional != conjectured:
            raise ValueError(
                f"Inconsistent conjectured-divergence metadata at index {index}"
            )
        if conjectured:
            excluded += 1
        else:
            selected.append({
                "index": index,
                "graph6": item["graph6"],
                "original_reason": item["reason"],
            })

    provenance = {
        "schema": 1,
        "order": 9,
        "source_run_manifest_sha256": digest(manifest_file),
        "source_run_summary_sha256": digest(summary_file),
        "unresolved_cohort_sha256": digest(cohort_file),
        "source_upstream_commit": manifest["upstream_commit"],
        "source_chunk_lineage_sha256": manifest.get("chunk_lineage_sha256"),
        "target": "complement_of_cycle(10)",
        "graph_under_test": "K(G)",
        "total_indeterminate": len(unresolved),
        "conjectured_excluded": excluded,
        "eligible": len(selected),
        "eligible_indices": [x["index"] for x in selected],
    }
    return provenance, selected


def search_retraction(
    graph: nx.Graph,
    *,
    max_embeddings: int = 1000,
    max_states: int = 100_000,
    max_assignments: int = 1_000_000,
) -> dict:
    """Search every induced target copy up to explicit resource limits."""
    target = complement_of_cycle(10)
    kg = clique_graph(graph)  # Exact, unbounded K(G): all maximal completes.
    if kg is None:
        raise RuntimeError("Unbounded clique graph construction failed")
    cliques = sorted(tuple(sorted(clique)) for clique in kg)
    numbered = nx.relabel_nodes(
        kg, {frozenset(vertices): i for i, vertices in enumerate(cliques)},
        copy=True,
    )
    result: dict = {
        "K_order": numbered.number_of_nodes(),
        "K_edges": numbered.number_of_edges(),
        "K_vertex_cliques": [list(clique) for clique in cliques],
        "embeddings_checked": 0,
        "limited_embeddings": 0,
        "states_explored": 0,
        "assignments_tried": 0,
        "witness": None,
    }
    if len(numbered) < len(target):
        result["status"] = "NO_RETRACTION"
        result["reason"] = "K(G) has fewer than 10 vertices"
        return result

    seen_target_sets: set[frozenset[int]] = set()
    limited = False
    for embedding in isomorphism.GraphMatcher(
        numbered, target
    ).subgraph_isomorphisms_iter():
        # Different target labelings of the same induced ten-vertex copy do
        # not affect the existence of a retraction.
        keys = frozenset(embedding)
        if keys in seen_target_sets:
            continue
        seen_target_sets.add(keys)
        if result["embeddings_checked"] >= max_embeddings:
            limited = True
            break
        result["embeddings_checked"] += 1
        induced = numbered.subgraph(keys).copy()
        attempt = bounded_retraction(
            numbered,
            induced,
            max_states=max_states,
            max_assignments=max_assignments,
        )
        result["states_explored"] += attempt.states_explored
        result["assignments_tried"] += attempt.assignments_tried
        if attempt.status is RetractionSearchStatus.LIMIT_REACHED:
            limited = True
            result["limited_embeddings"] += 1
            continue
        if attempt.status is not RetractionSearchStatus.FOUND:
            continue

        retraction = attempt.retraction
        if retraction is None:
            raise RuntimeError("Retraction search returned FOUND without a map")
        inverse = {value: key for key, value in embedding.items()}
        if set(inverse) != set(target) or set(retraction) != set(numbered):
            raise RuntimeError("Invalid retraction witness: incomplete maps")
        # Images in target vertex labels, indexed by K(G)'s numbered vertices.
        f = [embedding[retraction[v]] for v in range(len(numbered))]
        if any(f[u] != f[v] and not target.has_edge(f[u], f[v]) for u, v in numbered.edges()):
            raise RuntimeError("Retraction witness does not preserve adjacency-or-equality")
        if any(f[host_vertex] != target_vertex for target_vertex, host_vertex in inverse.items()):
            raise RuntimeError("Retraction witness does not fix the included target")
        if not nx.is_isomorphic(induced, target):
            raise RuntimeError("Retraction target is not an induced complement of C10")
        result["status"] = "RETRACTION_FOUND"
        result["reason"] = "Independently verified graph morphism fixing an induced complement of C10"
        result["witness"] = {
            "target_vertex_to_K_vertex": [inverse[i] for i in range(10)],
            "K_vertex_to_target_vertex": f,
        }
        return result

    result["status"] = "INCONCLUSIVE" if limited else "NO_RETRACTION"
    result["reason"] = (
        "At least one induced target embedding was not exhaustively searched"
        if limited
        else "All induced target embeddings were exhausted with no retraction"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir", type=Path, required=True,
        help="Completed order-9 census directory with summary.json",
    )
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--max-embeddings", type=int, default=1000)
    parser.add_argument("--max-states", type=int, default=100_000)
    parser.add_argument("--max-assignments", type=int, default=1_000_000)
    args = parser.parse_args()
    if min(args.max_embeddings, args.max_states, args.max_assignments) < 1:
        parser.error("All search budgets must be positive")
    run_dir = args.run_dir.resolve()
    output = (
        args.output_dir.resolve() if args.output_dir is not None
        else run_dir / "postpasses" / "clique_retract_comp_c10"
    )
    source = Path(__file__).resolve().parents[1] / ".deps" / "pycliques-project"
    commit = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    pin = (Path(__file__).resolve().parents[1] / "config" / "pycliques_commit.txt").read_text().strip()
    if commit != pin:
        raise ValueError("Installed dependency does not match the repository pin")
    meta, candidates = load_candidates(run_dir)
    meta.update({
        "postpass_source_sha256": digest(Path(__file__)),
        "executing_upstream_commit": commit,
        "max_embeddings": args.max_embeddings,
        "max_states": args.max_states,
        "max_assignments": args.max_assignments,
    })
    output.mkdir(parents=True, exist_ok=True)
    meta_file = output / "manifest.json"
    if meta_file.is_file():
        if json.loads(meta_file.read_text(encoding="utf-8")) != meta:
            raise ValueError("Existing post-pass manifest differs; choose another output directory")
    else:
        # Do not adopt an old output directory without a compatible manifest.
        if any(output.iterdir()):
            raise ValueError("Nonempty output directory without post-pass manifest")
        write_json_atomic(meta_file, meta)

    records = output / "records"
    records.mkdir(exist_ok=True)
    allowed = {f"{row['index']:06d}.json" for row in candidates}
    unexpected = {p.name for p in records.glob("*.json")} - allowed
    if unexpected:
        raise ValueError(f"Unexpected result files: {sorted(unexpected)}")
    for number, row in enumerate(candidates, start=1):
        idx = row["index"]
        dest = records / f"{idx:06d}.json"
        if dest.exists():
            saved = json.loads(dest.read_text(encoding="utf-8"))
            if saved.get("index") != idx or saved.get("graph6") != row["graph6"]:
                raise ValueError(f"Inconsistent saved post-pass record at index {idx}")
            print(f"[{number}/{len(candidates)}] index={idx} already checked", flush=True)
            continue
        graph = nx.from_graph6_bytes(row["graph6"].encode("ascii"))
        print(f"[{number}/{len(candidates)}] testing K(G), index={idx}, graph6={row['graph6']}", flush=True)
        result = search_retraction(
            graph,
            max_embeddings=args.max_embeddings,
            max_states=args.max_states,
            max_assignments=args.max_assignments,
        )
        write_json_atomic(dest, {"index": idx, "graph6": row["graph6"], **result})
        print(f"  {result['status']}: {result['reason']}", flush=True)

    rows = [json.loads((records / f"{row['index']:06d}.json").read_text(encoding="utf-8"))
            for row in candidates]
    counts = Counter(row["status"] for row in rows)
    result_summary = {
        "manifest": meta,
        "statuses": dict(sorted(counts.items())),
        "tested_indices": [row["index"] for row in rows],
        "retraction_indices": [row["index"] for row in rows if row["status"] == "RETRACTION_FOUND"],
        "inconclusive_indices": [row["index"] for row in rows if row["status"] == "INCONCLUSIVE"],
        "records": "records/{index:06d}.json",
    }
    write_json_atomic(output / "summary.json", result_summary)
    print(
        f"Complete: eligible={len(rows)}; "
        + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())),
        flush=True,
    )
    print(f"Summary saved: {output / 'summary.json'}", flush=True)


if __name__ == "__main__":
    main()
