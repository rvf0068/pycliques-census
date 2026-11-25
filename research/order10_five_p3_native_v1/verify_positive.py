"""Standalone complete O11 retraction proof for ten-original McKay 11656793.

This permanent positive theorem is independent of the native C++ solver,
bounded searches, and expiring Actions artifacts. Every original P3 edge,
target antipode and target cross-edge is explicitly checked.
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
    raise RuntimeError("Optimized O11 proof execution is forbidden")

import networkx as nx

from research.order10_full_nine_reference_v1 import index as refs
from research.order10_p3_global_v23_index.independent_verify import (
    independent_p3, verify_pair,
)
from research.order10_overcap_p3_coaffine_v1.pilot import (
    independent_octahedral_retraction_check, source_catalog,
)
from research.order10_five_p3_native_v1.search import MONOREPO_SHA

ARCHIVE = Path(__file__).with_name("positive_o11.json")
ARCHIVE_BLOB = "9fb18c43ac09967dd61feadf24d845e4f54c4841"
ORIGINAL = 11656793
OTHER_ORIGINAL = 11658674
GLOBAL_P3_INDEX_BLOB = "ab5a9f1c075dfad63b111929368147884519f2a3"
V25_BLOB = "d31d52d28427adcef6055cc1d277565fe88f32d5"
ROOT = Path(__file__).resolve().parents[2]


def check(ok: bool, reason: str) -> None:
    if not ok:
        raise AssertionError(reason)


def verify_positive() -> dict:
    raw = ARCHIVE.read_bytes()
    check(refs.blob(raw) == ARCHIVE_BLOB,
          "Permanent O11 proof archive Git blob altered")
    cert = json.loads(raw)
    check(
        cert["schema"] == 1
        and cert["kind"] ==
            "one_new_verified_P3_octahedral_retraction_from_current_monorepo"
        and cert["source_run"] == 45681814467
        and cert["monorepo_commit"] == MONOREPO_SHA
        and cert["original_mckay"] == ORIGINAL
        and cert["search_order"] == "label"
        and cert["search_states"] == 10643
        and cert["octahedron_dimension"] == 11
        and cert["retraction_map_encoding"] == "zlib_uint16_le_base64",
        "Permanent positive theorem provenance changed",
    )
    source = source_catalog()[ORIGINAL]
    check(source["graph6"] == cert["original_graph6"]
          and list(source["p3"]) == cert["p3"] == [216, 19663],
          "Frozen original or third-stage size changed")
    graph6 = source["p3_graph6"]
    check(hashlib.sha256(graph6.encode("ascii")).hexdigest() ==
          cert["p3_graph6_sha256"],
          "Frozen full P3 graph6 source checksum changed")
    graph = nx.from_graph6_bytes(graph6.encode("ascii"))
    check([len(graph), graph.number_of_edges()] == [216, 19663],
          "Frozen complete P3 adjacency dimension changed")
    raw_map = zlib.decompress(base64.b64decode(
        cert["retraction_map_zlib_base64"], validate=True
    ))
    check(
        len(raw_map) == 2 * len(graph)
        and hashlib.sha256(raw_map).hexdigest() ==
            cert["retraction_raw_sha256"],
        "Complete positive retraction mapping bytes were corrupted",
    )
    values = struct.unpack("<" + "H" * len(graph), raw_map)
    pairs = tuple(tuple(pair) for pair in cert["antipodal_pairs"])
    check(len(pairs) == 11, "Wrong octahedral dimension")
    # Independent of both the solver and the original native
    # mapping verifier: checks target induced O11 and all host edges.
    independent_octahedral_retraction_check(
        graph, pairs, dict(enumerate(values))
    )

    # A *second* original belongs to this exact historical P3 class.
    # Reconstruct its original third iterate independently and verify
    # the archived 216-coordinate bijection against every edge/nonedge.
    original_raw = (ROOT / "indeterminate_order_10_v25.txt").read_bytes()
    check(refs.blob(original_raw) == V25_BLOB,
          "Historical ten-v25 original graph6 snapshot was modified")
    original_rows = {}
    for line in original_raw.decode("ascii").splitlines():
        if line and not line.startswith("#"):
            fields = line.split()
            check(len(fields) == 6 and len(set(fields[3:])) == 1
                  and fields[3:] == ["-", "-", "-"],
                  "Malformed historical ten-v25 original census row")
            original_rows[int(fields[0])] = fields[2]
    check(original_rows[ORIGINAL] == cert["original_graph6"]
          and original_rows[OTHER_ORIGINAL] == "IEzTmvm^o",
          "Wrong historical source for the second octahedral class member")
    global_raw = (
        ROOT / "research/order10_p3_global_v23_index/certificates.json"
    ).read_bytes()
    check(refs.blob(global_raw) == GLOBAL_P3_INDEX_BLOB,
          "Historical exact P3-isomorphism archive was modified")
    global_data = json.loads(global_raw)
    matches = [
        item for item in global_data["nontrivial_classes"]
        if item["representative"] == ORIGINAL
    ]
    check(len(matches) == 1 and matches[0]["order"] == 216
          and matches[0]["edges"] == 19663
          and [m["index"] for m in matches[0]["members"]] ==
              [ORIGINAL, OTHER_ORIGINAL],
          "Exact full 216-vertex P3 class membership changed")
    second = next(
        item for item in matches[0]["members"]
        if item["index"] == OTHER_ORIGINAL
    )
    second_p3 = independent_p3(original_rows[OTHER_ORIGINAL])
    check([len(second_p3), second_p3.number_of_edges()] == [216, 19663],
          "Independent reconstruction of the second original P3 changed")
    verify_pair(second_p3, graph, second["bijection"])

    return {
        "kind": "complete_p3_o11_positive_divergence_certificate",
        "original_mckay": ORIGINAL,
        "p3_shape": [216, 19663],
        "target": "O11",
        "antipodal_pairs": len(pairs),
        "all_source_edges_checked": 19663,
        "ordinary_retraction_proved": True,
        "original_K_divergent": True,
        "second_original_by_exact_p3_isomorphism": OTHER_ORIGINAL,
        "p3_isomorphism_checked_on_all_pairs": True,
        "divergent_original_indices": [ORIGINAL, OTHER_ORIGINAL],
    }


if __name__ == "__main__":
    print(json.dumps(verify_positive(), sort_keys=True, indent=2))
    print("PASS: complete P3(McKay 11656793) -> O11 ordinary retraction")
