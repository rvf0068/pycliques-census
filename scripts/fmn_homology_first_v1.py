"""Replayable homology-first investigation of the path-join spheres F_(m,n).

All graph constructions and tests below are finite and exact; no random
choices, external solver, homology estimates or conjectural divergence
references enter the certificates. Nothing here proves K-divergence.

Generate:
  python scripts/fmn_homology_first_v1.py build --max-n 10 --output /tmp/fmn.json
Verify (recomputes graph, all collapses, full GF(2) boundary ranks):
  python scripts/fmn_homology_first_v1.py verify --input /tmp/fmn.json
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from itertools import combinations
import json
from pathlib import Path

import networkx as nx

MAX_FACES = 500_000
MAX_ITERATE_ORDER = 256


def family_graph(m: int, n: int) -> nx.Graph:
    """Flag sphere: boundary of P_m * P_n, with both paths vertex-labelled."""
    if not (3 <= m <= n):
        raise ValueError("Require 3 <= m <= n")
    graph = nx.Graph()
    graph.add_nodes_from(range(m + n))
    graph.add_edges_from((i, i + 1) for i in range(m - 1))
    graph.add_edges_from((m + j, m + j + 1) for j in range(n - 1))
    graph.add_edges_from(
        (i, m + j) for i in range(m) for j in range(n)
        if i in (0, m - 1) or j in (0, n - 1)
    )
    return graph


def independent_family_graph(m: int, n: int) -> nx.Graph:
    """Reconstruct F from its 2-dimensional facets, not its edge definition."""
    graph = nx.Graph()
    graph.add_nodes_from(range(m + n))
    facets = (
        [(a, m + j, m + j + 1)
         for a in (0, m - 1) for j in range(n - 1)]
        + [(m + b, i, i + 1)
           for b in (0, n - 1) for i in range(m - 1)]
    )
    for face in facets:
        graph.add_edges_from(combinations(face, 2))
    return graph


def raw_clique_graph(graph: nx.Graph) -> nx.Graph:
    """Deterministic vertex indexing by clique bitmasks at every iteration."""
    if len(graph) > MAX_ITERATE_ORDER:
        raise RuntimeError("Iterate size limit")
    cliques = sorted(
        (frozenset(q) for q in nx.find_cliques(graph)),
        key=lambda q: sum(1 << v for v in q),
    )
    if len(cliques) > MAX_ITERATE_ORDER:
        raise RuntimeError("Clique count limit")
    result = nx.Graph()
    result.add_nodes_from(range(len(cliques)))
    result.add_edges_from(
        (i, j) for i in range(len(cliques))
        for j in range(i + 1, len(cliques)) if cliques[i] & cliques[j]
    )
    return result


def third_iterate(m: int, n: int) -> tuple[nx.Graph, list[list[int]]]:
    graph = family_graph(m, n)
    stats = [[len(graph), graph.number_of_edges()]]
    for _ in range(3):
        graph = raw_clique_graph(graph)
        stats.append([len(graph), graph.number_of_edges()])
    return graph, stats


def link_fold_sequence(graph: nx.Graph, vertex: int) -> list[list[int]] | None:
    """A constructive contractibility certificate for an open neighborhood."""
    link = graph.subgraph(graph.neighbors(vertex)).copy()
    if not link:
        return None
    folds: list[list[int]] = []
    while len(link) > 1:
        pair = None
        for x in list(link):
            closed_x = set(link[x]) | {x}
            for y in link[x]:
                if closed_x <= (set(link[y]) | {y}):
                    pair = (x, y)
                    break
            if pair is not None:
                break
        if pair is None:
            return None
        x, y = pair
        folds.append([x, y])
        link.remove_node(x)
    return folds


def reduce_open_links(graph: nx.Graph) -> tuple[nx.Graph, list[dict]]:
    """Remove vertices with dismantlable open links; preserve clique homotopy."""
    result = graph.copy()
    trace = []
    while len(result) > 1:
        chosen = None
        for v in sorted(result, key=lambda u: (result.degree(u), u)):
            folds = link_fold_sequence(result, v)
            if folds is not None:
                chosen = (v, folds)
                break
        if chosen is None:
            break
        v, folds = chosen
        trace.append({"vertex": v, "link_folds": folds})
        result.remove_node(v)
    return result, trace


def faces_of(graph: nx.Graph) -> set[frozenset[int]]:
    """Complete face set of the flag complex, with a hard resource budget."""
    faces: set[frozenset[int]] = set()
    for facet in nx.find_cliques(graph):
        for size in range(1, len(facet) + 1):
            for face in combinations(sorted(facet), size):
                faces.add(frozenset(face))
                if len(faces) > MAX_FACES:
                    raise RuntimeError("Face budget exceeded; no homology verdict")
    return faces


def face_betti(faces: set[frozenset[int]]) -> tuple[dict[int, int], dict[int, int]]:
    """Complete exact reduced mod-2 homology using bitset Gaussian elimination."""
    columns: dict[int, list[tuple[int, ...]]] = defaultdict(list)
    for face in faces:
        columns[len(face) - 1].append(tuple(sorted(face)))
    ordered = {k: sorted(v) for k, v in columns.items()}
    f = {k: len(v) for k, v in ordered.items()}
    ranks: dict[int, int] = {}
    for k in range(1, max(ordered) + 1):
        positions = {face: i for i, face in enumerate(ordered[k - 1])}
        pivots: dict[int, int] = {}
        for face in ordered[k]:
            vector = 0
            for j in range(len(face)):
                vector ^= 1 << positions[face[:j] + face[j + 1:]]
            while vector:
                lead = vector.bit_length() - 1
                previous = pivots.get(lead)
                if previous is None:
                    pivots[lead] = vector
                    break
                vector ^= previous
        ranks[k] = len(pivots)
    betti = {
        k: f[k] - ranks.get(k, 0) - ranks.get(k + 1, 0)
           - (1 if k == 0 else 0)
        for k in f
    }
    if any(v < 0 for v in betti.values()):
        raise AssertionError("Negative Betti number")
    lhs = sum((-1) ** k * count for k, count in f.items()) - 1
    rhs = sum((-1) ** k * count for k, count in betti.items())
    if lhs != rhs:
        raise AssertionError("Euler/Poincare cross-check failed")
    return f, betti


def elementary_collapses(
    faces: set[frozenset[int]],
) -> tuple[set[frozenset[int]], list[list[list[int]]]]:
    """Greedy elementary collapses; transcript stores each facet/free face."""
    current = set(faces)
    trace = []
    while True:
        by_size: dict[int, list[frozenset[int]]] = defaultdict(list)
        for face in current:
            by_size[len(face)].append(face)
        chosen = None
        for size in sorted(by_size, reverse=True):
            if size <= 1:
                continue
            cofaces = Counter(
                facet - {v} for facet in by_size[size] for v in facet
            )
            for facet in sorted(by_size[size], key=lambda q: tuple(sorted(q))):
                if any(facet < larger for larger in current):
                    continue
                for v in sorted(facet):
                    free_face = facet - {v}
                    if cofaces[free_face] == 1:
                        chosen = (facet, free_face)
                        break
                if chosen is not None:
                    break
            if chosen is not None:
                break
        if chosen is None:
            return current, trace
        facet, free_face = chosen
        current.remove(facet)
        current.remove(free_face)
        trace.append([sorted(facet), sorted(free_face)])


def is_triangulated_sphere(faces: set[frozenset[int]]) -> bool:
    """Connected 2-manifold with Euler characteristic 2, checked by links."""
    if not faces or any(len(face) > 3 for face in faces):
        return False
    verts = [next(iter(q)) for q in faces if len(q) == 1]
    edges = [q for q in faces if len(q) == 2]
    triangles = [q for q in faces if len(q) == 3]
    if len(verts) - len(edges) + len(triangles) != 2:
        return False
    incidences = Counter(
        frozenset(e) for t in triangles for e in combinations(t, 2)
    )
    if any(incidences[e] != 2 for e in edges):
        return False
    graph = nx.Graph()
    graph.add_nodes_from(verts)
    graph.add_edges_from(tuple(e) for e in edges)
    if not graph or not nx.is_connected(graph):
        return False
    for v in verts:
        link = nx.Graph()
        link.add_nodes_from(graph[v])
        link.add_edges_from(tuple(t - {v}) for t in triangles if v in t)
        if not link or not nx.is_connected(link):
            return False
        if any(degree != 2 for _, degree in link.degree()):
            return False
    return True


def certify_case(m: int, n: int) -> dict:
    raw, stats = third_iterate(m, n)
    core, folds = reduce_open_links(raw)
    core_faces = faces_of(core)
    f, betti = face_betti(core_faces)
    result = {
        "m": m, "n": n, "iterate_stats": stats,
        "deletions": folds,
        "core_nodes": sorted(core),
        "core_edges": core.number_of_edges(),
        "core_f": f,
        "reduced_betti_mod2": betti,
    }
    if (m, n) not in ((4, 4), (4, 5)):
        end, collapses = elementary_collapses(core_faces)
        if not is_triangulated_sphere(end):
            raise AssertionError(f"Missing sphere certificate for F_{m,n}")
        result["elementary_collapses"] = collapses
        result["terminal_f"] = {
            k: sum(len(face) == k + 1 for face in end) for k in range(3)
        }
    return result


def _full_face_cofaces(faces: set[frozenset[int]], free: frozenset[int]):
    return [q for q in faces if free < q]


def verify_case(record: dict) -> None:
    """Replay every graph construction, link fold and simplicial collapse."""
    m, n = record["m"], record["n"]
    assert nx.utils.graphs_equal(family_graph(m, n), independent_family_graph(m, n))
    raw, stats = third_iterate(m, n)
    assert stats == record["iterate_stats"]
    if (m, n) == (4, 4):
        assert nx.is_isomorphic(family_graph(m, n),
                                nx.from_graph6_bytes(b"GQyuzw"))
    if (m, n) == (4, 5):
        assert nx.is_isomorphic(family_graph(m, n),
                                nx.from_graph6_bytes(br"HCZTf\}"))
    graph = raw.copy()
    for step in record["deletions"]:
        v = step["vertex"]
        assert v in graph
        link = graph.subgraph(graph[v]).copy()
        assert link
        for x, y in step["link_folds"]:
            assert x != y and x in link and y in link
            assert (set(link[x]) | {x}) <= (set(link[y]) | {y})
            link.remove_node(x)
        assert len(link) == 1
        graph.remove_node(v)
    assert sorted(graph) == record["core_nodes"]
    assert graph.number_of_edges() == record["core_edges"]
    faces = faces_of(graph)
    f, betti = face_betti(faces)
    assert {str(k): v for k, v in f.items()} == record["core_f"]
    assert {str(k): v for k, v in betti.items()} == record["reduced_betti_mod2"]
    positive = {k: v for k, v in betti.items() if v}
    if (m, n) == (4, 4):
        assert positive == {5: 5}
    elif (m, n) == (4, 5):
        assert positive == {3: 3}
    else:
        assert positive == {2: 1}
        for full, free in record["elementary_collapses"]:
            facet = frozenset(full)
            face = frozenset(free)
            assert facet in faces and face in faces
            assert face < facet and len(facet) == len(face) + 1
            assert _full_face_cofaces(faces, face) == [facet]
            faces.remove(facet)
            faces.remove(face)
        assert is_triangulated_sphere(faces)
        terminal = {
            str(k): sum(len(face) == k + 1 for face in faces) for k in range(3)
        }
        assert terminal == record["terminal_f"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify"))
    parser.add_argument("--max-n", type=int, default=10)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--input", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        if not 4 <= args.max_n <= 12:
            parser.error("--max-n must be between 4 and 12")
        records = [certify_case(m, n)
                   for m in range(4, args.max_n + 1)
                   for n in range(m, args.max_n + 1)]
        result = {"schema": 1, "cases": records}
        for record in records:
            verify_case(json.loads(json.dumps(record)))
        if args.output:
            args.output.write_text(json.dumps(result, indent=2) + "\n")
        for case in records:
            positive = {k: v for k, v in case["reduced_betti_mod2"].items() if v}
            print(f"F_{{{case['m']},{case['n']}}}: "
                  f"K3={case['iterate_stats'][3][0]} "
                  f"core={len(case['core_nodes'])} "
                  f"betti={positive} "
                  f"sphere={bool(case.get('terminal_f'))}")
        print(f"VERIFIED {len(records)} finite cases")
    else:
        if args.input is None:
            parser.error("verify requires --input")
        result = json.loads(args.input.read_text())
        assert result["schema"] == 1
        for record in result["cases"]:
            verify_case(record)
        print(f"REPLAYED {len(result['cases'])} finite certificates")


if __name__ == "__main__":
    main()
