"""Homology-guided non-special retractions in K^3 of two stiff nine-cores.

A new, immutable experiment. Its hypothesis is that ordinary retractions
onto induced O_d and complements of cycles C_n^c can certify K-divergence
even when *special* octahedra are absent.

Exact low-degree mod-two simplicial homology rules out impossible retracts
before enumeration. A cheap per-vertex closed-neighborhood necessary
condition rejects targets that cannot admit any graph retraction.
Remaining candidates use the general, independently verified bounded
retraction engine. A search that exhausts its budget certifies nothing
negative about K-dynamics. Every completed record is reconstructed and
compared in a separately time- and memory-limited verifier subprocess.

Usage after bash scripts/bootstrap_core9_three_target_v1.sh:
  .venv-core9-three-v1/bin/python scripts/core9_third_retractions_v2.py plan
  .venv-core9-three-v1/bin/python scripts/core9_third_retractions_v2.py run
  .venv-core9-three-v1/bin/python scripts/core9_third_retractions_v2.py verify
  .venv-core9-three-v1/bin/python scripts/core9_third_retractions_v2.py report
"""
from __future__ import annotations

import argparse
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
from pycliques.retractions import bounded_retraction, RetractionSearchStatus
from pycliques.targeted_retractions import (
    TargetRetractionResult, TargetSearchStatus, verify_targeted_retraction,
    _octahedra, _cycle_complements,
)
from pycombtop.bounded_betti import bounded_reduced_betti_mod2

import core9_three_target_v1 as prior

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research/order10_core9_third_retractions_v2"
FROZEN = ROOT / "research/order10_core9_three_target_v1"
PIN = ROOT / "config/pycliques_commit_core9_three_target_v1.txt"
CORES = (6914104, 6962151)
SCHEMA = 2
K_LEVEL = 3
MAX_DEGREE = 5
MAX_FACES = 500_000
MAX_TARGET_ORDER = 14
MAX_PATTERNS = 50_000
MAX_FEASIBLE = 5_000
MAX_STATES = 250_000
MAX_ASSIGNMENTS = 500_000
TIMEOUT_SECONDS = 125
MEMORY_MIB = 2048
FAMILIES = ("octahedra", "cycle_complements", "suspensions")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_low_betti(graph: nx.Graph, max_degree: int = MAX_DEGREE) -> dict[int, int]:
    """Exact reduced Betti in degrees 0..max_degree via independent GF(2) ranks.

    Enumerates every simplex of size <= max_degree + 2, not a sample.
    On overflow raises an error instead of returning spurious zeroes.
    """
    if graph.is_directed() or graph.is_multigraph() or max_degree < 0:
        raise ValueError("Unsupported graph or homology dimension")
    if graph.number_of_nodes() == 0:
        return {i: 0 for i in range(max_degree + 1)}
    if set(graph) != set(range(len(graph))):
        raise ValueError("Homology input must have consecutive integer labels")
    simplices: list[list[tuple[int, ...]]] = [
        [] for _ in range(max_degree + 2)
    ]
    total = 0
    for clique in nx.enumerate_all_cliques(graph):
        n = len(clique)
        if n > max_degree + 2:
            break
        simplices[n - 1].append(tuple(sorted(clique)))
        total += 1
        if total > MAX_FACES:
            raise ValueError("Exact simplicial face budget exceeded")
    ranks = [0] * (max_degree + 2)
    # Boundary of i-simplex lands in the group spanned by (i-1)-simplices.
    for degree in range(1, max_degree + 2):
        rows = {face: i for i, face in enumerate(simplices[degree - 1])}
        pivots: dict[int, int] = {}
        for face in simplices[degree]:
            bits = sum(
                1 << rows[tuple(part)]
                for part in combinations(face, degree)
            )
            while bits:
                leading = bits.bit_length() - 1
                if leading in pivots:
                    bits ^= pivots[leading]
                else:
                    pivots[leading] = bits
                    break
        ranks[degree] = len(pivots)
    result = {}
    for degree in range(max_degree + 1):
        betti = (
            len(simplices[degree])
            - ranks[degree] - ranks[degree + 1]
            - (degree == 0)
        )
        if betti < 0:
            raise AssertionError("Invalid negative exact Betti number")
        result[degree] = betti
    return result


