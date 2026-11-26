"""Independent audit of the four pinned-native P2 pilots for 11708967.

All positive graphs and complete coordinate maps are replayed against
the independently reconstructed 288-vertex P2 of the snub suspension.
No LIMIT_REACHED or EXHAUSTED solver result implies K-convergence.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("Cannot optimize away independent P2 positive map checks")

from research.order10_five_p3_native_v1.search import (
    MONOREPO_SHA, RUNTIME_VERSIONS,
)
from research.order10_overcap_p3_coaffine_v1.pilot import (
    independent_octahedral_retraction_check,
)
from research.order10_three_p3_coaffine_native_v1.verify import (
    audit_positive_map,
)
from research.order10_v28_p3_coaffine_all_v1.orbit_certificates import (
    orbit_certificate,
)
from research.order10_11708967_snub_suspension_P2_v1.search import (
    MAX_STATES, TIME_LIMIT, POLICIES, KINDS,
    INDEX, SOURCE_BLOB, SOURCE_G6, source, graph6_digest,
)


def need(ok: bool, why: str) -> None:
    if not ok:
        raise AssertionError(why)


def audit_batch(directory: Path) -> dict:
    G,P1,P2=source()
    expected={(p,k) for p in POLICIES for k in KINDS}
    paths=sorted(directory.glob("snub-suspension-P2-*.json"))
    need(len(paths)==len(expected),
         "Missing one of the four native P2 searches")
    observed=set()
    statuses=Counter()
    positives=[]
    for path in paths:
        d=json.loads(path.read_text(encoding="utf-8"))
        policy=d["policy"]
        kind=d["target_family"]
        need((policy,kind) in expected and (policy,kind) not in observed,
             "Duplicated or unknown pinned native source/target policy")
        observed.add((policy,kind))
        need(d.get("schema")==1
             and d.get("kind")=="bound_native_P2_of_suspension_of_snub"
             and d["original_index"]==INDEX
             and d["original_graph6"]==SOURCE_G6
             and d["immutable_source_blob"]==SOURCE_BLOB
             and d["monorepo_solver_commit"]==MONOREPO_SHA
             and d["installed_native_code_blobs_verified"] is True
             and d["dependency_versions"]==RUNTIME_VERSIONS
             and d["P1"]==[24,236] and d["P2"]==[288,37772]
             and d["P2_graph6_sha256"]==graph6_digest(P2)
             and d["max_states"]==MAX_STATES
             and d["time_limit_seconds"]==TIME_LIMIT
             and d["status"] in ("FOUND","EXHAUSTED","LIMIT_REACHED")
             and type(d["states_explored"]) is int
             and 0<=d["states_explored"]<=MAX_STATES
             and type(d["assignments_tried"]) is int
             and d["assignments_tried"]>=0
             and type(d["arc_revisions"]) is int
             and d["arc_revisions"]>=0
             and d["no_negative_behavior_from_exhaustion_or_limit"] is True,
             "An unproved native source, counter, or index was substituted")
        statuses[d["status"]]+=1
        if d["status"]=="FOUND":
            if kind=="coaffine":
                f=d["complete_coaffine_weak_endomorphism"]
                full=audit_positive_map(P2,f)
                orbit=orbit_certificate(P2,f)
                need(full==d["stable_retraction_analysis"]
                     and orbit==d["invariant_coaffine_orbit_analysis"],
                     "Complete coaffine map, stable image or orbit theorem changed")
                proved=bool(full["expansive_witness"]["proved"]
                            or orbit["expansive_coaffine_subgraph_proved"])
                witness={
                    "policy":policy,"kind":kind,
                    "stable_image_vertices":full["stable_order"],
                    "ordinary_retraction_checked_on_all_P2_edges":True,
                    "complete_288_coordinate_map_checked":True,
                    "certified_expansive_subgraph":proved,
                }
            else:
                pairs=d["antipodal_pairs"]
                projection=d["complete_ordinary_retraction"]
                need(type(d["target_dimension"]) is int
                     and d["target_dimension"]==len(pairs)>=3
                     and isinstance(projection,list)
                     and len(projection)==288,
                     "Octahedral native FOUND omitted its full map")
                independent_octahedral_retraction_check(
                    P2,tuple(tuple(pair) for pair in pairs),
                    dict(enumerate(projection)),
                )
                proved=True
                witness={
                    "policy":policy,"kind":kind,
                    "octahedron_dimension":d["target_dimension"],
                    "ordinary_retraction_checked_on_all_P2_edges":True,
                    "complete_288_coordinate_map_checked":True,
                    "certified_expansive_subgraph":True,
                }
            need(d["original_K_divergent_proved"] is proved,
                 "Native positive overclaimed original K-divergence")
            positives.append(witness)
        else:
            need("complete_coaffine_weak_endomorphism" not in d
                 and "complete_ordinary_retraction" not in d
                 and "original_K_divergent_proved" not in d,
                 "Negative or limited result contains an invented proof")
    need(observed==expected and sum(statuses.values())==4,
         "Not all native original P2 solver runs were archived")
    proved=any(item["certified_expansive_subgraph"] for item in positives)
    return {
        "schema":1,
        "kind":"independent_suspended_snub_P2_native_positive_only_audit",
        "original_mckay":INDEX,
        "original_graph6":SOURCE_G6,
        "isomorphic_to":"O1_join_snub_disphenoid",
        "P1":[24,236],
        "P2":[288,37772],
        "P2_graph6_sha256":graph6_digest(P2),
        "immutable_ten_v28_git_blob":SOURCE_BLOB,
        "four_native_source_and_solver_trials_checked":True,
        "statuses":dict(statuses),
        "full_positive_maps":positives,
        "original_K_divergent_certified":proved,
        "no_K_convergence_inference":True,
        "no_census_change":True,
    }


def main() -> None:
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--directory",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    report=audit_batch(args.directory)
    args.output.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "original":report["original_mckay"],
        "native_statuses":report["statuses"],
        "positives":len(report["full_positive_maps"]),
        "K_divergence_proved":report["original_K_divergent_certified"],
    },sort_keys=True))
    print("PASS: authentic suspended-snub P2 full source and four "
          "native trials independently verified",flush=True)


if __name__=="__main__":
    main()
