"""Reproducible elementary collapses to S^2 for two order-nine sphere cores.

NetworkX only. Simplices are positive integer vertex-set bitmasks.
The build command emits complete step-by-step certificates locally;
verify checks every step against the full simplicial face poset.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import heapq
from itertools import combinations
import json
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research/order9_two_sphere_collapses_v1/certificates.json"
INPUTS = {"208409": r"HCZTf\}", "248687": "HEher^{"}
EXPECTED = {
    "208409": {"raw_orders": [9, 14, 23], "steps": [0, 84, 1054],
               "residual_f": [[9, 21, 14], [14, 36, 24], [12, 30, 20]]},
    "248687": {"raw_orders": [9, 14, 23], "steps": [0, 76, 1048],
               "residual_f": [[9, 21, 14], [14, 36, 24], [13, 33, 22]]},
}


def raw_K(graph: nx.Graph) -> nx.Graph:
    facets = sorted(
        (frozenset(q) for q in nx.find_cliques(graph)),
        key=lambda q: sum(1 << v for v in q),
    )
    result = nx.Graph()
    result.add_nodes_from(range(len(facets)))
    result.add_edges_from((i, j) for i in range(len(facets))
                          for j in range(i + 1, len(facets)) if facets[i] & facets[j])
    return result


def simplex_faces(graph: nx.Graph) -> set[int]:
    faces = set()
    for clique in nx.find_cliques(graph):
        singleton_masks = [1 << v for v in clique]
        for size in range(1, len(singleton_masks) + 1):
            faces.update(sum(q) for q in combinations(singleton_masks, size))
    return faces


def boundary(face: int):
    remaining = face
    while remaining:
        bit = remaining & -remaining
        remaining -= bit
        if face != bit:
            yield face - bit


def upper_degrees(faces: set[int]) -> Counter[int]:
    counts: Counter[int] = Counter()
    for sigma in faces:
        for tau in boundary(sigma):
            counts[tau] += 1
    return counts


def collapse(original: set[int]):
    faces = set(original)
    upper = upper_degrees(faces)
    facets = {f for f in faces if upper[f] == 0}
    queue = []

    def enqueue(sigma):
        if sigma not in faces or upper[sigma] != 0:
            return
        for tau in boundary(sigma):
            if tau in faces and upper[tau] == 1:
                heapq.heappush(queue, (-sigma.bit_count(), sigma, tau))
                return

    for sigma in facets:
        enqueue(sigma)
    pairs = []
    while queue:
        _, sigma, tau = heapq.heappop(queue)
        if (sigma not in faces or tau not in faces
                or upper[sigma] != 0 or upper[tau] != 1
                or tau not in set(boundary(sigma))):
            continue
        faces.difference_update((sigma, tau))
        pairs.append([sigma, tau])
        facets.difference_update((sigma, tau))
        for removed in (sigma, tau):
            for subface in boundary(removed):
                if subface in faces:
                    upper[subface] -= 1
                    if upper[subface] < 0:
                        raise AssertionError("Invalid upper-degree accounting")
                    if upper[subface] == 0:
                        facets.add(subface)
                        enqueue(subface)
                    elif upper[subface] == 1:
                        for v in range(max(faces).bit_length()):
                            possible = subface | (1 << v)
                            if possible in facets:
                                enqueue(possible)
    return faces, pairs


def replay(original: set[int], pairs: list[list[int]]) -> set[int]:
    """Independent verifier: recompute all face-poset cofaces on every step."""
    faces = set(original)
    for index, (sigma, tau) in enumerate(pairs):
        if sigma not in faces or tau not in faces:
            raise ValueError(f"Step {index}: missing simplex")
        if tau not in set(boundary(sigma)):
            raise ValueError(f"Step {index}: not codimension one")
        if any((f & sigma) == sigma and f != sigma for f in faces):
            raise ValueError(f"Step {index}: sigma is not maximal")
        cofaces = [f for f in faces if f.bit_count() == tau.bit_count() + 1
                   and (f & tau) == tau]
        if cofaces != [sigma]:
            raise ValueError(f"Step {index}: tau is not free")
        faces.remove(sigma)
        faces.remove(tau)
    return faces


def sphere(faces: set[int]) -> dict:
    vertices = sorted(f for f in faces if f.bit_count() == 1)
    edges = sorted(f for f in faces if f.bit_count() == 2)
    triangles = sorted(f for f in faces if f.bit_count() == 3)
    if len(faces) != len(vertices) + len(edges) + len(triangles):
        raise ValueError("Residual complex dimension is not two")
    fvector = [len(vertices), len(edges), len(triangles)]
    if fvector[0] - fvector[1] + fvector[2] != 2:
        raise ValueError("Euler characteristic is not two")
    if any(sum(t & e == e for t in triangles) != 2 for e in edges):
        raise ValueError("An edge does not lie in two triangles")
    skeleton = nx.Graph()
    skeleton.add_nodes_from(vertices)
    for edge in edges:
        endpoints = [v for v in vertices if v & edge]
        if len(endpoints) != 2:
            raise ValueError("Bad edge mask")
        skeleton.add_edge(*endpoints)
    if not nx.is_connected(skeleton):
        raise ValueError("Disconnected complex")
    for v in vertices:
        link = nx.Graph()
        for t in triangles:
            if v & t:
                ends = [w for w in vertices if w != v and w & t]
                if len(ends) != 2:
                    raise ValueError("Bad triangle mask")
                link.add_edge(*ends)
        if not nx.is_connected(link) or any(d != 2 for _, d in link.degree()):
            raise ValueError("Vertex link not a single cycle")
    return {"fvector": fvector, "euler": 2, "connected": True,
            "edge_degree_two": True, "vertex_links_are_cycles": True}


def build() -> dict:
    entries = {}
    for index, graph6 in INPUTS.items():
        graph = nx.from_graph6_bytes(graph6.encode("ascii"))
        result = []
        for k in range(3):
            original = simplex_faces(graph)
            remaining, pairs = collapse(original)
            if replay(original, pairs) != remaining:
                raise AssertionError("Independent certificate replay mismatch")
            shape = sphere(remaining)
            if (len(graph) != EXPECTED[index]["raw_orders"][k]
                    or len(pairs) != EXPECTED[index]["steps"][k]
                    or shape["fvector"] != EXPECTED[index]["residual_f"][k]):
                raise AssertionError("Unrecognized source or collapse fingerprint")
            result.append({"level": k, "order": len(graph),
                           "edges": graph.number_of_edges(),
                           "initial_faces": len(original), "pairs": pairs,
                           "residual_triangles": sorted(
                               f for f in remaining if f.bit_count() == 3),
                           "remaining": shape})
            if k < 2:
                graph = raw_K(graph)
        entries[index] = {"graph6": graph6, "iterates": result}
    return {"schema": 1,
            "theorem": "Delta(K^j(G)) homotopy equivalent to S^2, j=0,1,2",
            "graphs": entries}


def verify(path: Path) -> None:
    expected = build()
    saved = json.loads(path.read_text(encoding="utf-8"))
    if expected != saved:
        raise ValueError("Saved certificate differs from reproducible search")
    for record in saved["graphs"].values():
        graph = nx.from_graph6_bytes(record["graph6"].encode("ascii"))
        for level in record["iterates"]:
            faces = replay(simplex_faces(graph), level["pairs"])
            if (sphere(faces) != level["remaining"] or
                    sorted(f for f in faces if f.bit_count() == 3)
                    != level["residual_triangles"]):
                raise ValueError("Invalid final residual sphere")
            graph = raw_K(graph)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify"))
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.command == "build":
        data = json.dumps(build(), sort_keys=True, indent=2) + "\n"
        if args.output.exists() and args.output.read_text(encoding="utf-8") != data:
            raise ValueError("Refusing to overwrite different existing artifact")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(data, encoding="utf-8")
    verify(args.output)
    print("Verified two exact S2 collapse certificates through K^2")
    print("sha256", hashlib.sha256(args.output.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
