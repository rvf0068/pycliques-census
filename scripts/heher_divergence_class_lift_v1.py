"""Certify and lift 99 historical conditional HEher^{ order-ten records.

This reruns the proved nine-vertex K^3->O4 retraction, then independently
constructs a proof for each historical dependency: isomorphism, direct
ordinary retraction, FANP non-triangle-edge deletion, or admissible
inverse-cutpoint extension. Does not trust a string saying 'conjectured'.
The original->completely-pared graph reductions remain certified by
the frozen previous stages; this script replays the final dependency.

Run:
  python scripts/heher_divergence_class_lift_v1.py verify
  python scripts/heher_divergence_class_lift_v1.py certificates --output /tmp/heher-certs.json
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations
import hashlib
import json
from pathlib import Path

import networkx as nx

import core9_o4_divergence_v1 as proof

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "indeterminate_order_10_v6.txt"
LATEST = ROOT / "indeterminate_order_10_v7.txt"
ROOT_LIST = ROOT / "indeterminate_order_10.txt"
REFERENCE = "HEher^{"
SOURCE_BLOB = "a625149c7b36ca5b37d818fba2776dea57cdb051"
EXPECTED = {"reference": 63, "retracts": 28,
            "non_triangle_edge": 6, "inverse_cutpoint_extension": 2}
TOTAL_BEFORE = 8223
TOTAL_AFTER = 8124
CONDITIONAL_AFTER = 4509


def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii")
                        + b"\0" + raw).hexdigest()


def decode(graph6: str) -> nx.Graph:
    return nx.from_graph6_bytes(graph6.encode("ascii"))


def canonical_isomorphism(a: nx.Graph, b: nx.Graph) -> dict[int, int] | None:
    return next(nx.isomorphism.GraphMatcher(a, b).isomorphisms_iter(), None)


def fold_trace(graph: nx.Graph) -> tuple[nx.Graph, list[list[int]]]:
    h = graph.copy()
    trace = []
    while len(h) > 1:
        pair = next(((u, v) for u in sorted(h) for v in sorted(h)
                     if u != v and set(h[u]) | {u} <= (set(h[v]) | {v})),
                    None)
        if pair is None:
            break
        u, v = pair
        trace.append([u, v])
        h.remove_node(u)
    return h, trace


def certify_reference(graph: nx.Graph, target: nx.Graph) -> dict:
    iso = canonical_isomorphism(graph, target)
    if iso is None:
        raise ValueError("Reference claim has no isomorphism")
    return {"type": "reference", "to_reference": sorted([u, v] for u, v in iso.items())}


def certify_retracts(graph: nx.Graph, target: nx.Graph) -> dict:
    if len(graph) != len(target) + 1:
        raise ValueError("Unexpected host order for direct reference retraction")
    for removed in sorted(graph):
        induced = graph.copy()
        induced.remove_node(removed)
        for iso in nx.isomorphism.GraphMatcher(induced, target).isomorphisms_iter():
            for image_vertex in sorted(induced):
                if not all(image_vertex == u or induced.has_edge(image_vertex, u)
                           for u in graph[removed]):
                    continue
                images = [iso.get(u, iso[image_vertex]) for u in sorted(graph)]
                if any(images[u] != images[v]
                       and not target.has_edge(images[u], images[v])
                       for u, v in graph.edges()):
                    raise AssertionError("Invalid explicit retraction")
                return {"type": "retracts", "removed": removed,
                        "image_vertex": image_vertex, "projection": images,
                        "to_reference": sorted([u, v] for u, v in iso.items())}
    raise ValueError("No ordinary retraction onto reference found")


def certify_nontriangle(graph: nx.Graph, target: nx.Graph) -> dict:
    for u, v in sorted(tuple(sorted(e)) for e in graph.edges()):
        if set(graph[u]) & set(graph[v]):
            continue
        modified = graph.copy()
        modified.remove_edge(u, v)
        reduced, folds = fold_trace(modified)
        iso = canonical_isomorphism(reduced, target)
        if iso is not None:
            return {"type": "non_triangle_edge", "edge": [u, v],
                    "dominated_folds": folds,
                    "to_reference": sorted([u, v] for u, v in iso.items())}
    raise ValueError("No valid nontriangular-edge and fold chain")


def certify_inverse_cutpoint(graph: nx.Graph, target: nx.Graph) -> dict:
    if len(graph) != 10:
        raise ValueError("Inverse-cutpoint source must have ten vertices")
    for cutpoint in sorted(graph):
        comps = [frozenset(c) for c in
                 nx.connected_components(graph.subgraph(list(graph[cutpoint])))]
        if len(comps) < 2:
            continue
        comps.sort(key=lambda c: min(c))
        first, other = comps[0], comps[1:]
        for size in range(len(other)):
            for indices in combinations(range(len(other)), size):
                A = set(first)
                for i in indices:
                    A.update(other[i])
                B = set(graph[cutpoint]) - A
                if not B:
                    continue
                u, v = max(graph) + 1, max(graph) + 2
                extended = graph.copy()
                extended.remove_node(cutpoint)
                extended.add_nodes_from((u, v))
                extended.add_edges_from((u, y) for y in A)
                extended.add_edges_from((v, y) for y in B)
                extended.add_edge(u, v)
                disconnected = extended.copy()
                disconnected.remove_edge(u, v)
                if (nx.has_path(disconnected, u, v)
                        and nx.shortest_path_length(disconnected, u, v) < 4):
                    continue
                reduced, folds = fold_trace(disconnected)
                iso = canonical_isomorphism(reduced, target)
                if iso is not None:
                    return {"type": "inverse_cutpoint_extension",
                            "cutpoint": cutpoint, "branches": [sorted(A), sorted(B)],
                            "bridge": [u, v], "bridge_distance": (
                                nx.shortest_path_length(disconnected, u, v)
                                if nx.has_path(disconnected, u, v) else None),
                            "dominated_folds": folds,
                            "to_reference": sorted([a, b] for a, b in iso.items())}
    raise ValueError("No admissible inverse cutpoint theorem chain")


CHECKS = {
    "reference": certify_reference,
    "retracts": certify_retracts,
    "non_triangle_edge": certify_nontriangle,
    "inverse_cutpoint_extension": certify_inverse_cutpoint,
}


def source_rows() -> tuple[list[str], list[dict]]:
    original = SOURCE.read_bytes()
    if blob(original) != SOURCE_BLOB:
        raise ValueError("Frozen v6 input changed unexpectedly")
    entries = [line for line in original.decode("utf-8").splitlines()
               if line and not line.startswith("#")]
    if len(entries) != TOTAL_BEFORE:
        raise ValueError("Incorrect v6 input population")
    conditional = []
    for line in entries:
        index, order, graph6, rule, status, label = line.split(" ", 5)
        if label != REFERENCE:
            continue
        if status != "conjectured_divergent" or rule not in CHECKS:
            raise ValueError("Unexpected HEher historical dependency")
        conditional.append({"index": int(index), "order": int(order),
                            "graph6": graph6, "rule": rule, "source_row": line})
    if len(conditional) != 99 or Counter(r["rule"] for r in conditional) != EXPECTED:
        raise ValueError("Unexpected historical dependency count")
    return entries, conditional


def certified() -> dict:
    # The critical positive nine-vertex proof is independently replayed here.
    witness = proof.positive_second_graph()
    if (witness["source_vertices"], witness["source_edges"]) != (60, 1225):
        raise AssertionError("Divergence source O4 certificate not reproduced")
    original, rows = source_rows()
    target = decode(REFERENCE)
    records = []
    for row in rows:
        host = decode(row["graph6"])
        if len(host) != row["order"]:
            raise ValueError("Pared source order mismatch")
        certificate = CHECKS[row["rule"]](host, target)
        records.append({**row, "certificate": certificate})
    retained = [line for line in original
                if not line.endswith(" " + REFERENCE)]
    if len(retained) != TOTAL_AFTER:
        raise AssertionError("Wrong number of certified removals")
    conditional_remaining = sum(line.split(" ")[4] == "conjectured_divergent"
                                for line in retained)
    if conditional_remaining != CONDITIONAL_AFTER:
        raise AssertionError("Some other conditional case was changed")
    return {"schema": 1, "proven_target_graph6": REFERENCE,
            "proof": {"K3_source_order": 60,
                      "K3_target": witness["target_vertices"],
                      "retraction": witness["retraction"]},
            "counts": dict(Counter(r["rule"] for r in records)),
            "removed_indices": [r["index"] for r in records],
            "records": records}


def v7_content() -> str:
    _, discarded = source_rows()
    excluded = {row["index"] for row in discarded}
    original = SOURCE.read_text(encoding="utf-8").splitlines()
    kept = [line for line in original if line.startswith("#") is False
            and line and int(line.split(" ", 1)[0]) not in excluded]
    assert len(kept) == TOTAL_AFTER
    return "\n".join([
        "# Order-10 unresolved after certified HEher^{ nine-sphere K-divergence lift",
        "# Remaining=8124 previous_v6=8223 newly_certified_divergent=99",
        "# Every previously conditional HEher^{ dependency has an independently replayed certificate.",
        "# Format: original_index pared_order pared_graph6 certificate_rule certificate_target_status certificate_target_label",
        *kept, "",
    ])


def verify() -> dict:
    result = certified()
    canonical = v7_content().encode("utf-8")
    if not LATEST.is_file() or LATEST.read_bytes() != canonical:
        raise ValueError("Versioned v7 index missing or differs from certified lift")
    if not ROOT_LIST.is_file() or ROOT_LIST.read_bytes() != canonical:
        raise ValueError("Root working index not synchronized with v7")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("verify", "certificates"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    data = verify()
    if args.command == "certificates":
        if args.output is None:
            raise ValueError("--output required for generated certificates")
        args.output.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n",
                               encoding="utf-8")
    print("PROVED 99 order-ten divergences", dict(sorted(data["counts"].items())))
    print("CURRENT remaining order-ten graphs", TOTAL_AFTER,
          "conditional", CONDITIONAL_AFTER)


if __name__ == "__main__":
    main()
