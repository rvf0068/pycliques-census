"""Reproducible, positive-only P4 certification for 203 ten-vertex cores.

No root census files or K-behavior classifications are modified.
Every original graph6 is authenticated against the frozen ten-v25 list,
the global P3 index, and the independently certified 210+98 P4 archives.
The ten remaining P3 classes are checked to exceed the explicitly
declared 6,000-facet fourth-stage budget.

Usage:
    python -m research.order10_p4_203_ears_v1.verify audit
    python -m research.order10_p4_203_ears_v1.verify primary --shard 0 --shards 4 --output /tmp/primary-0.json
    python -m research.order10_p4_203_ears_v1.verify aggregate --primary-dir /tmp/primary --independent-dir /tmp/independent
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import itertools
import json
from pathlib import Path
import re
import sys

if sys.flags.optimize:
    raise RuntimeError("Optimized execution bypasses P4 proof assertions")

import networkx as nx

from research.order10_full_nine_reference_v1 import index as refs
from research.order10_full_nine_p4_crossdepth_v1.search import (
    host_catalog as prior_210,
)
from research.order10_small_p4_98_v1.verify import (
    verify_record as replay_primary_p4,
)

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

BLOBS = {
    "research/order10_p4_203_ears_v1/p4_reconstructions.json":
        "83b0f9a6e0e5078eb47a7c49bd7d254e1441e81a",
    "research/order10_p4_203_ears_v1/ear_retractions.json":
        "fa34f82eb854984c7b2a4a31a6ce731af0436da0",
    "research/order10_small_p4_98_v1/exploratory_results.json":
        "68c3d3d196e4e19f1612a09a1e196df8aa4e1852",
    "indeterminate_order_9_v9.txt":
        "d18a7a843be935f3a7fe911691dd1c86dac2addd",
    "indeterminate_order_10_v25.txt":
        "d31d52d28427adcef6055cc1d277565fe88f32d5",
    "research/snub_ear_all_iterates_homotopy_v1.md":
        "d4f15e72928821f8623b3106c13b9f63e1bcefac",
}

TEN_P3_OVERCAP = (
    11367777, 11505012, 11595632, 11611429, 11623375,
    11656793, 11708546, 11709142, 11713770, 11713984,
)
FACET_LIMIT = 6000
EXPECTED_EAR_TARGETS = (251628, 260040)


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise AssertionError(reason)


def frozen(path: str) -> bytes:
    require(path in BLOBS, "Unrecognized immutable source path")
    raw = (ROOT / path).read_bytes()
    require(refs.blob(raw) == BLOBS[path],
            "Immutable Git blob identity mismatch: " + path)
    return raw


def validated_catalog() -> tuple[list[dict], dict[int, dict]]:
    """Check exact disjoint 210 + 98 + 203 + 10 partition of 521 P3 classes."""
    archive = json.loads(frozen(
        "research/order10_p4_203_ears_v1/p4_reconstructions.json"
    ))
    require(archive.get("schema") == 1
            and archive.get("source") ==
                "PR96 archived exact P3 host index and independently crosschecked local fourth-facet enumeration"
            and archive.get("coverage") ==
                "203 of the remaining 213 ten-P3 representative classes with P3 >=56"
            and len(archive.get("records", [])) == 203,
            "Wrong 203-case exploratory archive header or cardinality")

    # Rebuild all 521 P3 hosts from frozen originals and independent
    # third-stage clique enumeration. This is NOT a borrowed notebook list.
    frozen("indeterminate_order_10_v25.txt")
    hosts = refs.hosts()
    require(hosts["schema"] == 1 and len(hosts["records"]) == 521,
            "Historical 521-host P3 reconstruction changed")
    byhost = {r["index"]: r for r in hosts["records"]}
    require(len(byhost) == 521,
            "P3 host-index contains duplicate McKay representatives")

    old = prior_210()
    old_ids = {r["index"] for r in old["records"]}
    require(len(old_ids) == 210,
            "Prior certified 210 fourth-iterate cohort changed")
    small = json.loads(frozen(
        "research/order10_small_p4_98_v1/exploratory_results.json"
    ))
    small_ids = {r["index"] for r in small["records"]}
    require(len(small_ids) == 98 and
            all(i in byhost and byhost[i]["graph6"] == r["graph6"]
                and tuple(byhost[i]["p3"]) == tuple(r["p3"])
                and r["p3"][0] <= 40 for i, r in
                ((r["index"], r) for r in small["records"])),
            "Frozen 98-case predecessor does not match current P3 host index")

    records = archive["records"]
    ids = [r["index"] for r in records]
    require(ids == sorted(set(ids)),
            "The 203-case indices are not sorted and pairwise distinct")
    new_ids = set(ids)
    skipped = set(TEN_P3_OVERCAP)
    require(not (new_ids & old_ids or new_ids & small_ids or
                 old_ids & small_ids) and
            set(byhost) == old_ids | small_ids | new_ids | skipped and
            len(skipped) == 10,
            "The 521 original P3 classes do not split exactly as 210+98+203+10")
    require(all(r["p3"][0] >= 56 for r in records),
            "Unexpected fourth-stage P3 order below the expected window")

    older_dims = {tuple(r["p4"]) for r in old["records"]}
    older_dims.update(tuple(r["p4"]) for r in small["records"])
    require(all(tuple(r["p4"]) not in older_dims for r in records),
            "A new P4 signature repeats a previously certified 210/98 host")

    for rec in records:
        idx = rec["index"]
        h = byhost[idx]
        require(
            rec["graph6"] == h["graph6"]
            and tuple(rec["p3"]) == tuple(h["p3"])
            and type(rec["facets"]) is int and 0 < rec["facets"] <= 2500
            and rec["facets"] == rec["raw_p4"][0]
            and len(rec["p4"]) == len(rec["raw_p4"]) == 2
            and 0 < rec["p4"][0] <= rec["raw_p4"][0]
            and re.fullmatch(r"[0-9a-f]{64}", rec["p4_adj_sha256"])
            and isinstance(rec["fold_rounds"], list)
            and all(type(x) is int and x > 0 for x in rec["fold_rounds"])
            and sum(rec["fold_rounds"]) == rec["raw_p4"][0] - rec["p4"][0],
            "Archived P4 shape, root graph6 or folding-round coverage invalid "
            f"at McKay {idx}",
        )

    # No numerical verdict from a clique resource cap; this witnesses
    # explicitly that each excluded P3 yields >6000 fourth-stage facets.
    for i in TEN_P3_OVERCAP:
        h = byhost[i]
        g = nx.from_graph6_bytes(h["p3_graph6"].encode("ascii"))
        require([len(g), g.number_of_edges()] == list(h["p3"]),
                "The excluded P3 is not authenticated by its saved graph6")
        count = sum(1 for _ in itertools.islice(
            nx.find_cliques(g), FACET_LIMIT + 1
        ))
        require(count == FACET_LIMIT + 1,
                f"Excluded P4 input {i} does not exceed the 6000 facet cap")

    require(Counter(
        "56_60" if r["p3"][0] <= 60 else
        "61_80" if r["p3"][0] <= 80 else
        "over_80" for r in records
    ) == {"56_60": 144, "61_80": 58, "over_80": 1},
            "Unexpected 144/58/1 new P4 coverage")
    require(max(x["facets"] for x in records) == 2223,
            "The highest fourth-stage clique count changed")
    return records, byhost


def degree_profile(rows: list[int]) -> list[list[int]]:
    counts = Counter(x.bit_count() for x in rows)
    return [[degree, counts[degree]] for degree in sorted(counts)]


def verify_shard(shard: int, shards: int, *,
                 method: str = "primary") -> dict:
    require(0 <= shard < shards <= 32, "Invalid deterministic shard")
    require(method in {"primary", "independent"},
            "Invalid full-reconstruction method")
    cases, _ = validated_catalog()
    shared_dimensions = Counter(tuple(r["p4"]) for r in cases)
    if method == "independent":
        from research.order10_p4_203_ears_v1.independent_verify import (
            replay_independent_p4,
        )
        replayer = replay_independent_p4
    else:
        replayer = replay_primary_p4

    reports = []
    for r in cases[shard::shards]:
        _raw, pared = replayer(r)
        observed = {
            "index": r["index"],
            "p4": r["p4"],
            "p4_adj_sha256": r["p4_adj_sha256"],
        }
        if shared_dimensions[tuple(r["p4"])] > 1:
            observed["degree_profile"] = degree_profile(pared)
        reports.append(observed)
        print(f"REPLAY {method} shard={shard}/{shards} "
              f"McKay={r['index']} P4={r['p4'][0]}", flush=True)
    return {
        "schema": 1,
        "kind": "replayed_203_ten_P4_full_adjacency",
        "method": method,
        "shard": shard, "shards": shards,
        "records": reports,
    }


def aggregate(primary_files: list[Path],
              independent_files: list[Path]) -> dict:
    cases, _ = validated_catalog()
    expected = {r["index"]: r for r in cases}
    require(len(primary_files) == len(independent_files) == 4,
            "Exactly four files from each reconstruction route required")
    allmethods = {}
    for method, paths in (("primary", primary_files),
                          ("independent", independent_files)):
        seen = {}
        require(len(paths) == 4, "Missing fourth-stage verification shard")
        for path in paths:
            result = json.loads(path.read_text(encoding="utf-8"))
            s = result["shard"]
            require(
                result["schema"] == 1
                and result["kind"] == "replayed_203_ten_P4_full_adjacency"
                and result["method"] == method
                and result["shards"] == 4 and 0 <= s < 4
                and [r["index"] for r in result["records"]] ==
                    [r["index"] for r in cases[s::4]],
                "Wrong or misassigned fourth-stage reconstruction shard")
            require(s not in seen, "Duplicate fourth-stage shard")
            seen[s] = result["records"]
        require(set(seen) == {0, 1, 2, 3},
                "Missing fourth-stage shard index")
        flat = [r for group in seen.values() for r in group]
        require(len(flat) == len(expected) == 203,
                "Missing fourth-stage graphs")
        allmethods[method] = {r["index"]: r for r in flat}

    collisions = defaultdict(list)
    for idx, row in expected.items():
        first = allmethods["primary"][idx]
        second = allmethods["independent"][idx]
        require(
            first == second or
            (first["index"] == second["index"] == idx
             and first["p4"] == second["p4"] == row["p4"]
             and first["p4_adj_sha256"]
                 == second["p4_adj_sha256"] == row["p4_adj_sha256"]
             and first.get("degree_profile") ==
                 second.get("degree_profile")),
            f"The two independent full P4 results disagree for {idx}")
        require(first["p4"] == row["p4"]
                and first["p4_adj_sha256"] == row["p4_adj_sha256"],
                "A P4 replay did not reproduce the pinned archive")
        collisions[tuple(row["p4"])].append(idx)

    repeated = [g for g in collisions.values() if len(g) > 1]
    require(len(repeated) == 7
            and sorted(len(g) for g in repeated) ==
                [2, 2, 2, 2, 3, 7, 7],
            "The seven repeated P4 size-pair groups changed")
    for group in repeated:
        signatures = [
            allmethods["primary"][i].get("degree_profile") for i in group
        ]
        require(all(x is not None for x in signatures)
                and len({json.dumps(x) for x in signatures}) == len(group),
                "Equal P4 dimensions without a degree-sequence obstruction")
    result = {
        "schema": 1,
        "kind": "independently_dual_replayed_203_fourth_pared_clique_graphs",
        "current_P3_representatives": 521,
        "earlier_210_P4": 210,
        "earlier_98_P4": 98,
        "new_exact_P4": 203,
        "remaining_P3_classes_over_6000_facets": list(TEN_P3_OVERCAP),
        "complete_P4_coverage": 511,
        "all_203_pairwise_nonisomorphic": True,
        "no_shared_dimensions_with_prior_308_P4": True,
        "repeated_dimension_groups": [sorted(g) for g in repeated],
        "no_K_behaviour_promotions": True,
    }
    print(json.dumps(result, sort_keys=True, indent=2))
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=("audit", "primary", "independent",
                                       "aggregate"))
    p.add_argument("--shard", type=int, default=0)
    p.add_argument("--shards", type=int, default=4)
    p.add_argument("--output", type=Path)
    p.add_argument("--primary-dir", type=Path)
    p.add_argument("--independent-dir", type=Path)
    options = p.parse_args()
    if options.action == "audit":
        r, h = validated_catalog()
        print(f"AUTHENTICATED: {len(r)} complete P4 input claims, "
              f"{len(h)} certified P3 hosts, exactly ten over-cap inputs")
        return
    if options.action in ("primary", "independent"):
        require(options.output is not None, "Expected shard output path")
        data = verify_shard(options.shard, options.shards,
                            method=options.action)
    else:
        require(options.output is not None
                and options.primary_dir is not None
                and options.independent_dir is not None,
                "Expected complete primary/independent replay directories")
        data = aggregate(
            sorted(options.primary_dir.glob("shard-*.json")),
            sorted(options.independent_dir.glob("shard-*.json")),
        )
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(
        json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
