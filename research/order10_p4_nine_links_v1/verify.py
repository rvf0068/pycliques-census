"""Proof-only: four exact P4 links to the three unresolved nine-vertex cores.

The maps are complete vertex-bijection certificates, never mere signatures.
Reuses the independently cross-checked P3 and P4 reconstruction/verifiers
already merged in the census. Does not promote any classification.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import struct
import sys

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical assertions")

from research.order10_nine_core_dependency_v1.verify import (
    git_blob,
    parse_rows,
    require,
)
from research.order10_p4_cap_rescue_v24.verify import (
    check_bijection,
    constrained_matcher,
    p4_from_graph6,
)

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CERT = HERE / "certificates.json"
NINE = ROOT / "indeterminate_order_9_v9.txt"
TEN = ROOT / "indeterminate_order_10_v25.txt"
PRECEDING = ROOT / "research/order10_nine_core_dependency_v1/certificates.json"
GLOBAL_P3 = ROOT / "research/order10_p3_global_v23_index/certificates.json"

# Independent, code-pinned immutable provenance, not certificate-derived hashes.
EXPECTED_GIT_BLOBS = {
    "indeterminate_order_9_v9.txt":
        "d18a7a843be935f3a7fe911691dd1c86dac2addd",
    "indeterminate_order_10_v25.txt":
        "d31d52d28427adcef6055cc1d277565fe88f32d5",
    "research/order10_nine_core_dependency_v1/certificates.json":
        "0f3a367ae707e390e1ec21e74046923197f7f560",
    "research/order10_p3_global_v23_index/certificates.json":
        "ab5a9f1c075dfad63b111929368147884519f2a3",
}
NINE_SOURCES = {
    249576: ("HEhfvzu", (53, 1044), 783, (685, 199283), [76, 22]),
    251628: ("HEhvVn{", (55, 1156), 1034, (1034, 467517), []),
}
# (nine index, ten graph6, P3 dimensions, raw P4 order, fold rounds, P4 shape, full map SHA256)
POSITIVES = {
    11287666: (251628, "ICpvnr{yo", (58, 1274), 1077, [25, 5, 13],
               (1034, 467517),
               "2991915ac5bf4eb6645e90f8f3f7ec8fd2914ece763314f87e7a6e86cefad7f1"),
    11287670: (249576, "ICpvnr{{o", (57, 1184), 795, [88, 22],
               (685, 199283),
               "45973571e7974f91d22963fd1c5c1e35f589ab92f79176e7e9649fdc75d64191"),
    11567994: (249576, "IEhfuz{z_", (57, 1184), 796, [85, 20, 6],
               (685, 199283),
               "7c15456fa95a1181f320286f789e17166a96e5bf846d6b26b8bec2cef244d22d"),
    11568314: (249576, "IEhfvj{z_", (57, 1182), 795, [84, 26],
               (685, 199283),
               "7c15456fa95a1181f320286f789e17166a96e5bf846d6b26b8bec2cef244d22d"),
}


def immutable_bytes(path: str) -> bytes:
    """Reject an unknown path and any modified historical proof blob."""
    require(path in EXPECTED_GIT_BLOBS, "Unknown immutable evidence path")
    data = (ROOT / path).read_bytes()
    require(git_blob(data) == EXPECTED_GIT_BLOBS[path],
            f"Historical source Git blob differs: {path}")
    return data


def dimensions(rows: list[int]) -> tuple[int, int]:
    return len(rows), sum(row.bit_count() for row in rows) // 2


def decode_map(record: dict) -> list[int]:
    n = record["p4"][0]
    style = record["map_encoding"]
    if style == "identity_uint16_little_endian":
        require("map_b64" not in record,
                "Identity mapping must not include an untrusted alternate map")
        mapping = list(range(n))
        data = struct.pack("<" + "H" * n, *mapping)
    else:
        require(style == "uint16_little_endian_base64",
                "Unknown complete-map encoding")
        data = base64.b64decode(record["map_b64"], validate=True)
        require(len(data) == 2 * n, "Truncated complete P4 certificate")
        mapping = list(struct.unpack("<" + "H" * n, data))
    require(
        record["map_sha256"] == hashlib.sha256(data).hexdigest() ==
        POSITIVES[record["index"]][-1],
        "Full P4 bijection digest differs from code-pinned value",
    )
    require(sorted(mapping) == list(range(n)),
            "Missing, duplicated or out-of-range P4 map coordinates")
    return mapping


def verify_archive() -> None:
    data = json.loads(CERT.read_text(encoding="utf-8"))
    require(
        data["schema"] == 1
        and data["kind"] ==
            "four_exact_P4_links_to_unresolved_nine_cores_proof_only"
        and data["nine_snapshot"] == NINE.name
        and data["ten_snapshot"] == TEN.name
        and data["preceding_dependency_archive"] ==
            PRECEDING.relative_to(ROOT).as_posix(),
        "Unexpected new proof-only certificate schema",
    )
    nine_rows = parse_rows(immutable_bytes(NINE.name))
    ten_rows = parse_rows(immutable_bytes(TEN.name))
    require(
        NINE.read_bytes() == (ROOT / "indeterminate_order_9.txt").read_bytes()
        and TEN.read_bytes() == (ROOT / "indeterminate_order_10.txt").read_bytes()
        and len(nine_rows) == 3 and len(ten_rows) == 1052,
        "Authoritative nine-v9 / ten-v25 root has changed",
    )
    old = json.loads(immutable_bytes(PRECEDING.relative_to(ROOT).as_posix()))
    p3_archive = json.loads(immutable_bytes(GLOBAL_P3.relative_to(ROOT).as_posix()))
    require(
        old["schema"] == 1
        and old["counts"]["all_pending_nine_dependent"] == 496
        and old["counts"]["stiff_not_yet_linked"] == 556
        and p3_archive["counts"]["exact_isomorphism_classes"] == 525,
        "Prior exact 496-dependency proof or global P3 source changed",
    )
    require(
        [rec["index"] for rec in data["records"]] == sorted(POSITIVES),
        "Four new positive originals are missing, duplicated, or reordered",
    )
    prior_stiff: set[int] = set()
    for prior in old["three_p3_equivalences"]:
        group = [
            grp for grp in p3_archive["nontrivial_classes"]
            if grp["representative"] == prior["ten_rep_index"]
        ]
        require(len(group) == 1
                and len(group[0]["members"]) == prior["class_members"],
                "Prior P3 group missing from immutable archive")
        prior_stiff.update(mem["index"] for mem in group[0]["members"])
    prior_stiff.add(old["prior_p4_link"]["to_ten_index"])
    require(len(prior_stiff) == 66 and not prior_stiff.intersection(POSITIVES),
            "Previous 66 stiff dependencies overlap new positives")
    require(all(i in p3_archive["singleton_indices"] for i in POSITIVES),
            "Some new positive was not a historical P3 singleton")

    sources: dict[int, list[int]] = {}
    for ni, (g6, p3, raw_order, p4_dim, folds) in NINE_SOURCES.items():
        require(nine_rows[ni] == ("9", g6),
                "Nine-vertex source is not the frozen McKay original")
        raw, pared, rounds, got_p3 = p4_from_graph6(g6)
        require(tuple(got_p3) == p3
                and len(raw) == raw_order
                and dimensions(pared) == p4_dim
                and rounds == folds,
                "Reconstructed nine-vertex P4 reference changed")
        sources[ni] = pared

    added = {ni: 0 for ni in NINE_SOURCES}
    for record in data["records"]:
        index = record["index"]
        ni, graph6, p3, raw_order, rounds, p4_dim, digest = POSITIVES[index]
        require(
            ten_rows[index] == ("10", graph6)
            and record["graph6"] == graph6
            and record["nine_index"] == ni
            and record["nine_graph6"] == NINE_SOURCES[ni][0]
            and tuple(record["p3"]) == p3
            and record["raw_p4_order"] == raw_order
            and record["fold_rounds"] == rounds
            and tuple(record["p4"]) == p4_dim
            and record["map_sha256"] == digest,
            f"Original graph identity or claimed P4 shape changed: {index}",
        )
        raw, pared, got_rounds, got_p3 = p4_from_graph6(graph6)
        require(
            tuple(got_p3) == p3 and len(raw) == raw_order
            and got_rounds == rounds and dimensions(pared) == p4_dim,
            f"Independent P4 reconstruction disagrees: {index}",
        )
        mapping = decode_map(record)
        check_bijection(pared, sources[ni], mapping)
        constrained_matcher(pared, sources[ni], mapping)
        added[ni] += 1
        print(
            f"EXACT P4 ten McKay {index} -> unresolved nine McKay {ni}: "
            f"{p4_dim[0]} vertices, {p4_dim[1]} edges, "
            "complete all-pairs isomorphism verified",
            flush=True,
        )

    counts = data["expected_counts"]
    require(
        added == {249576: 3, 251628: 1}
        and counts == {
            "nine_pared": [141, 147, 142],
            "previous_stiff_p3": [17, 23, 25],
            "previous_stiff_p4": [1, 0, 0],
            "additional_stiff_p4": [3, 1, 0],
            "linked_per_nine": [162, 171, 167],
            "linked_all": 500,
            "unlinked_stiff": 552,
            "unresolved_ten": 1052,
        }
        and data["old_dependent_count"] == 496
        and data["new_dependent_count"] == 500
        and data["stiff_not_yet_linked"] == 552
        and sum(counts["linked_per_nine"]) == 500
        and sum(counts["nine_pared"]) == 430
        and 622 - 66 - sum(added.values()) == 552,
        "New exact 500/552 conditional partition is not supported",
    )
    print("CERTIFIED proof-only: 496 + four complete P4 links = 500 "
          "dependent ten-originals; 552 stiff originals not yet linked; "
          "3 nine and 1052 ten originals remain indeterminate",
          flush=True)


if __name__ == "__main__":
    verify_archive()
