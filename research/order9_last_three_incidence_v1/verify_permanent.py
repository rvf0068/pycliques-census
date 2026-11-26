"""Full solver-independent permanent proof of the LAST three nine-originals.

All projection images, target antipodal pairs, explicit P3 isomorphisms,
and raw P4 fold moves are archived in permanently committed compressed
JSON, not an expiring GitHub Actions artifact. Every checked statement
is rederived from the original connected-nine graph6 with NetworkX
and independent bitset Bron--Kerbosch maximal-clique enumeration.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path
import sys
import zlib

if sys.flags.optimize:
    raise RuntimeError("Cannot optimize away the permanent three-nine proof")

from research.order10_p4_crossdepth_o15_v25.verify import git_blob, source_rows
from research.order9_last_three_incidence_v1.discover import CASES,NINE,NINE_BLOB,MONOREPO
from research.order9_last_three_incidence_v1.verify import audit_case,need

ARCHIVE=Path(__file__).with_name("permanent_certificates.json")
ARCHIVE_BLOB="014285de9fe35c1e2e19aa644b2cef14843e8576"
EXPECTED_TARGETS={249576:17,251628:20,260040:22}
EXPECTED_P4_EDGES={249576:199283,251628:467517,260040:658528}


def load_full_certificates() -> dict[int,dict]:
    need(git_blob(ARCHIVE.read_bytes())==ARCHIVE_BLOB,
         "Permanent three-original complete source maps changed Git blob")
    data=json.loads(ARCHIVE.read_text(encoding="utf-8"))
    need(data.get("schema")==1
         and data.get("kind")=="three_complete_original_nine_P4_octahedral_retractions"
         and data.get("compression")=="zlib-utf8-json-base64"
         and data.get("source_nine_v9_git_blob")==NINE_BLOB
         and data.get("pinned_solver_commit")==MONOREPO
         and data.get("original_proof_run")==45912337172
         and data.get("independent_full_edge_verification_run")==45912337172
         and data.get("compression_export_run")==45912631195
         and set(data.get("certificates",{}))==
             {str(i) for i in EXPECTED_TARGETS},
         "Permanent full-positive provenance or exact three sources changed")
    output={}
    for key,encoded in data["certificates"].items():
        index=int(key)
        need(type(encoded) is str and len(encoded)<25000,
             "Unreasonably large or missing original projection archive")
        payload=zlib.decompress(base64.b64decode(encoded,validate=True))
        need(len(payload)<250000,"Decompressed projection archive unexpectedly large")
        row=json.loads(payload.decode("utf-8"))
        need(row["original_index"]==index
             and row["status"]=="FOUND"
             and row["target_dimension"]==EXPECTED_TARGETS[index]
             and row["P4"][1]==EXPECTED_P4_EDGES[index]
             and len(row["projection_images_in_active_raw_vertex_order"])==
                 row["P4"][0],
             "Permanent map dimension or exact target differs")
        output[index]=row
    return output


def verify_permanent() -> dict:
    need(git_blob(NINE.read_bytes())==NINE_BLOB,
         "Immutable nine-v9 census historical source changed")
    frozen=source_rows(NINE)
    need(set(frozen)==set(EXPECTED_TARGETS),
         "The three original nine-v9 graph identities changed")
    all_cases=load_full_certificates()
    certificates=[]
    for index in sorted(EXPECTED_TARGETS):
        report=audit_case(all_cases[index],frozen)
        need(report["K_divergence_by_neumann_lara_retraction_theorem"] is True,
             "A saved original lacks a verified ordinary P4 retraction")
        certificates.append(report)
    need([p["original_index"] for p in certificates]==sorted(CASES),
         "A previously unresolved nine-original is missing")
    return {
        "schema":1,
        "kind":"independent_permanent_all_three_nine_originals_divergent",
        "originals_proven_K_divergent":sorted(EXPECTED_TARGETS),
        "targets":EXPECTED_TARGETS,
        "complete_positive_retractions":certificates,
        "all_original_P4_edges_checked":
            sum(x["all_P4_source_edges_verified"] for x in certificates),
        "old_9_v9_git_blob":NINE_BLOB,
        "permanent_certificate_git_blob":ARCHIVE_BLOB,
        "all_original_nine_K_behaviors_determined":True,
        "census_indices_unchanged_pending_promotion":True,
    }


def main() -> None:
    result=verify_permanent()
    print(json.dumps(result,indent=2,sort_keys=True))
    print("PASS: all three permanent original nine-P4 ordinary octahedral "
          "retractions independently replayed from frozen graph6",flush=True)


if __name__=="__main__":
    main()
