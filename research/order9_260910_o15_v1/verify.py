"""Independent complete O15 retraction proof for nine-vertex McKay 260910.

Rebuild third completely pared clique iterate twice, with NetworkX
and with public pycliques. Check all 7880 source edge constraints.
No cached target search or solver outcome is trusted by this verifier.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import sys

import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from research.order9_f45_o9_v1.verify import (  # noqa: E402
    independent_clique_graph,
    independent_pare,
    require,
)

CERT = Path(__file__).with_name("certificate.json")


def independently_reconstruct() -> nx.Graph:
    source = nx.from_graph6_bytes(b"HUZvvzu")
    graph = independent_pare(source)
    for _ in range(3):
        graph = independent_pare(independent_clique_graph(graph))
    return nx.convert_node_labels_to_integers(graph)


def verify() -> None:
    c = json.loads(CERT.read_text(encoding="utf-8"))
    require(c["schema"] == 1 and c["original_index"] == 260910,
            "Wrong schema or original McKay index")
    require(c["source_graph6"] == "HUZvvzu" and c["pared_depth"] == 3,
            "Wrong source or iteration depth")
    v4 = (ROOT / "indeterminate_order_9_v4.txt").read_text()
    require(any(s.startswith("260910 9 HUZvvzu ") for s in v4.splitlines()),
            "Original source absent from frozen v4 census")
    a = independently_reconstruct()
    require((len(a), a.number_of_edges()) == (132, 7880),
            "Wrong independent P3 signature")
    encoding = nx.to_graph6_bytes(a, header=False).decode("ascii").strip()
    require(hashlib.sha256(encoding.encode("ascii")).hexdigest() ==
            c["pared_graph6_sha256"], "Independent P3 labeling changed")
    images = list(base64.b64decode(c["images_b64"], validate=True))
    pairs = [tuple(pair) for pair in c["opposite_pairs"]]
    vertices = [v for pair in pairs for v in pair]
    W = set(vertices)
    require(len(pairs) == c["target_dimension"] == 15 and len(W) == 30,
            "Wrong O15 target size or pair uniqueness")
    require(all(not a.has_edge(u, v) for u, v in pairs),
            "Antipodal pair is adjacent")
    require(all(
        a.has_edge(u, v) for i, (p, q) in enumerate(pairs)
        for r, t in pairs[i + 1:]
        for u in (p, q) for v in (r, t)
    ), "Missing O15 cross-pair edges")
    require(len(images) == 132 and set(images) == W,
            "Projection is not total onto O15")
    require(all(images[v] == v for v in W),
            "Projection does not fix O15")
    require(all(
        images[u] == images[v] or a.has_edge(images[u], images[v])
        for u, v in a.edges()
    ), "Projection violates a host edge")
    print("INDEPENDENT_P3_O15_RETRACTION_CERTIFIED 132 7880 15")

    import pycliques

    raw = nx.from_graph6_bytes(c["source_graph6"].encode("ascii"))
    b = pycliques.completely_pared_graph(raw)
    for step in range(3):
        k = pycliques.clique_graph(b)
        require(k is not None, f"Public K{step+1} unexpectedly failed")
        b = pycliques.completely_pared_graph(k)
    b = nx.convert_node_labels_to_integers(b)
    require((len(b), b.number_of_edges()) == (132, 7880),
            "Public P3 signature differs")
    matcher = nx.isomorphism.GraphMatcher(nx.complement(b), nx.complement(a))
    require(matcher.is_isomorphic(), "Public and independent P3 disagree")
    f = matcher.mapping
    require(all(
        b.has_edge(u, v) == a.has_edge(f[u], f[v])
        for u in b for v in b
    ), "Transport isomorphism does not preserve adjacency")
    inv = {v: u for u, v in f.items()}
    target_pairs = [tuple(inv[v] for v in pair) for pair in pairs]
    projection = {u: inv[images[f[u]]] for u in b}
    target = b.subgraph(v for pair in target_pairs for v in pair)
    inclusion = {v: v for v in target}
    require(pycliques.verify_induced_octahedron(b, target_pairs),
            "Public pycliques rejects induced O15")
    require(pycliques.verify_retraction_witness(
        b, target, (projection, inclusion)
    ), "Public pycliques rejects transported O15 projection")
    print("PUBLIC_PYCLIQUES_O15_RETRACTION_CERTIFIED McKay 260910")


if __name__ == "__main__":
    verify()
