"""Independent positive-only completion of the order-nine and order-ten census.

This certifies nine-v9 -> nine-v10 (3 -> 0) and ten-v29 -> ten-v30
(1037 -> 537) by replaying complete permanent original nine-P4
octahedral retractions and independently deriving all 500 original
ten-vertex dependencies from exact frozen P0/P3/P4 graph isomorphisms.

The six independent ten-v29 positive proofs and all historical sources
remain immutable; historical root assumptions are patched IN MEMORY
only when replaying the old six-positive transition.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys
from unittest.mock import patch

if sys.flags.optimize:
    raise RuntimeError("Cannot optimize away final nine-v10 ten-v30 positive proof")

from research.order10_p4_crossdepth_o15_v25.verify import git_blob, source_rows
from research.order9_last_three_incidence_v1.verify_permanent import (
    verify_permanent as replay_three_nine_originals,
)
from research.order9_last_three_incidence_v1.ten_dependents import (
    collect as derive_500_original_ten_dependents,
)
from research.order10_v29_six_coaffine_joins import verify as v29

ROOT=Path(__file__).resolve().parents[2]
NINE_BEFORE=ROOT/"indeterminate_order_9_v9.txt"
NINE_AFTER=ROOT/"indeterminate_order_9_v10.txt"
NINE_WORKING=ROOT/"indeterminate_order_9.txt"
TEN_BEFORE=ROOT/"indeterminate_order_10_v29.txt"
TEN_AFTER=ROOT/"indeterminate_order_10_v30.txt"
TEN_WORKING=ROOT/"indeterminate_order_10.txt"

NINE_V9_BLOB="d18a7a843be935f3a7fe911691dd1c86dac2addd"
NINE_V10_BLOB="b2c3773a1206472868708745d92bbb9b22f7fab6"
TEN_V29_BLOB="f26d392746391f40aa224d4e639627b4617caff1"
TEN_V30_BLOB="d5d70d113e78b90588041ebaf60a14b26e0d2bda"
PROVED_NINE=(249576,251628,260040)
TARGET_OCTAHEDRA={249576:17,251628:20,260040:22}
PROVED_SIX_TEN=(10481909,10586728,11438191,11578321,
                11715667,11716441)
EXPECTED_GROUP_SIZES={"249576":162,"251628":171,"260040":167}


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise AssertionError(reason)


def verify_snapshot_blobs(
    nine_before: bytes, nine_after: bytes,
    ten_before: bytes, ten_after: bytes,
) -> None:
    need(git_blob(nine_before)==NINE_V9_BLOB,
         "Immutable nine-v9 source Git blob changed")
    need(git_blob(nine_after)==NINE_V10_BLOB,
         "New nine-v10 complete census Git blob changed")
    need(git_blob(ten_before)==TEN_V29_BLOB,
         "Frozen six-positive ten-v29 source Git blob changed")
    need(git_blob(ten_after)==TEN_V30_BLOB,
         "New ten-v30 complete dependency promotion Git blob changed")


def audit_nine(
    before: dict[int,str], after: dict[int,str],
    certified: set[int],
) -> None:
    need(len(before)==3 and len(after)==0,
         "Wrong old/new nine-original indeterminate counts")
    need(certified==set(PROVED_NINE)
         and set(before)==certified,
         "Missing or uncertified original nine-vertex removal")
    expected={
        249576:"249576 9 HEhfvzu - - -",
        251628:"251628 9 HEhvVn{ - - -",
        260040:"260040 9 HQyvex} - - -",
    }
    need(before==expected and list(before)==sorted(before),
         "Frozen last-three nine-original identities or graph6 changed")


def audit_ten(
    before: dict[int,str], after: dict[int,str],
    certified: set[int],
) -> None:
    need(len(before)==1037 and len(after)==537,
         "Wrong ten-v29/ten-v30 original population")
    need(len(certified)==500 and set(before)-set(after)==certified
         and not set(after)-set(before),
         "Missing original or unsupported ten-vertex divergence promotion")
    need(all(before[i]==after[i] for i in after),
         "A retained ten-v29 six-column original row was modified")
    need(list(before)==sorted(before)
         and list(after)==sorted(after),
         "Canonical original McKay ordering changed")
    need(all(len(row.split())==6 for row in before.values())
         and all(len(row.split())==6 for row in after.values()),
         "Source six-column record format changed")
    count=lambda rows:dict(Counter(int(row.split()[1])
                                   for row in rows.values()))
    need(count(before)=={9:430,10:607}
         and count(after)=={10:537},
         "The 430 nine-pared and 70 stiff original removals were changed")
    need(set(PROVED_SIX_TEN).isdisjoint(certified)
         and set(PROVED_SIX_TEN).isdisjoint(set(before)),
         "Originals proved in ten-v29 are incorrectly double-promoted")


def replay_immutable_ten_v29() -> dict:
    need(v29.BEFORE==ROOT/"indeterminate_order_10_v28.txt"
         and v29.LATEST==TEN_BEFORE
         and v29.WORKING==TEN_WORKING
         and v29.NINE==NINE_WORKING
         and v29.NINE_FROZEN==NINE_BEFORE,
         "Unexpected location of immutable prior ten-v29 verification inputs")
    # The archived verifier intentionally checks that its former active
    # roots equaled ten-v29 and nine-v9. Temporarily redirect precisely
    # those two root paths to their unchanged frozen snapshots, without
    # editing the historical verifier or any actual on-disk file.
    with patch.object(v29,"WORKING",v29.LATEST), \
         patch.object(v29,"NINE",v29.NINE_FROZEN):
        result=v29.verify()
    need(result["proved_K_divergent_originals"]==list(PROVED_SIX_TEN)
         and result["population"]["after"]==1037
         and result["positive_P3_full_maps_replayed"]==4
         and result["positive_11_vertex_retracts_replayed"]==2,
         "Historical six-positive ten-v29 proof replay changed")
    return result


def verify(*, replay_historical:bool=True) -> dict:
    verify_snapshot_blobs(
        NINE_BEFORE.read_bytes(),NINE_AFTER.read_bytes(),
        TEN_BEFORE.read_bytes(),TEN_AFTER.read_bytes(),
    )
    need(NINE_WORKING.read_bytes()==NINE_AFTER.read_bytes(),
         "Current nine-original root differs from frozen nine-v10")
    need(TEN_WORKING.read_bytes()==TEN_AFTER.read_bytes(),
         "Current ten-original root differs from frozen ten-v30")
    nine_before=source_rows(NINE_BEFORE)
    nine_after=source_rows(NINE_AFTER)
    ten_before=source_rows(TEN_BEFORE)
    ten_after=source_rows(TEN_AFTER)

    nine_proof=replay_three_nine_originals()
    need(nine_proof["originals_proven_K_divergent"]==list(PROVED_NINE)
         and nine_proof["targets"]==TARGET_OCTAHEDRA
         and nine_proof["all_original_P4_edges_checked"]==1325328
         and nine_proof["all_original_nine_K_behaviors_determined"] is True,
         "A complete fourth-iterate nine-original retraction failed")
    audit_nine(nine_before,nine_after,set(nine_proof["originals_proven_K_divergent"]))

    ten_roster=derive_500_original_ten_dependents()
    need(ten_roster["schema"]==1
         and ten_roster["linked_original_ten_count"]==500
         and ten_roster["per_nine"]==EXPECTED_GROUP_SIZES
         and ten_roster["nine_pared_original_ten_count"]==430
         and ten_roster["linked_stiff_original_ten_count"]==70
         and ten_roster["expected_after_six_and_500_unresolved"]==537
         and ten_roster["no_census_changes"] is True,
         "Full independently authenticated ten-original dependency index failed")
    by_index=ten_roster["provenance_by_original_McKay"]
    certified={int(i) for i in by_index}
    need(len(certified)==len(by_index)==500
         and set(by_index)==set(map(str,certified))
         and set(certified)=={
             member for group in ten_roster["complete_dependents"].values()
             for member in group
         }
         and all(v["nine_reference"] in PROVED_NINE
                 for v in by_index.values()),
         "Complete 500 ten-original P0/P3/P4 source maps not authenticated")
    audit_ten(ten_before,ten_after,certified)

    history=None
    if replay_historical:
        history=replay_immutable_ten_v29()

    return {
        "schema":1,
        "kind":"fully_certified_nine_v9_to_v10_and_ten_v29_to_v30",
        "new_nine_snapshot":NINE_AFTER.name,
        "new_ten_snapshot":TEN_AFTER.name,
        "git_blobs":{
            "nine_v9":NINE_V9_BLOB,
            "nine_v10":NINE_V10_BLOB,
            "ten_v29":TEN_V29_BLOB,
            "ten_v30":TEN_V30_BLOB,
        },
        "population":{
            "nine_before":3,"nine_after":0,
            "nine_newly_proved_divergent":3,
            "ten_before":1037,"ten_after":537,
            "ten_newly_proved_divergent":500,
            "ten_pared_nine_originals_removed":430,
            "ten_stiff_originals_removed":70,
            "ten_stiff_originals_retained":537,
        },
        "original_nine_proved_K_divergent":list(PROVED_NINE),
        "complete_nine_P4_induced_Od_retractions":{
            str(i):d for i,d in TARGET_OCTAHEDRA.items()
        },
        "all_nine_P4_source_edges_verified":1325328,
        "ten_per_original_nine_group":EXPECTED_GROUP_SIZES,
        "ten_positive_originals_exact":[int(i) for i in sorted(certified)],
        "previous_six_ten_positive_proofs_replayed": history is not None,
        "all_unremoved_original_census_records_unchanged":True,
        "no_unproved_negative_search_promoted":True,
    }


def main() -> None:
    print(json.dumps(verify(),sort_keys=True,indent=2))
    print("PASS: exact zero-indeterminate nine-v10 and 537-indeterminate ten-v30 "
          "by fully replayed three P4 octahedral and 500 original lift proofs",
          flush=True)


if __name__=="__main__":
    main()
