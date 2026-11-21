"""Replay 120 frozen ten-vertex references to newly proved divergent F45.

No classification is accepted solely from the old conditional label.
Each original completely pared graph is checked against an explicit:
exact isomorphism, fixed-target ordinary retraction, valid nontriangle
edge deletion followed by dominated folds, or admissible inverse
cutpoint split plus local-bridge/edge deletion and folds.

These are independent NetworkX checks previously used in the historical
99-case proof, imported only for reusable complete positive witnesses.
The original->pared fold provenance remains that of the frozen census.

This proof-only routine does not delete any row or edit the current index.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from heher_divergence_class_lift_v1 import (  # noqa: E402
    certify_reference,
    certify_retracts,
    certify_nontriangle,
    certify_inverse_cutpoint,
)

SOURCE = ROOT / "indeterminate_order_10_v14.txt"
REFERENCE = "HCZTf\\}"
EXPECTED = {
    "reference": 72,
    "retracts": 35,
    "non_triangle_edge": 10,
    "inverse_cutpoint_extension": 3,
}
CHECKERS = {
    "reference": certify_reference,
    "retracts": certify_retracts,
    "non_triangle_edge": certify_nontriangle,
    "inverse_cutpoint_extension": certify_inverse_cutpoint,
}


def blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def verify() -> dict:
    from research.order9_f45_o9_v1.verify import verify as verify_source
    verify_source()  # Full positive O9 retraction, including public pycliques.
    raw = SOURCE.read_bytes()
    expected_blob = "3ee92e02891b3046059241d4a2304794b0e34380"
    if blob(raw) != expected_blob:
        raise ValueError("Historical ten-vertex v14 proof source has changed")
    lines = [
        line for line in raw.decode("utf-8").splitlines()
        if line and not line.startswith("#")
    ]
    if len(lines) != 2568:
        raise ValueError("Wrong frozen v14 count")
    source_rows = []
    for line in lines:
        i, order, graph6, rule, status, label = line.split(" ", 5)
        if label == REFERENCE:
            if status != "conjectured_divergent" or rule not in CHECKERS:
                raise ValueError(f"Unexpected conditional F45 claim at {i}")
            source_rows.append({
                "index": int(i), "order": int(order), "graph6": graph6,
                "rule": rule, "source_row": line,
            })
    if len(source_rows) != 120 or Counter(row["rule"] for row in source_rows) != EXPECTED:
        raise ValueError("The historical F45 conditional set is not the expected 120")
    target = nx.from_graph6_bytes(REFERENCE.encode("ascii"))
    records = []
    for row in source_rows:
        graph = nx.from_graph6_bytes(row["graph6"].encode("ascii"))
        if len(graph) != row["order"]:
            raise ValueError(f"Host pared order mismatch {row['index']}")
        cert = CHECKERS[row["rule"]](graph, target)
        records.append({**row, "proof": cert})
        print("PROVED_TEN", row["index"], row["rule"], flush=True)
    if [x["index"] for x in records] != sorted(x["index"] for x in records):
        raise ValueError("Positive cohort is not sorted")
    print("PROVED_ALL_120", dict(Counter(row["rule"] for row in records)))
    return {"schema": 1, "source_blob": expected_blob,
            "reference_graph6": REFERENCE, "proven": records}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify()
    if args.output:
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
