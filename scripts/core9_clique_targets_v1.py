"""Certified retraction search onto K(susp(C_n)) and K(C_n^c).

Input graphs are the third *completely pared* clique iterates of two
unresolved stiff nine-vertex graph classes. Exact mod-2 homology and
vertex/edge bounds prove that all except K(C_10^c) for core 6914104
are impossible as retracts. A finite induced-embedding search then
checks every K(C_10^c) copy (two independent isomorphism implementations)
and independently solves each ordinary graph-retraction CSP.

Explicitly ONLY the proven divergent source cycles/complements are
eligible: susp(C_n), n>=4, and C_n^c, n>=8. Rejection is neither a
K-convergence certificate nor a claim about other target families.
Historical reports and previously certified graphs are never mutated.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile

import networkx as nx
from networkx.algorithms.isomorphism import GraphMatcher, ISMAGS
from pycliques.retractions import bounded_retraction, RetractionSearchStatus

import core9_third_retractions_v2 as previous
import core9_three_target_v1 as initial

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research/order10_core9_clique_targets_v1"
PREVIOUS = ROOT / "research/order10_core9_third_retractions_v2"
SOURCE = ROOT / "runs/order10/core9-structure-v1/records"
PIN = ROOT / "config/pycliques_commit_core9_three_target_v1.txt"
CORES = (6914104, 6962151)
SCHEMA = 1
TARGET_PARAMS_SUSP = range(4, 21)
TARGET_PARAMS_COMP = range(8, 14)
TIMEOUT_SECONDS = 110
MEMORY_MIB = 2048
CSP_STATES = 30000
CSP_ASSIGNMENTS = 60000

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encode(graph: nx.Graph) -> str:
    return nx.to_graph6_bytes(
        nx.convert_node_labels_to_integers(graph), header=False
    ).decode("ascii").strip()


def raw_clique_graph(graph: nx.Graph) -> nx.Graph:
    """Independent clique graph construction (maximal cliques, not all completes)."""
    facets = tuple(sorted(tuple(sorted(q)) for q in nx.find_cliques(graph)))
    values = [set(q) for q in facets]
    result = nx.Graph()
    result.add_nodes_from(range(len(facets)))
    result.add_edges_from(
        (i, j) for i in range(len(facets))
        for j in range(i + 1, len(facets))
        if values[i] & values[j]
    )
    return result


def suspension_cycle(n: int) -> nx.Graph:
    if n < 4:
        raise ValueError("Require suspension of cycle length >= 4")
    base = nx.cycle_graph(n)
    base.add_nodes_from((n, n + 1))
    base.add_edges_from((i, p) for i in range(n) for p in (n, n + 1))
    return base


def complement_cycle(n: int) -> nx.Graph:
    if n < 8:
        raise ValueError("Only established K-divergent C_n complements n>=8")
    return nx.complement(nx.cycle_graph(n))


def perrin(n: int) -> int:
    """Number of maximal independent sets of a cycle of length n.

    Cyclic binary words for maximal independent sets have no adjacent
    ones and no three consecutive zeros; their transfer matrix has
    characteristic polynomial t^3-t-1. Hence the Perrin recurrence
    P_n=P_(n-2)+P_(n-3). The verified P8..P10 are 10,12,17.
    """
    if n < 8:
        raise ValueError("Only need cycle lengths >= 8")
    p = {8: 10, 9: 12, 10: 17}
    for k in range(11, n + 1):
        p[k] = p[k-2] + p[k-3]
    return p[n]


def host(core_id: int) -> tuple[nx.Graph, dict[int, int]]:
    """Recompute and authenticate the canonical, frozen graph6 source."""
    record = json.loads((SOURCE / f"{core_id:08d}.json").read_text())
    if core_id not in CORES or record["input_graph6"] != initial.CORE[core_id][0]:
        raise ValueError("Invalid stiff core ID or frozen graph6")
    third = record["iterates"][3]
    graph = nx.from_graph6_bytes(third["graph6"].encode("ascii"))
    if (
        len(graph) != third["order"]
        or graph.number_of_edges() != third["edges"]
        or not nx.is_isomorphic(graph, previous.third_iterate(core_id))
    ):
        raise ValueError("Frozen graph6 is not the authentic pinned K3 graph")
    earlier = json.loads(
        (PREVIOUS / "records" / f"{core_id:08d}.json").read_text()
    )
    expected = {
        int(k): v for k, v in
        earlier["reduced_mod2_betti_through_degree_5"].items()
    }
    computed = previous.exact_low_betti(graph)
    if expected != computed or earlier["positive_certificates"]:
        raise ValueError("Frozen homology or previous negative evidence changed")
    return graph, computed


def complement_edge_lower_bound(graph: nx.Graph, target_order: int) -> int:
    """Necessary complement-edge count for any induced target of this order."""
    n = len(graph)
    if target_order > n:
        raise ValueError("Target has more vertices than source")
    c = nx.complement(graph)
    omitted = n - target_order
    degree_sum = sum(sorted((d for _, d in c.degree()), reverse=True)[:omitted])
    return c.number_of_edges() - degree_sum


def compare_homology(
    source: dict[int, int], target: nx.Graph, degree: int,
) -> dict[str, object]:
    exact = previous.exact_low_betti(target, max_degree=degree)
    violating = [
        d for d, rank in exact.items() if rank > source.get(d, -1)
    ]
    return {
        "target_betti": {str(d): x for d, x in exact.items()},
        "obstructing_degrees": violating,
        "homologically_allowed": not violating,
    }


def enumerate_induced_c10(
    graph: nx.Graph, target: nx.Graph,
) -> tuple[list[list[int]], dict[str, int]]:
    """Two independent induced-isomorphism enumerators agree on image sets.

    Both operate on the complements to avoid dense adjacency scans.
    VF2 visits all labeled embeddings; ISMAGS may quotient target
    automorphisms. Their *sets of selected vertex subsets* must agree.
    """
    comp = nx.complement(graph)
    comp_target = nx.complement(target)
    ismags_sets = {
        frozenset(embedding)
        for embedding in ISMAGS(comp, comp_target).subgraph_isomorphisms_iter()
    }
    vf2_sets: set[frozenset[int]] = set()
    vf2_maps = 0
    for phi in GraphMatcher(comp, comp_target).subgraph_isomorphisms_iter():
        vf2_maps += 1
        vf2_sets.add(frozenset(phi))
    if not ismags_sets or ismags_sets != vf2_sets:
        raise AssertionError("Independent induced-embedding searches disagree")
    for vertices in vf2_sets:
        if not nx.is_isomorphic(graph.subgraph(vertices), target):
            raise AssertionError("Noninduced or spurious target embedding")
    selected = sorted((sorted(s) for s in vf2_sets))
    return selected, {
        "ismags_distinct_vertex_sets": len(ismags_sets),
        "vf2_labeled_mappings": vf2_maps,
        "vf2_distinct_vertex_sets": len(vf2_sets),
    }


def fixed_domains(graph: nx.Graph, target_vertices: set[int]) -> dict[int, list[int]]:
    """Necessary target-valued images for every outside vertex."""
    return {
        x: [
            v for v in sorted(target_vertices)
            if all(v == t or graph.has_edge(v, t)
                   for t in graph[x] if t in target_vertices)
        ]
        for x in graph if x not in target_vertices
    }


def exhaustive_retraction(
    graph: nx.Graph, target_vertices: list[int],
) -> dict[str, object]:
    """Complete deterministic CSP on the fixed-target image domains.

    All target vertices are fixed. Every outside assignment is tested
    against all already fixed/assigned neighbors, accepting adjacency
    *or equality* of the images. This is a self-contained independent
    retraction solver, not the library bounded engine.
    """
    target = set(target_vertices)
    d = fixed_domains(graph, target)
    assigned = {x: x for x in target}
    remaining = set(graph) - target
    counts = Counter()

    def walk():
        counts["states"] += 1
        if not remaining:
            return dict(assigned)
        choices = {}
        for x in remaining:
            choices[x] = [
                v for v in d[x]
                if all(v == assigned[u] or graph.has_edge(v, assigned[u])
                       for u in graph[x] if u in assigned)
            ]
        v = min(choices, key=lambda x: (len(choices[x]), x))
        remaining.remove(v)
        for image in choices[v]:
            counts["assignments"] += 1
            assigned[v] = image
            found = walk()
            if found is not None:
                return found
        assigned.pop(v, None)
        remaining.add(v)
        return None

    retraction = walk()
    result = {
        "status": "FOUND" if retraction is not None else "EXHAUSTED",
        "states": counts["states"],
        "assignments": counts["assignments"],
        "fixed_target_domains_empty": sum(not options for options in d.values()),
        "target_order": len(target),
        "retraction": (
            [[u, retraction[u]] for u in sorted(retraction)]
            if retraction is not None else None
        ),
    }
    if retraction is not None:
        if (
            set(retraction) != set(graph)
            or any(retraction[t] != t for t in target)
            or any(
                retraction[u] != retraction[v]
                and not graph.has_edge(retraction[u], retraction[v])
                for u, v in graph.edges()
            )
        ):
            raise AssertionError("Independent solver returned invalid retraction")
    return result


def search_induced_kc10(graph: nx.Graph) -> dict:
    target = raw_clique_graph(complement_cycle(10))
    all_sets, stats = enumerate_induced_c10(graph, target)
    attempts = []
    positives = []
    state_total = 0
    assignment_total = 0
    for vertices in all_sets:
        answer = exhaustive_retraction(graph, vertices)
        check = bounded_retraction(
            graph, graph.subgraph(vertices),
            max_states=CSP_STATES, max_assignments=CSP_ASSIGNMENTS,
        )
        if check.status is RetractionSearchStatus.LIMIT_REACHED:
            raise ValueError("Pinned CSP engine failed to exhaust a finite case")
        reference_status = (
            "FOUND" if check.status is RetractionSearchStatus.FOUND
            else "EXHAUSTED"
        )
        if answer["status"] != reference_status:
            raise AssertionError("Independent retraction solvers disagree")
        if answer["status"] == "FOUND":
            positives.append({
                "target_vertices": vertices,
                "retraction": answer["retraction"],
            })
        attempts.append({
            "target_vertices": vertices,
            "status": answer["status"],
            "independent_states": answer["states"],
            "independent_assignments": answer["assignments"],
            "pinned_states": check.states_explored,
            "pinned_assignments": check.assignments_tried,
        })
        state_total += check.states_explored
        assignment_total += check.assignments_tried
    return {
        "target": "K(C_10^c)",
        "target_order": len(target),
        "target_edges": target.number_of_edges(),
        "target_graph6": encode(target),
        "embedding_enumeration": stats,
        "candidate_embeddings": attempts,
        "independent_search_total_states": sum(
            x["independent_states"] for x in attempts
        ),
        "library_search_total_states": state_total,
        "library_search_total_assignments": assignment_total,
        "positive_witnesses": positives,
        "status": "FOUND" if positives else "EXHAUSTED",
    }


def classify_targets(graph: nx.Graph, betti: dict[int, int]) -> dict:
    """Exhaustively restrict all parameters to tiny finite candidate sets."""
    n = len(graph)
    susp = []
    for k in TARGET_PARAMS_SUSP:
        target = raw_clique_graph(suspension_cycle(k))
        if len(target) > n:
            continue
        # For k>=5 it suffices to compute exact H2, which excludes both
        # source graphs. For k=4 the target is O4, already checked in PR22.
        hom = compare_homology(betti, target, 3 if k == 4 else 2)
        susp.append({
            "n": k, "order": len(target),
            "target_edges": target.number_of_edges(),
            **hom,
            "prior_octahedron_exhausted": k == 4,
        })
        if k >= 5 and (
            hom["target_betti"]["2"] != 1
            or hom["homologically_allowed"]
        ):
            raise ValueError("Unexpected suspension-clique target homology")
        if k == 4 and not nx.is_isomorphic(
            target, previous.prototype("octahedra", 4)
        ):
            raise ValueError("K(susp C4) is not O4")
    if 2 * 21 <= n:
        raise AssertionError("Unexamined suspension target could fit into host")

    comp = []
    remaining = []
    for k in TARGET_PARAMS_COMP:
        target = raw_clique_graph(complement_cycle(k))
        if len(target) != perrin(k):
            raise ValueError("Perrin maximal-independent-set enumeration changed")
        row = {
            "n": k, "order": len(target),
            "edges": target.number_of_edges(),
            "complement_edges": nx.complement(target).number_of_edges(),
        }
        if len(target) > n:
            row["status"] = "ORDER_EXCLUDED"
        elif target.number_of_edges() > graph.number_of_edges():
            row["status"] = "EDGE_EXCLUDED"
        elif k >= 12:
            lower = complement_edge_lower_bound(graph, len(target))
            row["complement_edge_lower_bound"] = lower
            if lower > row["complement_edges"]:
                row["status"] = "COMPLEMENT_EDGE_EXCLUDED"
            else:
                raise ValueError("New large target requires fresh homology/embedding logic")
        else:
            hom = compare_homology(betti, target, 5)
            row.update(hom)
            if hom["homologically_allowed"]:
                remaining.append(k)
                row["status"] = "HOMOLOGICALLY_ADMISSIBLE"
            else:
                row["status"] = "HOMOLOGY_EXCLUDED"
        comp.append(row)
    if perrin(14) != 51 or perrin(13) != 39 or n > 40:
        raise ValueError("Cannot certify all larger cycle-complement orders")
    if n == 37 and remaining != [10] or n == 40 and remaining:
        raise ValueError("Unexpected admissible clique-graph targets")
    return {
        "suspension_targets": susp,
        "cycle_complement_targets": comp,
        "perrin_order_n14": perrin(14),
        "parameters_remaining_for_retraction": [
            f"K(C_{k}^c)" for k in remaining
        ],
    }


def authenticate_prior() -> None:
    previous.check_sources()
    saved = json.loads((PREVIOUS / "manifest.json").read_text())
    if saved != previous.manifest():
        raise ValueError("Previous versioned proof manifest differs from source")
    for core_id in CORES:
        row = json.loads(
            (PREVIOUS / "records" / f"{core_id:08d}.json").read_text()
        )
        if row.get("status") != "COMPLETED" or row.get("positive_certificates"):
            raise ValueError("Previously certified exhaustive negative stage changed")


def compute(core_id: int) -> dict:
    g, betti = host(core_id)
    reduced = classify_targets(g, betti)
    last = (
        search_induced_kc10(g) if core_id == 6914104 else None
    )
    if last is not None and last["status"] != "EXHAUSTED":
        # A valid positive must be stored and replayed as such; this
        # experiment never asserts a negative while containing a witness.
        pass
    return {
        "schema": SCHEMA, "core_id": core_id,
        "input_pared_iterate": 3,
        "source_graph6": encode(g),
        "source_order": len(g),
        "source_edges": g.number_of_edges(),
        "source_exact_betti_through5": {
            str(k): v for k, v in betti.items()
        },
        "target_screen": reduced,
        "k_c10_retraction_search": last,
        "positive_retraction_found": (
            last is not None and bool(last["positive_witnesses"])
        ),
        "status": "COMPLETED",
        "scope": (
            "Only K(susp(C_n)), n>=4, and K(C_n^c), n>=8; "
            "negative results do not establish K-convergence"
        ),
    }


def manifest() -> dict:
    authenticate_prior()
    deps = [
        Path(__file__), PIN,
        ROOT / "scripts/core9_third_retractions_v2.py",
        ROOT / "scripts/core9_three_target_v1.py",
        ROOT / "scripts/bootstrap_core9_three_target_v1.sh",
        PREVIOUS / "manifest.json",
    ] + [
        PREVIOUS / "records" / f"{id:08d}.json" for id in CORES
    ] + [
        SOURCE / f"{id:08d}.json" for id in CORES
    ]
    return {
        "schema": SCHEMA, "stage": "core9_clique_graph_target_retractions_v1",
        "core_ids": list(CORES),
        "total_represented_order10_members": 461,
        "target_families": ["K(susp(C_n)),n>=4", "K(C_n^c),n>=8"],
        "suspension_parameters_checked": [4, 20],
        "complement_cycle_parameters_checked": [8, 13],
        "all_larger_complement_targets_order_at_least": perrin(14),
        "full_embedding_isomorphism_engines": ["ISMAGS", "VF2"],
        "independent_retraction_search": True,
        "library_retraction_states_per_embedding": CSP_STATES,
        "library_retraction_assignments_per_embedding": CSP_ASSIGNMENTS,
        "worker_and_verifier_limit_seconds": TIMEOUT_SECONDS,
        "worker_and_verifier_memory_mib": MEMORY_MIB,
        "upstream_pycliques_project_sha": PIN.read_text().strip(),
        "source_sha256": {
            str(p.relative_to(ROOT)): sha(p) for p in deps
        },
    }


def save(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent,
        prefix=".clique-target-", suffix=".partial",
        delete=False,
    ) as tmp:
        temp = Path(tmp.name)
        json.dump(payload, tmp, sort_keys=True, indent=2)
        tmp.write("\n")
    try:
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def resource_limits() -> None:
    limit = MEMORY_MIB * 1024 ** 2
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))


def bounded(action: str, core_id: int, path: Path) -> None:
    command = [
        sys.executable, str(Path(__file__)), action,
        "--core-id", str(core_id), "--output", str(path),
    ]
    try:
        job = subprocess.run(
            command, timeout=TIMEOUT_SECONDS,
            preexec_fn=resource_limits, capture_output=True, text=True,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(
            f"Bounded {action} of core {core_id} timed out"
        ) from exc
    if job.returncode:
        raise RuntimeError(
            f"Bounded {action} failed for core {core_id}:\n{job.stderr[-4000:]}"
        )


def authenticate_record(path: Path, core_id: int) -> None:
    saved = json.loads(path.read_text())
    expected_identity = {
        "schema": SCHEMA, "core_id": core_id,
    }
    if any(saved.get(k) != v for k, v in expected_identity.items()):
        raise ValueError("Incorrect saved core identity")
    if saved.get("status") == "TIMEOUT":
        expected = {
            **expected_identity, "status": "TIMEOUT",
            "phase": "worker", "limit_seconds": TIMEOUT_SECONDS,
        }
        if saved != expected:
            raise ValueError("Forged timeout record or positive data")
        return
    if saved.get("status") != "COMPLETED" or saved != compute(core_id):
        raise ValueError("Saved search record differs from independently replayed result")


def run(directory: Path) -> None:
    metadata = manifest()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "manifest.json"
    if path.exists():
        if json.loads(path.read_text()) != metadata:
            raise ValueError("Existing manifest differs from pinned provenance")
    else:
        if any(directory.iterdir()):
            raise ValueError("Existing records without a manifest")
        save(path, metadata)
    for core_id in CORES:
        record = directory / "records" / f"{core_id:08d}.json"
        if record.exists():
            bounded("check", core_id, record)
            print(f"Existing record {core_id} replayed", flush=True)
            continue
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "result.json"
            try:
                bounded("worker", core_id, output)
            except TimeoutError:
                save(record, {
                    "schema": SCHEMA, "core_id": core_id,
                    "status": "TIMEOUT", "phase": "worker",
                    "limit_seconds": TIMEOUT_SECONDS,
                })
                print(f"Core {core_id}: TIMEOUT (no mathematical negative claim)")
                continue
            bounded("check", core_id, output)
            data = json.loads(output.read_text())
            save(record, data)
            print(f"Core {core_id}: {data['status']}", flush=True)
    verify(directory)


def verify(directory: Path) -> None:
    if json.loads((directory / "manifest.json").read_text()) != manifest():
        raise ValueError("Experiment provenance differs")
    records = directory / "records"
    expected = {f"{id:08d}.json" for id in CORES}
    if not records.is_dir() or {p.name for p in records.iterdir()} != expected:
        raise ValueError("Missing or extra saved core records")
    for core_id in CORES:
        bounded("check", core_id, records / f"{core_id:08d}.json")
    print("Verified both independent clique-target experiments")


def report(directory: Path) -> None:
    verify(directory)
    for core_id in CORES:
        row = json.loads(
            (directory / "records" / f"{core_id:08d}.json").read_text()
        )
        if row["status"] == "TIMEOUT":
            print(json.dumps({"core_id": core_id, "status": "INCONCLUSIVE_TIMEOUT"}))
            continue
        info = row["k_c10_retraction_search"]
        print(json.dumps({
            "core_id": core_id, "order": row["source_order"],
            "eligible": row["target_screen"]["parameters_remaining_for_retraction"],
            "induced_targets": (
                info["embedding_enumeration"] if info else None
            ),
            "negative_embeddings": (
                sum(x["status"] == "EXHAUSTED" for x in info["candidate_embeddings"])
                if info else 0
            ),
            "positive_retraction": row["positive_retraction_found"],
            "classification": (
                "DIVERGENT_NINE_CORE_ONLY" if row["positive_retraction_found"]
                else "UNRESOLVED"
            ),
        }, sort_keys=True))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("plan", "run", "worker", "check", "verify", "report"))
    p.add_argument("--core-id", type=int)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    if a.action in ("worker", "check"):
        if a.core_id not in CORES or a.output is None:
            p.error("Worker/check requires a selected core and output file")
        if a.action == "worker":
            save(a.output, compute(a.core_id))
        else:
            authenticate_record(a.output, a.core_id)
        return
    if a.action == "plan":
        print(json.dumps(manifest(), sort_keys=True, indent=2))
        return
    directory = OUTPUT if a.output is None else a.output
    if a.action == "run":
        run(directory)
    elif a.action == "verify":
        verify(directory)
    else:
        report(directory)


if __name__ == "__main__":
    main()
