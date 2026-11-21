"""Positive-only exact P2-isomorphism lift pilot for known divergent references.

Sources: frozen v14 unresolved order-ten census (2568 records).
References: the 36 nine-vertex graphs independently certified by the
archived snub v3 promotion, the new O12-positive 248936 nine-core, and
six separate original ten-core O6/O12 retraction certificates.

Only genuine exact isomorphisms can generate positive certificates.
No failed, skipped, or bounded computation yields a K-convergence claim.
Uses public pycliques routines; this file does not change census indices.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx
import pycliques

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "indeterminate_order_10_v14.txt"
NINE_BEFORE = ROOT / "indeterminate_order_9_v2.txt"
NINE_AFTER = ROOT / "indeterminate_order_9_v3.txt"
SNUB_OLD = 49
SNUB_NEW = 13
NINE_REFERENCE = ("nine-248936-O12", "HEhev^{")
# These six original nine-vertex cores have positive historical divergence
# certificates in the archived initial census and later 167-member lift.
HISTORICAL_NINE_REFERENCES = [
    ("historical-6938923", "HEht}pl"),
    ("historical-6939350", "HEht~bl"),
    ("historical-7454135", "HEnb~jl"),
    ("historical-9678187", "HQyuzpt"),
    ("historical-10768817", "HUZ~v~}"),
    ("historical-11363569", "HUzrv~}"),
]
TEN_REFERENCES = [
    ("ten-10223405-O12", "ICXnRi^uo"),
    ("ten-10775850-O12", "ICpVUjx|_"),
    ("ten-10223467-O6", "ICXnRjZmo"),
    ("ten-11104269-O6", "ICpdupvZo"),
    ("ten-11563706-O6", "IEhfe^{zO"),
    ("ten-10510367-O12", "ICZVByz~_"),
]


def rows(path: Path) -> dict[int, list[str]]:
    data = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        cols = line.split()
        if len(cols) != 6:
            raise AssertionError(f"Unexpected census row in {path}")
        index = int(cols[0])
        if index in data:
            raise AssertionError(f"Duplicate index {index}")
        data[index] = cols
    if list(data) != sorted(data):
        raise AssertionError(f"Unsorted index {path}")
    return data


def digest(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def build(graph6: str, depth: int, *, bound: int | None) -> nx.Graph | None:
    graph = pycliques.completely_pared_graph(
        nx.from_graph6_bytes(graph6.encode("ascii"))
    )
    for _ in range(depth):
        # None means truly unbounded exact verification. A finite bound
        # belongs only to an exploratory, explicitly incomplete pilot.
        graph = (
            pycliques.clique_graph(graph)
            if bound is None
            else pycliques.clique_graph(graph, bound=bound)
        )
        if graph is None:
            return None
        graph = pycliques.completely_pared_graph(graph)
    return nx.convert_node_labels_to_integers(graph)


def fingerprint(graph: nx.Graph):
    return (
        len(graph),
        graph.number_of_edges(),
        tuple(sorted(degree for _, degree in graph.degree())),
        nx.weisfeiler_lehman_graph_hash(nx.complement(graph)),
    )


def exact_map(a: nx.Graph, b: nx.Graph) -> list[int] | None:
    if fingerprint(a) != fingerprint(b):
        return None
    matcher = nx.algorithms.isomorphism.GraphMatcher(
        nx.complement(a), nx.complement(b)
    )
    if not matcher.is_isomorphic():
        return None
    mapping = matcher.mapping
    assert set(mapping) == set(a) and set(mapping.values()) == set(b)
    assert all(
        a.has_edge(i, j) == b.has_edge(mapping[i], mapping[j])
        for i in a for j in a
    )
    return [mapping[i] for i in range(len(a))]


def references(depth: int, bound: int | None) -> dict[tuple, list[tuple[str, str, nx.Graph]]]:
    before, after = rows(NINE_BEFORE), rows(NINE_AFTER)
    if len(before) != SNUB_OLD or len(after) != SNUB_NEW:
        raise AssertionError("Wrong source snapshot sizes")
    removed = sorted(set(before) - set(after))
    if len(removed) != 36:
        raise AssertionError("Historical snub cohort differs")
    if any(
        before[i][4:] != ["conjectured_divergent", "snub_disphenoid"]
        for i in removed
    ):
        raise AssertionError("Unexpected historical reference class")

    cases = [(f"snub9-{i}", before[i][2]) for i in removed]
    cases.append(NINE_REFERENCE)
    cases.extend(HISTORICAL_NINE_REFERENCES)
    cases.extend(TEN_REFERENCES)

    ref_graphs = defaultdict(list)
    cache = {}
    skipped = []
    for label, graph6 in cases:
        if graph6 not in cache:
            cache[graph6] = build(graph6, depth, bound=bound)
        graph = cache[graph6]
        if graph is None:
            # Never silently reduce the certified reference set: otherwise
            # a purported complete positive set could miss true matches.
            raise AssertionError(
                f"Certified reference {label} exceeded the clique bound"
            )
        ref_graphs[fingerprint(graph)].append((label, graph6, graph))
    print("REFERENCES", depth, "certified", len(cases),
          "distinct_graph6", len(cache),
          "eligible", sum(len(x) for x in ref_graphs.values()),
          "distinct_signatures", len(ref_graphs),
          "skipped", skipped, flush=True)
    if not ref_graphs:
        raise AssertionError("No reference graphs could be reconstructed")
    return ref_graphs


def scan(shard: int, shards: int, depth: int, bound: int | None) -> dict:
    if not 0 <= shard < shards:
        raise ValueError("Invalid shard")
    if depth not in (2, 3):
        raise ValueError("Supported depths are 2 and 3")
    frozen = rows(SOURCE)
    assert len(frozen) == 2568
    ref_graphs = references(depth, bound)
    active = [(index, row) for index, row in frozen.items()
              if index % shards == shard]
    cache = {}
    matches = []
    failures = []
    t0 = time.monotonic()
    for count, (index, row) in enumerate(active, 1):
        graph6 = row[2]
        if graph6 not in cache:
            try:
                graph = build(graph6, depth, bound=bound)
                if graph is None:
                    cache[graph6] = None
                else:
                    possible = ref_graphs.get(fingerprint(graph), ())
                    matches_for_core = []
                    for name, base, target in possible:
                        witness = exact_map(graph, target)
                        if witness is not None:
                            matches_for_core.append({
                                "reference": name, "reference_g6": base,
                                "depth": depth, "map": witness,
                                "order": len(graph),
                                "edges": graph.number_of_edges(),
                            })
                    cache[graph6] = matches_for_core
            except (MemoryError, RecursionError) as exc:
                failures.append([index, type(exc).__name__])
                cache[graph6] = None
        if cache[graph6]:
            witness = cache[graph6][0]
            matches.append({"index": index, "graph6": graph6, **witness})
            print("POSITIVE", index, witness["reference"],
                  "P" + str(depth), witness["order"], witness["edges"],
                  flush=True)
        if count % 40 == 0:
            print("PROGRESS", shard, depth, count, "/", len(active),
                  "positive", len(matches),
                  "distinct", len(cache), "elapsed",
                  round(time.monotonic() - t0, 1), flush=True)
    result = {
        "schema": 1,
        "phase": depth,
        "shard": shard,
        "shards": shards,
        "source_git_blob": digest(SOURCE),
        "reference_before_blob": digest(NINE_BEFORE),
        "reference_after_blob": digest(NINE_AFTER),
        "processed_original_indices": len(active),
        "distinct_core_graph6": len(cache),
        "bound_exhausted_distinct_core_graph6": sum(v is None for v in cache.values()),
        "exceptions": failures,
        "positive": matches,
        "elapsed_seconds": round(time.monotonic() - t0, 2),
    }
    print("PILOT_SUMMARY", json.dumps({k: v for k, v in result.items()
                                      if k not in ("positive", "exceptions")}),
          "positive_count", len(matches), flush=True)
    print("POSITIVE_INDICES", json.dumps([p["index"] for p in matches]), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard", type=int, required=True)
    parser.add_argument("--shards", type=int, default=8)
    parser.add_argument("--depth", type=int, default=2, choices=(2, 3))
    parser.add_argument("--bound", type=int, default=1500)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = scan(args.shard, args.shards, args.depth, args.bound)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")


if __name__ == "__main__":
    main()
