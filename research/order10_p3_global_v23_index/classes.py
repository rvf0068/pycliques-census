"""Global exact P3 equivalence census of the 629 unresolved stiff order-ten cores.

Read-only with respect to classification. Graph construction is from the
immutable ten-v23 graph6; all positive equivalences have full bijections.
Skipped resource-limited cases are neither positive nor negative results.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys

import networkx as nx

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical checks")

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "indeterminate_order_10_v23.txt"
CURRENT = ROOT / "indeterminate_order_10.txt"
CERT = Path(__file__).with_name("certificates.json")
SOURCE_BLOB = "f32ceb913b44583f472402e14c596598fef71aaa"
MAX_INTERMEDIATE = 110
MAX_FACETS = 750
EXPECTED_SKIPS = {11708967, 11715667, 11716441}


class BoundedSkip(Exception):
    def __init__(self, stage: int, reason: str, sizes: list[int]):
        self.stage = stage
        self.reason = reason
        self.sizes = list(sizes)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_blob(data: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()


def source_rows() -> dict[int, str]:
    require(git_blob(SOURCE.read_bytes()) == SOURCE_BLOB,
            "Original ten-v23 source Git blob changed")
    require(SOURCE.read_bytes() == CURRENT.read_bytes(),
            "Current working root no longer equals ten-v23")
    require((ROOT / "indeterminate_order_9.txt").read_bytes()
            == (ROOT / "indeterminate_order_9_v9.txt").read_bytes(),
            "Nine-vertex root unexpectedly changed")
    rows = {}
    for line in SOURCE.read_text(encoding="ascii").splitlines():
        if not line or line.startswith("#"):
            continue
        idx, order, g6, rule, status, label = line.split()
        if order != "10":
            continue
        require((rule, status, label) == ("-", "-", "-"),
                f"Conditional record {idx}")
        index = int(idx)
        require(index not in rows, f"Duplicate original index {index}")
        require(len(nx.from_graph6_bytes(g6.encode("ascii"))) == 10,
                f"Bad graph6 for {index}")
        rows[index] = g6
    require(list(rows) == sorted(rows) and len(rows) == 629,
            "Unexpected ten-v23 stiff cohort")
    return rows


def pare(graph: nx.Graph) -> nx.Graph:
    """Sequential smallest-node dominated deletions, canonical final labels."""
    graph = graph.copy()
    while True:
        victim = None
        for u in sorted(graph):
            closed = set(graph[u]) | {u}
            if any(u != v and closed <= (set(graph[v]) | {v})
                   for v in sorted(graph)):
                victim = u
                break
        if victim is None:
            break
        graph.remove_node(victim)
    return nx.convert_node_labels_to_integers(graph, ordering="sorted")


def clique_graph(graph: nx.Graph, stage: int, sizes: list[int]) -> nx.Graph:
    """Cap maximal-clique enumeration *during* generation, not afterward."""
    facets = []
    for c in nx.find_cliques(graph):
        facets.append(sum(1 << int(v) for v in c))
        if len(facets) > MAX_FACETS:
            raise BoundedSkip(stage, "maximal_clique_cap", sizes)
    facets.sort()
    graph2 = nx.Graph()
    graph2.add_nodes_from(range(len(facets)))
    graph2.add_edges_from(
        (i, j) for i in range(len(facets))
        for j in range(i + 1, len(facets))
        if facets[i] & facets[j]
    )
    return graph2


def reconstruct(graph6: str) -> nx.Graph:
    graph = pare(nx.from_graph6_bytes(graph6.encode("ascii")))
    sizes = [len(graph)]
    for stage in range(1, 4):
        if len(graph) > MAX_INTERMEDIATE:
            raise BoundedSkip(stage, "intermediate_order_cap", sizes)
        graph = pare(clique_graph(graph, stage, sizes))
        sizes.append(len(graph))
    return graph


def fingerprint(graph: nx.Graph) -> tuple:
    deg = dict(graph.degree)
    profiles = tuple(sorted(
        (deg[v], tuple(sorted(deg[u] for u in graph[v])))
        for v in graph
    ))
    return (
        len(graph), graph.number_of_edges(), profiles,
        nx.weisfeiler_lehman_graph_hash(graph, iterations=3),
    )


def build() -> dict:
    rows = source_rows()
    bucket: dict[tuple, list[dict]] = defaultdict(list)
    skips = []
    for index, g6 in rows.items():
        try:
            graph = reconstruct(g6)
        except BoundedSkip as exc:
            skips.append({
                "index": index, "reason": exc.reason,
                "stage": exc.stage, "pared_orders": exc.sizes,
            })
            continue
        key = fingerprint(graph)
        candidate = None
        mapping = None
        for cls in bucket[key]:
            matcher = nx.algorithms.isomorphism.GraphMatcher(graph, cls["graph"])
            if matcher.is_isomorphic():
                candidate = cls
                mapping = [matcher.mapping[v] for v in range(len(graph))]
                break
        if candidate is None:
            candidate = {
                "rep": index, "graph": graph, "members": [],
            }
            bucket[key].append(candidate)
            mapping = list(range(len(graph)))
        candidate["members"].append({"index": index, "bijection": mapping})
    require({s["index"] for s in skips} == EXPECTED_SKIPS,
            f"Unexpected explicit resource-limit cohort: {skips}")
    classes = sorted(
        (cl for group in bucket.values() for cl in group),
        key=lambda cl: cl["rep"],
    )
    multi = [
        {
            "representative": cl["rep"],
            "order": len(cl["graph"]),
            "edges": cl["graph"].number_of_edges(),
            "members": cl["members"],
        }
        for cl in classes if len(cl["members"]) > 1
    ]
    singletons = [cl["rep"] for cl in classes if len(cl["members"]) == 1]
    counts = {
        "stiff_originals": 629,
        "reconstructed": 629 - len(skips),
        "explicitly_skipped": len(skips),
        "exact_isomorphism_classes": len(classes),
        "nontrivial_classes": len(multi),
        "members_in_nontrivial_classes": sum(len(c["members"]) for c in multi),
        "singleton_classes": len(singletons),
    }
    require((counts["reconstructed"], counts["exact_isomorphism_classes"],
             counts["nontrivial_classes"], counts["members_in_nontrivial_classes"],
             counts["singleton_classes"]) == (626, 525, 33, 134, 492),
            f"Unexpected global third-iterate class counts: {counts}")
    return {
        "schema": 1,
        "immutable_source_git_blob": SOURCE_BLOB,
        "limits": {"intermediate_order": MAX_INTERMEDIATE,
                   "maximal_cliques": MAX_FACETS},
        "counts": counts,
        "skips": skips,
        "singleton_indices": singletons,
        "nontrivial_classes": multi,
    }


def verify_witness(graph: nx.Graph, reference: nx.Graph, mapping: list[int]) -> None:
    n = len(graph)
    require(n == len(reference) and len(mapping) == n
            and sorted(mapping) == list(range(n)),
            "Invalid saved complete P3 bijection")
    require(all(
        graph.has_edge(u, v) == reference.has_edge(mapping[u], mapping[v])
        for u in range(n) for v in range(n)
    ), "Saved bijection does not preserve all edges and nonedges")


def verify() -> None:
    saved = json.loads(CERT.read_text(encoding="utf-8"))
    require(saved["schema"] == 1
            and saved["immutable_source_git_blob"] == SOURCE_BLOB,
            "Wrong archive source provenance")
    require(saved["limits"] ==
            {"intermediate_order": MAX_INTERMEDIATE,
             "maximal_cliques": MAX_FACETS},
            "Missing resource-limit declaration")
    rows = source_rows()
    all_indices = set(saved["singleton_indices"])
    for cls in saved["nontrivial_classes"]:
        require(cls["members"][0]["index"] == cls["representative"],
                "Noncanonical class representative")
        members = [x["index"] for x in cls["members"]]
        require(len(members) > 1 and members == sorted(set(members)),
                "Incorrect exact equivalence class membership")
        require(not all_indices.intersection(members),
                "Repeated source across certified groups")
        all_indices.update(members)
        ref = reconstruct(rows[cls["representative"]])
        require((len(ref), ref.number_of_edges()) ==
                (cls["order"], cls["edges"]),
                "Reference pared-iterate dimensions changed")
        for witness in cls["members"]:
            graph = reconstruct(rows[witness["index"]])
            verify_witness(graph, ref, witness["bijection"])
    skips = saved["skips"]
    require({x["index"] for x in skips} == EXPECTED_SKIPS,
            "Missing or unexpected bounded skip")
    require(all_indices | EXPECTED_SKIPS == set(rows)
            and not all_indices.intersection(EXPECTED_SKIPS),
            "Incomplete global index coverage")
    independently_rebuilt = build()
    require({key: value for key, value in saved.items()
             if key != "nontrivial_classes"} ==
            {key: value for key, value in independently_rebuilt.items()
             if key != "nontrivial_classes"},
            "Independent exact global classification differs")
    require([
        (cl["representative"], [w["index"] for w in cl["members"]])
        for cl in saved["nontrivial_classes"]
    ] == [
        (cl["representative"], [w["index"] for w in cl["members"]])
        for cl in independently_rebuilt["nontrivial_classes"]
    ], "Different exact nontrivial graph-equivalence classes")
    print("PASS: exact global P3 index; 626/629 reconstructed,"
          " 525 classes, 33 nontrivial classes with 134 originals,"
          " 492 singletons and three explicit bounded exceptions.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["build", "verify"])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.action == "verify":
        verify()
    else:
        content = json.dumps(build(), indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(content, encoding="utf-8")
        else:
            print(content, end="")
        print("Global third-iterate class index constructed successfully",
              file=sys.stderr)


if __name__ == "__main__":
    main()
