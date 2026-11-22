"""Independently replay all 242 v16 ten-vertex consequences of McKay 253650.

The archived v16 row for each original graph states its completely pared
nine-vertex graph6. Recompute exact graph isomorphism against the proven
nine-vertex divergent source and independently check all saved bijections.
Do not change historical snapshots or authoritative indices.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import networkx as nx

if sys.flags.optimize:
    raise RuntimeError("Never run the exact certificate verifier with -O")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = nx.from_graph6_bytes(b"HEjer~{")
FROZEN = ROOT / "indeterminate_order_10_v16.txt"
CERT = HERE / "lift_v16_certificate.json"
EXPECTED_V16_BLOB = "0dd845dad16904c30ad7bf2057f2f6c5c3aeeb89"
EXPECTED_COUNT = 242


def check(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(data)).encode() + b"\0" + data
    ).hexdigest()


def verify(*, public: bool = False) -> None:
    from research.order9_253650_o12_v1.verify import verify as verify_source

    verify_source(public=public)
    saved = json.loads(CERT.read_text(encoding="utf-8"))
    check(saved["schema"] == 1, "Unexpected saved certificate schema")
    check(saved["reference_index"] == 253650, "Wrong reference McKay index")
    check(saved["reference_graph6"] == "HEjer~{", "Wrong reference graph6")
    check(saved["stage"] == "order9_253650_o12_lifts_v16", "Wrong saved stage")
    check(saved["source_v16_git_blob_sha"] == EXPECTED_V16_BLOB,
          "Unexpected saved source hash")
    check(saved["expected_count"] == EXPECTED_COUNT, "Unexpected saved count")

    raw = FROZEN.read_bytes()
    check(git_blob_sha(raw) == EXPECTED_V16_BLOB,
          "The frozen order-ten v16 census changed")
    rows: dict[int, tuple[str, ...]] = {}
    for line in raw.decode("utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = tuple(line.split())
        check(len(parts) == 6, "Malformed frozen census row")
        index = int(parts[0])
        check(index not in rows, f"Duplicated index {index}")
        rows[index] = parts
    check(len(rows) == 2341, "Unexpected v16 population")

    # Independently discover ALL positive source-isomorphism matches.
    actual: set[int] = set()
    for index, parts in rows.items():
        if parts[1] != "9":
            continue
        graph = nx.from_graph6_bytes(parts[2].encode("ascii"))
        if nx.is_isomorphic(SOURCE, graph):
            check(parts[3:] == ("-", "-", "-"),
                  f"Index {index} has nonempty classification fields")
            actual.add(index)
    check(len(actual) == EXPECTED_COUNT,
          f"Independent complete v16 scan found {len(actual)} matches")

    witnesses = saved["certificates"]
    check(len(witnesses) == EXPECTED_COUNT,
          "Incorrect number of explicit bijections")
    indexed = [item["original_index"] for item in witnesses]
    check(indexed == sorted(set(indexed)),
          "Certificate indices are duplicated or unsorted")
    check(set(indexed) == actual,
          "Certificate cohort does not equal independent exact scan")

    for item in witnesses:
        index = item["original_index"]
        parts = rows[index]
        check(parts[1] == "9" and parts[2] == item["pared_graph6"],
              f"Unmatched index/graph6: {index}")
        target = nx.from_graph6_bytes(parts[2].encode("ascii"))
        mapping = item["source_to_pared"]
        check(len(mapping) == len(SOURCE)
              and sorted(mapping) == list(range(len(target))),
              f"Not a bijection: {index}")
        check(all(SOURCE.has_edge(u, v) == target.has_edge(mapping[u], mapping[v])
                  for u in SOURCE for v in SOURCE if u != v),
              f"Not an induced graph isomorphism: {index}")

    print(f"VERIFIED {len(actual)} exact ten-vertex v16 original records "
          f"with nine-vertex pared core isomorphic to K-divergent "
          f"McKay 253650; frozen_v16=PASS; all bijections=PASS")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--public", action="store_true")
    args = parser.parse_args()
    verify(public=args.public)
