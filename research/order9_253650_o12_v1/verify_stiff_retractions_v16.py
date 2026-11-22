"""Exact independent audit of all stiff-ten -> nine-vertex McKay 253650 retracts.

Enumerates *all* 955 stiff ten-vertex v16 pared cores; for each possible
deleted vertex, checks the induced nine-vertex subgraph isomorphic to
HEjer~{ and all possible images of the deleted vertex under a retraction.
Rechecks each of the 71 saved positive source-to-target bijections.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import networkx as nx

if sys.flags.optimize:
    raise RuntimeError("Never optimize certificate checks")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
V16 = ROOT / "indeterminate_order_10_v16.txt"
CERT = HERE / "stiff_retractions_v16_certificate.json"
REF = nx.from_graph6_bytes(b"HEjer~{")
V16_BLOB = "0dd845dad16904c30ad7bf2057f2f6c5c3aeeb89"


def check(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(data)).encode() + b"\0" + data
    ).hexdigest()


def candidate(graph: nx.Graph) -> tuple[tuple[int, int] | None, bool]:
    """Return some exact snub-independent retraction (deleted, image).

    Every order-ten to order-nine induced target is a one-vertex deletion.
    A target isomorphic to REF is fixed pointwise; the deleted vertex
    must map to a target vertex adjacent or equal to every neighbor.
    """
    has_induced = False
    for deleted in graph:
        remain = [v for v in graph if v != deleted]
        target = graph.subgraph(remain)
        if not nx.is_isomorphic(target, REF):
            continue
        has_induced = True
        for image in remain:
            if all(image == z or target.has_edge(image, z)
                   for z in graph[deleted]):
                return (deleted, image), True
    return None, has_induced


def verify(*, public: bool = False) -> None:
    from research.order9_253650_o12_v1.verify import verify as verify_anchor
    verify_anchor(public=public)

    data = json.loads(CERT.read_text(encoding="utf-8"))
    check(data["schema"] == 1 and data["reference_index"] == 253650,
          "Unexpected certificate schema or reference")
    check(data["reference_graph6"] == "HEjer~{", "Wrong reference")
    check(data["stage"] == "order9_253650_o12_v16_stiff_retractions",
          "Unexpected stage")
    check(data["source_v16_git_blob_sha"] == V16_BLOB,
          "Incorrect source blob")
    check(data["expected_stiff"] == 955
          and data["expected_retractions"] == 71
          and data["expected_induced_only"] == 29,
          "Unexpected declared counts")

    frozen = V16.read_bytes()
    check(git_blob_sha(frozen) == V16_BLOB, "Frozen v16 changed")
    records = {}
    for line in frozen.decode().splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        check(len(fields) == 6, "Bad census row")
        index = int(fields[0])
        check(index not in records, "Duplicate census index")
        records[index] = fields
    check(len(records) == 2341, "Unexpected v16 record population")
    stiff = {
        idx: row for idx, row in records.items()
        if row[1] == "10"
    }
    check(len(stiff) == 955, "Unexpected stiff cohort")

    positive: set[int] = set()
    induced_only: set[int] = set()
    for index, row in stiff.items():
        graph = nx.from_graph6_bytes(row[2].encode("ascii"))
        check(len(graph) == 10 and row[3:] == ["-", "-", "-"],
              f"Bad stiff source metadata for {index}")
        retract, induced = candidate(graph)
        if retract is not None:
            positive.add(index)
        elif induced:
            induced_only.add(index)
    check(len(positive) == 71 and len(induced_only) == 29,
          f"Recomputed positives/induced-only: {len(positive)}/{len(induced_only)}")

    saved = data["certificates"]
    ids = [item["original_index"] for item in saved]
    check(len(saved) == 71 and ids == sorted(set(ids)),
          "Wrong or duplicate saved indices")
    check(set(ids) == positive, "Saved and discovered cohorts differ")
    check(positive.isdisjoint({9804321, 10185592, 10472553}),
          "Stiff retractions overlap the three already proved flag spheres")

    for item in saved:
        i = item["original_index"]
        row = stiff[i]
        check(row[2] == item["pared_graph6"], f"Wrong source graph6: {i}")
        graph = nx.from_graph6_bytes(row[2].encode("ascii"))
        deleted = item["deleted_vertex"]
        image = item["image_of_deleted"]
        check(deleted in graph and image in graph and image != deleted,
              f"Invalid projection pivot: {i}")
        retained = set(graph) - {deleted}
        check(set(item["source_to_pared"]) == retained
              and len(item["source_to_pared"]) == len(REF),
              f"Nonbijective saved source embedding: {i}")
        embedding = dict(enumerate(item["source_to_pared"]))
        check(all(
            REF.has_edge(u, v) == graph.has_edge(embedding[u], embedding[v])
            for u in REF for v in REF if u != v
        ), f"Not an induced REF copy: {i}")
        projection = {v: (image if v == deleted else v) for v in graph}
        check(all(
            projection[u] == projection[v]
            or graph.has_edge(projection[u], projection[v])
            for u, v in graph.edges()
        ), f"Not a retraction: {i}")

    print(
        "VERIFIED all 955 stiff v16 cores: 71 exact new "
        "McKay 253650 ordinary graph retracts, 29 induced-only; "
        "all 71 frozen identities and explicit maps replayed"
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--public", action="store_true")
    args = p.parse_args()
    verify(public=args.public)
