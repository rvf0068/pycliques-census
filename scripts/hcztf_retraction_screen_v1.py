"""Exhaustive small-target retraction obstructions for HCZTf\}.

Screen raw K(G) and K²(G) against fixed proved-divergent nine-cores,
their clique graphs, and the still-conditional snub family.
For every induced target, exhibit a vertex outside the target whose
retraction-image domain is empty. All target copies are enumerated,
not timeboxed. This does NOT classify the source graph's K behavior.
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations
import json

import networkx as nx

SOURCE_GRAPH6 = r"HCZTf\}"
EXPECTED = (
    (1, "GQyuzw", 2),
    (1, "HEher^{", 0),
    (2, "HEht}pl", 12),
    (2, "HQyuzpt", 44),
    (2, "GQyuzw", 76),
    (2, "K:GQyuzw", 6),
    (2, "HEher^{", 0),
    (2, "K:HEher^{", 0),
    (2, "K:HEht}pl", 0),
    (2, "K:HQyuzpt", 0),
)


def decode(graph6: str) -> nx.Graph:
    return nx.from_graph6_bytes(graph6.encode("ascii"))


def clique_graph(graph: nx.Graph) -> nx.Graph:
    """Independent deterministic maximal-clique intersection construction."""
    cliques = sorted(
        (frozenset(q) for q in nx.find_cliques(graph)),
        key=lambda q: sum(1 << v for v in q),
    )
    result = nx.Graph()
    result.add_nodes_from(range(len(cliques)))
    result.add_edges_from(
        (i, j) for i, j in combinations(range(len(cliques)), 2)
        if cliques[i] & cliques[j]
    )
    return result


def target_graph(spec: str) -> nx.Graph:
    return clique_graph(decode(spec[2:])) if spec.startswith("K:") else decode(spec)


def obstructed_outside_vertex(
    host: nx.Graph, target: tuple[int, ...]
) -> int | None:
    """Exact necessary failure for a graph retraction fixing the target."""
    fixed = set(target)
    compatible = {
        v: {v} | (set(host[v]) & fixed) for v in fixed
    }
    for outside in sorted(set(host) - fixed):
        possible = set(fixed)
        for t in host[outside]:
            if t in fixed:
                possible.intersection_update(compatible[t])
                if not possible:
                    return outside
    return None


def screen(host: nx.Graph, target: nx.Graph) -> dict:
    copies: set[tuple[int, ...]] = set()
    for embedding in nx.isomorphism.GraphMatcher(
        host, target
    ).subgraph_isomorphisms_iter():
        copies.add(tuple(sorted(embedding)))
    witnesses = []
    for vertices in sorted(copies):
        if not nx.is_isomorphic(host.subgraph(vertices), target):
            raise AssertionError("Induced copy failed independent verification")
        outside = obstructed_outside_vertex(host, vertices)
        if outside is None:
            raise AssertionError("A target escaped the necessary local test")
        witnesses.append({"vertices": list(vertices), "outside": outside})
    return {"induced_target_sets": len(copies),
            "failed_local_condition": len(witnesses),
            "witnesses": witnesses}


def run() -> dict:
    source = decode(SOURCE_GRAPH6)
    first = clique_graph(source)
    second = clique_graph(first)
    assert (len(source), source.number_of_edges()) == (9, 21)
    assert (len(first), first.number_of_edges()) == (14, 59)
    assert (len(second), second.number_of_edges()) == (23, 158)
    host = {1: first, 2: second}
    cases = []
    for level, target_spec, expected_copies in EXPECTED:
        target = target_graph(target_spec)
        result = screen(host[level], target)
        if result["induced_target_sets"] != expected_copies:
            raise AssertionError("Induced-target count differs from fixed result")
        cases.append({"level": level, "target": target_spec,
                      "target_order": len(target), **result})
    return {"schema": 1, "source_graph6": SOURCE_GRAPH6,
            "scope": "raw K and K² ordinary graph retractions only",
            "interpretation": "No positive or negative K-behavior verdict",
            "cases": cases}


def independent_clique_graph(graph: nx.Graph) -> nx.Graph:
    """Construct K(graph) without find_cliques or the search's helper.

    All graphs replayed here have at most fourteen labeled vertices.
    Enumerate all nonempty vertex subsets, test completeness directly,
    and retain exactly the maximal complete subsets.
    """
    nodes = sorted(graph)
    if nodes != list(range(len(nodes))) or len(nodes) > 14:
        raise ValueError("Unexpected vertex labels/order in independent replay")
    facets = []
    for mask in range(1, 1 << len(nodes)):
        subset = [v for v in nodes if mask & (1 << v)]
        if not all(graph.has_edge(u, v) for u, v in combinations(subset, 2)):
            continue
        if any(
            not (mask & (1 << w))
            and all(graph.has_edge(w, v) for v in subset)
            for w in nodes
        ):
            continue
        facets.append(frozenset(subset))
    facets.sort(key=lambda q: sum(1 << v for v in q))
    result = nx.Graph()
    result.add_nodes_from(range(len(facets)))
    for i, j in combinations(range(len(facets)), 2):
        if not facets[i].isdisjoint(facets[j]):
            result.add_edge(i, j)
    return result


def independent_target_graph(spec: str) -> nx.Graph:
    """Build named target without using the generator's target_graph."""
    if spec.startswith("K:"):
        return independent_clique_graph(decode(spec[2:]))
    return decode(spec)


