"""Proof-positive sharded index of historically proved nine-vertex K-divergences.

All historical input evidence comes from the existing authenticated census
reader and immutable nine-v1/v2/v3/v9 snapshots. No graph is promoted based
on a signature, a timeout, or an unverified historical conjecture.

Commands: inventory, hosts, shard, aggregate.
Run from the repository root.  This script does not modify census indices.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import signal
import sys

import networkx as nx

if sys.flags.optimize:
    raise RuntimeError("Optimized Python is forbidden in a proof workflow")

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))

from research.order10_p3_global_v23_index.independent_verify import (
    independent_p3, independent_pare, independent_clique_graph,
)
from research.order10_p3_global_v23_index.classes import fingerprint as p3_fingerprint

PROVENANCE = {
    "indeterminate_order_9_v1.txt":
        "4f210949dad5e7350fc0185c34738e2bf46f9012",
    "indeterminate_order_9_v2.txt":
        "0a18b1a67434e0995e768b175878a5875bff7de1",
    "indeterminate_order_9_v3.txt":
        "446cbb0be5f40b6014cdb530b1a314de95ff72b2",
    "indeterminate_order_9_v9.txt":
        "d18a7a843be935f3a7fe911691dd1c86dac2addd",
    "indeterminate_order_10_v25.txt":
        "d31d52d28427adcef6055cc1d277565fe88f32d5",
    "research/order10_p3_global_v23_index/certificates.json":
        "ab5a9f1c075dfad63b111929368147884519f2a3",
}

EXPECTED_HISTORICAL = {
    "initial": 10096, "c10": 4, "bound60": 1, "bound70": 3,
}
EXPECTED_PROMOTIONS = (5, 36, 10)
SKIP_LIMIT = 5000
MAX_INTERMEDIATE = 250


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def archive(path: str) -> bytes:
    require(path in PROVENANCE, "Unrecognized proof input path")
    raw = (ROOT / path).read_bytes()
    require(blob(raw) == PROVENANCE[path],
            f"Previously certified source was modified: {path}")
    return raw


def write(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def graph6(graph: nx.Graph) -> str:
    return nx.to_graph6_bytes(
        nx.convert_node_labels_to_integers(graph, ordering="sorted"),
        header=False
    ).decode("ascii").strip()


def from_g6(g6: str) -> nx.Graph:
    require(isinstance(g6, str) and g6.isascii(), "Invalid graph6 text")
    return nx.from_graph6_bytes(g6.encode("ascii"))


def dimensions(graph: nx.Graph) -> tuple[int, int]:
    return len(graph), graph.number_of_edges()


def rows(path: str) -> dict[int, tuple[int, str]]:
    result = {}
    for line in archive(path).decode("ascii").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        require(
            len(fields) == 6,
            f"Incorrect frozen unresolved record in {path}",
        )
        index = int(fields[0])
        require(index not in result, "Duplicate nine-original McKay index")
        order = int(fields[1])
        graph = from_g6(fields[2])
        require(len(graph) == order and order in (8, 9),
                "Wrong frozen nine-core size")
        result[index] = (order, fields[2])
    require(list(result) == sorted(result), "Noncanonical frozen source")
    return result


def inventory() -> dict:
    # This is the existing authenticated 261,080-original order-nine reader,
    # not an ad hoc reinterpretation of the historical verdict strings.
    import historical_divergent_targets_v1 as historical

    counts = Counter()
    items = []
    for source, graph in historical.historic_inputs():
        stage = source["stage"]
        counts[stage] += 1
        require(stage in EXPECTED_HISTORICAL
                and len(graph) == source["order"]
                and graph6(graph) == source["graph6"],
                "Historical original identity or positive provenance differs")
        items.append({
            "original_order": source["order"],
            "original_index": source["index"],
            "graph6": source["graph6"],
            "provenance": "historical_" + stage,
            "reference_is_pared": False,
        })
    require(dict(counts) == EXPECTED_HISTORICAL
            and len(items) == 10104, "Incomplete historical divergent cohort")

    versions = [rows(f"indeterminate_order_9_v{i}.txt")
                for i in (1, 2, 3, 9)]
    for step, (before, after) in enumerate(zip(versions, versions[1:])):
        lost = sorted(set(before) - set(after))
        require(len(lost) == EXPECTED_PROMOTIONS[step]
                and all(before[k] == after[k] for k in after),
                "Nine-vertex promotion chain is not the certified one")
        for index in lost:
            order, g6 = before[index]
            items.append({
                "original_order": 9, "original_index": index,
                "graph6": g6,
                "provenance": ("proved_nine_promotion_v1_v2",
                               "proved_nine_promotion_v2_v3",
                               "proved_nine_promotion_v3_v9")[step],
                "reference_is_pared": True,
                "pared_order": order,
            })
    require(len(items) == 10155
            and len(set((x["original_order"], x["original_index"])
                        for x in items)) == 10155,
            "Duplicate or missing authenticated divergent original")
    items.sort(key=lambda x: (x["original_order"], x["original_index"]))
    return {
        "schema": 1,
        "kind": "authenticated_historical_divergent_nine_reference_inventory",
        "counts": {**EXPECTED_HISTORICAL,
                   "later_proved_promotions": sum(EXPECTED_PROMOTIONS),
                   "total": 10155},
        "frozen_git_blobs": PROVENANCE,
        "sources": items,
    }


def hosts() -> dict:
    # Reuse the complete immutable exact 10-v23 P3 class archive.  Current
    # ten-v25, not ten-v23, determines which representatives survive.
    ten = {}
    for line in archive("indeterminate_order_10_v25.txt").decode().splitlines():
        if line and not line.startswith("#"):
            fields = line.split()
            require(len(fields) == 6, "Malformed ten-v25 source")
            if fields[1] == "10":
                ten[int(fields[0])] = fields[2]
    require(len(ten) == 622, "Incorrect surviving stiff-ten cohort")
    old = json.loads(archive(
        "research/order10_p3_global_v23_index/certificates.json"
    ))
    rep_to_members = {
        grp["representative"]: [m["index"] for m in grp["members"]]
        for grp in old["nontrivial_classes"]
    }
    for i in old["singleton_indices"]:
        rep_to_members[i] = [i]
    representatives = sorted(i for i in rep_to_members if i in ten)
    require(len(representatives) == 521,
            "Unexpected surviving v25 exact P3 classes")
    records = []
    for i in representatives:
        members = rep_to_members[i]
        require(all(m in ten for m in members),
                "Global P3 original class unexpectedly fragmented")
        g = independent_p3(ten[i])
        records.append({
            "index": i,
            "graph6": ten[i],
            "p3_graph6": graph6(g),
            "p3": dimensions(g),
            "members": members,
        })
    require(sum(len(r["members"]) for r in records) == 619,
            "Incorrect P3 equivalence class population")
    return {
        "schema": 1,
        "kind": "surviving_521_complete_p3_classes_from_immutable_global_archive",
        "ten_v25_blob": PROVENANCE["indeterminate_order_10_v25.txt"],
        "global_p3_blob": PROVENANCE[
            "research/order10_p3_global_v23_index/certificates.json"],
        "records": records,
    }


def signature(g: nx.Graph) -> tuple:
    # Necessary invariant only; matches never establish an isomorphism.
    return p3_fingerprint(g)


class MatchingLimit(Exception):
    pass


def exact_map(graph: nx.Graph, target: nx.Graph, seconds: float = 3.0
              ) -> list[int] | None:
    """Full isomorphism with strict TIME_LIMIT status; no false negatives."""
    if signature(graph) != signature(target):
        return None
    if graph6(graph) == graph6(target):
        return list(range(len(graph)))
    def interrupt(_s, _f):
        raise MatchingLimit("Exact GraphMatcher hit the explicit time limit")
    old = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, interrupt)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        matcher = nx.algorithms.isomorphism.GraphMatcher(
            nx.complement(graph), nx.complement(target)
        )
        if not matcher.is_isomorphic():
            return None
        mapping = matcher.mapping
        result = [mapping[i] for i in range(len(graph))]
        require(sorted(result) == list(range(len(graph))),
                "Incomplete positive permutation")
        require(all(
            graph.has_edge(u, v)
            == target.has_edge(result[u], result[v])
            for u in graph for v in graph
        ), "Saved positive map fails an edge or nonedge")
        return result
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)


def next_pared(g: nx.Graph, level: int) -> nx.Graph:
    require(len(g) <= MAX_INTERMEDIATE,
            f"Intermediate order {len(g)} exceeds {MAX_INTERMEDIATE}")
    try:
        # Reuse independently cross-checked BK / NetworkX enumerators.
        # These are bounded at 750 facets; LIMIT is inconclusive.
        return independent_pare(independent_clique_graph(
            g, stage=level, orders=[len(g)]
        ))
    except Exception as exc:
        if type(exc).__name__ in ("LimitHit", "TooManyCliques"):
            raise MatchingLimit(str(exc)) from exc
        raise


def scan(items: dict, host_data: dict, shard: int, shards: int) -> dict:
    require(items["schema"] == host_data["schema"] == 1
            and items["counts"]["total"] == 10155
            and len(host_data["records"]) == 521,
            "Malformed authenticated input artifacts")
    require(0 <= shard < shards and 1 <= shards <= 64,
            "Invalid reference shard")
    host_buckets = defaultdict(list)
    for row in host_data["records"]:
        graph = from_g6(row["p3_graph6"])
        require(dimensions(graph) == tuple(row["p3"]),
                "Host pre-computed P3 signature changed")
        host_buckets[signature(graph)].append((row["index"], graph))
    source_subset = [
        source for pos, source in enumerate(items["sources"])
        if pos % shards == shard
    ]
    buckets = defaultdict(list)
    unique = []
    skipped = []
    matches = []
    unresolved_pairs = []
    checked = Counter()
    # P0 root bucketing is an optimization: every original has its
    # complete and individually verified isomorphism to its representative.
    for source in source_subset:
        root = independent_pare(from_g6(source["graph6"]))
        root_key = signature(root)
        record = next(
            (entry for entry in buckets[root_key]
             if nx.is_isomorphic(root, entry["root"])), None
        )
        if record is None:
            record = {"root": root, "sources": []}
            unique.append(record)
            buckets[root_key].append(record)
        record["sources"].append(source)

    for rec in unique:
        graph = rec["root"]
        provenance = rec["sources"]
        for depth in range(4):
            if depth:
                try:
                    graph = next_pared(graph, depth)
                except (MatchingLimit, AssertionError) as exc:
                    skipped.append({
                        "representative_source": provenance[0],
                        "failed_depth": depth,
                        "reason": type(exc).__name__ + ": " + str(exc),
                        "source_count": len(provenance),
                    })
                    break
            checked[f"P{depth}"] += 1
            possible = host_buckets.get(signature(graph), [])
            for index, target in possible:
                try:
                    mapping = exact_map(graph, target)
                except MatchingLimit:
                    unresolved_pairs.append({
                        "representative_source": provenance[0],
                        "depth": depth, "ten_rep": index,
                        "status": "TIME_LIMIT_INCONCLUSIVE",
                    })
                    continue
                if mapping is not None:
                    matches.append({
                        "source": provenance[0],
                        "all_equal_P0_sources": provenance,
                        "reference_depth": depth,
                        "reference_iterate_graph6": graph6(graph),
                        "ten_p3_class_rep": index,
                        "source_to_ten_p3_map": mapping,
                        "p3_dimensions": dimensions(graph),
                    })
                    print(
                        "POSITIVE", provenance[0]["original_index"],
                        "at P", depth, "to ten", index,
                        "class; source cohort", len(provenance),
                        flush=True,
                    )
    return {
        "schema": 1, "shard": shard, "shards": shards,
        "source_original_count": len(source_subset),
        "different_P0_isomorphism_classes": len(unique),
        "levels_checked": dict(checked),
        "skips": skipped,
        "unresolved_candidate_comparisons": unresolved_pairs,
        "positives": matches,
        "scope": "Positive-only, per-shard P0 root dedup; no negative behavior verdict",
    }


def aggregate(inventory_data: dict, host_data: dict, results: list[dict]
              ) -> dict:
    expected = sorted(range(len(results)))
    require(sorted(x["shard"] for x in results) == expected
            and {x["shards"] for x in results} == {len(results)}
            and sum(x["source_original_count"] for x in results) == 10155,
            "Missing or duplicated historical inventory shard")
    sources = {
        (s["original_order"], s["original_index"]): s
        for s in inventory_data["sources"]
    }
    hosts_index = {r["index"]: r for r in host_data["records"]}
    verified = []
    for result in results:
        for record in result["positives"]:
            source = record["source"]
            key = (source["original_order"], source["original_index"])
            require(key in sources and sources[key] == source,
                    "Positive witness does not belong to certified source")
            require(record["ten_p3_class_rep"] in hosts_index,
                    "Positive references missing ten-v25 P3 representative")
            graph = independent_pare(from_g6(source["graph6"]))
            for stage in range(1, record["reference_depth"] + 1):
                graph = next_pared(graph, stage)
            target = independent_p3(hosts_index[
                record["ten_p3_class_rep"]]["graph6"])
            mapping = record["source_to_ten_p3_map"]
            require(
                dimensions(graph) == tuple(record["p3_dimensions"])
                and graph6(graph) == record["reference_iterate_graph6"]
                and len(mapping) == len(graph) == len(target)
                and sorted(mapping) == list(range(len(graph)))
                and all(
                    graph.has_edge(u, v)
                    == target.has_edge(mapping[u], mapping[v])
                    for u in graph for v in graph
                ),
                "Aggregated positive proof fails full independent replay",
            )
            verified.append(record)
    return {
        "schema": 1, "kind": "verified_positive_cross_depth_P3_reference_matches",
        "historical_proved_reference_count": len(inventory_data["sources"]),
        "ten_p3_class_count": len(host_data["records"]),
        "shard_count": len(results),
        "source_p0_classes_within_shards": sum(
            x["different_P0_isomorphism_classes"] for x in results),
        "reconstruction_resource_limits": sum(len(x["skips"]) for x in results),
        "comparison_time_limits": sum(
            len(x["unresolved_candidate_comparisons"]) for x in results),
        "positive_matches": verified,
        "proven_ten_original_indices": sorted({
            member for positive in verified
            for member in hosts_index[
                positive["ten_p3_class_rep"]]["members"]
        }),
        "does_not_prove_nondivergence": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("inventory", "hosts",
                                          "shard", "aggregate"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--hosts", type=Path)
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--shards", type=int, default=8)
    parser.add_argument("--results", type=Path)
    opts = parser.parse_args()
    if opts.action == "inventory":
        answer = inventory()
    elif opts.action == "hosts":
        answer = hosts()
    elif opts.action == "shard":
        require(opts.inventory is not None and opts.hosts is not None,
                "Worker requires both authenticated indexes")
        answer = scan(read(opts.inventory), read(opts.hosts),
                      opts.shard, opts.shards)
    else:
        require(opts.inventory is not None and opts.hosts is not None
                and opts.results is not None,
                "Aggregator needs both indexes and result folder")
        result_files = sorted(opts.results.glob("shard-*.json"))
        require(len(result_files) == opts.shards,
                "Not all reference shards completed")
        answer = aggregate(
            read(opts.inventory), read(opts.hosts),
            [read(path) for path in result_files]
        )
    write(opts.output, answer)
    print(json.dumps({
        "action": opts.action,
        "sources": (len(answer.get("sources", []))
                    or answer.get("source_original_count")
                    or answer.get("historical_proved_reference_count")),
        "hosts": len(answer.get("records", []))
                 or answer.get("ten_p3_class_count"),
        "positive": len(answer.get("positives", []))
                    or len(answer.get("positive_matches", [])),
        "limits": len(answer.get("skips", []))
                  or answer.get("reconstruction_resource_limits"),
        "artifact": str(opts.output),
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
