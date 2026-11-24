"""Exact recovery of all 26 P4 cases capped at 750 facets in PR 89.

Every candidate is rebuilt from its frozen ten-v24 source graph6 and
independently enumerated with NetworkX and pivoted bitset BK. Full
incidence adjacency is followed by *complete* rounds of simultaneous
closed-neighborhood folds, with terminal surviving dominators checked
at every round. No heuristic partial P4 is treated as exact.

After recovering all 26, a pinned complete 685-vertex permutation
establishes a previously unknown P4 isomorphism between distinct
global P3 classes, with an independent label-constrained GraphMatcher.
A second dimension collision is proved NONisomorphic by degree sequences.

No clique convergence/divergence conclusion is asserted.
"""
from __future__ import annotations

import base64
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

import networkx as nx

if sys.flags.optimize:
    raise RuntimeError("Optimized proof replay bypasses assertions")

from research.order10_p3_global_v23_index.independent_verify import (
    independent_p3,
)

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ARCHIVE = HERE / "certificates.json"
PRIOR = ROOT / "research/order10_p4_reference_pilot_v24/results.json"
P3_INDEX = ROOT / "research/order10_p3_global_v23_index/certificates.json"

# Independent immutable Git blob anchors from merged PRs #87 and #89.
# These MUST NOT be derived from this PR's mutable certificates.json.
EXPECTED_PRIOR_GIT_BLOB = "171908472fe4037e0653a08056877fb956bd8d54"
EXPECTED_P3_GIT_BLOB = "ab5a9f1c075dfad63b111929368147884519f2a3"


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise AssertionError(reason)


def blob(content: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(content)).encode("ascii") + b"\0" + content
    ).hexdigest()


def bits(mask: int):
    while mask:
        first = mask & -mask
        yield first.bit_length()-1
        mask -= first


def p4_facets(g: nx.Graph) -> list[int]:
    n=len(g)
    need(set(g) == set(range(n)), "Noncanonical P3 labels")
    nx_facets=[]
    for clique in nx.find_cliques(g):
        nx_facets.append(sum(1<<v for v in clique))
        need(len(nx_facets)<=6000, "Explicit P4 facet resource limit")
    adj=[sum(1<<v for v in g[u]) for u in range(n)]
    bk_facets=[]

    def bk(r: int,p:int,x:int) -> None:
        if not p and not x:
            bk_facets.append(r)
            need(len(bk_facets)<=6000, "Independent BK P4 facet cap")
            return
        both=p|x
        pivot=max(bits(both),key=lambda u:(p&adj[u]).bit_count()) if both else None
        branch=p&~adj[pivot] if pivot is not None else p
        for u in list(bits(branch)):
            bit=1<<u
            bk(r|bit,p&adj[u],x&adj[u])
            p &= ~bit
            x |= bit

    bk(0,(1<<n)-1,0)
    nx_facets.sort()
    need(nx_facets==sorted(bk_facets),
         "Independent fourth-stage maximal-clique enumerators disagree")
    return nx_facets


def raw_from_facets(facets: list[int], source_order: int) -> list[int]:
    incident=[0]*source_order
    for i,clique in enumerate(facets):
        for v in bits(clique):
            incident[v]|=1<<i
    adj=[]
    for i,clique in enumerate(facets):
        neighbors=0
        for v in bits(clique):
            neighbors|=incident[v]
        adj.append(neighbors &~(1<<i))
    return adj


def fully_pare(
    raw: list[int],
) -> tuple[list[int],list[int],list[int]]:
    """All simultaneous fold rounds, with a terminal dominator per deletion."""
    n=len(raw)
    alive=(1<<n)-1
    fold_rounds=[]
    for step in range(n+1):
        members=list(bits(alive))
        complement={u:alive&~(raw[u]|(1<<u)) for u in members}
        missing={u:mask.bit_count() for u,mask in complement.items()}
        ordered=sorted(members,key=lambda u:(missing[u],u))
        dominated={}
        for u in members:
            for v in ordered:
                if missing[v]>missing[u] or (
                    missing[v]==missing[u] and v>=u
                ):
                    break
                if not (complement[v]&~complement[u]):
                    dominated[u]=v
                    break
        if not dominated:
            # Exhaustive pairwise stiffness is already established by the
            # search above. Verify it using direct closed neighborhoods.
            for u in members:
                closed_u=(raw[u]|(1<<u))&alive
                for v in members:
                    if u!=v:
                        need(bool(closed_u &~((raw[v]|(1<<v))&alive)),
                             "Final P4 contains a dominated vertex")
            break
        for u in dominated:
            v=u
            while v in dominated:
                v=dominated[v]
            need(v in members and v not in dominated and
                 not(complement[v]&~complement[u]),
                 f"Deleted fourth-stage vertex {u} has no retained dominator")
        fold_rounds.append(len(dominated))
        alive &= ~sum(1<<u for u in dominated)
    else:
        raise AssertionError("Unbounded fourth-stage fold rounds")
    survivors=list(bits(alive))
    relabel={old:i for i,old in enumerate(survivors)}
    pared=[
        sum(1<<relabel[v] for v in bits(raw[u]&alive))
        for u in survivors
    ]
    return survivors,pared,fold_rounds


