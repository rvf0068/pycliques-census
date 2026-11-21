#!/usr/bin/env python3
"""Audit every bounded K3-paring shard without claiming global maximality.

Positive within-shard classes have complete pairwise-checked vertex maps.
This audit verifies original McKay identity, exact disjoint source coverage,
and reported classification limits. It makes NO negative isomorphism claims.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import networkx as nx
from classes import cases


def require(condition, message):
    if not condition:
        raise ValueError(message)


def parse(g6):
    G=nx.from_graph6_bytes(g6.encode("ascii"))
    require(set(G)==set(range(len(G))), "Invalid pared graph labels")
    return G


def check_map(G,H,images):
    require(len(G)==len(H) and len(images)==len(G)
            and sorted(images)==list(range(len(H))),
            "Invalid bijection cardinality or permutation")
    for u in range(len(G)):
        for v in range(u+1,len(G)):
            require(G.has_edge(u,v)==H.has_edge(images[u],images[v]),
                    "Explicit purported isomorphism does not preserve all vertex pairs")


def audit(paths):
    paths=sorted(Path(p) for p in paths)
    require(len(paths)==8, "Expected exactly eight independent shard artifacts")
    originals=cases()  # authenticates immutable v10 original McKay-index archive
    source=dict(originals)
    require(len(source)==1043, "Original source size changed")
    seen_shards=set()
    covered=set()
    source_skips=[]
    processed=0
    groups=0
    group_members=0
    for path in paths:
        archive=json.loads(path.read_text())
        require(archive.get("schema")==1
                and archive.get("source")=="indeterminate_order_10_v10.txt",
                "Invalid shard archive")
        summary=archive["summary"]
        shard=summary["shard"]
        require(isinstance(shard,int) and shard in range(8)
                and shard not in seen_shards and summary["shards"]==8,
                "Duplicated or malformed shard")
        seen_shards.add(shard)
        expected={idx for place,(idx,_) in enumerate(originals)
                  if place%8==shard}
        batch=set()
        batch_processed=0
        for cls in archive["classes"]:
            members=cls["members"]
            require(members, "Empty claimed class")
            rep=next((m for m in members if m["index"]==cls["representative"]),None)
            require(rep is not None, "Missing class representative")
            target=parse(rep["pared_graph6"])
            if len(members)>1:
                groups+=1
                group_members+=len(members)
            for m in members:
                idx=m["index"]
                require(idx in expected and idx not in covered,
                        "Duplicated or incorrect original McKay index")
                require(m["graph6"]==source[idx], "Original graph6 identity changed")
                require(len(m["stages"])==4 and m["stages"][-1]["level"]==3,
                        "Incomplete iterated-fold provenance")
                G=parse(m["pared_graph6"])
                require(m["stages"][-1]["pared"]==[len(G),G.number_of_edges()],
                        "Final fold dimensions disagree")
                check_map(G,target,m["to_representative"])
                covered.add(idx)
                batch.add(idx)
                batch_processed+=1
        for m in archive["skipped"]:
            idx=m["index"]
            require(idx in expected and idx not in covered,
                    "Duplicated or incorrect skipped McKay index")
            require(m["graph6"]==source[idx], "Skipped graph6 identity changed")
            require(m["reason"] in {"clique graph exceeds 250 vertices",
                                    "per-source deadline 8s exceeded"},
                    "Unrecognized resource-bounded skip reason")
            covered.add(idx)
            batch.add(idx)
            source_skips.append({"index":idx,"reason":m["reason"]})
        require(batch==expected, "Missing original sources within shard")
        require(summary["sources"]==1043 and summary["selected"]==len(expected)
                and summary["processed"]==batch_processed
                and summary["skipped"]==len(archive["skipped"]),
                "Inconsistent shard totals")
        processed+=batch_processed
    require(seen_shards==set(range(8)) and covered==set(source),
            "The eight shards do not cover the original source exactly once")
    require(processed+len(source_skips)==1043, "Incorrect global source accounting")
    return {
        "schema":1,
        "scope":"positive batch-local K3-pared equivalence certificates only",
        "source":"indeterminate_order_10_v10.txt",
        "sources":1043,
        "processed":processed,
        "skipped":len(source_skips),
        "nontrivial_batch_groups":groups,
        "members_in_nontrivial_batch_groups":group_members,
        "skipped_original_mckay":sorted(source_skips,key=lambda m:m["index"]),
        "global_maximality_certified":False,
        "new_K_behavior_verdicts":0,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("shards",nargs="+",type=Path)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    result=audit(args.shards)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("VERIFIED_BATCH_AUDIT_JSON "+json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
