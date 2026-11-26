"""Exact second-iterate coaffine exhaustion for four oversized-source graphs.

Run both EXISTING pycliques backends with explicit complete budgets.
EXHAUSTED excludes a coaffine weak endomorphism at P2 only; it does
not establish clique convergence, as original 11713984 explicitly
demonstrates at P3 by its verified expansive retract.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import sys

if sys.flags.optimize:
    raise RuntimeError("Do not optimize away coaffine exhaustion checks")

import networkx as nx

from research.order10_p4_crossdepth_o15_v25.verify import git_blob, source_rows
from research.order10_p3_global_v23_index.independent_verify import (
    independent_pare, independent_clique_graph,
)

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "indeterminate_order_10_v28.txt"
SNAPSHOT_BLOB = "35bb83b56bb8b4fd453b0ba272d354dc6b42e68c"
EXPECTED = {
    11505012: (29, 316, "5b2445d2e477c60f4350858a4ef28b68bcdb152b10f996a8232584b24a37a5d8"),
    11595632: (26, 251, "512771c26527e563f07ab52472d50440c8a51bab4422fca7a3316ddb9aa1a6b3"),
    11709142: (24, 223, "0aa5e5acf0761944dd56646ad583c38e4b4efbc5c1d403395ed85dba49344806"),
    11713984: (25, 244, "36c900f34d052d2293fb10d24f723f98c542b7ad49192eb5503418c44978cb99"),
}
MAX_STATES = 100_000
TIME_LIMIT = 20


def require(ok: bool, explanation: str) -> None:
    if not ok:
        raise AssertionError(explanation)


def source_p2(index: int) -> tuple[nx.Graph, str]:
    """Independent BK/NetworkX reconstruction from immutable original."""
    require(index in EXPECTED, "Unrecognized original for second-stage audit")
    require(git_blob(SNAPSHOT.read_bytes()) == SNAPSHOT_BLOB,
            "Immutable ten-v28 Git blob changed")
    source = source_rows(SNAPSHOT)[index]
    fields = source.split()
    require(len(fields) == 6
            and fields[:2] == [str(index), "10"]
            and fields[3:] == ["-", "-", "-"],
            "Unexpected original ten-v28 source entry")
    original = fields[2]
    G = independent_pare(nx.from_graph6_bytes(original.encode("ascii")))
    previous = [len(G)]
    for stage in (1, 2):
        graph = independent_clique_graph(G, stage=stage, orders=previous)
        G = independent_pare(graph)
        previous.append(len(G))
    graph6 = nx.to_graph6_bytes(G, header=False).decode("ascii").strip()
    shape = EXPECTED[index]
    require((len(G), G.number_of_edges()) == shape[:2]
            and hashlib.sha256(graph6.encode("ascii")).hexdigest() == shape[2],
            "Independently rebuilt canonical P2 graph6 differs")
    return G, original


def exhaustive_check(index: int, backend: str, order: str) -> dict:
    require(backend in ("python", "native")
            and order in ("label", "fiber"),
            "Unknown solver backend or branching order")
    from pycliques import find_coaffine_endomorphism
    G, original = source_p2(index)
    result = find_coaffine_endomorphism(
        G,
        backend=backend, value_order=order,
        max_states=MAX_STATES, time_limit=TIME_LIMIT,
    )
    require(result.status.name == "EXHAUSTED"
            and result.endomorphism is None
            and type(result.states_explored) is int
            and 0 <= result.states_explored < MAX_STATES
            and type(result.assignments_tried) is int
            and result.assignments_tried >= 0
            and type(result.arc_revisions) is int
            and result.arc_revisions >= 0,
            "Did not exhaust all coaffine weak endomorphisms at P2")
    return {
        "index": index,
        "original_graph6": original,
        "p2": list(EXPECTED[index][:2]),
        "p2_graph6_sha256": EXPECTED[index][2],
        "backend": backend,
        "value_order": order,
        "status": result.status.name,
        "states_explored": result.states_explored,
        "assignments_tried": result.assignments_tried,
        "arc_revisions": result.arc_revisions,
        "no_coaffine_weak_endomorphism_at_P2": True,
        "does_not_establish_K_convergence": True,
    }


def verify_all(*, include_native: bool = True) -> dict:
    if include_native:
        from research.order10_five_p3_native_v1.search import (
            MONOREPO_SHA, validate_runtime,
        )
        require(len(MONOREPO_SHA) == 40, "Missing pinned code revision")
        installed = validate_runtime()
    else:
        installed = None
    results = []
    for index in EXPECTED:
        for order in ("label", "fiber"):
            results.append(exhaustive_check(index, "python", order))
            if include_native:
                results.append(exhaustive_check(index, "native", order))
    require(len(results) == (16 if include_native else 8)
            and all(x["status"] == "EXHAUSTED" for x in results),
            "A second-stage coaffine exhaustion job was omitted")
    return {
        "schema": 1,
        "kind": "exact_P2_coaffine_weak_endomorphism_exhaustion",
        "source_snapshot": SNAPSHOT.name,
        "immutable_source_git_blob": SNAPSHOT_BLOB,
        "p2_shapes": {str(i): list(v[:2]) for i, v in EXPECTED.items()},
        "solver_backends": ["python", "native"] if include_native else ["python"],
        "native_solver_source_blobs_and_dependencies_checked": include_native,
        "dependency_versions": installed,
        "originals_no_coaffine_at_P2": sorted(EXPECTED),
        "fourth_graph_is_certified_divergent_by_P3_retract": 11713984,
        "cannot_infer_convergence_from_P2_exhaustion": True,
        "results": results,
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend-scope", choices=("both", "python"),
                        default="both")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    outcome = verify_all(include_native=args.backend_scope == "both")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(outcome, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "P2_exhausted_originals": outcome["originals_no_coaffine_at_P2"],
        "backends": outcome["solver_backends"],
        "complete_checks": len(outcome["results"]),
    }, sort_keys=True), flush=True)
    print("PASS: exact P2 coaffine endomorphism exhaustion in both public backends",
          flush=True)


if __name__ == "__main__":
    main()