def p4_from_graph6(g6: str) -> tuple[list[int],list[int],list[int],tuple[int,int]]:
    p3=independent_p3(g6)
    facets=p4_facets(p3)
    raw=raw_from_facets(facets,len(p3))
    _,pared,rounds=fully_pare(raw)
    return raw,pared,rounds,(len(p3),p3.number_of_edges())


def check_bijection(first: list[int], second: list[int], mapping: list[int]) -> None:
    n=len(first)
    need(n==len(second)==len(mapping)
         and sorted(mapping)==list(range(n)),
         "Not a complete P4 vertex bijection")
    for u in range(n):
        for v in range(n):
            need(bool(first[u] & (1<<v)) ==
                 bool(second[mapping[u]] & (1<<mapping[v])),
                 "Complete P4 mapping fails adjacency or nonadjacency")


def constrained_matcher(first: list[int],second:list[int],mapping:list[int]) -> None:
    """Second algorithm independently confirms the *specific* pinned map."""
    n=len(first)
    def complement_graph(rows: list[int]) -> nx.Graph:
        g=nx.Graph()
        g.add_nodes_from(range(n))
        g.add_edges_from(
            (u,v) for u in range(n)
            for v in range(u+1,n)
            if not (rows[u] & (1<<v))
        )
        return g
    left=complement_graph(first)
    right=complement_graph(second)
    nx.set_node_attributes(left,{u:u for u in range(n)},"certificate_label")
    nx.set_node_attributes(
        right,{mapping[u]:u for u in range(n)},"certificate_label"
    )
    gm=nx.algorithms.isomorphism.GraphMatcher(
        left,right,
        node_match=lambda a,b:a["certificate_label"]==b["certificate_label"],
    )
    need(gm.is_isomorphic() and
         gm.mapping=={u:mapping[u] for u in range(n)},
         "Independent label-constrained matcher rejects exact P4 certificate")


def verify_upstream_archives(data: dict) -> tuple[dict, dict]:
    """Pin historical proof bytes independently and invoke the PR #89 audit.

    The global P3 PR #87 independent *full* archive replayer is
    additionally run in a separate CI job with the historical v23
    mutable-root alias. See the workflow and the original
    order10_p4_o12_lifts_v24/replay_v23.py wrapper.
    """
    need(
        data["schema"] == 1 and
        data["kind"] ==
        "complete_fourth_iterate_reconstruction_after_750_facet_cap_and_exact_P4_isomorphism"
        and data["from"] == PRIOR.relative_to(ROOT).as_posix()
        and data["global_p3"] == P3_INDEX.relative_to(ROOT).as_posix()
        and blob(PRIOR.read_bytes()) == EXPECTED_PRIOR_GIT_BLOB
        and blob(P3_INDEX.read_bytes()) == EXPECTED_P3_GIT_BLOB
        and data["from_git_blob"] == EXPECTED_PRIOR_GIT_BLOB
        and data["global_p3_git_blob"] == EXPECTED_P3_GIT_BLOB,
        "Immutable historical P3/P4 pilot proof anchors disagree",
    )

    # The existing PR #89 audit checks its own archived 206-case
    # records, frozen v24 source, independent P3 representatives,
    # historical O6/O12 reference proofs, and all 12 shard counts.
    from research.order10_p4_reference_pilot_v24.verify_results import (
        audit as audit_prior_p4,
    )

    prior = audit_prior_p4()
    global_index = json.loads(P3_INDEX.read_text(encoding="utf-8"))
    need(
        global_index["immutable_source_git_blob"] ==
        "f32ceb913b44583f472402e14c596598fef71aaa"
        and global_index["counts"]["exact_isomorphism_classes"] == 525,
        "Frozen ten-v23 P3 archive header or global counts changed",
    )
    return prior, global_index


