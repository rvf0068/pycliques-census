"""Audit nine-v6 and ten-v17 indices by exact positive certificates.

Archived v16 proof files are read-only. --proofs replays independent
octahedral retractions and all 313 nine-core isomorphism/retraction lifts.
--families independently checks all 1144 surviving nine-vertex core
classes. --surfaces screens all remaining flag triangulations.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import networkx as nx

if sys.flags.optimize:
    raise RuntimeError("Never use optimized Python to verify proofs")

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
NINE5, NINE6 = (ROOT / f"indeterminate_order_9_{v}.txt" for v in ("v5", "v6"))
TEN16, TEN17 = (ROOT / f"indeterminate_order_10_{v}.txt" for v in ("v16", "v17"))
ROOT9, ROOT10 = ROOT / "indeterminate_order_9.txt", ROOT / "indeterminate_order_10.txt"
MANIFEST = HERE / "promotion_manifest.json"
LIFT = ROOT / "research/order9_253650_o12_v1/lift_v16_certificate.json"
RETRACT = ROOT / "research/order9_253650_o12_v1/stiff_retractions_v16_certificate.json"
V5_SHA = "d803ee83273b44f60e5078b7beb3d11a3f4eb2ee"
V16_SHA = "0dd845dad16904c30ad7bf2057f2f6c5c3aeeb89"
PROVED_9 = "253650 9 HEjer~{ - - -"
SPHERES = {
    9804321: ("ICR" + chr(96) + "tlmv_", 5),
    10185592: ("ICXmdbj\\o", 6),
    10472553: ("ICZTeYj^_", 4),
}
SURFACES_LEFT = {6499365, 8559181, 10803453, 11031156, 11138607, 11548392}
FAMILIES = {
    249436: 141, 249574: 82, 249576: 141,
    250814: 121, 251628: 147, 251759: 129,
    251902: 150, 254369: 91, 260040: 142,
}
CATEGORIES = {
    "pared_nine_exact_isomorphism": 242,
    "stiff_ten_ordinary_retraction": 71,
    "sphere_p4_o5_retraction": 1,
    "sphere_p4_o6_retraction": 1,
    "sphere_p4_o4_retraction": 1,
}


def check(condition, explanation):
    if not condition:
        raise AssertionError(explanation)


def blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def rows(path):
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        check(len(fields) == 6, f"Invalid row {path}: {line}")
        i = int(fields[0])
        check(i not in out, f"Duplicate original McKay index {i}")
        out[i] = line
    check(list(out) == sorted(out), f"Unsorted source {path}")
    return out


def graph(g6):
    return nx.from_graph6_bytes(g6.encode("ascii"))


def original_certificate_cohorts(old10):
    reference = graph("HEjer~{")
    lift = json.loads(LIFT.read_text(encoding="utf-8"))
    retract = json.loads(RETRACT.read_text(encoding="utf-8"))
    for d in (lift, retract):
        check(d["schema"] == 1 and d["reference_index"] == 253650
              and d["reference_graph6"] == "HEjer~{"
              and d["source_v16_git_blob_sha"] == V16_SHA,
              "Wrong archived McKay 253650 proof metadata")
    check(len(lift["certificates"]) == lift["expected_count"] == 242,
          "Wrong lift cohort")
    check(len(retract["certificates"]) == retract["expected_retractions"] == 71
          and retract["expected_stiff"] == 955
          and retract["expected_induced_only"] == 29,
          "Wrong retraction cohort")

    c242 = set()
    for item in lift["certificates"]:
        index = item["original_index"]
        check(index in old10 and index not in c242, f"Bad index {index}")
        c242.add(index)
        row = old10[index].split()
        check(row[1] == "9" and row[2] == item["pared_graph6"]
              and row[3:] == ["-", "-", "-"], f"Wrong nine-core row {index}")
        target = graph(row[2])
        iso = item["source_to_pared"]
        check(len(iso) == 9 and set(iso) == set(target),
              f"Not a bijection for {index}")
        check(all(reference.has_edge(u, v) == target.has_edge(iso[u], iso[v])
                  for u in reference for v in reference),
              f"False nine-core isomorphism {index}")

    c71 = set()
    for item in retract["certificates"]:
        index = item["original_index"]
        check(index in old10 and index not in c71, f"Bad index {index}")
        c71.add(index)
        row = old10[index].split()
        check(row[1] == "10" and row[2] == item["pared_graph6"]
              and row[3:] == ["-", "-", "-"], f"Wrong stiff row {index}")
        host = graph(row[2])
        deleted, image = item["deleted_vertex"], item["image_of_deleted"]
        iso = item["source_to_pared"]
        check(deleted in host and image in host and image != deleted
              and len(iso) == 9 and set(iso) == set(host) - {deleted},
              f"Invalid induced target of {index}")
        check(all(reference.has_edge(u, v) == host.has_edge(iso[u], iso[v])
                  for u in reference for v in reference),
              f"Target not induced-isomorphic for {index}")
        projection = {v: image if v == deleted else v for v in host}
        check(all(projection[u] == projection[v] or
                  host.has_edge(projection[u], projection[v])
                  for u, v in host.edges()),
              f"Not a graph retraction for {index}")

    check(not c242 & c71, "Overlapping core certificates")
    for index, (g6, _) in SPHERES.items():
        check(index in old10 and old10[index].split()[1:] ==
              ["10", g6, "-", "-", "-"] and index not in c242 | c71,
              f"Wrong or overlapping sphere {index}")
    return c242, c71


def verify_indices():
    check(blob(NINE5.read_bytes()) == V5_SHA, "Frozen nine-v5 source changed")
    check(blob(TEN16.read_bytes()) == V16_SHA, "Frozen ten-v16 source changed")
    check(ROOT9.read_bytes() == NINE6.read_bytes(), "Current nine root != v6")
    check(ROOT10.read_bytes() == TEN17.read_bytes(), "Current ten root != v17")
    old9, new9 = rows(NINE5), rows(NINE6)
    old10, new10 = rows(TEN16), rows(TEN17)
    check((len(old9), len(new9), len(old10), len(new10)) ==
          (10, 9, 2341, 2025), "Incorrect unresolved population")
    check(old9.get(253650) == PROVED_9 and
          set(old9) - set(new9) == {253650}, "Wrong removed nine-vertex graph")
    check(all(old9[i] == line for i, line in new9.items()),
          "Changed retained nine-vertex record")
    check(all(old10[i] == line for i, line in new10.items()),
          "Changed retained ten-vertex record")
    check(all(line.split()[3:] == ["-", "-", "-"] for line in new10.values()),
          "Still-conditional ten-vertex record in v17")
    c242, c71 = original_certificate_cohorts(old10)
    deleted = c242 | c71 | set(SPHERES)
    check(len(deleted) == 316 and set(old10) - set(new10) == deleted,
          "Missing/unjustified ten-vertex deletion")
    check(Counter(int(line.split()[1]) for line in new10.values()) ==
          {9: 1144, 10: 881}, "Wrong remaining nine/ten pared partition")

    saved = json.loads(MANIFEST.read_text(encoding="utf-8"))
    check(saved["schema"] == 1
          and saved["previous_order9_git_blob"] == V5_SHA
          and saved["previous_order10_git_blob"] == V16_SHA
          and saved["remaining_order9"] == 9
          and saved["remaining_order10"] == 2025
          and saved["ten_proof_classes"] == CATEGORIES
          and saved["proved_nine"]["source_row"] == PROVED_9,
          "Wrong promotion manifest metadata")
    records = saved["removed_order10"]
    check(len(records) == 316 and
          [item["index"] for item in records] == sorted(deleted)
          and Counter(item["kind"] for item in records) == CATEGORIES,
          "Incorrect 316-member manifest cohort")
    for item in records:
        index = item["index"]
        if index in c242:
            kind = "pared_nine_exact_isomorphism"
        elif index in c71:
            kind = "stiff_ten_ordinary_retraction"
        else:
            kind = f"sphere_p4_o{SPHERES[index][1]}_retraction"
        check(item["kind"] == kind and item["source_row"] == old10[index]
              and (ROOT / item["certificate"]).is_file(),
              f"Broken manifest proof reference for {index}")
    print("INDEX_AUDIT_PASS nine_v6=9 ten_v17=2025")
    print("EXACT_316_PROOFS 242-nine-core 71-stiff-retraction 3-spheres")
    print("FROZEN_GIT_BLOBS_VERIFIED RETAINED_ROWS_UNCHANGED")
    print("PARED_NINE=1144 STIFF_TEN=881")


def verify_families():
    nine, ten = rows(NINE6), rows(TEN17)
    reference = {i: graph(row.split()[2]) for i, row in nine.items()}
    check(set(reference) == set(FAMILIES), "Wrong nine-vertex remaining cohort")
    for i, g in reference.items():
        check(not any(nx.is_isomorphic(g, reference[j])
                      for j in reference if j < i),
              "Two nine-vertex representatives are isomorphic")
    counts = Counter()
    for index, row in ten.items():
        fields = row.split()
        if fields[1] != "9":
            continue
        g = graph(fields[2])
        matches = [i for i, r in reference.items() if nx.is_isomorphic(g, r)]
        check(len(matches) == 1, f"Ten-index {index} matched {matches} nine-cores")
        counts[matches[0]] += 1
    check(dict(counts) == FAMILIES, f"Unexpected nine-family sizes {counts}")
    print("FAMILY_AUDIT_PASS all_1144_nine_pared_ten_originals")
    for i in sorted(counts):
        print("UNRESOLVED_NINE_CORE", i, "TEN_ORIGINALS", counts[i])


def verify_surfaces():
    def is_surface(g):
        for v in g:
            link = g.subgraph(g[v])
            if len(link) < 4 or not nx.is_connected(link):
                return False
            if any(degree != 2 for _, degree in link.degree()):
                return False
        return True
    check(not any(is_surface(graph(row.split()[2])) for row in rows(NINE6).values()),
          "Unresolved order-nine surface")
    remaining = rows(TEN17)
    found = {i for i, row in remaining.items() if is_surface(graph(row.split()[2]))}
    check(found == SURFACES_LEFT, f"Wrong ten-vertex surface cohort: {found}")
    for i in found:
        g = graph(remaining[i].split()[2])
        triangles = sum(len(c) == 3 for c in nx.enumerate_all_cliques(g))
        check((len(g), g.number_of_edges(), triangles) == (10, 24, 16),
              f"Wrong flag-sphere face vector for {i}")
    print("FLAG_SURFACE_AUDIT_PASS nine=0 ten=6")
    print("SURFACE_INDICES", " ".join(map(str, sorted(found))))


def verify_proofs(*, public=False):
    from research.order9_253650_o12_v1.verify import verify as prove9
    from research.order9_253650_o12_v1.verify_lifts_v16 import verify as prove242
    from research.order9_253650_o12_v1.verify_stiff_retractions_v16 import verify as prove71
    from research.order10_surface_9804321_o5_v1.verify import verify as prove5
    from research.order10_surface_10185592_o6_v1.verify import verify as prove6
    from research.order10_surface_10472553_o4_v1.verify import verify as prove4
    for verify in (prove9, prove242, prove71, prove5, prove6, prove4):
        verify(public=public)
    print("SIX_ARCHIVED_FULL_PROOF_REPLAYS_PASS", "public" if public else "independent")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--families", action="store_true")
    parser.add_argument("--surfaces", action="store_true")
    parser.add_argument("--proofs", action="store_true")
    parser.add_argument("--public", action="store_true")
    args = parser.parse_args()
    if args.public and not args.proofs:
        parser.error("--public requires --proofs")
    verify_indices()
    if args.families:
        verify_families()
    if args.surfaces:
        verify_surfaces()
    if args.proofs:
        verify_proofs(public=args.public)
