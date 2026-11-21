#!/usr/bin/env python3
"""Merge independently replayed shards into exact McKay-indexed K^3-pared classes.

The reducer never trusts WL hashes or integer labels as isomorphism proofs:
every claimed source-to-representative bijection is checked edge by edge.
No graph is assigned a convergence or divergence verdict.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path

import networkx as nx
from classes import cases, complete_map, key


def require(condition, message):
    if not condition:
        raise ValueError(message)


def graph(g6):
    G = nx.from_graph6_bytes(g6.encode("ascii"))
    require(set(G) == set(range(len(G))), "Invalid graph6 vertex labels")
    return G


def check_map(source, target, mapping):
    require(len(source) == len(target), "Different graph orders in explicit map")
    require(len(mapping) == len(source), "Incomplete explicit map")
    require(sorted(mapping) == list(range(len(target))), "Non-bijective explicit map")
    for u in range(len(source)):
        for v in range(u + 1, len(source)):
            require(source.has_edge(u, v) == target.has_edge(mapping[u], mapping[v]),
                    "Invalid adjacency or nonadjacency under explicit map")


def merge(shard_files):
    paths = sorted(Path(p) for p in shard_files)
    require(len(paths) > 0, "No shard artifacts")
    source = dict(cases())  # authenticates original frozen v10 Git blob
    shards = len(paths)
    seen_shards = set()
    seen_indices = set()
    records = []
    skips = []

    for path in paths:
        data = json.loads(path.read_text())
        require(data.get("schema") == 1, "Unknown shard schema")
        require(data.get("source") == "indeterminate_order_10_v10.txt", "Unexpected source")
        summary = data["summary"]
        shard = summary["shard"]
        require(summary["sources"] == 1043 and summary["shards"] == shards,
                "Incorrect total source count or shard partition")
        require(isinstance(shard, int) and 0 <= shard < shards and shard not in seen_shards,
                "Missing or duplicate shard")
        seen_shards.add(shard)
        expected_indices = {idx for place, (idx, _) in enumerate(cases())
                            if place % shards == shard}
        batch_seen = set()
        for c in data["classes"]:
            members = c["members"]
            require(len(members) > 0, "Empty class in shard")
            local_rep = next((m for m in members if m["index"] == c["representative"]), None)
            require(local_rep is not None, "Missing shard representative")
            target = graph(local_rep["pared_graph6"])
            for m in members:
                i = m["index"]
                require(i in expected_indices and i not in seen_indices,
                        "Unexpected or repeated source McKay index")
                require(source[i] == m["graph6"], "Source graph6 disagrees with McKay archive")
                G = graph(m["pared_graph6"])
                require(m["stages"][-1]["level"] == 3
                        and m["stages"][-1]["pared"] == [len(G), G.number_of_edges()],
                        "Final fold provenance does not match saved graph")
                check_map(G, target, m["to_representative"])
                seen_indices.add(i)
                batch_seen.add(i)
                records.append((i, m, G))
        for s in data["skipped"]:
            i = s["index"]
            require(i in expected_indices and i not in seen_indices,
                    "Unexpected or repeated skipped McKay index")
            require(source[i] == s["graph6"], "Skipped source identity mismatch")
            require(s["reason"] in {"clique graph exceeds 250 vertices",
                                    "per-source deadline 8s exceeded"},
                    "Unknown skip reason")
            seen_indices.add(i)
            batch_seen.add(i)
            skips.append(s)
        require(batch_seen == expected_indices, "Incomplete shard partition")
        require(summary["selected"] == len(expected_indices)
                and summary["processed"] == len(batch_seen) - len(data["skipped"])
                and summary["skipped"] == len(data["skipped"]),
                "Shard totals mismatch")
    require(seen_shards == set(range(shards)) and seen_indices == set(source),
            "Incomplete original ten-vertex McKay partition")

    groups = defaultdict(list)
    for i, m, G in sorted(records, key=lambda item: item[0]):
        bucket = groups[key(G)]
        selected = None
        for entry in bucket:
            mapping = complete_map(G, entry["graph"])
            if mapping is not None:
                selected = (entry, mapping)
                break
        if selected is None:
            entry = {"representative": i, "graph": G, "members": []}
            bucket.append(entry)
            selected = (entry, list(range(len(G))))
        entry, mapping = selected
        check_map(G, entry["graph"], mapping)
        member = dict(m)
        member["to_representative"] = mapping
        entry["members"].append(member)

    classes = [{"representative": entry["representative"], "members": entry["members"]}
               for bucket in groups.values() for entry in bucket]
    classes.sort(key=lambda c: c["representative"])
    skips.sort(key=lambda s: s["index"])
    family = next((c for c in classes if c["representative"] == 7002338), None)
    require(family is not None and len(family["members"]) == 33,
            "Independent merged replay lost known 33-member class")
    summary = {
        "sources": 1043,
        "processed": len(records),
        "skipped": len(skips),
        "isomorphism_classes": len(classes),
        "nontrivial_classes": sum(len(c["members"]) > 1 for c in classes),
        "members_in_nontrivial": sum(len(c["members"]) for c in classes
                                      if len(c["members"]) > 1),
    }
    return {"schema": 2, "source": "indeterminate_order_10_v10.txt",
            "summary": summary, "classes": classes, "skipped": skips}


def verify_final(data, shard_files):
    # Check claimed maps directly before comparing with independent merge.
    for c in data["classes"]:
        rep = next((m for m in c["members"] if m["index"] == c["representative"]),
                   None)
        require(rep is not None, "Missing final representative")
        H = graph(rep["pared_graph6"])
        for m in c["members"]:
            check_map(graph(m["pared_graph6"]), H, m["to_representative"])
    require(data == merge(shard_files), "Final class artifact differs from exact merge")
    return data["summary"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("shards", nargs="+", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--verify", type=Path)
    args = p.parse_args()
    if args.verify:
        stored = json.loads(args.verify.read_text())
        print("VERIFIED_JSON " + json.dumps(verify_final(stored, args.shards), sort_keys=True))
    else:
        result = merge(args.shards)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
        print("SUMMARY_JSON " + json.dumps(result["summary"], sort_keys=True))
        for c in result["classes"]:
            if len(c["members"]) >= 3:
                print("CLASS_JSON " + json.dumps({
                    "representative": c["representative"],
                    "members": [m["index"] for m in c["members"]]
                }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
