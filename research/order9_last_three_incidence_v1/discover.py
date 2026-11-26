"""Recover full P4-to-octahedron certificates for last three nine-originals.

Uses ONLY existing cross-checked census P3/P4 reconstruction and public
pinned pycliques native coaffine/incidence algorithms. No new search
algorithm or assumed antipodal pair is introduced. All full found maps,
the raw P4 fold moves, source fingerprints, and complete target
pairs are archived for independent replay without pycliques.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import sys

if sys.flags.optimize:
    raise RuntimeError("Proof-critical last-three discovery checks disabled")

import networkx as nx

from research.order10_p4_crossdepth_o15_v25.verify import git_blob, source_rows
from research.order10_p3_global_v23_index.independent_verify import independent_p3
from research.order10_p4_cap_rescue_v24.verify import p4_facets, raw_from_facets, fully_pare

ROOT = Path(__file__).resolve().parents[2]
NINE = ROOT / "indeterminate_order_9_v9.txt"
NINE_BLOB = "d18a7a843be935f3a7fe911691dd1c86dac2addd"
MONOREPO = "e1e9ed04f5c1f962a5f7e70312fb8df16e5a6a78"
CASES = {
    249576: ("HEhfvzu", (53,1044), (685,199283)),
    251628: ("HEhvVn{", (55,1156), (1034,467517)),
    260040: ("HQyvex}", (58,1289), (1227,658528)),
}


def need(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def source(index: int):
    import pycliques as pc
    need(index in CASES, "Unknown nine-original")
    g6,p3shape,p4shape=CASES[index]
    need(git_blob(NINE.read_bytes())==NINE_BLOB,
         "Immutable nine-v9 source Git blob modified")
    need(source_rows(NINE)[index]==f"{index} 9 {g6} - - -",
         "Nine-original McKay graph6 or record altered")
    p3=independent_p3(g6)
    need((len(p3),p3.number_of_edges())==p3shape,
         "Independent P3 reconstruction disagrees")
    # Both NetworkX and bitset Bron--Kerbosch must enumerate the
    # exact SAME family of maximal cliques of the independently built P3.
    independently_enumerated=p4_facets(p3)
    implicit=pc.ImplicitCliqueGraph.from_graph(p3,max_cliques=3000)
    need(implicit is not None
         and list(implicit.clique_masks)==independently_enumerated,
         "Pinned public implicit host disagrees with independent BK facets")
    raw_rows=raw_from_facets(independently_enumerated,len(p3))
    need(len(raw_rows)==len(implicit.clique_masks),
         "Incomplete fourth clique-graph source")
    pared=implicit.pare()
    need(pc.verify_implicit_paring(implicit,pared),
         "Implicit paring lacks a complete ordinary fold certificate")
    host=pared.core
    need((len(host),host.number_of_edges())==p4shape,
         "Exact fourth pared iterate size or edges changed")
    independent_survivors,independent_pared,_=fully_pare(raw_rows)
    need((len(independent_pared),
          sum(a.bit_count() for a in independent_pared)//2)==p4shape,
         "Independent bitset P4 fold algorithm disagrees")
    return host,pared.moves,raw_rows,p3shape,p4shape


def proof(index: int,policy: str="native-then-walk"):
    import pycliques as pc
    g6,p3shape,p4shape=CASES[index]
    host,moves,raw_rows,_,_=source(index)
    graph=host.to_networkx()
    need(graph is not None and len(graph)==p4shape[0],
         "Pared implicit source is not a complete explicit graph")
    status_history=[]
    positive=None

    # This reproduces the native-first search discovered in
    # blind_octahedral_retractions.org. The solver's first full
    # witness (not a target dimension requested in advance) suffices.
    for shuffle in (False,True):
        ids=sorted(graph)
        if shuffle:
            random.Random(10).shuffle(ids)
        ordered=nx.Graph()
        ordered.add_nodes_from(ids)
        ordered.add_edges_from(graph.edges())
        need(ordered.number_of_edges()==graph.number_of_edges()
             and all(ordered.has_edge(u,v) for u,v in graph.edges()),
             "Reordered graph changed its mathematical edges")
        result=pc.find_octahedral_retraction_coaffine(
            ordered,backend="native",min_dimension=3,
            max_states=3000,time_limit=90.0,
        )
        status=result.status.name
        status_history.append({
            "algorithm":"public_native_coaffine_octahedron",
            "ordering":"shuffle_seed_10" if shuffle else "canonical",
            "status":status,"states":result.states_explored,
        })
        if status=="FOUND":
            positive=result
            break

    if positive is None:
        result=pc.find_octahedral_retraction_incidence(
            host,backend="walk",min_dimension=3,
            seed=139,max_steps=250_000,time_limit=270.0,
        )
        status_history.append({
            "algorithm":"public_incidence_weighted_walk",
            "seed":139,"max_steps":250_000,
            "status":result.status.name,
            "states":result.states_explored,
        })
        if result.status.name=="FOUND":
            positive=result

    record={
        "schema":1,
        "kind":"independently_replayable_P4_octahedral_retraction",
        "original_index":index,"original_graph6":g6,
        "historical_nine_v9_git_blob":NINE_BLOB,
        "pinned_monorepo_commit":MONOREPO,
        "P3":list(p3shape),"P4":list(p4shape),
        "raw_P4_order":len(raw_rows),
        "raw_P4_facet_sha256":hashlib.sha256(
            "|".join(str(x) for x in host.clique_masks).encode("ascii")
        ).hexdigest(),
        "paring_moves":[list(pair) for pair in moves],
        "source_active_raw_vertex_ids":list(host),
        "search_history":status_history,
        "no_negative_K_conclusion":True,
    }
    if positive is None:
        record["status"]="LIMIT_REACHED"
        return record

    need(positive.antipodal_pairs is not None
         and positive.retraction is not None
         and positive.inclusion is not None,
         "Native result lacks full pairs/retraction/inclusion")
    pairs=[list(x) for x in positive.antipodal_pairs]
    target={v for pair in pairs for v in pair}
    projection=positive.retraction
    verts=list(host)
    need(len(pairs)>=3 and len(target)==2*len(pairs)
         and set(projection)==set(verts)
         and set(projection.values())==target
         and all(projection[v]==v for v in target)
         and all(not graph.has_edge(a,b) for a,b in pairs)
         and all(graph.has_edge(a,b) for i,p in enumerate(pairs)
                 for q in pairs[i+1:] for a in p for b in q)
         and all(projection[u]==projection[v]
                 or graph.has_edge(projection[u],projection[v])
                 for u,v in graph.edges()),
         "Full complete octahedral retraction proof fails")
    record["status"]="FOUND"
    record["target_dimension"]=len(pairs)
    record["antipodal_pairs"]=pairs
    record["projection_images_in_active_raw_vertex_order"]=[
        projection[v] for v in verts
    ]
    print(f"PROVED original={index} P4={len(graph)} "
          f"target=O{len(pairs)} edges={graph.number_of_edges()} "
          f"search={status_history}",flush=True)
    return record


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--index",type=int,choices=sorted(CASES),required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    certificate=proof(args.index)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(
        json.dumps(certificate,sort_keys=True,indent=2)+"\n",
        encoding="utf-8"
    )
    print("PASS: nine-original fourth-iterate complete source audited "
          f"index={args.index} status={certificate['status']}",flush=True)


if __name__=="__main__":
    main()
