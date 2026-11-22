"""Replay the exact P4 -> O4 retraction for ten-vertex McKay 10472553.

Independent of the coaffine discovery routine; NetworkX-only default replay.
Optional --public cross-check uses the public pycliques functions at all levels
and its independent octahedron/retraction verifiers. Does not change census.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
from pathlib import Path

import networkx as nx

# All invariants below use assert. Fail closed under -O / PYTHONOPTIMIZE.
if sys.flags.optimize:
    raise RuntimeError("Certificate verification must run without Python optimization")

HERE = Path(__file__).resolve().parent
CERT = HERE / "certificate.json"
SOURCE_G6 = "ICZTeYj^_"
ORDERS = (10, 16, 26, 63, 365)
EDGES = (24, 69, 186, 1201, 42351)
P4_SHA256 = "8cff877406cde4b00bcadee4dca5986972ec9fe6d13cf892347a96bedcf1cff9"


def pare(g: nx.Graph) -> nx.Graph:
    """Independent sequential closed-neighborhood dismantling."""
    h = g.copy()
    while True:
        closed = {v: {v} | set(h[v]) for v in h}
        dominated = next(
            (u for u in h for v in h if u != v and closed[u] <= closed[v]),
            None,
        )
        if dominated is None:
            return h
        h.remove_node(dominated)


def next_iterate(g: nx.Graph) -> nx.Graph:
    """Independently construct K(g) by pairwise clique intersections."""
    cliques = [frozenset(c) for c in nx.find_cliques(g)]
    k = nx.Graph()
    k.add_nodes_from(range(len(cliques)))
    for i, c in enumerate(cliques):
        for j in range(i + 1, len(cliques)):
            if c & cliques[j]:
                k.add_edge(i, j)
    return pare(k)


def signature(g: nx.Graph) -> str:
    edges = sorted((min(u, v), max(u, v)) for u, v in g.edges())
    data = "\n".join(f"{u},{v}" for u, v in edges)
    return hashlib.sha256(data.encode("ascii")).hexdigest()


def reconstruct(*, public: bool = False) -> nx.Graph:
    h = pare(nx.from_graph6_bytes(SOURCE_G6.encode("ascii")))
    if public:
        import pycliques

        p = pycliques.completely_pared_graph(
            nx.from_graph6_bytes(SOURCE_G6.encode("ascii"))
        )
    for depth, (order, edges) in enumerate(zip(ORDERS, EDGES, strict=True)):
        assert (len(h), h.number_of_edges()) == (order, edges), depth
        if public:
            assert set(h) == set(p) and nx.utils.edges_equal(h.edges(), p.edges())
        if depth == 4:
            break
        if public:
            # Public clique vertices are frozensets. Re-label them in their
            # insertion order, matching the independent maximal-clique index.
            kp = pycliques.clique_graph(p)
            assert kp is not None
            kp = nx.relabel_nodes(kp, {v: i for i, v in enumerate(kp)}, copy=True)
            p = pycliques.completely_pared_graph(kp)
        h = next_iterate(h)
    if public:
        assert set(h) == set(p) and nx.utils.edges_equal(h.edges(), p.edges())
    return h


def verify(*, public: bool = False) -> None:
    saved = json.loads(CERT.read_text(encoding="utf-8"))
    assert (saved["mckay_index"], saved["pared_depth"], saved["original_graph6"]) == (
        10472553, 4, SOURCE_G6
    )
    assert saved["schema"] == 2
    assert (saved["host_order"], saved["host_edges"]) == (365, 42351)
    assert saved["host_edge_sha256"] == P4_SHA256
    assert saved["image_encoding"] == "uint8_target_ordinal_in_sorted_host_order"
    # Independently match the claimed original graph to the frozen v16 census.
    frozen = HERE.parents[1] / "indeterminate_order_10_v16.txt"
    entries = [line for line in frozen.read_text(encoding="utf-8").splitlines()
               if line and not line.startswith("#")]
    matching = [line for line in entries if line.split()[0] == "10472553"]
    assert matching == [f"10472553 10 {SOURCE_G6} - - -"], (
        "Wrong McKay index, graph6, or frozen v16 census status"
    )

    h = reconstruct(public=public)
    assert signature(h) == P4_SHA256, "Unexpected P4 labeling or edges"

    images = base64.b64decode(saved["images_b64"], validate=True)
    assert len(images) == len(h), "Incomplete target-ordinal image array"
    pairs = [tuple(map(int, pair)) for pair in saved["antipodal_pairs"]]
    assert len(pairs) == 4
    target_vertices = {v for a, b in pairs for v in (a, b)}
    assert len(target_vertices) == 8
    target_order = sorted(target_vertices)
    assert saved["target_order"] == target_order
    assert all(image_index < len(target_order) for image_index in images)
    # Encode each projection image by its position in the SORTED target,
    # ordered by SORTED host labels (which may have gaps after paring).
    host_nodes = sorted(h)
    assert len(host_nodes) == len(set(host_nodes))
    projection = dict(zip(
        host_nodes, (target_order[k] for k in images), strict=True
    ))
    assert set(projection) == set(h), "Projection is not total"
    assert set(projection.values()) == target_vertices
    assert all(projection[v] == v for v in target_vertices)

    target = h.subgraph(target_vertices)
    complement = nx.complement(target)
    assert all(d == 1 for _, d in complement.degree()), "Target is not O4"
    assert {frozenset(pair) for pair in pairs} == {
        frozenset(edge) for edge in complement.edges()
    }, "Wrong antipodal pairs"
    assert all(
        projection[a] == projection[b]
        or h.has_edge(projection[a], projection[b])
        for a, b in h.edges()
    ), "Projection does not preserve a host edge"

    if public:
        import pycliques

        assert pycliques.verify_induced_octahedron(h, pairs)
        assert pycliques.verify_retraction_witness(
            h, target, (projection, {v: v for v in target})
        )
    print(
        "PROVED_MCKAY_10472553_K_DIVERGENT P4_ORDER=365 "
        "P4_EDGES=42351 O4_PAIRS=4 ALL_365_IMAGES_VERIFIED "
        + ("PUBLIC_PYCLIQUES_REPLAY=PASS" if public else "NETWORKX_REPLAY=PASS")
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--public", action="store_true")
    args = parser.parse_args()
    verify(public=args.public)
