"""Authenticated index of surviving P3 classes for a broad coaffine pilot.

Reuses the pre-existing 521-class independent reconstructed P3 catalog
and the proven global P3 isomorphisms. No new clique-graph implementation,
no census classification edits, no inference from resource limits.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("Do not optimize away exact index assertions")

import networkx as nx

from research.order10_p4_crossdepth_o15_v25.verify import git_blob, source_rows
from research.order10_full_nine_reference_v1.index import hosts

ROOT = Path(__file__).resolve().parents[2]
TEN_V28 = ROOT / "indeterminate_order_10_v28.txt"
TEN_V28_BLOB = "35bb83b56bb8b4fd453b0ba272d354dc6b42e68c"
GLOBAL_INDEX = ROOT / "research/order10_p3_global_v23_index/certificates.json"
GLOBAL_INDEX_BLOB = "ab5a9f1c075dfad63b111929368147884519f2a3"
P3_OVERSIZED = {11505012, 11595632, 11709142}
P3_UNRECONSTRUCTED = {11708967, 11715667, 11716441}
SHARDS = 8


def need(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def build_index() -> dict:
    need(git_blob(TEN_V28.read_bytes()) == TEN_V28_BLOB,
         "Authoritative immutable ten-v28 source was modified")
    need(git_blob(GLOBAL_INDEX.read_bytes()) == GLOBAL_INDEX_BLOB,
         "Historical exact P3 class certificates were modified")
    rows = source_rows(TEN_V28)
    need(len(rows) == 1043, "Unexpected current ten-v28 original population")
    stiff = {i: fields.split()[2] for i, fields in rows.items()
             if fields.split()[1] == "10"}
    need(len(stiff) == 613, "Unexpected stiff original population")
    original = hosts()  # complete pinned historical 521-class P3 reconstruction
    need(len(original["records"]) == 521,
         "Historical reference P3 inventory changed")

    existing = []
    for item in original["records"]:
        remaining = [m for m in item["members"] if m in stiff]
        need(len(remaining) in (0, len(item["members"])),
             "A certified historical third-iterate class was fragmented")
        if not remaining:
            continue
        need(item["index"] in stiff
             and all(stiff[m] == rows[m].split()[2] for m in remaining),
             "Unexpected survivor original graph6 or representative")
        need(item["graph6"] == stiff[item["index"]]
             and item["members"] == remaining,
             "Authenticated historical host does not match ten-v28 original")
        G = nx.from_graph6_bytes(item["p3_graph6"].encode("ascii"))
        need((len(G), G.number_of_edges()) == tuple(item["p3"]),
             "P3 graph6 dimensions changed")
        existing.append(item)

    need(len(existing) == 514
         and sum(len(x["members"]) for x in existing) == 610,
         "Surviving v28 class count is not 514 / 610")
    unindexed = set(stiff) - {
        member for x in existing for member in x["members"]
    }
    need(unindexed == P3_UNRECONSTRUCTED,
         "Wrong historical third-iterate source reconstruction limits")
    ignored = [x for x in existing if x["index"] in P3_OVERSIZED]
    require_big = {x["index"] for x in ignored}
    need(require_big == P3_OVERSIZED
         and sum(len(x["members"]) for x in ignored) == 4,
         "Wrong oversized P3 class membership")

    pilot = [x for x in existing if x["index"] not in P3_OVERSIZED]
    need(len(pilot) == 511
         and sum(len(x["members"]) for x in pilot) == 606,
         "Wrong coaffine pilot cohort of 511 classes / 606 originals")
    for rec in pilot:
        rec["p3_graph6_sha256"] = hashlib.sha256(
            rec["p3_graph6"].encode("ascii")
        ).hexdigest()
    return {
        "schema": 1,
        "kind": "current_ten_v28_511_reconstructed_P3_class_coaffine_pilot",
        "ten_v28_blob": TEN_V28_BLOB,
        "historical_P3_class_blob": GLOBAL_INDEX_BLOB,
        "surviving_exact_P3_classes": 514,
        "originals_in_certified_classes": 610,
        "pilot_classes": 511,
        "pilot_originals": 606,
        "excluded_resource_limited_P3_representatives": sorted(P3_OVERSIZED),
        "excluded_resource_limited_P3_originals": sorted({
            m for x in ignored for m in x["members"]
        }),
        "historically_unreconstructed_P3_originals": sorted(P3_UNRECONSTRUCTED),
        "shards": SHARDS,
        "records": pilot,
        "no_classification_changes": True,
    }


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = build_index()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print("PASS: exact current ten-v28 P3 coaffine source index "
          "511 classes covering 606 unresolved stiff originals", flush=True)


if __name__ == "__main__":
    main()
