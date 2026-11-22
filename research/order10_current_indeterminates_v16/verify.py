"""Audit certified order-nine v5 and order-ten v16 index promotions.

The authoritative roots must be exact byte copies of the versioned files.
Every retained predecessor row is preserved; exclusions are precisely the
two proved nine-vertex O9/O15 sources, the 120 F45 dependency proofs, and
the 80 complete O15-reference lifts. No negative search is used.

Optional proof modes rerun independent saved witnesses with public pycliques.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
V4_9 = ROOT / "indeterminate_order_9_v4.txt"
V5_9 = ROOT / "indeterminate_order_9_v5.txt"
V15_10 = ROOT / "indeterminate_order_10_v15.txt"
V16_10 = ROOT / "indeterminate_order_10_v16.txt"
ROOT_9 = ROOT / "indeterminate_order_9.txt"
ROOT_10 = ROOT / "indeterminate_order_10.txt"
MANIFEST = HERE / "promotion_manifest.json"
O15_CERT = ROOT / "research/order9_260910_o15_v1/lift_v14_certificate.json"

V4_BLOB = "9055247c5778091c07717fde17c68ee207764621"
V15_BLOB = "4d174e1ffa8d39492ae90c44d67afdf67ec2022e"
NINE_REMOVED = {208409: "HCZTf\\}", 260910: "HUZvvzu"}
METHODS_F45 = {
    "reference": 72,
    "retracts": 35,
    "non_triangle_edge": 10,
    "inverse_cutpoint_extension": 3,
}
METHODS_O15 = {"reference": 62, "retraction": 14, "P2_iso": 4}
SURFACE10 = {
    6499365, 8559181, 9804321, 10185592, 10472553,
    10803453, 11031156, 11138607, 11548392,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def rows(path: Path) -> dict[int, tuple[str, list[str]]]:
    records = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        require(len(fields) == 6, f"Malformed record: {path}: {line}")
        idx = int(fields[0])
        require(idx not in records, f"Duplicate original McKay index: {idx}")
        records[idx] = line, fields
    require(list(records) == sorted(records), f"Unsorted list: {path}")
    return records


def verify_indices() -> None:
    require(blob(V4_9.read_bytes()) == V4_BLOB, "Historical nine v4 changed")
    require(blob(V15_10.read_bytes()) == V15_BLOB, "Historical ten v15 changed")
    require(ROOT_9.read_bytes() == V5_9.read_bytes(),
            "Order-nine root is not the v5 snapshot")
    require(ROOT_10.read_bytes() == V16_10.read_bytes(),
            "Order-ten root is not the v16 snapshot")

    old9, new9 = rows(V4_9), rows(V5_9)
    old10, new10 = rows(V15_10), rows(V16_10)
    require((len(old9), len(new9)) == (12, 10),
            "Nine-vertex population must be 12 -> 10")
    require((len(old10), len(new10)) == (2541, 2341),
            "Ten-vertex population must be 2541 -> 2341")
    require(all(old9[k] == value for k, value in new9.items()),
            "Retained nine-vertex row modified")
    require(all(old10[k] == value for k, value in new10.items()),
            "Retained ten-vertex row modified")
    require(set(old9) - set(new9) == set(NINE_REMOVED),
            "Wrong nine-vertex deletions")
    require(all(old9[k][1][2] == g6 and old9[k][1][3:] == ["-", "-", "-"]
                for k, g6 in NINE_REMOVED.items()),
            "Nine-vertex deleted source does not match its proved identity")

    conditional = {
        idx for idx, (_, fields) in old10.items()
        if fields[4] == "conjectured_divergent"
    }
    require(len(conditional) == 120, "Historical F45 cohort is not 120")
    require(all(old10[k][1][5] == "HCZTf\\}" for k in conditional),
            "A conditional reference is not the proved F45 target")
    require(Counter(old10[k][1][3] for k in conditional) == METHODS_F45,
            "Wrong 120-case F45 proof mechanism partition")

    saved = json.loads(O15_CERT.read_text(encoding="utf-8"))
    require(saved["schema"] == 1 and saved["reference_g6"] == "HUZvvzu",
            "Unexpected O15 reference-certificate metadata")
    require(saved["source_v14_git_blob"] ==
            "3ee92e02891b3046059241d4a2304794b0e34380",
            "Wrong frozen source for the O15 lift cohort")
    positives = saved["positive"]
    o15 = {item["index"] for item in positives}
    require(len(positives) == len(o15) == 80 and
            [item["index"] for item in positives] == sorted(o15),
            "O15 certificate cohort is incomplete or duplicated")
    require(Counter(item["kind"] for item in positives) == METHODS_O15,
            "Wrong O15 proof mechanism partition")
    require(conditional.isdisjoint(o15), "Overlapping 120 and 80 cohorts")
    require(all(k in old10 and old10[k][1][3:] == ["-", "-", "-"]
                for k in o15), "An O15 member was not unconditionally unresolved")
    require(all(old10[item["index"]][1][2] == item["source_g6"] and
                int(old10[item["index"]][1][1]) == item["source_order"]
                for item in positives), "Original McKay identity differs from O15 proof")

    removed = set(old10) - set(new10)
    require(len(removed) == 200 and removed == conditional | o15,
            "Wrong ten-vertex deletion set")
    require(all(fields[4] == "-" for _, fields in new10.values()),
            "A conjecture-dependent record survived v16")
    require(Counter(int(f[1]) for _, f in new10.values()) ==
            {9: 1386, 10: 955}, "Unexpected pared-order partition")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    require(manifest["schema"] == 1 and
            manifest["source_order9_blob"] == V4_BLOB and
            manifest["source_order10_blob"] == V15_BLOB,
            "Wrong frozen predecessor references in promotion manifest")
    require({r["index"]: r["graph6"] for r in manifest["removed_order9"]} ==
            NINE_REMOVED, "Nine-vertex manifest mismatch")
    m_f45 = manifest["removed_order10_f45"]
    m_o15 = manifest["removed_order10_o15"]
    require({r["index"] for r in m_f45} == conditional and
            {r["index"] for r in m_o15} == o15,
            "Ten-vertex manifest deletion sets disagree with certificates")
    require(all(r["original_record"] == old10[r["index"]][0] and
                r["method"] == old10[r["index"]][1][3] and
                r["reference_graph6"] == "HCZTf\\}" for r in m_f45),
            "F45 manifest record or proof rule differs")
    kind_by_idx = {item["index"]: item["kind"] for item in positives}
    require(all(r["original_record"] == old10[r["index"]][0] and
                r["method"] == kind_by_idx[r["index"]] and
                r["reference_graph6"] == "HUZvvzu" for r in m_o15),
            "O15 manifest record or proof rule differs")
    require(manifest["remaining_order9"] == 10 and
            manifest["remaining_order10"] == 2341,
            "Wrong manifest residual counts")

    print("CERTIFIED_ORDER9_V5 original_12 -> 10 removed_2")
    print("CERTIFIED_ORDER10_V16 original_2541 -> 2341 removed_200")
    print("F45_DEPENDENCIES_120 O15_REFERENCE_LIFTS_80")
    print("RETAINED_RECORDS_IDENTICAL ALL_PRIOR_SNAPSHOTS_UNCHANGED")
    print("ZERO_REMAINING_CONDITIONAL_RECORDS")


def verify_surfaces() -> None:
    import networkx as nx

    def closed_flag_surface(graph6: str) -> bool:
        graph = nx.from_graph6_bytes(graph6.encode("ascii"))
        for vertex in graph:
            link = graph.subgraph(graph[vertex])
            if len(link) < 4 or any(d != 2 for _, d in link.degree()):
                return False
            if not nx.is_connected(link):
                return False
        return True

    nine = rows(V5_9)
    ten = rows(V16_10)
    require(not any(closed_flag_surface(r[1][2]) for r in nine.values()),
            "An unresolved nine-vertex flag surface remains")
    found = {i for i, r in ten.items() if closed_flag_surface(r[1][2])}
    require(found == SURFACE10, "Ten-vertex sphere census differs")
    for i in sorted(found):
        graph = nx.from_graph6_bytes(ten[i][1][2].encode("ascii"))
        triangle_count = sum(1 for clique in nx.enumerate_all_cliques(graph)
                             if len(clique) == 3)
        require((len(graph), graph.number_of_edges(), triangle_count) ==
                (10, 24, 16), f"Wrong flag sphere f-vector: {i}")
    print("SURFACE_AUDIT nine=0 ten=9 all_flag_triangulations_of_S2")
    print("TEN_SURFACE_MCKAY_INDICES", " ".join(map(str, sorted(found))))


def replay_f45() -> None:
    from research.order9_f45_o9_v1.lift120 import verify as check_120

    data = check_120()
    require(len(data["proven"]) == 120, "Incomplete full F45 certificate replay")
    print("PROOF_REPLAY_F45_120_PASS")


def replay_o15(*, full: bool = False) -> None:
    from research.order9_260910_o15_v1.verify_lifts_v14 import verify as check_80

    check_80(full=full)
    print("PROOF_REPLAY_O15_80_PASS")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--surfaces", action="store_true")
    parser.add_argument("--f45", action="store_true")
    parser.add_argument("--o15", action="store_true")
    parser.add_argument("--o15-full", action="store_true")
    args = parser.parse_args()
    verify_indices()
    if args.surfaces:
        verify_surfaces()
    if args.f45:
        replay_f45()
    if args.o15 or args.o15_full:
        replay_o15(full=args.o15_full)
