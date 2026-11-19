"""Exact wedge-of-three-3-spheres certificate for two third clique iterates.

For each raw K^3(G), delete vertices with dismantlable *open* neighborhoods,
independently checking their link fold traces. The final induced graph is
the complement of the octagonal prism C8 square K2. Its clique complex
collapses to a 3-complex R such that removing three tetrahedral facets
leaves a complex collapsing to a point.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import networkx as nx

from core9_sphere_collapse_v1 import INPUTS, raw_K, simplex_faces, collapse, replay

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research/order9_two_sphere_collapses_v1/prism_wedge_certificate.json"
TETRAHEDRA = [20490, 34849, 36929]
EXPECTED = {
    "208409": {"initial": [56, 1060], "deleted": 40, "last": [16, 96]},
    "248687": {"initial": [60, 1225], "deleted": 44, "last": [16, 96]},
}


def closed(graph: nx.Graph, x: int) -> set[int]:
    return set(graph[x]) | {x}


def dismantle_link(link: nx.Graph) -> list[list[int]] | None:
    """Complete deterministic closed-neighborhood fold sequence, if any."""
    h = link.copy()
    if not h:
        return None
    pairs = []
    while len(h) > 1:
        pair = next(
            ((x, y) for x in sorted(h) for y in sorted(h)
             if x != y and closed(h, x) <= closed(h, y)),
            None,
        )
        if pair is None:
            return None
        x, y = pair
        pairs.append([x, y])
        h.remove_node(x)
    return pairs


def reduce_by_links(graph: nx.Graph) -> tuple[nx.Graph, list[dict]]:
    h = graph.copy()
    trace = []
    while True:
        found = None
        for v in sorted(h, key=lambda u: (h.degree(u), u)):
            folds = dismantle_link(h.subgraph(h[v]))
            if folds is not None:
                found = (v, folds)
                break
        if found is None:
            break
        v, folds = found
        trace.append({"removed": v, "link_folds": folds})
        h.remove_node(v)
    return h, trace


def replay_deletions(graph: nx.Graph, trace: list[dict]) -> nx.Graph:
    """Verify each open link is dismantlable immediately before deletion."""
    h = graph.copy()
    for index, row in enumerate(trace):
        v = row["removed"]
        if v not in h:
            raise ValueError(f"Invalid vertex deletion {index}")
        link = h.subgraph(list(h[v])).copy()
        if not link:
            raise ValueError(f"Empty open neighborhood at step {index}")
        for x, y in row["link_folds"]:
            if x not in link or y not in link or x == y:
                raise ValueError("Bad link-fold vertices")
            if not closed(link, x) <= closed(link, y):
                raise ValueError("Invalid dominated-vertex fold in open link")
            link.remove_node(x)
        if len(link) != 1:
            raise ValueError("Open neighborhood did not dismantle to one vertex")
        h.remove_node(v)
    return h


def prism() -> nx.Graph:
    """Complement of the circular ladder (octagonal prism graph)."""
    return nx.complement(nx.circular_ladder_graph(8))


def prism_wedge() -> dict:
    graph = prism()
    original = simplex_faces(graph)
    r, first_pairs = collapse(original)
    if replay(original, first_pairs) != r:
        raise AssertionError("First simplicial collapse failed replay")
    for tau in TETRAHEDRA:
        if (tau not in r or tau.bit_count() != 4
                or any((f & tau) == tau and f != tau for f in r)):
            raise AssertionError("The removed tetrahedron is not maximal")
    contractible = r - set(TETRAHEDRA)
    point, second_pairs = collapse(contractible)
    if replay(contractible, second_pairs) != point or len(point) != 1:
        raise AssertionError("Complement of three tetrahedra not collapsible")
    fvector = [sum(f.bit_count() == i for f in r) for i in range(1, 5)]
    if (len(original), len(first_pairs), len(r), fvector,
            len(contractible), len(second_pairs)) != (
            1154, 407, 340, [16, 82, 153, 89], 337, 168
    ):
        raise AssertionError("Prism clique-complex fingerprint changed")
    return {"initial_faces": len(original), "first_pairs": first_pairs,
            "residual_fvector": fvector, "removed_tetrahedra": TETRAHEDRA,
            "second_pairs": second_pairs,
            "final_vertex_mask": next(iter(point))}


def build() -> dict:
    target = prism()
    result = {}
    for index, graph6 in INPUTS.items():
        graph = nx.from_graph6_bytes(graph6.encode("ascii"))
        for _ in range(3):
            graph = raw_K(graph)
        if [len(graph), graph.number_of_edges()] != EXPECTED[index]["initial"]:
            raise AssertionError("Unexpected third clique iterate")
        core, deletions = reduce_by_links(graph)
        if (len(deletions) != EXPECTED[index]["deleted"]
                or [len(core), core.number_of_edges()] != EXPECTED[index]["last"]
                or not nx.is_isomorphic(core, target)):
            raise AssertionError("Common octagonal-prism core not found")
        if not nx.is_isomorphic(replay_deletions(graph, deletions), core):
            raise AssertionError("Independent vertex-link replay disagrees")
        phi = next(nx.isomorphism.GraphMatcher(core, target).isomorphisms_iter())
        result[index] = {"graph6": graph6, "deletions": deletions,
                         "core_vertices": sorted(core),
                         "core_to_prism": [[v, phi[v]] for v in sorted(phi)]}
    return {"schema": 1,
            "statement": "Delta(K^3(G)) homotopy equivalent to wedge of 3 copies of S^3",
            "graphs": result, "prism": prism_wedge()}


def verify(data: dict) -> None:
    canonical = prism()
    if data != build():
        raise ValueError("Saved proof differs from freshly generated witness")
    for index, row in data["graphs"].items():
        graph = nx.from_graph6_bytes(row["graph6"].encode("ascii"))
        for _ in range(3):
            graph = raw_K(graph)
        core = replay_deletions(graph, row["deletions"])
        phi = dict(row["core_to_prism"])
        if set(phi) != set(core) or set(phi.values()) != set(canonical):
            raise ValueError("Prism correspondence is not a bijection")
        if any(core.has_edge(a, b) != canonical.has_edge(phi[a], phi[b])
               for a in core for b in core if a < b):
            raise ValueError("Final core map is not an induced isomorphism")
        if sorted(core) != row["core_vertices"]:
            raise ValueError("Invalid terminal vertex set")
    certificate = data["prism"]
    original = simplex_faces(canonical)
    r = replay(original, certificate["first_pairs"])
    if [sum(f.bit_count() == i for f in r) for i in range(1, 5)] != certificate["residual_fvector"]:
        raise ValueError("First prism collapse does not leave recorded 3-complex")
    tetra = certificate["removed_tetrahedra"]
    if (len(set(tetra)) != 3 or any(
        t not in r or t.bit_count() != 4
        or any((x & t) == t and x != t for x in r) for t in tetra
    )):
        raise ValueError("Three removed tetrahedra not maximal")
    final = replay(r - set(tetra), certificate["second_pairs"])
    if final != {certificate["final_vertex_mask"]}:
        raise ValueError("Punctured complex does not collapse to one point")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify"))
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.command == "build":
        value = json.dumps(build(), sort_keys=True, indent=2) + "\n"
        if args.output.exists() and args.output.read_text(encoding="utf-8") != value:
            raise ValueError("Refusing to overwrite a different existing witness")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(value, encoding="utf-8")
    data = json.loads(args.output.read_text(encoding="utf-8"))
    verify(data)
    print("CERTIFIED: Delta(K^3(G)) ~= S3 wedge S3 wedge S3, both order-nine graphs")
    print("sha256", hashlib.sha256(args.output.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
