"""Exact current ten-v28 roster conditionally determined by three nine cores.

Positive exact references already permanently certified in historical
ten-v25 PR #94 and four exact ten-to-nine P4 links. Construct, check,
and archive the complete 500 ORIGINAL McKay indices, not a count-only
claim. This script performs no census promotion and does not assume
the three new nine-source divergence certificates have passed.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

import networkx as nx

from research.order10_p4_crossdepth_o15_v25.verify import git_blob, source_rows
from research.order9_last_three_incidence_v1.discover import (
    CASES,NINE,NINE_BLOB,ROOT,
)

TEN=ROOT/"indeterminate_order_10_v28.txt"
TEN_BLOB="35bb83b56bb8b4fd453b0ba272d354dc6b42e68c"
P3=ROOT/"research/order10_p3_global_v23_index/certificates.json"
P3_BLOB="ab5a9f1c075dfad63b111929368147884519f2a3"
DEPEND=ROOT/"research/order10_nine_core_dependency_v1/certificates.json"
DEPEND_BLOB="0f3a367ae707e390e1ec21e74046923197f7f560"
P4_LINK=ROOT/"research/order10_p4_nine_links_v1/certificates.json"


def need(ok: bool,reason: str) -> None:
    if not ok:
        raise AssertionError(reason)


def collect() -> dict:
    need(git_blob(NINE.read_bytes())==NINE_BLOB
         and git_blob(TEN.read_bytes())==TEN_BLOB
         and git_blob(P3.read_bytes())==P3_BLOB
         and git_blob(DEPEND.read_bytes())==DEPEND_BLOB,
         "One immutable original nine/ten dependency archive was modified")
    nr=source_rows(NINE)
    ten=source_rows(TEN)
    need(len(nr)==3 and len(ten)==1043
         and list(nr)==sorted(CASES),
         "Unexpected historical unresolved cohort")
    global_p3=json.loads(P3.read_text(encoding="utf-8"))
    dep=json.loads(DEPEND.read_text(encoding="utf-8"))
    more=json.loads(P4_LINK.read_text(encoding="utf-8"))
    need(dep["counts"]["all_pending_nine_dependent"]==496
         and more["expected_counts"]["linked_all"]==500
         and more["preceding_dependency_archive"]==
             "research/order10_nine_core_dependency_v1/certificates.json",
         "Immutable previous P3/P4 link source manifests changed")

    groups={str(i):[] for i in CASES}
    how={}
    nine_graphs={
        i:nx.from_graph6_bytes(CASES[i][0].encode("ascii"))
        for i in CASES
    }

    def record(original:int,nine:int,route:str) -> None:
        need(original in ten and nine in CASES
             and original not in how,
             "Duplicate, nonexistent, or unclassified exact ten-original")
        groups[str(nine)].append(original)
        how[original]={"nine_reference":nine,"route":route}

    # All 430 original ten-vertex records whose P0 is a nine-vertex
    # graph isomorphic to one of the three pending sources.
    for index,line in ten.items():
        cols=line.split()
        if cols[1]!="9":
            continue
        core=nx.from_graph6_bytes(cols[2].encode("ascii"))
        matches=[i for i,H in nine_graphs.items()
                 if nx.is_isomorphic(core,H)]
        need(len(matches)==1,"Pared-nine dependent lacked a unique exact source")
        record(index,matches[0],"original_pared_nine_graph_isomorphism")

    # The historical global P3 atlas includes full original-to-
    # representative maps for three proven ten-to-nine P3 links.
    reps={z["ten_rep_index"]:z["nine_index"]
          for z in dep["three_p3_equivalences"]}
    need(reps=={7044680:249576,7070392:251628,7479384:260040},
         "Unexpected exact historical P3 representative references")
    for item in global_p3["nontrivial_classes"]:
        rep=item["representative"]
        if rep not in reps:
            continue
        n=reps[rep]
        need((item["order"],item["edges"])==CASES[n][1],
             "A historical class is not a certified P3-isomorphic source")
        for row in item["members"]:
            need(len(row["bijection"])==item["order"]
                 and sorted(row["bijection"])==list(range(item["order"])),
                 "Historical complete class member bijection absent")
            record(row["index"],n,"historical_exact_P3_class_bijection")

    extra=dep["prior_p4_link"]
    need(extra["from_ten_index"]==7044680
         and extra["to_ten_index"]==11614797,
         "One historical fourth-iterate reference link changed")
    record(11614797,249576,"historical_exact_P4_cross_reference")

    # The four remaining authenticated fourth-iterate equivalences
    # were separately checked on 685 or 1034 source coordinates.
    expected={11287666:251628,11287670:249576,
              11567994:249576,11568314:249576}
    need({z["index"]:z["nine_index"] for z in more["records"]}==expected,
         "Four additional complete P4 dependency archive records changed")
    for row in more["records"]:
        need(len(row["map_sha256"])==64
             and row["p4"][0] in (685,1034),
             "Historical P4 full map or provenance changed")
        record(row["index"],row["nine_index"],
               "historical_exact_P4_nine_core_bijection")

    for group in groups.values():
        group.sort()
    sizes={k:len(v) for k,v in groups.items()}
    need(sizes=={"249576":162,"251628":171,"260040":167}
         and len(how)==500
         and sum(1 for r in ten.values() if r.split()[1]=="9")==430
         and sum(1 for r in ten.values() if r.split()[1]=="10")==613
         and len(set(how))==500,
         "Exactly 500 mutually disjoint ten-original dependent identities required")

    previous_six={10481909,10586728,11438191,11578321,
                  11715667,11716441}
    need(not set(how)&previous_six,
         "Six separate ten-v29 positive originals overlap the pending 500")
    return {
        "schema":1,
        "kind":"original_ten_v28_exact_500_conditional_nine_core_dependents",
        "historical_ten_v28_git_blob":TEN_BLOB,
        "historical_nine_v9_git_blob":NINE_BLOB,
        "global_original_P3_classes_git_blob":P3_BLOB,
        "previous_conditional_dependency_git_blob":DEPEND_BLOB,
        "per_nine":sizes,
        "linked_original_ten_count":len(how),
        "nine_pared_original_ten_count":430,
        "linked_stiff_original_ten_count":70,
        "unrelated_six_positive_ten_v29":sorted(previous_six),
        "expected_after_six_and_500_unresolved":537,
        "complete_dependents":groups,
        "provenance_by_original_McKay":{str(k):how[k] for k in sorted(how)},
        "no_census_changes":True,
    }


def main() -> None:
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result=collect()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(
        json.dumps(result,indent=2,sort_keys=True)+"\n",
        encoding="utf-8"
    )
    print(f"PASS: exact 500 ten-original dependencies on three nine-v9 "
          f"sources verified {result['per_nine']}",flush=True)


if __name__=="__main__":
    main()