def verify() -> None:
    data=json.loads(ARCHIVE.read_text(encoding="utf-8"))
    prior, global_index=verify_upstream_archives(data)

    source={
        row["index"]:row
        for row in prior["records"] if row["status"]=="P4_FACET_CAP"
    }
    indices=[record["index"] for record in data["recovered_records"]]
    need(len(source)==len(indices)==26 and
         indices==sorted(set(source)),
         "The exact 26 previously capped P4 representatives changed")

    graphs={}
    observed=[]
    for record in data["recovered_records"]:
        idx=record["index"]
        original=source[idx]
        raw,pared,rounds,p3=p4_from_graph6(original["graph6"])
        need(list(p3)==original["p3"],f"Original P3 {idx} changed")
        candidate={
            "index":idx,
            "raw_P4":[len(raw),sum(row.bit_count() for row in raw)//2],
            "P4":[len(pared),sum(row.bit_count() for row in pared)//2],
            "fold_rounds":rounds,
        }
        need(candidate==record,f"New independent P4 counts disagree: {idx}")
        need(len(raw)>750,f"Index {idx} was not an original facet-cap case")
        observed.append(candidate)
        graphs[idx]=pared

    old_completed=[
        row for row in prior["records"]
        if row["status"]=="NO_REFERENCE_DIMENSION_MATCH"
    ]
    need(len(old_completed)==180 and
         len({tuple(x["p4"]) for x in old_completed})==180 and
         max(x["p4"][0] for x in old_completed)==643 and
         min(x["P4"][0] for x in observed)>=685,
         "Old 180 exact P4 signatures overlap or changed")

    classes=defaultdict(list)
    for row in observed:
        classes[tuple(row["P4"])].append(row["index"])
    collisions=[
        {"signature":list(sig),"indices":ids,
         "status":(
             "EXACT_ISOMORPHIC" if ids==[7044680,11614797]
             else "DEGREE_SEQUENCE_DISTINCT"
         )}
        for sig,ids in sorted(classes.items())
        if len(ids)>1
    ]
    need(len(classes)==24 and
         collisions==sorted(
             data["known_equal_signatures"],
             key=lambda item:tuple(item["signature"])
         ) and
         len(collisions)==2,
         "Unexpected fourth-iterate dimension collisions")

    # The dimension collision 6927388/10302846 is NOT an isomorphism.
    degrees=lambda A: sorted(row.bit_count() for row in A)
    need(degrees(graphs[6927388])!=degrees(graphs[10302846]),
         "Supposedly distinct dimension-collision pair has same degree sequence")

    iso=data["positive_isomorphism"]
    need(iso["from_index"]==7044680 and iso["to_index"]==11614797
         and iso["vertices"]==685 and iso["edges"]==199283 and
         iso["map_format"]=="uint16_little_endian_base64",
         "Wrong source or label encoding for positive P4 isomorphism")
    binary=base64.b64decode(iso["map_b64"],validate=True)
    need(len(binary)==1370 and
         hashlib.sha256(binary).hexdigest()==iso["map_sha256"],
         "Complete P4 permutation digest or dimension invalid")
    permutation=[
        int.from_bytes(binary[2*i:2*i+2],"little")
        for i in range(685)
    ]
    check_bijection(graphs[7044680],graphs[11614797],permutation)
    constrained_matcher(graphs[7044680],graphs[11614797],permutation)

    # P3 class 7044680 contains 17 original graphs; 11614797
    # was an independent singleton. The new P4 class has 18 originals.
    p3_class=next(
        item for item in global_index["nontrivial_classes"]
        if item["representative"]==7044680
    )
    need(len(p3_class["members"]) ==
         iso["former_p3_source_class_members"]==17
         and 11614797 in global_index["singleton_indices"]
         and iso["merged_originals"]==18,
         "Wrong 18-original fourth-iterate isomorphism class")
    need(data["aggregate"]=={
        "selected_p3_classes":206,
        "raw_P4_reconstructed":206,
        "individual_P4_signatures":204,
        "exact_P4_isomorphism_classes":205,
        "positive_nontrivial_P4_groups":1,
        "positive_P4_group_members":2,
        "census_originals_reclassified":0,
    }, "Exact aggregate fourth-iterate class counts changed")

    print(
        "CERTIFIED: all 26 former P4 750-facet caps fully reconstructed;"
        " 180+26=206 complete P4 graphs, 204 order/edge signatures,"
        " exactly 205 full P4 isomorphism classes. McKay 7044680"
        " and 11614797 share a certified complete 685-vertex P4 map,"
        " merging 17+1=18 original graphs; McKay 6927388 and"
        " 10302846 have the same P4 order/edges but different degree"
        " sequences. No additional K-behavior classification.",
        flush=True,
    )


if __name__=="__main__":
    verify()
