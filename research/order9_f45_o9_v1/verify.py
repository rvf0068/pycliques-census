"""Positive proof that McKay 208409 (F_{4,5}) is K-divergent.

Independently reconstruct its fourth completely pared clique iterate and
check a full 202-coordinate projection fixing an induced O9. Reconstruct
again with the public pycliques algorithms and transport the certificate
through an exact graph isomorphism. Nothing is inferred from a solver status.

Environment: NetworkX 3.6.1; pinned public pycliques.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
CERT = Path(__file__).with_name("certificate.json")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def explicit_f45() -> nx.Graph:
    g = nx.Graph()
    g.add_nodes_from(range(9))
    g.add_edges_from((i, i + 1) for i in range(3))
    g.add_edges_from((i, i + 1) for i in range(4, 8))
    g.add_edges_from(
        (i, 4 + j) for i in range(4) for j in range(5)
        if i in (0, 3) or j in (0, 4)
    )
    return g


def independent_pare(g: nx.Graph) -> nx.Graph:
    g = g.copy()
    while True:
        closed = {v: set(g[v]) | {v} for v in g}
        vertex = next(
            (u for u in g if any(
                v != u and closed[u] <= closed[v] for v in g
            )), None
        )
        if vertex is None:
            return g
        g.remove_node(vertex)


def independent_clique_graph(g: nx.Graph) -> nx.Graph:
    facets = [frozenset(c) for c in nx.find_cliques(g)]
    k = nx.Graph()
    k.add_nodes_from(range(len(facets)))
    k.add_edges_from(
        (i, j) for i, a in enumerate(facets)
        for j in range(i + 1, len(facets)) if a & facets[j]
    )
    return k


def independent_p4() -> nx.Graph:
    g = independent_pare(explicit_f45())
    for _ in range(4):
        g = independent_pare(independent_clique_graph(g))
    return nx.convert_node_labels_to_integers(g)


def verify() -> None:
    c = json.loads(CERT.read_text(encoding="utf-8"))
    require(c["schema"] == 1 and c["pared_depth"] == 4, "Wrong schema/depth")
    require(c["source_graph6"] == "HCZTf\\}", "Wrong McKay source graph")
    raw = nx.from_graph6_bytes(c["source_graph6"].encode("ascii"))
    require(nx.is_isomorphic(raw, explicit_f45()), "McKay source not F45")
    v4 = (ROOT / "indeterminate_order_9_v4.txt").read_text()
    require(any(s.startswith("208409 9 HCZTf\\} ")
                for s in v4.splitlines()),
            "McKay 208409 not in frozen order-nine v4")

    a = independent_p4()
    require((len(a), a.number_of_edges()) == (202, 16289),
            "Incorrect P4 size")
    s = nx.to_graph6_bytes(a, header=False).decode("ascii").strip()
    require(hashlib.sha256(s.encode("ascii")).hexdigest() ==
            c["pared_graph6_sha256"], "Labeled independent P4 changed")
    images = list(base64.b64decode(c["images_b64"], validate=True))
    pairs = [tuple(p) for p in c["opposite_pairs"]]
    W = {v for pair in pairs for v in pair}
    require(len(pairs) == c["target_dimension"] == 9 and len(W) == 18,
            "Incorrect antipodal pairs")
    require(all(not a.has_edge(u, v) for u, v in pairs),
            "An antipodal pair is an edge")
    require(all(
        a.has_edge(u, v) for i, (p, q) in enumerate(pairs)
        for r, t in pairs[i + 1:]
        for u in (p, q) for v in (r, t)
    ), "Missing cross-pair edges")
    require(len(images) == 202 and set(images) == W,
            "Projection image is not exactly O9")
    require(all(images[v] == v for v in W),
            "Projection does not fix O9")
    require(all(
        images[u] == images[v] or a.has_edge(images[u], images[v])
        for u, v in a.edges()
    ), "Projection is not a graph morphism")
    print("INDEPENDENT_P4_O9_RETRACTION_CERTIFIED 202 16289 9")

    import pycliques

    b = pycliques.completely_pared_graph(raw)
    for step in range(4):
        k = pycliques.clique_graph(b)
        require(k is not None, f"Public K{step+1} unexpectedly failed")
        b = pycliques.completely_pared_graph(k)
    b = nx.convert_node_labels_to_integers(b)
    require((len(b), b.number_of_edges()) == (202, 16289),
            "Public pycliques P4 counts differ")
    # A sparse-complement exact isomorphism avoids relying on internal
    # NetworkX clique enumeration order to transport the certificate.
    matcher = nx.isomorphism.GraphMatcher(nx.complement(b), nx.complement(a))
    require(matcher.is_isomorphic(), "Public P4 not isomorphic")
    f = matcher.mapping
    require(all(
        b.has_edge(u, v) == a.has_edge(f[u], f[v])
        for u in b for v in b
    ), "Transport bijection not adjacency-preserving")
    inv = {v: u for u, v in f.items()}
    target_pairs = [tuple(inv[v] for v in pair) for pair in pairs]
    projection = {u: inv[images[f[u]]] for u in b}
    target = b.subgraph({v for pair in target_pairs for v in pair}).copy()
    inclusion = {v: v for v in target}
    require(pycliques.verify_induced_octahedron(b, target_pairs),
            "Public verifier rejects O9")
    require(pycliques.verify_retraction_witness(
        b, target, (projection, inclusion)
    ), "Public verifier rejects complete transported retraction")
    print("PUBLIC_PYCLIQUES_O9_RETRACTION_CERTIFIED McKay 208409")


if __name__ == "__main__":
    verify()
