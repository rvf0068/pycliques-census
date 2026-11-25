"""Positive-only full nine-reference versus certified ten-P4 cross-depth screen.

This extends the existing authenticated historical source inventory and the
exact current ten-P3 class index without modifying original census results.
All positive results use fully reconstructed graph isomorphisms; failed caps,
timeouts and missing stages are explicit inconclusive outcomes.

Commands:
    hosts --output /tmp/p4-hosts.json
    shard --inventory /tmp/inventory.json --hosts /tmp/p4-hosts.json
          --shards 8 --shard 0 --output /tmp/shards/shard-0.json
    aggregate --inventory ... --hosts ... --results /tmp/shards
              --shards 8 --output /tmp/replay.json
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

import networkx as nx

if sys.flags.optimize:
    raise RuntimeError("Optimized Python is forbidden in a proof workflow")

from research.order10_full_nine_reference_v1 import index as old
from research.order10_p4_cap_rescue_v24.verify import (
    p4_from_graph6, check_bijection, constrained_matcher,
)

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

PINNED_BLOBS = {
    "research/order10_p4_reference_pilot_v24/results.json":
        "171908472fe4037e0653a08056877fb956bd8d54",
    "research/order10_p4_cap_rescue_v24/certificates.json":
        "b452338cb199a596e1ee2ce853ef73d410b900ac",
    "research/order10_p4_nine_links_v1/certificates.json":
        "8e43de32414f846820e151dade65057237251426",
    "indeterminate_order_10_v25.txt":
        "d31d52d28427adcef6055cc1d277565fe88f32d5",
    "research/order10_p3_global_v23_index/certificates.json":
        "ab5a9f1c075dfad63b111929368147884519f2a3",
}
MAX_REF_INTERMEDIATE = old.MAX_INTERMEDIATE
MAX_REF_FACETS = 750
MAX_REF_P3_VERTICES = 750
EXPECTED_HOST_COUNTS = {
    "pilot_complete": 180,
    "rescue_complete": 26,
    "new_p4_links": 4,
    "all": 210,
    "within_reference_bound": 202,
    "over_reference_bound": 8,
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def frozen(name: str) -> dict | bytes:
    require(name in PINNED_BLOBS, "Unrecognized immutable P4 evidence")
    raw = (ROOT / name).read_bytes()
    require(old.blob(raw) == PINNED_BLOBS[name],
            f"Previously certified P4 source changed: {name}")
    return json.loads(raw) if name.endswith(".json") else raw


def dims(graph: nx.Graph) -> tuple[int, int]:
    return len(graph), graph.number_of_edges()


def as_graph(rows: list[int]) -> nx.Graph:
    n = len(rows)
    graph = nx.Graph()
    graph.add_nodes_from(range(n))
    for i, mask in enumerate(rows):
        require((mask >> n) == 0 and not (mask & (1 << i)),
                "Malformed adjacency mask")
        for j in range(i + 1, n):
            if mask & (1 << j):
                require(bool(rows[j] & (1 << i)),
                        "P4 adjacency masks are not symmetric")
                graph.add_edge(i, j)
    return graph


def host_catalog() -> dict:
    """Authenticate 210 frozen P4 dimensions, without rebuilding dense P4."""
    prior = frozen("research/order10_p4_reference_pilot_v24/results.json")
    rescue = frozen("research/order10_p4_cap_rescue_v24/certificates.json")
    links = frozen("research/order10_p4_nine_links_v1/certificates.json")
    gindex = frozen("research/order10_p3_global_v23_index/certificates.json")
    rows = old.index_rows if hasattr(old, "index_rows") else None
    require(rows is None, "Unexpected legacy source-index override")
    ten_rows = {}
    for line in frozen("indeterminate_order_10_v25.txt").decode("ascii").splitlines():
        if not line or line.startswith("#"):
            continue
        row = line.split()
        require(len(row) == 6, "Malformed frozen ten-v25 source")
        if row[1] == "10":
            ten_rows[int(row[0])] = row[2]
    require(len(ten_rows) == 622, "Unexpected surviving ten-vertex stiff count")

    known_reps = set(gindex["singleton_indices"]) | {
        cl["representative"] for cl in gindex["nontrivial_classes"]
    }
    require(gindex["counts"]["exact_isomorphism_classes"] == 525
            and len(known_reps) == 525,
            "Historical global P3 classes changed")

    entries = {}
    status_counts = Counter()
    for record in prior["records"]:
        idx = record["index"]
        if record["status"] == "P4_FACET_CAP":
            status_counts["pilot_limited"] += 1
            continue
        require(record["status"] in
                ("NO_REFERENCE_DIMENSION_MATCH", "CHECKED_NONMATCH", "EXACT_MATCH")
                and record.get("p4") is not None,
                "Historical P4 pilot incomplete or unexpected")
        require(idx not in entries, "Duplicate P4 pilot representative")
        entries[idx] = {"index": idx, "p4": record["p4"],
                        "origin": "pilot_complete"}
        status_counts["pilot_complete"] += 1
    require(status_counts["pilot_complete"] == 180
            and status_counts["pilot_limited"] == 26,
            "Historical 180/26 pilot proof cohort changed")
    formerly_limited = {
        r["index"] for r in prior["records"]
        if r["status"] == "P4_FACET_CAP"
    }
    require(len(rescue["recovered_records"]) == 26
            and set(r["index"] for r in rescue["recovered_records"])
            == formerly_limited,
            "Formerly limited 26 sources not completely rescued")
    for rec in rescue["recovered_records"]:
        idx = rec["index"]
        require(idx not in entries, "Rescued graph repeats completed P4")
        entries[idx] = {"index": idx, "p4": rec["P4"],
                        "origin": "rescue_complete"}
        status_counts["rescue_complete"] += 1

    require(len(links["records"]) == 4
            and links["expected_counts"]["linked_all"] == 500,
            "Prior four proof-only P4 links changed")
    for rec in links["records"]:
        idx = rec["index"]
        require(idx not in entries, "Prior P4 links duplicate a pilot P4")
        entries[idx] = {"index": idx, "p4": rec["p4"],
                        "origin": "new_p4_links"}
        status_counts["new_p4_links"] += 1
    require(len(entries) == 210, "Missing one of the 210 certified P4 hosts")
    for idx, item in entries.items():
        require(idx in ten_rows and idx in known_reps
                and len(item["p4"]) == 2
                and all(type(x) is int and x >= 0 for x in item["p4"]),
                "P4 index, original McKay identity or dimensions invalid")
        item["original_graph6"] = ten_rows[idx]
    entries_list = [entries[i] for i in sorted(entries)]
    small = sum(item["p4"][0] <= MAX_REF_P3_VERTICES
                for item in entries_list)
    counts = {
        **dict(status_counts),
        "all": len(entries_list),
        "within_reference_bound": small,
        "over_reference_bound": len(entries_list) - small,
    }
    require(counts == EXPECTED_HOST_COUNTS,
            "Stored P4 host coverage or resource scope changed")
    return {
        "schema": 1,
        "kind": "frozen_certified_p4_shapes_210_unresolved_ten_p3_classes",
        "git_blobs": PINNED_BLOBS,
        "counts": counts,
        "reference_intermediate_cap": MAX_REF_INTERMEDIATE,
        "reference_p3_facets_cap": MAX_REF_FACETS,
        "records": entries_list,
    }


def rebuild_p4(record: dict) -> tuple[list[int], nx.Graph]:
    """Use existing independently cross-checked and multi-round P4 verifier."""
    raw, pared, _rounds, _p3_dims = p4_from_graph6(record["original_graph6"])
    require(len(raw) >= len(pared), "P4 dominated folding enlarged graph")
    graph = as_graph(pared)
    require(list(dims(graph)) == record["p4"],
            f"Stored P4 dimensions changed: McKay {record['index']}")
    return pared, graph


def exact_p4_map(reference: nx.Graph, record: dict, cache: dict
                 ) -> list[int] | None:
    """Lazily reconstruct only dimension-compatible saved ten-P4 hosts."""
    i = record["index"]
    if i not in cache:
        cache[i] = rebuild_p4(record)[1]
    target = cache[i]
    require(dims(reference) == dims(target),
            "Attempted exact check of incompatible dimensions")
    # This method is independently checked on all ordered vertex pairs.
    return old.exact_map(reference, target, seconds=20.0)


def scan(inventory: dict, hosts: dict, shard: int, shards: int) -> dict:
    require(inventory.get("schema") == hosts.get("schema") == 1
            and inventory["counts"]["total"] == 10155
            and hosts["counts"] == EXPECTED_HOST_COUNTS,
            "Wrong complete source/host inventory")
    require(0 <= shard < shards <= 32, "Invalid deterministic shard")
    targets = defaultdict(list)
    for record in hosts["records"]:
        if record["p4"][0] <= MAX_REF_P3_VERTICES:
            targets[tuple(record["p4"])].append(record)
    sources = inventory["sources"][shard::shards]
    root_buckets = defaultdict(list)
    roots = []
    for source in sources:
        root = old.independent_pare(old.from_g6(source["graph6"]))
        bucket = root_buckets[old.signature(root)]
        same = next((existing for existing in bucket
                     if nx.is_isomorphic(root, existing["root"])), None)
        if same is None:
            same = {"root": root, "sources": []}
            bucket.append(same)
            roots.append(same)
        same["sources"].append(source)
    cache = {}
    stats = Counter()
    skipped = []
    collisions = []
    positives = []
    timed = []
    for item in roots:
        current = item["root"]
        proof_source = item["sources"][0]
        for depth in range(4):
            if depth:
                try:
                    current = old.next_pared(current, depth)
                except old.ReconstructionLimit as exc:
                    skipped.append({
                        "source": proof_source, "depth": depth,
                        "represented_sources": len(item["sources"]),
                        "reason": str(exc),
                    })
                    break
            stats[f"reconstructed_P{depth}"] += 1
            same_dimensions = targets.get(dims(current), [])
            for host in same_dimensions:
                stats["dimension_collisions"] += 1
                # A full isomorphism is the only positive witness.
                # Necessary structural refinements may reject collision.
                try:
                    mapping = exact_p4_map(current, host, cache)
                except old.MatchingLimit:
                    timed.append({
                        "source": proof_source,
                        "reference_depth": depth,
                        "ten_original": host["index"],
                        "status": "ISOMORPHISM_TIMEOUT_INCONCLUSIVE",
                    })
                    continue
                rec = {
                    "source": proof_source,
                    "all_equal_p0_sources": item["sources"],
                    "reference_depth": depth,
                    "ten_original": host["index"],
                    "shape": host["p4"],
                    "source_iterate_g6": old.graph6(current),
                }
                if mapping is None:
                    collisions.append({
                        "source": proof_source,
                        "reference_depth": depth,
                        "ten_original": host["index"],
                        "shape": host["p4"],
                        "status": "CHECKED_NOT_ISOMORPHIC",
                    })
                    continue
                positives.append({**rec, "map": mapping})
                print("POSITIVE nine/early source", proof_source["original_index"],
                      "depth", depth, "to ten P4", host["index"],
                      "order", host["p4"][0], flush=True)
    return {
        "schema": 1, "kind": "cross_depth_p4_positive_only_shard",
        "shard": shard, "shards": shards,
        "source_original_count": len(sources),
        "different_p0_classes_in_shard": len(roots),
        "levels": dict(stats),
        "bounded_reconstruction_skips": skipped,
        "comparison_timeouts": timed,
        "nonisomorphic_dimension_collisions": collisions,
        "positives": positives,
        "scope": "All frozen 210 P4 shapes; 202 within 750-vertex reference cap",
    }


def replay(inventory: dict, hosts: dict, shards: list[dict]) -> dict:
    require(len(shards) >= 1
            and sorted(x["shard"] for x in shards) == list(range(len(shards)))
            and all(x["shards"] == len(shards)
                    and x["kind"] == "cross_depth_p4_positive_only_shard"
                    for x in shards)
            and sum(x["source_original_count"] for x in shards) == 10155,
            "Missing/overlapping cross-depth reference shards")
    require(hosts["counts"] == EXPECTED_HOST_COUNTS
            and inventory["counts"]["total"] == 10155,
            "Wrong authenticated input or P4 host cohort")
    original_refs = {
        (s["original_order"], s["original_index"]): s
        for s in inventory["sources"]
    }
    byhost = {x["index"]: x for x in hosts["records"]}
    positive = []
    certified = set()
    for shard in shards:
        for cert in shard["positives"]:
            source = cert["source"]
            require(original_refs.get(
                (source["original_order"], source["original_index"])) == source,
                "Positive reference not historically proved divergent")
            require(cert["ten_original"] in byhost
                    and cert["reference_depth"] in (0, 1, 2, 3),
                    "Positive noncurrent P4 original or invalid stage")
            # Rebuild reference and host from their original graph6; the
            # worker's saved graph6 and complete permutation are separately
            # checked rather than trusting its candidate fingerprint.
            g = old.independent_pare(old.from_g6(source["graph6"]))
            for d in range(1, cert["reference_depth"] + 1):
                g = old.next_pared(g, d)
            target_rows, target = rebuild_p4(byhost[cert["ten_original"]])
            mapping = cert["map"]
            require(
                cert["shape"] == byhost[cert["ten_original"]]["p4"]
                and cert["source_iterate_g6"] == old.graph6(g)
                and len(g) == len(mapping) == len(target)
                and sorted(mapping) == list(range(len(target))),
                "Incomplete or forged replay evidence")
            g_rows = [
                sum(1 << j for j in g[i]) for i in range(len(g))
            ]
            check_bijection(g_rows, target_rows, mapping)
            constrained_matcher(g_rows, target_rows, mapping)
            certified.add(cert["ten_original"])
            positive.append(cert)
    return {
        "schema": 1,
        "kind": "independently_replayed_cross_depth_P0_P3_vs_P4_positive_matches",
        "certified_historical_reference_count": len(original_refs),
        "frozen_p4_host_count": len(byhost),
        "within_bounded_scope": hosts["counts"]["within_reference_bound"],
        "shards": len(shards),
        "p0_classes_within_shards": sum(
            x["different_p0_classes_in_shard"] for x in shards
        ),
        "dimension_collisions": sum(
            x["levels"].get("dimension_collisions", 0) for x in shards
        ),
        "ref_stage_reconstruction_limits": sum(
            len(x["bounded_reconstruction_skips"]) for x in shards
        ),
        "exact_isomorphism_timeouts": sum(
            len(x["comparison_timeouts"]) for x in shards
        ),
        "full_positive_certificates": positive,
        "ten_v25_positive_original_indices": sorted(certified),
        "not_classification": True,
        "not_negative_exhaustive": True,
    }


def write(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, sort_keys=True, separators=(",", ":"))
                    + "\n", encoding="utf-8")


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("hosts", "shard", "replay"))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--hosts", type=Path)
    parser.add_argument("--shards", type=int, default=8)
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--results", type=Path)
    opts = parser.parse_args()
    if opts.action == "hosts":
        answer = host_catalog()
    elif opts.action == "shard":
        require(opts.inventory and opts.hosts, "Missing authenticated inputs")
        answer = scan(read(opts.inventory), read(opts.hosts),
                      opts.shard, opts.shards)
    else:
        require(opts.inventory and opts.hosts and opts.results,
                "Missing cross-depth proof inputs")
        files = sorted(opts.results.glob("shard-*.json"))
        require(len(files) == opts.shards, "Missing a reference shard")
        answer = replay(read(opts.inventory), read(opts.hosts),
                        [read(p) for p in files])
    write(opts.output, answer)
    print(json.dumps({
        "action": opts.action, "artifact": str(opts.output),
        "count": answer.get("counts", {}).get("all")
                 or answer.get("source_original_count")
                 or answer.get("certified_historical_reference_count"),
        "positive": len(answer.get("positives", []))
                    or len(answer.get("full_positive_certificates", [])),
        "collisions": answer.get("dimension_collisions",
                 answer.get("levels", {}).get("dimension_collisions")),
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
