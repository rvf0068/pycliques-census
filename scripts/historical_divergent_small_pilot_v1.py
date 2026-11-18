"""Fast independently replayed 240-source pilot from the *early* census.

Uses the 232 historically proved divergent original graphs on 6..8 vertices
and the eight newly certified order-nine post-stage graphs (4 C10, 1
bound60, 3 bound70). Their early raw K iterates, and exact
closed-neighborhood stiff cores, give a useful first nonconjectural
target catalog while the much larger 9-vertex initial cohort is sharded.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile

import networkx as nx
from pycombtop.bounded_betti import bounded_reduced_betti_mod2

import historical_divergent_targets_v1 as full
from validate import iter_chunks
from graph_sources import connected_graphs,EXPECTED_COUNTS

ROOT=full.ROOT
OUTPUT=ROOT/"research/order10_historical_divergent_targets_v1/pilot"
SCHEMA=1
TIMEOUT_SECONDS=240
MEMORY_MIB=2500


def sources():
    # The pilot must authenticate the 6..8 graph6 archives too,
    # rather than relying on a checksum check only in the full worker.
    full.validate_source_archives()
    seen=Counter()
    for n in (6,7,8):
        records=iter_chunks(full.BASE/f"order{n}",n,500)
        for index,g in enumerate(connected_graphs(n)):
            ix,status,reason=next(records)
            if ix!=index:raise ValueError("Historical index mismatched")
            if status=="DIVERGENT":
                # Only certified positive reasons are admissible. Share
                # exactly the same rule as the complete historical scan.
                full.require_certified_initial_reason(reason,n,index)
                seen[n]+=1
                yield {"order":n,"index":index,"graph6":full.graph6(g),
                       "stage":"initial","historical_reason":reason},g
        if seen[n]!=full.HIST_COUNTS[n]:
            raise ValueError("Wrong early historical positive count")
    eight=full.staged_proven_positive_indices()
    for idx,record in sorted(eight.items()):
        g=full.graph_from_g6(record["graph6"])
        if len(g)!=9:
            raise ValueError("Later positive has wrong graph order")
        yield {
            "order":9,"index":idx,"graph6":record["graph6"],
            "stage":record["stage"],
            "historical_reason":record["reason"],
            "historical_record_sha256":record["record_sha256"],
        },g


def compute():
    hosts={i:full.prior.host(i)[0] for i in full.HOST_IDS}
    hom={i:full.prior.host(i)[1] for i in full.HOST_IDS}
    classes=[]
    buckets=defaultdict(list)
    skipped=Counter()
    counts=Counter()
    for source,g in sources():
        counts[source["stage"]]+=1
        current=g
        for level in range(3):
            if level:
                current=full.raw_clique_graph_bounded(current)
                if current is None:
                    skipped[f"K{level}"]+=1
                    break
            stiff,steps=full.stiff_fold(current)
            occurrence={
                "historical_graph":dict(source),
                "raw_iterate_level":level,
                "raw_iterate_graph6":full.graph6(current),
                "folded_graph6":full.graph6(stiff),
                "dominated_deletions":steps,
            }
            key=full.candidate_isomorphic_key(stiff)
            existing=next((k for k in buckets[key]
                           if full.bounded_isomorphic(classes[k]["graph"],stiff,skipped)),None)
            if existing is not None:
                classes[existing]["instances"]+=1
                classes[existing]["all_provenance"].append(occurrence)
                continue
            k=len(classes)
            classes.append({
                "graph":stiff,"instances":1,
                "provenance":occurrence,
                "all_provenance":[occurrence],
            })
            buckets[key].append(k)
    if counts!=Counter({"initial":232,"c10":4,"bound60":1,"bound70":3}):
        raise ValueError(f"Pilot historical proof counts disagree: {counts}")
    models=full.known_target_models()
    results=[]
    filter_counts=Counter()
    for row in classes:
        graph=row["graph"]
        struc={i:full.structural_necessary(graph,hosts[i])
               for i in full.HOST_IDS}
        if all(v is not None for v in struc.values()):
            filter_counts["both_structural"]+=1
            continue
        betti=bounded_reduced_betti_mod2(
            graph,max_faces=full.MAX_FACES,max_degree=5)
        if betti is None:filter_counts["homology_limited"]+=1
        eligible=[]
        checked={}
        for cid in full.HOST_IDS:
            status,blocked=full.homology_necessary(betti,hom[cid])
            checked[str(cid)]={
                "status":status,
                "obstructing_degrees":blocked,
            }
            if struc[cid] is not None:continue
            if blocked:
                filter_counts[f"homology_{cid}"]+=1
                continue
            eligible.append(cid)
        if not eligible:continue
        known=next((
            label for label,model in models
            if len(graph)==len(model) and
            graph.number_of_edges()==model.number_of_edges()
            and nx.is_isomorphic(graph,model)
        ),None)
        results.append({
            "graph6":full.graph6(graph),"order":len(graph),
            "edges":graph.number_of_edges(),
            "instances":row["instances"],
            "provenance":row["provenance"],
            "all_provenance":row["all_provenance"],
            "homology_obstructions_by_host":checked,
            "mod2_betti_degrees_0_to_5":(
                {str(k):v for k,v in betti.items()} if betti is not None else None
            ),
            "homology_status":"EXACT_THROUGH_5" if betti is not None else "LIMIT",
            "eligible_hosts":eligible,
            "previously_searched_family":known,
        })
    results.sort(key=lambda row:(
        row["previously_searched_family"] is not None,
        row["order"], row["edges"],-row["instances"],row["graph6"]
    ))
    return {
        "schema":SCHEMA,"status":"COMPLETED",
        "historical_source_archives_sha256":full.validate_source_archives(),
        "source_graphs":sum(counts.values()),
        "historical_positive_stages":dict(counts),
        "unique_stiff_isomorphism_classes":len(classes),
        "raw_iterate_skips_exceeding_40":{
            k:v for k,v in skipped.items() if k.startswith("K")
        },
        "timed_out_graph_isomorphisms_kept_separate":skipped["isomorphism_timeouts"],
        "filter_counts":dict(filter_counts),
        "eligible_target_classes":len(results),
        "novel_target_classes":sum(
            r["previously_searched_family"] is None for r in results
        ),
        "eligible_by_host":{
            str(i):sum(i in r["eligible_hosts"] for r in results)
            for i in full.HOST_IDS
        },
        "candidate_targets":results,
        "scope":"historical certified 6..8 and eight later nine-positive graphs only; "
                "all initial nine-vertex divergence sources excluded from this pilot",
    }


def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()


def manifest():
    files=[
        Path(__file__),
        ROOT/"scripts/historical_divergent_targets_v1.py",
        ROOT/"scripts/core9_crossref.py",
        ROOT/"scripts/validate.py",
        ROOT/"scripts/graph_sources.py",
        ROOT/"scripts/core_isomorphism_index.py",
        ROOT/"scripts/bootstrap_core9_three_target_v1.sh",
        ROOT/"scripts/core9_clique_targets_v1.py",
        ROOT/"scripts/core9_third_retractions_v2.py",
        ROOT/"scripts/core9_three_target_v1.py",
        ROOT/"config/pycliques_commit_core9_three_target_v1.txt",
        ROOT/"research/order10_core9_three_target_v1/manifest.json",
        ROOT/"research/order10_core9_third_retractions_v2/manifest.json",
        ROOT/"runs/baseline-through8-bound30/summary.json",
        ROOT/"runs/baseline-through8-bound30/manifest.json",
        ROOT/"runs/order9/initial/summary.json",
        ROOT/"runs/order9/initial/manifest.json",
        ROOT/"runs/order9/initial/order9/indeterminate_order_9.txt",
        ROOT/"indeterminate_order_9.txt",
    ]
    for n in (6,7,8):
        files.extend(sorted((full.BASE/f"order{n}"/"chunks").glob("*.tsv.gz")))
    for core_id in full.HOST_IDS:
        files.extend([
            ROOT/f"runs/order10/core9-structure-v1/records/{core_id:08d}.json",
            ROOT/f"research/order10_core9_three_target_v1/records/{core_id:08d}.json",
            ROOT/f"research/order10_core9_third_retractions_v2/records/{core_id:08d}.json",
        ])
    for stage in full.ADDITIONAL_NINE:
        # Full historical cohort validation reads BOTH the named cohort
        # manifest and the summary, as well as every stage record.
        files.extend(sorted((full.NINE/stage/"records").glob("*.json")))
        files.append(full.NINE/stage/"summary.json")
        files.append(full.NINE/stage/"manifest.json")
    # Do not accidentally accept a source-dependent output under a
    # provenance manifest that omits or duplicates an input path.
    names=[str(p.relative_to(ROOT)) for p in files]
    if len(names)!=len(set(names)):
        raise ValueError("Duplicate historical provenance dependency")
    return {
        "schema":SCHEMA,"stage":"historical_divergent_small_pilot_v1",
        "expected_positive_graphs":240,
        "indexed_graph6_archives_sha256":full.validate_source_archives(),
        "complete_target_occurrence_provenance":True,
        "exact_betti_inequalities_required":list(range(6)),
        "max_raw_K_level":2,"max_target_order":40,
        "source_sha256":{str(p.relative_to(ROOT)):sha(p) for p in files},
        "worker_and_verifier_seconds":TIMEOUT_SECONDS,
        "memory_mib":MEMORY_MIB,
    }


def save(path:Path,data:dict):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",dir=path.parent,encoding="utf-8",
        prefix=".pilot-",suffix=".tmp",delete=False,
    ) as f:
        temporary=Path(f.name)
        json.dump(data,f,indent=2,sort_keys=True)
        f.write("\n")
    try:os.replace(temporary,path)
    finally:temporary.unlink(missing_ok=True)


def limit():
    n=MEMORY_MIB*1024**2
    resource.setrlimit(resource.RLIMIT_AS,(n,n))


def bounded(action:str,path:Path):
    try:
        p=subprocess.run(
            [sys.executable,str(Path(__file__)),action,"--output",str(path)],
            timeout=TIMEOUT_SECONDS,preexec_fn=limit,
            capture_output=True,text=True,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError("Historical pilot computation/replay timed out") from exc
    if p.returncode:
        raise RuntimeError(f"Historical pilot {action} failed: {p.stderr[-3800:]}")


def authenticate(path:Path):
    saved=json.loads(path.read_text())
    if saved!=compute():
        raise ValueError("Pilot result differs from completely independent replay")


def run(directory:Path):
    meta=manifest()
    directory.mkdir(parents=True,exist_ok=True)
    head=directory/"manifest.json"
    if head.exists():
        if json.loads(head.read_text())!=meta:
            raise ValueError("Historical pilot provenance changed")
    else:
        if any(directory.iterdir()):raise ValueError("Unversioned pilot results")
        save(head,meta)
    target=directory/"catalog.json"
    if target.exists():bounded("check",target);return
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)/"result.json"
        bounded("worker",tmp)
        bounded("check",tmp)
        save(target,json.loads(tmp.read_text()))


def verify(directory:Path):
    if json.loads((directory/"manifest.json").read_text())!=manifest():
        raise ValueError("Pilot source hash differs")
    bounded("check",directory/"catalog.json")
    print("Independent historical 240-target pilot replay passed")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=("run","worker","check","verify","report"))
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    if args.action in ("worker","check"):
        if args.output is None:p.error("Need output")
        if args.action=="worker":save(args.output,compute())
        else:authenticate(args.output)
        return
    folder=args.output or OUTPUT
    if args.action=="run":run(folder);return
    if args.action=="verify":verify(folder);return
    # Report is cheap because both independent passes already validated.
    data=json.loads((folder/"catalog.json").read_text())
    print(json.dumps({k:v for k,v in data.items() if k!="candidate_targets"},
                     indent=2,sort_keys=True))
    for h in full.HOST_IDS:
        rows=[r for r in data["candidate_targets"]
              if h in r["eligible_hosts"] and
              r["previously_searched_family"] is None]
        print(f"HOST {h} novel candidates: {len(rows)}")
        for r in rows[:25]:
            o=r["provenance"]["historical_graph"]
            print(f"  {r['graph6']} vertices={r['order']} "
                  f"edges={r['edges']} beta={r['mod2_betti_degrees_0_to_5']} "
                  f"origin={o['order']}:{o['index']}:{o['stage']} "
                  f"level={r['provenance']['raw_iterate_level']}")


if __name__=="__main__":main()
