"""Solver-independent complete proof of three connected-nine P4 -> O_d retractions.

Reconstruct each P3 from original graph6 using the historical double
enumerator; independently verify both NetworkX and Bron--Kerbosch
families of ALL P4 maximal cliques; replay every ordinary
dominated-vertex deletion on raw clique incidence; check stiffness
and every edge of the complete saved P4 -> induced O_d projection.
Does not import pycliques, a native search tool, or a mutable census.
"""
from __future__ import annotations

from collections import Counter

import networkx as nx
import hashlib
import json
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("Cannot optimize away original P4 retraction proof")

from research.order10_p4_crossdepth_o15_v25.verify import git_blob, source_rows
from research.order10_p3_global_v23_index.independent_verify import independent_p3
from research.order10_p4_cap_rescue_v24.verify import (
    p4_facets, raw_from_facets, fully_pare,
)
from research.order9_last_three_incidence_v1.discover import (
    CASES, NINE, NINE_BLOB, MONOREPO,
)


def need(ok: bool, why: str) -> None:
    if not ok:
        raise AssertionError(why)


def check_fold_chain(raw: list[int], moves: list[list[int]],
                     survivors: list[int]) -> None:
    n=len(raw)
    alive=(1<<n)-1
    need(len(moves)==n-len(survivors),
         "Deleted vertices missing from complete paring chain")
    for pair in moves:
        need(type(pair) is list and len(pair)==2
             and all(type(v) is int and 0<=v<n for v in pair),
             "Malformed dominated-vertex deletion")
        p,q=pair
        need(p!=q and alive & (1<<p) and alive & (1<<q),
             "Deleted vertex or its claimed dominator is already absent")
        closed_p=(raw[p]|(1<<p))&alive
        closed_q=(raw[q]|(1<<q))&alive
        need(not closed_p &~closed_q,
             "The alleged historical ordinary dominated vertex was not dominated")
        alive &= ~(1<<p)
    need(survivors==[v for v in range(n) if alive & (1<<v)],
         "P4 active raw facet IDs do not equal completely replayed fold chain")
    for u in survivors:
        for v in survivors:
            if u!=v:
                need(bool(((raw[u]|(1<<u))&alive)
                          &~((raw[v]|(1<<v))&alive)),
                     "The final fourth iterate was not stiff")