def prototype(family: str, parameter: int) -> nx.Graph:
    """Independently construct the three relevant candidate target families."""
    if family == "octahedra":
        return nx.complement(nx.disjoint_union_all([
            nx.path_graph(2) for _ in range(parameter)
        ]))
    if family == "cycle_complements":
        return nx.complement(nx.cycle_graph(parameter))
    if family == "suspensions":
        graph = nx.cycle_graph(parameter)
        graph.add_nodes_from([parameter, parameter + 1])
        for v in range(parameter):
            graph.add_edge(v, parameter)
            graph.add_edge(v, parameter + 1)
        return graph
    raise ValueError(f"Unknown family {family}")


def target_candidates(betti: dict[int, int]) -> dict[str, list[dict]]:
    """Use exact *target* homology and natural retraction-injectivity.

    This intentionally computes the Betti vector of every small prototype
    rather than trusting an unverified formula. The only target graphs
    allowed in this experiment have <=12 vertices and homology in degrees
    <=5, checked against the complete vector supplied for their source.
    """
    answer: dict[str, list[dict]] = {family: [] for family in FAMILIES}
    parameters = {
        # Larger O_d contains an induced O_6; its absence is authenticated
        # independently by structural_target_ceiling before using this list.
        "octahedra": range(3, min(5, MAX_TARGET_ORDER // 2) + 1),
        "cycle_complements": range(8, MAX_TARGET_ORDER + 1),
        "suspensions": range(4, MAX_TARGET_ORDER - 1),
    }
    for family in FAMILIES:
        for p in parameters[family]:
            shape = prototype(family, p)
            exact = bounded_reduced_betti_mod2(
                shape, max_faces=60_000, max_degree=MAX_DEGREE,
            )
            if exact is None:
                raise ValueError(f"Could not certify target homology {family}:{p}")
            if not any(exact.values()):
                # These target families are expected noncontractible; never
                # classify a generic acyclic target as a divergent witness.
                raise ValueError(f"Target {family}:{p} unexpectedly acyclic")
            if all(rank <= betti[dim] for dim, rank in exact.items()):
                answer[family].append({
                    "parameter": p,
                    "target_betti": {str(k): v for k, v in exact.items()},
                })
    return answer


def structural_target_ceiling(graph: nx.Graph) -> dict:
    """Exhaustively rule out *all* named targets above the parameter cutoff.

    An induced O_d with d >= 6 necessarily contains an induced O_6.
    An induced C_n^c is a chordless n-cycle in the complement. We count
    every such cycle, not a bounded prefix, to rule out all n > 14.
    A suspension of any cycle has nonzero reduced H_2 and is excluded
    at every order by the exact host Betti-2 calculation.
    """
    induced_o5 = sum(1 for _ in _octahedra(graph, {5}))
    induced_o6 = sum(1 for _ in _octahedra(graph, {6}))
    cycles: dict[int, int] = {}
    complement = nx.complement(graph)
    for cycle in nx.chordless_cycles(complement, length_bound=len(graph)):
        n = len(cycle)
        if n >= 8:
            cycles[n] = cycles.get(n, 0) + 1
    last = max(cycles, default=0)
    if induced_o6 or last > MAX_TARGET_ORDER:
        raise ValueError(
            "Named targets exceed the certified structural ceilings; "
            "a new versioned target family is required"
        )
    return {
        "induced_o5": induced_o5, "induced_o6": induced_o6,
        "maximum_complement_chordless_cycle": last,
        "cycle_complement_candidates_by_length": {
            str(k): v for k, v in sorted(cycles.items())
        },
        "certified_no_larger_octahedra": induced_o6 == 0,
        "certified_no_larger_cycle_complements": last <= MAX_TARGET_ORDER,
    }


def fixed_target_feasible(graph: nx.Graph, vertices: frozenset[int]) -> bool:
    """Necessary local condition for a graph retraction onto this target.

    Each outside vertex x must map to some t in H. Every neighbor y of x
    already in H is fixed by the retraction, so r(x)=t requires
    N_G(x) intersect V(H) subset N_H[t] (closed neighborhood).
    Graph morphisms may collapse an edge to a vertex.
    This check is a *necessary* filter, NEVER sufficient proof.
    """
    target = graph.subgraph(vertices)
    closed = [set(target[v]) | {v} for v in target]
    for x in graph:
        if x in vertices:
            continue
        boundary = set(graph[x]) & vertices
        if not any(boundary <= neighborhood for neighborhood in closed):
            return False
    return True


def ensure_positive_retraction(
    graph: nx.Graph, family: str, parameter: int,
    vertices: tuple[int, ...], map_pairs: list[list[int]],
) -> None:
    """Check an ordinary graph retraction and its known divergent shape."""
    candidate = TargetRetractionResult(
        family=family, status=TargetSearchStatus.FOUND,
        target_kind=f"{family}:{parameter}", target_vertices=vertices,
        projection=dict(map(tuple, map_pairs)),
    )
    if not verify_targeted_retraction(graph, candidate):
        raise ValueError("Positive named-target retraction failed independent replay")
    if set(candidate.projection) != set(graph) or set(candidate.projection.values()) - set(vertices):
        raise ValueError("Positive retraction map is not a total target-valued map")
    for t in vertices:
        if candidate.projection[t] != t:
            raise ValueError("Positive witness does not fix its target")
    for a, b in graph.edges():
        x, y = candidate.projection[a], candidate.projection[b]
        if x != y and not graph.has_edge(x, y):
            raise ValueError("Positive witness fails adjacency-or-equality preservation")


def run_family(
    graph: nx.Graph, family: str, admissible: list[dict],
) -> dict:
    """Exhaustive only if the bounded generator and all CSPs finish."""
    allowed = {row["parameter"] for row in admissible}
    out = {
        "family": family, "admissible_parameters": sorted(allowed),
        "status": "HOMOLOGY_EXCLUDED" if not allowed else "EXHAUSTED",
        "patterns": 0, "duplicate_targets": 0,
        "locally_impossible": 0, "locally_feasible": 0,
        "retractions_attempted": 0, "states": 0, "assignments": 0,
        "incomplete_csp": 0, "witness": None,
        "limits": {
            "max_patterns": MAX_PATTERNS, "max_locally_feasible": MAX_FEASIBLE,
            "max_states": MAX_STATES, "max_assignments": MAX_ASSIGNMENTS,
        },
    }
    if not allowed:
        return out
    if family == "octahedra":
        iterator = _octahedra(graph, allowed)
    elif family == "cycle_complements":
        iterator = _cycle_complements(graph, allowed)
    else:
        # Suspension targets are homologically excluded in the two frozen
        # cases. Abort rather than falsely claim a search if that changes.
        raise ValueError("A suspension target would require a new versioned search")
    seen: set[frozenset[int]] = set()
    for parameter, raw_vertices in iterator:
        if out["patterns"] >= MAX_PATTERNS:
            out["status"] = "LIMIT_REACHED"
            break
        out["patterns"] += 1
        vertices = frozenset(raw_vertices)
        if vertices in seen:
            out["duplicate_targets"] += 1
            continue
        seen.add(vertices)
        if not fixed_target_feasible(graph, vertices):
            out["locally_impossible"] += 1
            continue
        if out["locally_feasible"] >= MAX_FEASIBLE:
            out["status"] = "LIMIT_REACHED"
            break
        out["locally_feasible"] += 1
        left_states = MAX_STATES - out["states"]
        left_assignments = MAX_ASSIGNMENTS - out["assignments"]
        if left_states < 1 or left_assignments < 1:
            out["status"] = "LIMIT_REACHED"
            break
        check = bounded_retraction(
            graph, graph.subgraph(vertices),
            max_states=left_states, max_assignments=left_assignments,
        )
        out["retractions_attempted"] += 1
        out["states"] += check.states_explored
        out["assignments"] += check.assignments_tried
        if check.status is RetractionSearchStatus.LIMIT_REACHED:
            out["incomplete_csp"] += 1
            out["status"] = "LIMIT_REACHED"
            break
        if check.status is RetractionSearchStatus.FOUND:
            projection = [[int(a), int(b)] for a, b in sorted(check.retraction.items())]
            witness = {
                "family": family, "parameter": parameter,
                "target_vertices": sorted(vertices),
                "projection": projection,
            }
            ensure_positive_retraction(
                graph, family, parameter,
                tuple(witness["target_vertices"]), projection,
            )
            out["witness"] = witness
            out["status"] = "FOUND"
            break
    return out


def check_sources() -> dict:
    """Independently authenticate the original three-core experiment."""
    prior.check_sources()
    frozen_meta = json.loads((FROZEN / "manifest.json").read_text())
    if frozen_meta != prior.manifest():
        raise ValueError("The earlier three-core frozen manifest differs")
    selected = {}
    for core_id in CORES:
        record = json.loads(
            (FROZEN / "records" / f"{core_id:08d}.json").read_text()
        )
        if record.get("status") != "COMPLETED" or record.get("positive_certificates"):
            raise ValueError("Frozen core does not match the documented unresolved pilot")
        if len(record.get("pared_levels", [])) != K_LEVEL + 1:
            raise ValueError("Frozen prior record missing the third pared iterate")
        if record["pared_levels"][-1]["special"]["status"] != "ABSENT_EXHAUSTIVE":
            raise ValueError("Frozen third iterate is not a non-special target")
        selected[core_id] = record
    return selected


def third_iterate(core_id: int) -> nx.Graph:
    """Fresh pinned reconstruction checked against frozen structural source."""
    graph = prior.pared_iterates(core_id)[K_LEVEL]
    frozen = json.loads(
        (FROZEN / "records" / f"{core_id:08d}.json").read_text()
    )
    last = frozen["pared_levels"][-1]
    if (
        len(graph) != last["order"]
        or graph.number_of_edges() != last["edges"]
        or prior.special_result(graph) != last["special"]
        or last["special"]["status"] != "ABSENT_EXHAUSTIVE"
    ):
        raise ValueError("Third-iterate provenance/special status changed")
    return graph


def compute(core_id: int) -> dict:
    graph = third_iterate(core_id)
    betti = exact_low_betti(graph)
    # Freeze exact values for the research result; recomputation in the
    # independent verifier will reject any drift.
    expected = {
        6914104: {0: 0, 1: 0, 2: 0, 3: 1, 4: 0, 5: 0},
        6962151: {0: 0, 1: 0, 2: 0, 3: 0, 4: 1, 5: 0},
    }
    if betti != expected[core_id]:
        raise ValueError(f"Exact independently computed Betti disagrees: {core_id}: {betti}")
    bounds = structural_target_ceiling(graph)
    if betti[2] != 0:
        raise ValueError("Cannot exclude longer cycle-suspension targets")
    candidates = target_candidates(betti)
    searches = [run_family(graph, family, candidates[family]) for family in FAMILIES]
    positives = [
        row["witness"] for row in searches if row["status"] == "FOUND"
    ]
    return {
        "schema": SCHEMA, "core_id": core_id,
        "core_graph6": prior.CORE[core_id][0],
        "represented_originals": prior.CORE[core_id][1],
        "pared_iterate": K_LEVEL, "third_order": len(graph),
        "third_edges": graph.number_of_edges(),
        "reduced_mod2_betti_through_degree_5": {
            str(k): v for k, v in betti.items()
        },
        "eligible_target_parameters": candidates,
        "structural_target_ceiling": bounds,
        "family_searches": searches,
        "positive_certificates": positives,
        "status": "COMPLETED",
        "interpretation": (
            "A verified named divergent target retraction in pared K3 "
            "certifies divergence of the nine-core. EXHAUSTED is restricted "
            "to this family and target-order cap; LIMIT_REACHED and "
            "HOMOLOGY_EXCLUDED never imply K-convergence."
        ),
    }


def manifest() -> dict:
    check_sources()
    dependencies = [
        Path(__file__),
        ROOT / "scripts/core9_three_target_v1.py",
        ROOT / "scripts/bootstrap_core9_three_target_v1.sh",
        ROOT / "scripts/core9_structure_worker.py",
        ROOT / "scripts/special_octahedron_class_lift_v1.py",
        PIN, FROZEN / "manifest.json",
        ROOT / "reports/order10_core_index_v1/manifest.json",
    ] + [
        FROZEN / "records" / f"{core_id:08d}.json" for core_id in CORES
    ]
    return {
        "schema": SCHEMA, "stage": "core9_third_nonspecial_retractions_v2",
        "core_ids": list(CORES),
        "total_represented_originals": sum(prior.CORE[i][1] for i in CORES),
        "input_pared_iterate": K_LEVEL,
        "maximum_prototype_order": MAX_TARGET_ORDER,
        "named_family_search_complete_above_cutoff": (
            "All larger octahedra contain an induced O6; all larger cycle "
            "complements require a longer chordless complement cycle; "
            "all suspensions have nonzero reduced H2"
        ),
        "homology_degree_max": MAX_DEGREE,
        "max_simplicial_faces": MAX_FACES,
        "family_limits": {
            "patterns": MAX_PATTERNS, "feasible": MAX_FEASIBLE,
            "states": MAX_STATES, "assignments": MAX_ASSIGNMENTS,
        },
        "per_core_timeout_seconds": TIMEOUT_SECONDS,
        "per_worker_memory_mib": MEMORY_MIB,
        "upstream_pycliques_project_pin": PIN.read_text().strip(),
        "source_sha256": {
            str(p.relative_to(ROOT)): sha256(p) for p in dependencies
        },
        "claim_scope": (
            "exact homology constraints and independently replayed positive "
            "ordinary retractions; bounded negatives do not classify K-behavior"
        ),
    }


def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", prefix=".core9-third-",
        suffix=".partial", dir=path.parent, delete=False,
    ) as tmp:
        pathname = Path(tmp.name)
        json.dump(data, tmp, sort_keys=True, indent=2)
        tmp.write("\n")
    try:
        os.replace(pathname, path)
    finally:
        pathname.unlink(missing_ok=True)


def limit_resources() -> None:
    maximum = MEMORY_MIB * (1024 ** 2)
    resource.setrlimit(resource.RLIMIT_AS, (maximum, maximum))


def bounded_subprocess(action: str, core_id: int, path: Path) -> None:
    """All expensive processing and verification respects both limits."""
    command = [
        sys.executable, str(Path(__file__)), action,
        "--core-id", str(core_id), "--output", str(path),
    ]
    try:
        completed = subprocess.run(
            command, timeout=TIMEOUT_SECONDS, preexec_fn=limit_resources,
            capture_output=True, text=True,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(
            f"{action} for {core_id} exceeded {TIMEOUT_SECONDS} seconds"
        ) from exc
    if completed.returncode:
        raise RuntimeError(
            f"{action} failed for {core_id}: {completed.stderr[-4000:]}"
        )


def authenticate_record(path: Path, core_id: int) -> None:
    """Fresh, independent replay including ALL nonpositive statuses."""
    row = json.loads(path.read_text(encoding="utf-8"))
    expected_identity = {
        "schema": SCHEMA, "core_id": core_id,
        "core_graph6": prior.CORE[core_id][0],
        "represented_originals": prior.CORE[core_id][1],
    }
    if any(row.get(k) != v for k, v in expected_identity.items()):
        raise ValueError("Record identity does not match frozen source")
    if row.get("status") == "TIMEOUT":
        expected = {
            **expected_identity, "status": "TIMEOUT",
            "phase": "compute", "limit_seconds": TIMEOUT_SECONDS,
        }
        if row != expected:
            raise ValueError("Forged timeout status or extra proof fields")
        return
    if row.get("status") != "COMPLETED" or row != compute(core_id):
        raise ValueError("Saved candidate search differs from independent full replay")


def run(directory: Path) -> None:
    meta = manifest()
    directory.mkdir(parents=True, exist_ok=True)
    header = directory / "manifest.json"
    if header.is_file():
        if json.loads(header.read_text()) != meta:
            raise ValueError("Refusing to overwrite changed frozen manifest")
    else:
        if any(directory.iterdir()):
            raise ValueError("Existing data without matching provenance manifest")
        atomic_json(header, meta)
    for core_id in CORES:
        path = directory / "records" / f"{core_id:08d}.json"
        if path.is_file():
            bounded_subprocess("check", core_id, path)
            print(f"Already independently checked {core_id}", flush=True)
            continue
        with tempfile.TemporaryDirectory(prefix="core9-third-retractions-") as tmp:
            result = Path(tmp) / "record.json"
            try:
                bounded_subprocess("worker", core_id, result)
            except TimeoutError:
                atomic_json(path, {
                    "schema": SCHEMA, "core_id": core_id,
                    "core_graph6": prior.CORE[core_id][0],
                    "represented_originals": prior.CORE[core_id][1],
                    "status": "TIMEOUT", "phase": "compute",
                    "limit_seconds": TIMEOUT_SECONDS,
                })
                print(f"TIMEOUT for {core_id}, without mathematical conclusion", flush=True)
                continue
            bounded_subprocess("check", core_id, result)
            atomic_json(path, json.loads(result.read_text()))
            print(f"Computed and independently replayed {core_id}", flush=True)
    verify(directory)


def verify(directory: Path) -> None:
    meta = manifest()
    if json.loads((directory / "manifest.json").read_text()) != meta:
        raise ValueError("Experiment manifest differs from pinned source/code")
    paths = directory / "records"
    expected = {f"{id:08d}.json" for id in CORES}
    if not paths.is_dir() or {p.name for p in paths.iterdir()} != expected:
        raise ValueError("Incomplete or extra three-core retargeting output")
    for core_id in CORES:
        bounded_subprocess("check", core_id, paths / f"{core_id:08d}.json")
    print("Verified homology and all positive/negative bounded results")


def report(directory: Path) -> None:
    verify(directory)
    for core_id in CORES:
        row = json.loads(
            (directory / "records" / f"{core_id:08d}.json").read_text()
        )
        if row["status"] == "TIMEOUT":
            print(json.dumps({
                "core_id": core_id, "status": "TIMEOUT",
                "classification": "UNRESOLVED",
            }))
            continue
        print(json.dumps({
            "core_id": core_id, "members": row["represented_originals"],
            "betti": row["reduced_mod2_betti_through_degree_5"],
            "eligible": {
                f: [r["parameter"] for r in ps]
                for f, ps in row["eligible_target_parameters"].items()
            },
            "search": [
                {key: entry[key] for key in (
                    "family", "status", "patterns", "locally_impossible",
                    "locally_feasible", "retractions_attempted",
                    "states", "assignments"
                )}
                for entry in row["family_searches"]
            ],
            "positive_certificates": row["positive_certificates"],
        }, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=(
        "plan", "worker", "check", "run", "verify", "report",
    ))
    parser.add_argument("--core-id", type=int)
    parser.add_argument("--output", type=Path)
    options = parser.parse_args()
    if options.action in {"worker", "check"}:
        if options.core_id not in CORES or options.output is None:
            parser.error("worker/check requires a selected core ID and file path")
        if options.action == "worker":
            atomic_json(options.output, compute(options.core_id))
        else:
            authenticate_record(options.output, options.core_id)
        return
    if options.action == "plan":
        print(json.dumps(manifest(), indent=2, sort_keys=True))
        return
    output = OUTPUT if options.output is None else options.output
    if options.action == "run":
        run(output)
    elif options.action == "verify":
        verify(output)
    else:
        report(output)


if __name__ == "__main__":
    main()
