"""Positive-only K2 isomorphism search against all certified historical sources.

Reference corpus is reconstructed from exactly 10,104 archived, *proved*
divergent original graphs at orders 6..9 via the existing authenticated
historical source loader, not from an unverified verdict label. Every
candidate and reference K2 uses public pycliques completely_pared_graph
and clique_graph routines; all positives are checked by a full
GraphMatcher vertex-pair bijection.

No reference-index or graph6 artifact is hardcoded here. This is an
independent research pilot; it never edits the census indices or claims
that a bounded/skipped graph is K-convergent.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx
import pycliques

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from historical_divergent_targets_v1 import historic_inputs  # noqa: E402

SOURCE = ROOT / "indeterminate_order_10_v15.txt"
SOURCE9 = ROOT / "indeterminate_order_9_v4.txt"
EXPECTED_HISTORICAL = 10104
EXPECTED_V15 = 2541
K_BOUND = 1500


def g6(graph):
    return nx.to_graph6_bytes(
        nx.convert_node_labels_to_integers(graph), header=False
    ).decode("ascii").strip()


def p2(graph):
    p = pycliques.completely_pared_graph(graph)
    for _ in range(2):
        out = pycliques.clique_graph(p, bound=K_BOUND)
        if out is None:
            return None
        p = pycliques.completely_pared_graph(out)
    return nx.convert_node_labels_to_integers(p)


def fingerprint(graph):
    return (
        len(graph), graph.number_of_edges(),
        tuple(sorted(d for _, d in graph.degree())),
        nx.weisfeiler_lehman_graph_hash(nx.complement(graph)),
    )


def exact_iso(a, b):
    iso = nx.algorithms.isomorphism.GraphMatcher(
        nx.complement(a), nx.complement(b)
    )
    if not iso.is_isomorphic():
        return None
    f = iso.mapping
    assert set(f) == set(a) and set(f.values()) == set(b)
    assert all(
        a.has_edge(u, v) == b.has_edge(f[u], f[v])
        for u in a for v in a
    )
    return [f[u] for u in range(len(a))]


def census_rows():
    source = SOURCE.read_bytes()
    lines = [x.split() for x in source.decode().splitlines()
             if x and not x.startswith("#")]
    assert len(lines) == EXPECTED_V15
    assert len({int(x[0]) for x in lines}) == EXPECTED_V15
    return lines


def main():
    start = time.monotonic()
    buckets = defaultdict(list)
    cached = {}
    seen = Counter()
    skipped = Counter()
    for proof, source in historic_inputs():
        seen[proof["stage"]] += 1
        pared = pycliques.completely_pared_graph(source)
        source_key = g6(pared)
        if source_key not in cached:
            cached[source_key] = p2(source)
        graph = cached[source_key]
        if graph is None:
            skipped["historical_K2_bound"] += 1
            print(
                "HISTORICAL_SKIPPED", proof["order"], proof["index"],
                proof["graph6"], "K_bound", K_BOUND, flush=True,
            )
            continue
        key = fingerprint(graph)
        candidates = buckets[key]
        if not any(exact_iso(graph, r["graph"]) is not None for r in candidates):
            candidates.append({
                "graph": graph,
                "proof": {
                    "order": proof["order"],
                    "index": proof["index"],
                    "graph6": proof["graph6"],
                    "stage": proof["stage"],
                    "reason": proof["historical_reason"],
                },
            })
        if sum(seen.values()) % 1000 == 0:
            print(
                "HISTORICAL_PROGRESS", sum(seen.values()),
                "P0_cache", len(cached), "distinct_K2_classes",
                sum(len(v) for v in buckets.values()),
                "skipped", sum(skipped.values()),
                "seconds", round(time.monotonic() - start, 1),
                flush=True,
            )
    assert sum(seen.values()) == EXPECTED_HISTORICAL, seen
    print("HISTORICAL_REFERENCES", dict(seen), "classes",
          sum(len(v) for v in buckets.values()), "skipped", dict(skipped),
          "elapsed", round(time.monotonic()-start,1), flush=True)

    matches = []
    cache_current = {}
    for index, row in enumerate(census_rows(), 1):
        original_index = int(row[0])
        source_g6 = row[2]
        if source_g6 not in cache_current:
            graph = p2(nx.from_graph6_bytes(source_g6.encode("ascii")))
            if graph is None:
                skipped["current_K2_bound"] += 1
                cache_current[source_g6] = None
            else:
                match = None
                for reference in buckets.get(fingerprint(graph), []):
                    f = exact_iso(graph, reference["graph"])
                    if f is not None:
                        match = {
                            "reference": reference["proof"],
                            "source_graph6": source_g6,
                            "p2_order": len(graph),
                            "p2_edges": graph.number_of_edges(),
                            "p2_iso": f,
                        }
                        break
                cache_current[source_g6] = match
        if cache_current[source_g6] is not None:
            witness = cache_current[source_g6]
            matches.append({"index": original_index, **witness})
            print(
                "NEW_POSITIVE", original_index,
                witness["reference"]["order"],
                witness["reference"]["index"],
                witness["p2_order"], witness["p2_edges"],
                flush=True,
            )
        if index % 500 == 0:
            print("CURRENT_PROGRESS", index,
                  "positive", len(matches),
                  "time", round(time.monotonic()-start,1),flush=True)
    nine_rows = [
        fields for line in SOURCE9.read_text().splitlines()
        if line and not line.startswith("#")
        for fields in [line.split()]
    ]
    assert len(nine_rows) == 12
    nine_matches = []
    for row in nine_rows:
        nine_index, nine_graph6 = int(row[0]), row[2]
        graph = p2(nx.from_graph6_bytes(nine_graph6.encode("ascii")))
        if graph is None:
            skipped["nine_current_K2_bound"] += 1
            print("NINE_SKIPPED", nine_index, flush=True)
            continue
        for reference in buckets.get(fingerprint(graph), []):
            witness = exact_iso(graph, reference["graph"])
            if witness is not None:
                nine_matches.append({
                    "index": nine_index, "source_graph6": nine_graph6,
                    "reference": reference["proof"],
                    "p2_order": len(graph), "p2_edges": graph.number_of_edges(),
                    "p2_iso": witness,
                })
                print("NINE_NEW_POSITIVE", nine_index,
                      reference["proof"]["order"], reference["proof"]["index"],
                      len(graph), graph.number_of_edges(), flush=True)
                break

    result = {
        "schema": 1,
        "source_v15_count": EXPECTED_V15,
        "historical_count": sum(seen.values()),
        "historical_by_stage": dict(seen),
        "K_bound": K_BOUND,
        "distinct_reference_K2_classes": sum(len(v) for v in buckets.values()),
        "skipped": dict(skipped),
        "matched": matches,
        "nine_source_count": len(nine_rows),
        "nine_matched": nine_matches,
        "elapsed_seconds": round(time.monotonic()-start,2),
    }
    print("FINAL_SUMMARY", json.dumps({
        k:v for k,v in result.items() if k not in ("matched", "nine_matched")
    },sort_keys=True),flush=True)
    print("NEW_POSITIVE_INDICES",
          [x["index"] for x in matches], flush=True)
    print("NINE_POSITIVE_INDICES",
          [x["index"] for x in nine_matches], flush=True)
    result_path=ROOT / "research/order10_historical_all9_p2_pilot/last_run.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")


if __name__ == "__main__":
    main()