def replay_local_obstruction(
    host: nx.Graph, vertices: tuple[int, ...], outside: int
) -> bool:
    """Independently evaluate the closed-neighborhood intersection D_v."""
    fixed = set(vertices)
    if outside not in host or outside in fixed:
        return False
    possible = {
        candidate for candidate in fixed
        if all(
            candidate == neighbor or host.has_edge(candidate, neighbor)
            for neighbor in host[outside] if neighbor in fixed
        )
    }
    return not possible


def verify(saved: dict) -> None:
    """Independently replay every recorded witness and completeness claim.

    Unlike the original implementation, this function never calls run(),
    screen(), target_graph(), clique_graph(), or obstructed_outside_vertex().
    The first two raw iterates are independently reconstructed by exhaustive
    complete-subset enumeration, and all local obstruction domains are
    recomputed directly from adjacency. VF2 is used only to independently
    check the completeness of the recorded induced-target vertex sets.
    """
    if not isinstance(saved, dict) or set(saved) != {
        "schema", "source_graph6", "scope", "interpretation", "cases"
    }:
        raise ValueError("Malformed retraction screen report")
    if (
        saved["schema"] != 1 or saved["source_graph6"] != SOURCE_GRAPH6
        or saved["scope"] != "raw K and K² ordinary graph retractions only"
        or saved["interpretation"] != "No positive or negative K-behavior verdict"
        or not isinstance(saved["cases"], list)
        or len(saved["cases"]) != len(EXPECTED)
    ):
        raise ValueError("Unexpected saved report header or case count")

    first = independent_clique_graph(decode(SOURCE_GRAPH6))
    second = independent_clique_graph(first)
    if (len(first), first.number_of_edges()) != (14, 59):
        raise ValueError("Independent K(G) construction disagrees")
    if (len(second), second.number_of_edges()) != (23, 158):
        raise ValueError("Independent K²(G) construction disagrees")
    hosts = {1: first, 2: second}

    for (level, spec, expected), row in zip(EXPECTED, saved["cases"]):
        if not isinstance(row, dict) or set(row) != {
            "level", "target", "target_order", "induced_target_sets",
            "failed_local_condition", "witnesses"
        }:
            raise ValueError("Malformed target case")
        target = independent_target_graph(spec)
        if (
            row["level"] != level or row["target"] != spec
            or row["target_order"] != len(target)
            or row["induced_target_sets"] != expected
            or row["failed_local_condition"] != expected
            or not isinstance(row["witnesses"], list)
            or len(row["witnesses"]) != expected
        ):
            raise ValueError("Reported target metadata or counts disagree")

        host = hosts[level]
        recorded = set()
        for witness in row["witnesses"]:
            if not isinstance(witness, dict) or set(witness) != {
                "vertices", "outside"
            }:
                raise ValueError("Malformed local obstruction witness")
            vertices = witness["vertices"]
            outside = witness["outside"]
            if (
                not isinstance(vertices, list)
                or len(vertices) != len(target)
                or any(type(v) is not int or v not in host for v in vertices)
                or vertices != sorted(set(vertices))
                or type(outside) is not int
                or not nx.is_isomorphic(host.subgraph(vertices), target)
                or not replay_local_obstruction(host, tuple(vertices), outside)
            ):
                raise ValueError("Induced target or outside-vertex obstruction invalid")
            key = tuple(vertices)
            if key in recorded:
                raise ValueError("Duplicate induced target witness")
            recorded.add(key)

        # Verify *completeness* as well as validity. The saved candidates
        # must match every induced embedding, after deduplicating target
        # automorphisms. This check does not trust run() or its counts.
        exhaustive = {
            tuple(sorted(mapping))
            for mapping in nx.isomorphism.GraphMatcher(
                host, target
            ).subgraph_isomorphisms_iter()
        }
        if recorded != exhaustive or len(exhaustive) != expected:
            raise ValueError("Missing or unexpected induced target vertex sets")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "verify"))
    parser.add_argument("--file", type=argparse.FileType("r"))
    args = parser.parse_args()
    result = run()
    if args.command == "verify":
        if args.file is None:
            parser.error("verify requires --file")
        verify(json.load(args.file))
    else:
        print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
