"""Versioned retraction search onto coaffine joins C_n^c * O_r.

The graphs are certified K-divergent by the suspension/2-coaffination
criterion (LNP09, Theorem 4.6): C_n^c, n>=5, admits the cyclic
nonadjacent-vertex coaffination v -> v+1, O_(r-1) admits the antipodal
one, and C_n^c * O_r = susp(C_n^c * O_(r-1)) for r>=1.

The source graphs are *third completely pared iterates* of frozen nine
vertex cores. The search covers exactly the non-acyclic, rank-one targets
whose *known* unique reduced mod-2 homology is in dimension three or
four, matching that of the respective source. It does not claim to
exclude candidate targets with different homology in dimensions that
were not established for these source graphs.

For each target (n,r), enumerate induced C_n + r disjoint K2 patterns
in the *complement* of the source; use closed-neighborhood fixed-target
necessary conditions; then independently solve all locally feasible
ordinary graph-retraction CSPs by separate unbounded backtracking and
the pinned pycliques library with explicit resource bounds.

Completed negative records are independently regenerated in a bounded
worker; timeouts never become negative K-behavior classifications.
No historical census verdict or earlier proof is modified.
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
from pycombtop.bounded_betti import bounded_reduced_betti_mod2

import core9_clique_targets_v1 as earlier

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research/order10_core9_coaffine_join_targets_v1"
SCHEMA = 1
CORES = (6914104, 6962151)
HOMOLOGY_DIM = {6914104: 3, 6962151: 4}
TARGET_MAX_ORDER = 40
TIMEOUT_SECONDS = 115
MEMORY_MIB = 2048
CSP_MAX_STATES = 25000
CSP_MAX_ASSIGNMENTS = 40000
EXPECTED = {
    6914104: ((5, 2), (7, 2), (8, 1), (10, 1)),
    6962151: ((5, 3), (7, 3), (8, 2), (10, 2), (11, 1), (13, 1)),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cycle_independence_homology(n: int) -> tuple[int, int]:
    """Known exact homology of Ind(C_n), n>=5: a sphere or two spheres.

    Ind(C_(3k)) is a wedge of two S^(k-1);
    Ind(C_(3k+1)) is S^(k-1);
    Ind(C_(3k+2)) is S^k.
    """
    if n < 5:
        raise ValueError("The coaffination family starts at n>=5")
    k, remainder = divmod(n, 3)
    if remainder == 0:
        return k-1, 2
    if remainder == 1:
        return k-1, 1
    return k, 1


def candidate_parameters(core_id: int) -> tuple[tuple[int, int], ...]:
    """All rank-one targets with unique homology in the selected dimension."""
    d = HOMOLOGY_DIM[core_id]
    matches = []
    for n in range(5, TARGET_MAX_ORDER-1):
        dimension, rank = cycle_independence_homology(n)
        if rank != 1:
            continue
        r = d - dimension
        if r >= 1 and n + 2*r <= TARGET_MAX_ORDER:
            matches.append((n, r))
    result = tuple(matches)
    if result != EXPECTED[core_id]:
        raise AssertionError(f"Unexpected admissible family: {core_id}: {result}")
    return result


def join_target(n: int, r: int) -> nx.Graph:
    if n < 5 or r < 1:
        raise ValueError("Require C_n^c joined with O_r, n>=5 and r>=1")
    cycle_complement = nx.complement(nx.cycle_graph(n))
    octahedron = nx.complement(nx.disjoint_union_all([
        nx.path_graph(2) for _ in range(r)
    ]))
    target = nx.join(
        cycle_complement, nx.relabel_nodes(octahedron, {i:i+n for i in octahedron})
    ) if hasattr(nx, "join") else nx.disjoint_union(cycle_complement, octahedron)
    # NetworkX's graph join is not available in all pinned versions.
    # Independently enforce exactly the cross join edges in either case.
    target.add_edges_from((i, n+j) for i in range(n) for j in range(2*r))
    target = nx.convert_node_labels_to_integers(target)
    if (
        len(target) != n+2*r or
        not nx.is_isomorphic(
            nx.complement(target),
            nx.disjoint_union_all(
                [nx.cycle_graph(n)] + [nx.path_graph(2) for _ in range(r)]
            ),
        )
    ):
        raise AssertionError("Independent complement of disjoint cycle and edges differs")
    return target


def validate_candidate_homology(
    host: nx.Graph, core_id: int, parameters: tuple[tuple[int,int], ...],
) -> list[dict]:
    source_betti = earlier.previous.exact_low_betti(host, max_degree=5)
    expected = {i: int(i == HOMOLOGY_DIM[core_id]) for i in range(6)}
    if source_betti != expected:
        raise ValueError("Exact frozen source Betti profile changed")
    answers = []
    for n, r in parameters:
        t = join_target(n,r)
        hom = bounded_reduced_betti_mod2(
            t, max_degree=5, max_faces=100_000
        )
        if hom is None:
            raise ValueError("Candidate homology exceeded face budget")
        theoretical_dim, multiplicity = cycle_independence_homology(n)
        if hom != {i: int(i == theoretical_dim+r)*multiplicity for i in range(6)}:
            raise ValueError(f"Computed homology disagrees with theorem for {(n,r)}")
        answers.append({
            "n": n, "r": r, "vertices": len(t), "edges": t.number_of_edges(),
            "reduced_mod2_betti_0_to_5": {str(i): int(hom[i]) for i in range(6)},
        })
    return answers


def induced_patterns(
    host: nx.Graph, n: int, r: int,
) -> tuple[list[list[int]], int]:
    """Exhaustive induced C_n + r K2 selection in the complement.

    Enumerates every chordless n-cycle, then every set of r disjoint
    complement edges with no cross-complement adjacencies and no edges
    into the cycle. This is an exact characterization of induced copies
    of C_n^c * O_r.
    """
    comp = nx.complement(host)
    candidate_edges = [tuple(sorted(e)) for e in comp.edges()]
    candidate_edges.sort()
    all_sets: set[tuple[int,...]] = set()
    chordless_cycles = 0
    for cycle in nx.chordless_cycles(comp, length_bound=n):
        if len(cycle) != n:
            continue
        chordless_cycles += 1
        forbidden = set(cycle)
        for v in cycle:
            forbidden.update(comp[v])
        eligible = set(comp) - forbidden
        suitable = [e for e in candidate_edges
                    if e[0] in eligible and e[1] in eligible]
        for edges in combinations(suitable, r):
            ends = [v for e in edges for v in e]
            if len(set(ends)) != 2*r:
                continue
            if any(comp.has_edge(u,v)
                   for a,b in combinations(edges,2)
                   for u in a for v in b):
                continue
            vertices = tuple(sorted(set(cycle) | set(ends)))
            if len(vertices) != n+2*r:
                raise AssertionError("Invalid induced target size")
            all_sets.add(vertices)
    targets = sorted(map(list, all_sets))
    # Every selected target has exactly one n-cycle component in the
    # complement, because all other components are independent K2.
    # A unique target vertex set is therefore counted once.
    return targets, chordless_cycles


def replay_induced_target(host: nx.Graph, n: int, r: int, vertices: list[int]) -> None:
    sub = nx.complement(host.subgraph(vertices))
    model = nx.disjoint_union_all(
        [nx.cycle_graph(n)] + [nx.path_graph(2) for _ in range(r)]
    )
    if not nx.is_isomorphic(sub, model):
        raise ValueError("Selected vertex set is not an induced coaffine join")


def check_retraction(
    host: nx.Graph, vertices: list[int],
) -> dict:
    """Two logically independent solvers agree, or reject the claim."""
    domains = earlier.fixed_domains(host, set(vertices))
    impossible = sum(not domain for domain in domains.values())
    if impossible:
        return {"status": "LOCAL_IMPOSSIBLE", "empty_domains": impossible,
                "independent_states": 0, "pinned_states": 0, "witness": None}
    independent = earlier.exhaustive_retraction(host, vertices)
    pinned = bounded_retraction(
        host, host.subgraph(vertices),
        max_states=CSP_MAX_STATES,
        max_assignments=CSP_MAX_ASSIGNMENTS,
    )
    if pinned.status is RetractionSearchStatus.LIMIT_REACHED:
        raise RuntimeError("Pinned solver failed to exhaust target under configured bounds")
    found = pinned.status is RetractionSearchStatus.FOUND
    if (independent["status"] == "FOUND") != found:
        raise AssertionError("Two independent graph-retraction solvers disagree")
    if found:
        map1 = dict(map(tuple, independent["retraction"]))
        if (
            set(map1) != set(host)
            or set(map1.values()) - set(vertices)
            or any(map1[v] != v for v in vertices)
            or any(
                map1[u] != map1[v] and
                not host.has_edge(map1[u],map1[v])
                for u,v in host.edges()
            )
        ):
            raise AssertionError("Found graph morphism fails direct replay")
    return {
        "status": "FOUND" if found else "EXHAUSTED",
        "empty_domains": 0,
        "independent_states": independent["states"],
        "pinned_states": pinned.states_explored,
        "witness": independent["retraction"] if found else None,
    }


def probe_family(host: nx.Graph, n: int, r: int) -> dict:
    targets, ncycles = induced_patterns(host,n,r)
    tested = []
    for vertices in targets:
        # The combinatorial generator operates on the complement, while
        # the independent shape replay tests the original host graph.
        replay_induced_target(host,n,r,vertices)
        result = check_retraction(host,vertices)
        tested.append({"vertices": vertices, **result})
    statuses = {item["status"] for item in tested}
    if statuses - {"LOCAL_IMPOSSIBLE", "EXHAUSTED", "FOUND"}:
        raise ValueError("Unsupported retraction-search status")
    return {
        "n": n, "r": r, "cycle_count": ncycles,
        "induced_target_count": len(targets),
        "local_impossible": sum(item["status"] == "LOCAL_IMPOSSIBLE" for item in tested),
        "csp_exhausted": sum(item["status"] == "EXHAUSTED" for item in tested),
        "csp_states_total": sum(item["independent_states"] for item in tested),
        "pinned_states_total": sum(item["pinned_states"] for item in tested),
        "found_count": sum(item["status"] == "FOUND" for item in tested),
        "target_sets_sha256": hashlib.sha256(
            json.dumps(targets, separators=(",", ":")).encode()
        ).hexdigest(),
        "targets": tested,
        "status": "FOUND" if "FOUND" in statuses else "EXHAUSTED",
    }


def compute(core_id: int) -> dict:
    if core_id not in CORES:
        raise ValueError("Unknown core")
    host, betti = earlier.host(core_id)
    parameters = candidate_parameters(core_id)
    candidates = validate_candidate_homology(host, core_id, parameters)
    proofs = [probe_family(host,n,r) for n,r in parameters]
    if [tuple((p["n"],p["r"])) for p in proofs] != list(parameters):
        raise AssertionError("Missing an admissible target family")
    return {
        "schema": SCHEMA, "core_id": core_id,
        "core_graph6": earlier.initial.CORE[core_id][0],
        "represented_ten_vertex_graphs": earlier.initial.CORE[core_id][1],
        "source_third_iterate_graph6": earlier.encode(host),
        "source_order": len(host), "source_edges": host.number_of_edges(),
        "source_homology": {str(i): betti[i] for i in range(6)},
        "target_homology": candidates,
        "probes": proofs,
        "positive_witnesses": [
            {"n":p["n"],"r":p["r"],"vertices":x["vertices"],"map":x["witness"]}
            for p in proofs for x in p["targets"] if x["status"] == "FOUND"
        ],
        "status": "COMPLETED",
        "scope": "Only homology-matched rank-one coaffine joins with degree 3/4; "
                 "negative searches do not certify K-convergence or exclude other targets",
    }


def manifest() -> dict:
    earlier.authenticate_prior()
    dependencies = [
        Path(__file__),
        ROOT/"scripts/core9_clique_targets_v1.py",
        ROOT/"scripts/core9_third_retractions_v2.py",
        ROOT/"scripts/core9_three_target_v1.py",
        ROOT/"scripts/bootstrap_core9_three_target_v1.sh",
        ROOT/"config/pycliques_commit_core9_three_target_v1.txt",
        ROOT/"research/order10_core9_third_retractions_v2/manifest.json",
    ] + [
        ROOT/f"research/order10_core9_third_retractions_v2/records/{core_id:08d}.json"
        for core_id in CORES
    ] + [
        ROOT/f"runs/order10/core9-structure-v1/records/{core_id:08d}.json"
        for core_id in CORES
    ]
    return {
        "schema":SCHEMA, "stage":"core9_coaffine_join_retractions_v1",
        "core_ids":list(CORES), "represented_ten_vertex_graphs":461,
        "target_construction":"C_n^c * O_r, n>=5, r>=1; dimension/rank matched",
        "admissible_parameters": {
            str(i):[list(t) for t in candidate_parameters(i)] for i in CORES
        },
        "homology_upper_degree_certified":5,
        "induced_patterns":"chordless complement cycles + separated matching edges",
        "retraction_verifiers":["independent backtracking","pinned bounded_retraction"],
        "worker_and_verifier_timeout_seconds":TIMEOUT_SECONDS,
        "worker_and_verifier_memory_mib":MEMORY_MIB,
        "pinned_solver_max_states":CSP_MAX_STATES,
        "pinned_solver_max_assignments":CSP_MAX_ASSIGNMENTS,
        "source_sha256":{
            str(p.relative_to(ROOT)):sha(p) for p in dependencies
        },
    }


def save(path:Path, row:dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",encoding="utf-8",dir=path.parent,prefix=".coaffine-",
        suffix=".tmp",delete=False,
    ) as tmp:
        candidate=Path(tmp.name)
        json.dump(row,tmp,indent=2,sort_keys=True)
        tmp.write("\n")
    try:
        os.replace(candidate,path)
    finally:
        candidate.unlink(missing_ok=True)


def restrict_resources() -> None:
    size=MEMORY_MIB*1024**2
    resource.setrlimit(resource.RLIMIT_AS,(size,size))


def bounded(action:str,core_id:int,path:Path) -> None:
    args=[sys.executable,str(Path(__file__)),action,
          "--core-id",str(core_id),"--output",str(path)]
    try:
        proc=subprocess.run(args,capture_output=True,text=True,
                            preexec_fn=restrict_resources,timeout=TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as e:
        raise TimeoutError(f"Bounded {action} for {core_id} exceeded wall-time") from e
    if proc.returncode:
        raise RuntimeError(f"Bounded {action} for {core_id} failed: {proc.stderr[-4000:]}")


def authenticate(path:Path,core_id:int) -> None:
    actual=json.loads(path.read_text())
    identity={"schema":SCHEMA,"core_id":core_id}
    if any(actual.get(k)!=v for k,v in identity.items()):
        raise ValueError("Saved core identity differs")
    if actual.get("status")=="TIMEOUT":
        if actual!={**identity,"status":"TIMEOUT","phase":"worker",
                    "limit_seconds":TIMEOUT_SECONDS}:
            raise ValueError("Forged timeout record or concealed proof")
        return
    if actual.get("status")!="COMPLETED" or actual!=compute(core_id):
        raise ValueError("Saved negative or positive record differs from full replay")


def run(directory:Path) -> None:
    m=manifest()
    directory.mkdir(parents=True,exist_ok=True)
    meta=directory/"manifest.json"
    if meta.exists():
        if json.loads(meta.read_text())!=m:
            raise ValueError("Refusing to change existing provenance manifest")
    else:
        if any(directory.iterdir()):
            raise ValueError("Refusing to reuse data directory without manifest")
        save(meta,m)
    for core_id in CORES:
        destination=directory/"records"/f"{core_id:08d}.json"
        if destination.exists():
            bounded("check",core_id,destination)
            continue
        with tempfile.TemporaryDirectory() as td:
            temp=Path(td)/"result.json"
            try:
                bounded("worker",core_id,temp)
            except TimeoutError:
                save(destination,{
                    "schema":SCHEMA,"core_id":core_id,
                    "status":"TIMEOUT","phase":"worker",
                    "limit_seconds":TIMEOUT_SECONDS,
                })
                continue
            bounded("check",core_id,temp)
            save(destination,json.loads(temp.read_text()))
    verify(directory)


def verify(directory:Path) -> None:
    if json.loads((directory/"manifest.json").read_text())!=manifest():
        raise ValueError("Stage manifest differs from pinned code and data")
    rec=directory/"records"
    files={f"{i:08d}.json" for i in CORES}
    if not rec.is_dir() or {p.name for p in rec.iterdir()}!=files:
        raise ValueError("Missing or extra records")
    for core_id in CORES:
        bounded("check",core_id,rec/f"{core_id:08d}.json")
    print("All coaffine-join retraction records independently replayed")


def report(directory:Path) -> None:
    verify(directory)
    for core_id in CORES:
        r=json.loads((directory/"records"/f"{core_id:08d}.json").read_text())
        if r["status"]=="TIMEOUT":
            print(json.dumps({"core_id":core_id,"status":"TIMEOUT", "classification":"UNRESOLVED"}))
            continue
        print(json.dumps({
            "core_id":core_id, "status":r["status"],
            "positive_count":len(r["positive_witnesses"]),
            "families":[{
                "n":p["n"],"r":p["r"],"chordless_cycles":p["cycle_count"],
                "induced_targets":p["induced_target_count"],
                "locally_impossible":p["local_impossible"],
                "csp_exhausted":p["csp_exhausted"],
                "csp_states":p["csp_states_total"],
                "found":p["found_count"]
            } for p in r["probes"]],
            "classification":(
                "POTENTIALLY_DIVERGENT_CORE_NEEDS_LIFT" if r["positive_witnesses"]
                else "UNRESOLVED"
            ),
        },sort_keys=True))


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=["plan","run","worker","check","verify","report"])
    p.add_argument("--core-id",type=int)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.action in ("worker","check"):
        if a.core_id not in CORES or a.output is None:
            p.error("worker/check requires an allowed core and output file")
        if a.action=="worker":
            save(a.output,compute(a.core_id))
        else:
            authenticate(a.output,a.core_id)
        return
    if a.action=="plan":
        print(json.dumps(manifest(),indent=2,sort_keys=True))
        return
    dest=a.output or OUTPUT
    if a.action=="run":
        run(dest)
    elif a.action=="verify":
        verify(dest)
    else:
        report(dest)


if __name__=="__main__":
    main()
