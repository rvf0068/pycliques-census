"""Independently verify five permanent P3 -> O_d certificates.

No native solver or access to the expiring Actions artifact is needed:
all five complete maps are frozen in positive_retractions.json. Also
verify the sixth divergent original 11651749 using its old, separately
certified exact P3 isomorphism to 11611429.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

if sys.flags.optimize:
    raise RuntimeError("Proof verifier must not run optimized")

import networkx as nx

from research.order10_full_nine_reference_v1 import index as refs
from research.order10_overcap_p3_coaffine_v1.pilot import (
    PYCLIQUES_SHA, require, source_catalog,
    independent_octahedral_retraction_check,
)
from research.order10_p3_global_v23_index.independent_verify import (
    independent_p3, verify_pair,
)

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = Path(__file__).with_name("positive_retractions.json")
ARCHIVE_BLOB = "73f2e6c4f45bed5a4258e45c9da2669eb8a1156d"
P3_CLASS_BLOB = "ab5a9f1c075dfad63b111929368147884519f2a3"
TEN_V25_BLOB = "d31d52d28427adcef6055cc1d277565fe88f32d5"
EXPECTED = {
    11367777: (240, 22724, 12),
    11611429: (119, 6412, 15),
    11623375: (266, 28046, 12),
    11708546: (140, 8822, 14),
    11713770: (95, 4099, 14),
}
PROMOTABLE_ORIGINALS = (
    11367777, 11611429, 11623375, 11651749, 11708546, 11713770,
)


def read_pinned(path: Path, sha: str) -> bytes:
    raw = path.read_bytes()
    require(refs.blob(raw) == sha,
            f"Immutable source file changed: {path.name}")
    return raw


def replay_positive_witnesses() -> dict:
    src = source_catalog()
    raw = read_pinned(ARCHIVE, ARCHIVE_BLOB)
    cert = json.loads(raw)
    require(cert.get("schema") == 1 and
            cert.get("kind") ==
                "five_exact_octahedral_retractions_from_third_pared_clique_iterates"
            and cert.get("source_census_pr") == 100 and
            cert.get("source_workflow_run") == 45637104784 and
            cert.get("pinned_pycliques_project_commit") == PYCLIQUES_SHA
            and cert.get("encoding") == "zlib_uint16_little_endian_base64",
            "Permanent positive-certificate header or provenance changed")
    rows = cert["records"]
    require([r["index"] for r in rows] == sorted(EXPECTED),
            "Missing, duplicated or unexpected octahedral positive case")
    reports = []
    for item in rows:
        idx = item["index"]
        g6 = src[idx]["p3_graph6"]
        graph = nx.from_graph6_bytes(g6.encode("ascii"))
        n, m, dim = EXPECTED[idx]
        require(item["p3"] == [n, m]
                and list(src[idx]["p3"]) == [n, m]
                and [len(graph), graph.number_of_edges()] == [n, m]
                and item["p3_graph6_sha256"] ==
                    hashlib.sha256(g6.encode("ascii")).hexdigest()
                and item["target_dimension"] == dim,
                f"P3 graph6, shape or O_d target changed at McKay {idx}")
        encoded = zlib.decompress(base64.b64decode(
            item["retraction_zlib_base64"], validate=True
        ))
        require(len(encoded) == n * 2 and
                hashlib.sha256(encoded).hexdigest()
                    == item["retraction_bytes_sha256"],
                f"Corrupted complete retraction map at McKay {idx}")
        labels = struct.unpack("<" + "H"*n, encoded)
        ret = dict(enumerate(labels))
        pairs = tuple(tuple(p) for p in item["antipodal_pairs"])
        require(len(pairs) == dim and
                type(item["native_states_explored"]) is int
                and 0 < item["native_states_explored"] <= 100000,
                "Malformed exact target dimension or solver provenance")
        # Every source edge and target nonedge/edge is checked.
        independent_octahedral_retraction_check(graph, pairs, ret)
        reports.append({
            "index": idx, "p3": [n, m],
            "ordinary_octahedral_retraction": True,
            "target": f"O{dim}", "dimension": dim,
            "source_edge_count_verified": m,
            "target_order": 2*dim,
        })
        print(f"REPLAY CERTIFIED: original {idx} P3 -> O_{dim}, "
              f"all {m} source edges", flush=True)

    # Sixth stiff ten-original is in the same *exact* third-iterate
    # class as McKay 11611429. Authenticate the original ten-vertex
    # graph6 and the nontrivial bijection, then reconstruct P3
    # independently and verify the *specific* complete permutation.
    old = json.loads(read_pinned(
        ROOT / "research/order10_p3_global_v23_index/certificates.json",
        P3_CLASS_BLOB,
    ))
    targets = [
        rec for rec in old["nontrivial_classes"]
        if rec["representative"] == 11611429
    ]
    require(len(targets) == 1
            and {x["index"] for x in targets[0]["members"]} ==
                {11611429, 11651749}
            and targets[0]["order"] == 119
            and targets[0]["edges"] == 6412,
            "Archived global third-iterate equivalence changed")
    row = next(
        x for x in targets[0]["members"] if x["index"] == 11651749
    )
    snapshot = read_pinned(ROOT / "indeterminate_order_10_v25.txt",
                           TEN_V25_BLOB).decode("ascii")
    original = {}
    for line in snapshot.splitlines():
        if line and not line.startswith("#"):
            fields = line.split()
            require(len(fields) == 6,
                    "Malformed original ten-v25 row")
            original[int(fields[0])] = fields[2]
    require(set(PROMOTABLE_ORIGINALS) <= set(original)
            and all(original[i] == src[i]["graph6"]
                    for i in EXPECTED),
            "Positive original no longer in the frozen unresolved ten cohort")
    member = independent_p3(original[11651749])
    rep = nx.from_graph6_bytes(src[11611429]["p3_graph6"].encode("ascii"))
    require([len(member), member.number_of_edges()] == [119, 6412],
            "Original 11651749 P3 failed independent reconstruction")
    verify_pair(member, rep, row["bijection"])
    reports.append({
        "index": 11651749,
        "p3_isomorphic_to": 11611429,
        "target": "O15",
        "ordinary_octahedral_retraction": True,
        "via_exact_p3_bijection": True,
    })
    require(tuple(sorted(x["index"] for x in reports))
            == PROMOTABLE_ORIGINALS,
            "Six original ten-vertex divergent proofs incomplete")
    return {
        "kind": "six_certified_divergent_ten_v25_originals",
        "positive_p3_retraction_count": 5,
        "exact_p3_isomorphic_originals": 1,
        "divergent_original_indices": list(PROMOTABLE_ORIGINALS),
        "remaining_five_oversized_p3_classes_not_classified": True,
        "root_census_modified": False,
        "records": sorted(reports, key=lambda r:r["index"]),
    }


if __name__ == "__main__":
    r = replay_positive_witnesses()
    print(json.dumps(r, sort_keys=True, indent=2))
