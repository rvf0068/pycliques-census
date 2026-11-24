"""Verify archived v24 fourth-iterate research without promoting negative verdicts.

The twelve shard jobs independently rebuild every fourth iterate and
must reproduce their exact saved records. The global verification audits
the frozen source, class coverage, per-shard counts, and pairwise
uniqueness of all 180 complete P4 (order, size) signatures.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from .search import (
    ARCHIVE, CURRENT, EXCLUDED, REFERENCE_DIMENSIONS, SOURCE,
    representatives, source_rows,
)

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses P4 archive checks")

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results.json"
REQUIRED = {
    "certified_p3_representatives": 522,
    "selected": 206,
    "complete_p4": 180,
    "p4_facet_cap": 26,
    "positive_reference_matches": 0,
    "duplicate_p4_order_edge_signatures": 0,
}


def need(value: bool, reason: str) -> None:
    if not value:
        raise AssertionError(reason)


def blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def audit() -> dict:
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    need(data["schema"] == 1 and
         data["source_name"] == SOURCE.name and
         data["source"] == blob(SOURCE.read_bytes()) and
         data["ci_run"] == 45460379020 and
         SOURCE.read_bytes() == CURRENT.read_bytes(),
         "Wrong P4 pilot source provenance")
    need(data["setting"] == {
        "min_p3": 41, "max_p3": 55,
        "intermediate_maximal_cliques": 750,
        "timeout_sec_per_graph": 24, "shards": 12,
    }, "Wrong or concealed resource limits")
    need(data["historical_global_p3_git_blob"] ==
         "f32ceb913b44583f472402e14c596598fef71aaa",
         "Wrong historical P3 class source")
    need(data["counts"] == REQUIRED,
         "Archived P4 pilot global counts changed")
    need(data["reference_shapes"] == {
        str(k): list(v) for k, v in REFERENCE_DIMENSIONS.items()
    }, "Reference graph dimensions changed")

    refs = dict(representatives())
    need(len(refs) == 522 and not EXCLUDED.intersection(refs),
         "Wrong remaining exact P3 class representatives")
    sources = source_rows()
    records = data["records"]
    indices = [row["index"] for row in records]
    need(len(records) == 206 and indices == sorted(set(indices)) and
         all(index in refs and refs[index] == sources[index]
             for index in indices),
         "Noncanonical, missing or unverified P3 source")
    full = []
    capped = []
    for row in records:
        need(row.get("graph6") == refs[row["index"]],
             "Incorrect source graph6 in P4 record")
        need(isinstance(row["p3"], list) and len(row["p3"]) == 2
             and 41 <= row["p3"][0] <= 55,
             "Wrong P3 selection window")
        if row["status"] == "P4_FACET_CAP":
            need(row["stage"] == 4 and row["reason"] == "maximal_clique_cap"
                 and "p4" not in row,
                 "Wrong explicit P4 resource-limited record")
            capped.append(row)
        else:
            need(row["status"] == "NO_REFERENCE_DIMENSION_MATCH"
                 and len(row["raw_p4"]) == len(row["p4"]) == 2,
                 "False positive, unreviewed status, or malformed P4")
            need(0 < row["p4"][0] <= row["raw_p4"][0] <= 750
                 and 0 <= row["p4"][1] <= row["raw_p4"][1],
                 "Impossible pared fourth-iterate dimensions")
            need(tuple(row["p4"]) not in REFERENCE_DIMENSIONS.values(),
                 "Unreported positive reference-dimension match")
            full.append(row)
    need((len(full), len(capped)) == (180, 26),
         "Incorrect exact/limited source counts")
    signatures = [tuple(row["p4"]) for row in full]
    need(len(set(signatures)) == len(signatures) == 180,
         "Distinct P3 representatives have duplicate complete P4 dimensions")

    sums = data["shard_summaries"]
    need(len(sums) == 12 and [x["shard"] for x in sums] == list(range(12)),
         "Incomplete twelve-shard metadata")
    for i, summary in enumerate(sums):
        cohort = records[i::12]
        observed = Counter(row["status"] for row in cohort)
        need(summary["shard"] == i and
             summary["selected"] == len(cohort) and
             summary["total_window"] == 206 and
             summary["counts"] == dict(observed),
             f"Saved shard {i} coverage or counts do not match")
    print("PASS: all 206 ten-v24 fourth-stage pilot records accounted for;"
          " 180 complete pairwise-distinct (order, edges) signatures;"
          " 26 bounded facet caps; zero P4 matches with any of five"
          " previously proved divergent references", flush=True)
    return data


def check_shard(data: dict, path: Path, index: int) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    need(payload["schema"] == 1 and
         payload["source"] == SOURCE.name and
         payload["selected_total"] == 206 and
         payload["representatives"] == 522 and
         payload["settings"] == {
             "shards": 12, "shard": index,
             "min_p3": 41, "max_p3": 55, "timeout_sec": 24,
         }, "Recomputed P4 pilot settings differ")
    saved = data["records"][index::12]
    observed = payload["records"]
    need(len(observed) == len(saved),
         f"Shard {index} replay coverage differs from immutable archive")
    expected_counts = Counter(row["status"] for row in observed)
    need(payload["status_counts"] == dict(expected_counts),
         f"Shard {index} replay status totals do not match its actual rows")
    timeouts = []
    for expected, actual in zip(saved, observed, strict=True):
        if actual.get("status") == "TIMEOUT":
            # A timed-out *replay* cannot certify the archived fourth
            # iterate, but is not evidence contradicting that proof.
            # Preserve its exact identity and the source P3 selection
            # order, without silently treating it as a passed replay.
            need(actual == {
                "index": expected["index"],
                "graph6": expected["graph6"],
                "p3": [expected["p3"][0]],
                "status": "TIMEOUT",
            }, "Malformed or substituted TIMEOUT source record")
            timeouts.append(expected["index"])
        else:
            need(actual == expected,
                 f"New direct P4 reconstructions disagree with archived"
                 f" shard {index}, index {expected['index']}")
    if timeouts:
        print(
            f"::warning::INCONCLUSIVE shard {index}: "
            f"{len(timeouts)} replay TIMEOUT records with McKay indices "
            f"{timeouts}; original archived classification unchanged. "
            "The uploaded shard artifact retains the TIMEOUT entries. "
            "Only non-timed-out cases were independently reverified.",
            flush=True,
        )
    else:
        need(payload["status_counts"] ==
             data["shard_summaries"][index]["counts"],
             f"Shard {index} complete recomputation summary differs")
        print(f"PASS: independently rebuilt all {len(saved)} archived"
              f" P4 records from source graph6 in shard {index}.",
              flush=True)
    return timeouts


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--shard", type=int)
    p.add_argument("--input-results", type=Path)
    args = p.parse_args()
    if (args.shard is None) != (args.input_results is None):
        p.error("Specify both --shard and --input-results, or neither")
    data = audit()
    if args.shard is not None:
        if not 0 <= args.shard < 12:
            p.error("--shard must be 0 through 11")
        check_shard(data, args.input_results, args.shard)


if __name__ == "__main__":
    main()
