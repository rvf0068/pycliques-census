"""Independently certify nonretractions onto novel historical-census targets.

First reconstruct all 240 nonconjectural early historical positive graph
sources and their K^0,K^1,K^2 stiff targets (the complete independent
pilot). Select only the stiff candidates not isomorphic to previously
searched named targets and whose exact 0..5 Betti vectors satisfy the
necessary host constraints. All selected instances are proven divergent
by original historical verdicts plus replayable domination folds.

Enumerate EVERY induced embedding into each eligible third completely
pared clique iterate via NetworkX's complete VF2/ISMAGS subgraph
isomorphism algorithms on complements. For each induced copy, a
fixed-target-neighborhood obstruction is either verified or else two
independent bounded complete retraction searches are compared. A
nonpositive result cannot be inferred from timeouts/limited searches.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile

import networkx as nx
from networkx.algorithms.isomorphism import GraphMatcher,ISMAGS
from pycliques.retractions import bounded_retraction,RetractionSearchStatus

import historical_divergent_small_pilot_v1 as pilot
import core9_clique_targets_v1 as prior

ROOT=pilot.ROOT
OUTPUT=ROOT/"research/order10_historical_divergent_targets_v1/retraction_pilot"
SCHEMA=1
TIMEOUT_SECONDS=300
MEMORY_MIB=2500
MAX_CSP_STATES=100_000
MAX_CSP_ASSIGNMENTS=200_000
EXPECTED_ENGINES={
    (16,94):"ISMAGS",
    (20,174):"ISMAGS",
    (24,220):"VF2",
    (24,234):"VF2",
    (25,268):"VF2",
    (26,256):"VF2",
}


def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()


def domain_obstruction(host:nx.Graph,vertices:set[int]) -> int|None:
    """Find a vertex forced to have empty image domain by fixed targets."""
    for x in sorted(set(host)-vertices):
        neighbors=set(host[x])&vertices
        if not any(
            all(t==y or host.has_edge(t,y) for y in neighbors)
            for t in vertices
        ):
            return x
    return None


def two_solvers(host:nx.Graph,vertices:list[int]) -> dict:
    """A positive result must be independently replayed as a total retraction."""
    independent=prior.exhaustive_retraction(host,vertices)
    pinned=bounded_retraction(
        host,host.subgraph(vertices),
        max_states=MAX_CSP_STATES,
        max_assignments=MAX_CSP_ASSIGNMENTS,
    )
    if pinned.status is RetractionSearchStatus.LIMIT_REACHED:
        return {"status":"LIMIT_REACHED","independent_states":independent["states"],
                "pinned_states":pinned.states_explored}
    found=pinned.status is RetractionSearchStatus.FOUND
    if (independent["status"]=="FOUND")!=found:
        raise AssertionError("Independent retraction solvers disagree")
    if found:
        projection=dict(map(tuple,independent["retraction"]))
        if (
            set(projection)!=set(host)
            or set(projection.values())-set(vertices)
            or any(projection[t]!=t for t in vertices)
            or any(
                projection[u]!=projection[v] and
                not host.has_edge(projection[u],projection[v])
                for u,v in host.edges()
            )
        ):
            raise AssertionError("Positive map fails adjacency-or-equality")
    return {
        "status":"FOUND" if found else "EXHAUSTED",
        "independent_states":independent["states"],
        "pinned_states":pinned.states_explored,
        "projection":independent["retraction"] if found else None,
    }


def probe(host:nx.Graph,target:nx.Graph,method:str) -> dict:
    h_comp=nx.complement(host)
    t_comp=nx.complement(target)
    matcher=(
        ISMAGS(h_comp,t_comp) if method=="ISMAGS"
        else GraphMatcher(h_comp,t_comp)
    )
    choices:dict[tuple[int,...],dict]={}
    maps=0
    for map_ in matcher.subgraph_isomorphisms_iter():
        maps+=1
        vertices=tuple(sorted(map_))
        if vertices in choices:
            continue
        if not nx.is_isomorphic(host.subgraph(vertices),target):
            raise AssertionError("Candidate embedding is not induced")
        forced=domain_obstruction(host,set(vertices))
        if forced is not None:
            row={"vertices":list(vertices),"status":"LOCAL_IMPOSSIBLE",
                 "empty_domain_vertex":forced}
        else:
            row={"vertices":list(vertices),
                 "status":"UNDETERMINED","empty_domain_vertex":None,
                 **two_solvers(host,list(vertices))}
        choices[vertices]=row
    cases=[choices[k] for k in sorted(choices)]
    if any(row["status"]=="LIMIT_REACHED" for row in cases):
        status="LIMIT_REACHED"
    elif any(row["status"]=="FOUND" for row in cases):
        status="FOUND"
    else:
        status="EXHAUSTED"
    return {
        "status":status,
        "method":method,
        "labeled_embedding_maps":maps,
        "induced_vertex_sets":len(cases),
        "locally_impossible":sum(
            row["status"]=="LOCAL_IMPOSSIBLE" for row in cases
        ),
        "fully_tested_csp":sum(
            row["status"] in ("EXHAUSTED","FOUND") for row in cases
        ),
        "positive_retractions":sum(row["status"]=="FOUND" for row in cases),
        "negative_certificates":cases,
    }


def compute()->dict:
    survey=pilot.compute()
    if survey["status"]!="COMPLETED" or survey["source_graphs"]!=240:
        raise ValueError("240-source pilot did not complete")
    candidates=[
        c for c in survey["candidate_targets"]
        if c["previously_searched_family"] is None
    ]
    observed={(x["order"],x["edges"]) for x in candidates}
    # There are NINE distinct stiff graph classes in SIX (order,edges)
    # buckets. Multiple nonisomorphic graphs have order 25 and 268
    # edges; never collapse them just because these invariants agree!
    if (
        observed!=set(EXPECTED_ENGINES)
        or len(candidates)!=9
        or len({x["graph6"] for x in candidates})!=9
    ):
        raise ValueError(
            f"New historical candidate classes differ: "
            f"{len(candidates)} classes in buckets {observed}"
        )
    hosts={cid:prior.host(cid)[0] for cid in (6914104,6962151)}
    rows=[]
    for case in candidates:
        graph=nx.from_graph6_bytes(case["graph6"].encode("ascii"))
        engine=EXPECTED_ENGINES[(len(graph),graph.number_of_edges())]
        searches=[]
        for cid in case["eligible_hosts"]:
            result=probe(hosts[cid],graph,engine)
            searches.append({"host_core_id":cid,**result})
        rows.append({
            "candidate_graph6":case["graph6"],
            "order":case["order"],"edges":case["edges"],
            "historical_provenance":case["provenance"],
            "betti_0_to_5":case["mod2_betti_degrees_0_to_5"],
            "retraction_searches":searches,
        })
    rows.sort(key=lambda x:(x["order"],x["edges"],x["candidate_graph6"]))
    return {
        "schema":SCHEMA,"status":"COMPLETED",
        "historical_positives_screened":240,
        "historical_stiff_classes":survey["unique_stiff_isomorphism_classes"],
        "new_candidate_graphs":len(rows),
        "candidate_host_pairs":sum(len(x["retraction_searches"]) for x in rows),
        "induced_target_copies":sum(
            q["induced_vertex_sets"]
            for x in rows for q in x["retraction_searches"]
        ),
        "local_retraction_obstructions":sum(
            q["locally_impossible"]
            for x in rows for q in x["retraction_searches"]
        ),
        "positive_retractions":sum(
            q["positive_retractions"]
            for x in rows for q in x["retraction_searches"]
        ),
        "incomplete_searches":sum(
            q["status"]=="LIMIT_REACHED"
            for x in rows for q in x["retraction_searches"]
        ),
        "source_pilot_sha256":hashlib.sha256(
            json.dumps(survey,sort_keys=True,separators=(",",":")).encode()
        ).hexdigest(),
        "candidates":rows,
        "scope":"Only the 232 original positive 6..8 graphs, eight extra proved "
                "order9 graphs and their K^0..K^2 stiff reductions; "
                "no claim of convergence or nondivergence for the host cores",
    }


def manifest()->dict:
    deps=[
        Path(__file__),
        ROOT/"scripts/historical_divergent_small_pilot_v1.py",
        ROOT/"scripts/historical_divergent_targets_v1.py",
        ROOT/"scripts/core9_clique_targets_v1.py",
        ROOT/"runs/baseline-through8-bound30/summary.json",
        ROOT/"research/order10_core9_clique_targets_v1/summary.md",
    ]
    return {
        "schema":SCHEMA,"stage":"historical_small_retractions_v1",
        "input_historically_proven_graphs":240,
        "distinct_target_classes_expected":9,
        "candidate_host_pairs_expected":12,
        "candidate_size_edge_buckets":sorted([list(x) for x in EXPECTED_ENGINES]),
        "isomorphism_engines":dict((str(k),v) for k,v in EXPECTED_ENGINES.items()),
        "max_csp_states":MAX_CSP_STATES,
        "max_csp_assignments":MAX_CSP_ASSIGNMENTS,
        "worker_and_verifier_seconds":TIMEOUT_SECONDS,
        "worker_and_verifier_memory_mib":MEMORY_MIB,
        "source_sha256":{str(p.relative_to(ROOT)):sha(p) for p in deps},
    }


def save(path:Path,data:dict):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",dir=path.parent,encoding="utf-8",delete=False,
        prefix=".historical-retract-",suffix=".tmp",
    ) as f:
        p=Path(f.name)
        json.dump(data,f,indent=2,sort_keys=True)
        f.write("\n")
    try:os.replace(p,path)
    finally:p.unlink(missing_ok=True)


def limit():
    bytes_=MEMORY_MIB*1024**2
    resource.setrlimit(resource.RLIMIT_AS,(bytes_,bytes_))


def bounded(action:str,path:Path):
    try:
        process=subprocess.run(
            [sys.executable,str(Path(__file__)),action,"--output",str(path)],
            capture_output=True,text=True,timeout=TIMEOUT_SECONDS,
            preexec_fn=limit,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError("Bounded independent historical retraction search timed out") from exc
    if process.returncode:
        raise RuntimeError(f"Historical {action} failed: {process.stderr[-3500:]}")


def authenticate(path:Path):
    if json.loads(path.read_text())!=compute():
        raise ValueError("Saved positive or negative retraction claims differ from full replay")


def run(directory:Path):
    meta=manifest()
    directory.mkdir(parents=True,exist_ok=True)
    head=directory/"manifest.json"
    if head.exists():
        if json.loads(head.read_text())!=meta:raise ValueError("Provenance changed")
    else:
        if any(directory.iterdir()):raise ValueError("Existing unversioned results")
        save(head,meta)
    result=directory/"records.json"
    if result.exists():bounded("check",result);return
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td)/"result.json"
        bounded("worker",temp)
        bounded("check",temp)
        save(result,json.loads(temp.read_text()))


def verify(directory:Path):
    if json.loads((directory/"manifest.json").read_text())!=manifest():
        raise ValueError("Source code/provenance differs")
    bounded("check",directory/"records.json")
    print("All six new targets independently replayed")


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("action",choices=("run","worker","check","verify","report"))
    a.add_argument("--output",type=Path)
    args=a.parse_args()
    if args.action in ("worker","check"):
        if args.output is None:a.error("Need --output record")
        if args.action=="worker":save(args.output,compute())
        else:authenticate(args.output)
        return
    root=args.output or OUTPUT
    if args.action=="run":run(root);return
    if args.action=="verify":verify(root);return
    data=json.loads((root/"records.json").read_text())
    print(json.dumps({k:v for k,v in data.items() if k!="candidates"},indent=2,sort_keys=True))
    for x in data["candidates"]:
        for q in x["retraction_searches"]:
            print(json.dumps({
                "graph6":x["candidate_graph6"],
                "order":x["order"],"edges":x["edges"],
                "host":q["host_core_id"],"method":q["method"],
                "status":q["status"],"induced_copies":q["induced_vertex_sets"],
                "local_obstructions":q["locally_impossible"],
                "retractions_found":q["positive_retractions"],
            },sort_keys=True))


if __name__=="__main__":main()