def audit_case(rec: dict, frozen: dict[int,str]) -> dict:
    index=rec.get("original_index")
    need(index in CASES, "Unknown source nine McKay original")
    g6,p3_expected,p4_expected=CASES[index]
    need(rec.get("schema")==1
         and rec.get("kind")=="independently_replayable_P4_octahedral_retraction"
         and rec.get("status")=="FOUND"
         and rec.get("original_graph6")==g6
         and rec.get("historical_nine_v9_git_blob")==NINE_BLOB
         and rec.get("pinned_monorepo_commit")==MONOREPO
         and rec.get("P3")==list(p3_expected)
         and rec.get("P4")==list(p4_expected)
         and rec.get("no_negative_K_conclusion") is True
         and frozen[index]==f"{index} 9 {g6} - - -",
         "Nine-original source or alleged native positive provenance changed")
    independent=independent_p3(g6)
    need((len(independent),independent.number_of_edges())==p3_expected
         and set(independent)==set(range(p3_expected[0])),
         "Original P3 reconstructed graph differs")
    public_string=rec["public_sequence_P3_graph6"]
    need(isinstance(public_string,str)
         and not public_string.startswith(">>"),
         "Recorded public P3 graph6 is malformed")
    G=nx.from_graph6_bytes(public_string.encode("ascii"))
    need((len(G),G.number_of_edges())==p3_expected
         and set(G)==set(range(p3_expected[0])),
         "Public P3 source dimension or canonical labels changed")
    mapping=rec["independent_P3_to_public_P3_bijection"]
    need(isinstance(mapping,list)
         and len(mapping)==len(G)
         and sorted(mapping)==list(range(len(G)))
         and all(independent.has_edge(u,v)==
                 G.has_edge(mapping[u],mapping[v])
                 for u in independent for v in independent),
         "Independent P3 from original graph6 is not isomorphic by saved complete map")
    facets=p4_facets(G)
    need(hashlib.sha256(
        "|".join(str(x) for x in facets).encode("ascii")
    ).hexdigest()==rec["raw_P4_facet_sha256"]
         and len(facets)==rec["raw_P4_order"],
         "P4 maximal-clique incidence source differs from original graph6")
    raw=raw_from_facets(facets,len(G))
    active=rec["source_active_raw_vertex_ids"]
    need(type(active) is list
         and active==sorted(set(active))
         and all(type(v) is int and 0<=v<len(raw) for v in active),
         "Invalid retraction source raw P4 vertex identities")
    check_fold_chain(raw,rec["paring_moves"],active)
    n=len(active)
    active_mask=sum(1<<v for v in active)
    edges=sum((raw[u]&active_mask).bit_count() for u in active)//2
    need((n,edges)==p4_expected,
         "Independently reconstructed fourth pared iterate dimensions differ")
    independent_survivors,independent_pared,_=fully_pare(raw)
    need((len(independent_pared),
          sum(v.bit_count() for v in independent_pared)//2)==p4_expected,
         "Independent second P4 paring method disagrees")

    dimension=rec["target_dimension"]
    pairs=rec["antipodal_pairs"]
    need(type(dimension) is int and dimension>=3
         and type(pairs) is list and len(pairs)==dimension
         and all(type(pair) is list and len(pair)==2
                 and all(type(v) is int and v in active for v in pair)
                 for pair in pairs),
         "Invalid complete target antipodal pairs")
    endpoints=[v for pair in pairs for v in pair]
    target=set(endpoints)
    need(len(target)==2*dimension
         and all(not(raw[a]&(1<<b)) for a,b in pairs),
         "The alleged induced octahedron antipodes are adjacent")
    for i,p in enumerate(pairs):
        for q in pairs[i+1:]:
            need(all(raw[a]&(1<<b) for a in p for b in q),
                 "Different octahedral pairs are not completely joined")
    images=rec["projection_images_in_active_raw_vertex_order"]
    need(type(images) is list and len(images)==len(active)
         and all(type(v) is int and v in target for v in images),
         "Full ordinary P4 projection is missing or has wrong labels")
    f=dict(zip(active,images,strict=True))
    need(set(f.values())==target
         and all(f[v]==v for v in target),
         "Alleged P4 ordinary retraction fails target fixation/surjectivity")
    checked=0
    for i,u in enumerate(active):
        for v in active[i+1:]:
            if raw[u]&(1<<v):
                checked+=1
                need(f[u]==f[v] or raw[f[u]]&(1<<f[v]),
                     "An original P4 edge maps to an octahedral missing edge")
    need(checked==edges, "Not every original P4 source edge was checked")
    return {
        "original_index":index, "original_graph6":g6,
        "pared_depth":4,
        "P4":[n,edges],"target_dimension":dimension,
        "independent_maximal_clique_enumerators_agree":True,
        "every_dominated_vertex_deletion_verified":True,
        "final_P4_stiffness_verified":True,
        "induced_octahedral_pairs_verified":True,
        "all_P4_source_edges_verified":checked,
        "ordinary_retraction_fixes_target":True,
        "K_divergence_by_neumann_lara_retraction_theorem":True,
    }


def verify_all(directory:Path) -> dict:
    need(git_blob(NINE.read_bytes())==NINE_BLOB,
         "Immutable nine-v9 historical Git blob changed")
    frozen=source_rows(NINE)
    need(list(frozen)==sorted(CASES),
         "Original nine-v9 remaining McKay identities are not exactly three")
    files=sorted(directory.glob("order9-last-three-*.json"))
    need(len(files)==3,"Exactly three complete nine-original certificates required")
    proved=[]
    for file in files:
        rec=json.loads(file.read_text(encoding="utf-8"))
        index=rec.get("original_index")
        need(index not in {x["original_index"] for x in proved},
             "Repeated nine-vertex source in complete certificate batch")
        audit=audit_case(rec,frozen)
        proved.append(audit)
        print(f"CERTIFIED original={index} P4={audit['P4'][0]} "
              f"target=O{audit['target_dimension']} "
              f"verified_edges={audit['all_P4_source_edges_verified']}",
              flush=True)
    proved.sort(key=lambda item:item["original_index"])
    need([x["original_index"] for x in proved]==sorted(CASES),
         "A former nine-v9 original was not independently proved divergent")
    return {
        "schema":1,
        "kind":"all_three_last_nine_originals_divergent_by_P4_octahedral_retractions",
        "historical_nine_v9_git_blob":NINE_BLOB,
        "proved_nine_originals":sorted(CASES),
        "complete_retractions":proved,
        "historical_index_unchanged":True,
        "nine_v10_promotion_not_yet_applied":True,
        "no_inference_from_bounded_search":True,
    }


def main() -> None:
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--directory",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    report=verify_all(args.directory)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",
                           encoding="utf-8")
    print("PASS: last three nine-original P4 ordinary octahedral "
          "retractions independently proved on every source edge",flush=True)


if __name__=="__main__":
    main()
