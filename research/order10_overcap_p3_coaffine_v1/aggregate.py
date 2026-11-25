"""Independent replay of every bounded native coaffine pilot result."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import networkx as nx

from research.order10_overcap_p3_coaffine_v1.pilot import (
    PYCLIQUES_SHA, SHARDS, TEN_P3_OVERCAP, degree_obstruction,
    independent_coaffine_check, independent_octahedral_retraction_check,
    require, source_catalog,
)


def verify_shards(shards: list[Path]) -> dict:
    require(len(shards) == SHARDS, "Need five independent source shards")
    full = source_catalog()
    merged = {}
    seen = set()
    caps = set()
    for path in shards:
        item = json.loads(path.read_text(encoding="utf-8"))
        i = item["shard"]
        require(item.get("schema") == 1
                and item.get("kind") ==
                    "bounded_native_pycliques_coaffine_on_ten_oversized_P3"
                and item.get("monorepo_commit") == PYCLIQUES_SHA
                and item.get("full_current_p3_classes") == 521
                and item.get("oversized_p3_count") == 10
                and item.get("shards") == SHARDS
                and type(i) is int and 0 <= i < SHARDS
                and i not in seen,
                "Wrong native proof archive source/shard provenance")
        seen.add(i)
        caps.add((item["max_states"], item["time_limit_seconds_per_algorithm"]))
        wanted = sorted(TEN_P3_OVERCAP)[i::SHARDS]
        require([r["index"] for r in item["records"]] == wanted,
                "Source shard incorrectly assigned or incomplete")
        for record in item["records"]:
            idx = record["index"]
            src = full[idx]
            g = nx.from_graph6_bytes(src["p3_graph6"].encode("ascii"))
            require(record["original_graph6"] == src["graph6"]
                    and tuple(record["p3"]) == tuple(src["p3"])
                    and record["p3_graph6_sha256"] ==
                        hashlib.sha256(
                            src["p3_graph6"].encode("ascii")
                        ).hexdigest(),
                    "Native pilot graph6 or full input SHA differs")
            require(record["complement_components"] ==
                    nx.number_connected_components(nx.complement(g)),
                    "Complement connected components changed")
            require(record["no_coaffine_automorphism"] is True
                    and record["degree_obstruction"] == degree_obstruction(g),
                    "Missing degree obstruction to every coaffine automorphism")
            general = record["coaffine_weak_endomorphism"]
            octa = record["octahedral_retraction"]
            require(general["status"] in {
                "FOUND", "EXHAUSTED", "LIMIT_REACHED"
            }, "Inadmissible general search result")
            require(all(type(general[k]) is int and general[k] >= 0
                        for k in (
                            "states_explored", "assignments_tried",
                            "arc_revisions",
                        )), "Malformed general CSP counters")
            if general["status"] == "FOUND":
                m = general["map"]
                require(isinstance(m, list) and len(m) == len(g),
                        "Missing complete general endomorphism map")
                independent_coaffine_check(
                    g, dict(enumerate(m))
                )
            else:
                require("map" not in general,
                        "Unexpected purported witness for limit/absence")
            if general["status"] == "EXHAUSTED":
                require(octa["status"] ==
                        "EXCLUDED_BY_EXHAUSTIVE_COAFFINE_SEARCH",
                        "A coaffine EXHAUSTED result cannot have O_d retract")
            else:
                require(octa["status"] in {
                    "FOUND", "EXHAUSTED", "LIMIT_REACHED"
                }, "Malformed octahedral search result")
                if octa["status"] == "FOUND":
                    pairs = [tuple(p) for p in octa["antipodal_pairs"]]
                    ret = dict(enumerate(octa["retraction_map"]))
                    independent_octahedral_retraction_check(g,pairs,ret)
                    require(octa["dimension"] == len(pairs),
                            "Wrong proved octahedron dimension")
                else:
                    require("retraction_map" not in octa,
                            "Inconclusive octahedral attempt invented a map")
            require(idx not in merged, "Duplicated P3 host certificate")
            merged[idx] = record
    require(seen == set(range(SHARDS)) and len(merged) == 10
            and len(caps) == 1,
            "Missing shards, duplicated sources, or mismatched budgets")
    status_counts = {}
    for kind, key in [
        ("coaffine", "coaffine_weak_endomorphism"),
        ("octahedral", "octahedral_retraction"),
    ]:
        statuses = [v[key]["status"] for v in merged.values()]
        status_counts[kind] = {
            s: statuses.count(s) for s in sorted(set(statuses))
        }
    return {
        "schema": 1,
        "kind": "authenticated_full_ten_p3_native_coaffine_pilot",
        "pin": PYCLIQUES_SHA,
        "budget": sorted(caps)[0],
        "original_indices": sorted(merged),
        "all_ten_exclude_coaffine_automorphisms": True,
        "general_results": status_counts["coaffine"],
        "octahedral_results": status_counts["octahedral"],
        "octahedral_positive_witness_indices": [
            i for i in sorted(merged)
            if merged[i]["octahedral_retraction"]["status"] == "FOUND"
        ],
        "no_census_classification_changes": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    opts = parser.parse_args()
    report = verify_shards(sorted(opts.directory.glob("shard-*.json")))
    opts.output.write_text(json.dumps(report, sort_keys=True, indent=2)
                           + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
