"""Independently reconstruct and verify saved fourth-iterate O6 retractions.

Only NetworkX is needed. This verifier does not import pycliques, reuse any
search routine, or trust a claimed homomorphism without checking every edge.
Each dominated-vertex deletion is checked against current closed neighborhoods.
NetworkX facet generation is cross-checked against bitset Bron-Kerbosch.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "indeterminate_order_10_v11.txt"
PINNED_BLOB = "34023e9323945c4a6e5e1249c37ba955ba62473f"
CERTIFICATES = Path(__file__).with_name("o6_certificates.json")


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def bits(mask: int):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def bk_cliques(g: nx.Graph) -> list[int]:
    """All maximal cliques by a separate Bron-Kerbosch implementation."""
    n = len(g)
    require(set(g) == set(range(n)), "Graph not relabeled")
    neighbors = [sum(1 << v for v in g[i]) for i in range(n)]
    results = []

    def visit(r: int, p: int, x: int) -> None:
        if not (p | x):
            results.append(r)
            return
        pivot = max(bits(p | x), key=lambda v: (p & neighbors[v]).bit_count())
        for v in list(bits(p & ~neighbors[pivot])):
            bit = 1 << v
            visit(r | bit, p & neighbors[v], x & neighbors[v])
            p &= ~bit
            x |= bit

    visit(0, (1 << n) - 1, 0)
    return sorted(results)


def clique(g: nx.Graph) -> nx.Graph:
    """Clique graph with deterministic NetworkX facet ordering."""
    facets = [list(q) for q in nx.find_cliques(g)]
    masks = [sum(1 << v for v in q) for q in facets]
    require(sorted(masks) == bk_cliques(g), "Independent facet enumeration differs")
    h = nx.Graph()
    h.add_nodes_from(range(len(facets)))
    incidence = {}
    for i, q in enumerate(facets):
        for v in q:
            incidence.setdefault(v, []).append(i)
    for members in incidence.values():
        for i, current in enumerate(members):
            for previous in members[:i]:
                h.add_edge(previous, current)
    return h


def pare(g: nx.Graph) -> nx.Graph:
    """Delete closed-neighborhood-dominated vertices with checked folds.

    Exactly reproduces deterministic first-available closed-neighborhood
    pair removal used for the saved witness indexing. Remaining vertices
    are relabeled in their original iteration order.
    """
    nodes = list(g)
    positions = {v: i for i, v in enumerate(nodes)}
    n = len(nodes)
    closed = [1 << i for i in range(n)]
    for u, v in g.edges():
        i, j = positions[u], positions[v]
        closed[i] |= 1 << j
        closed[j] |= 1 << i
    active = (1 << n) - 1
    while True:
        victim = None
        for i in range(n):
            if not (active >> i) & 1:
                continue
            current = closed[i] & active
            for j in range(n):
                if i != j and (active >> j) & 1 and not (current & ~closed[j]):
                    require((closed[i] & active) & ~(closed[j] & active) == 0,
                            "A saved fold is not dominated")
                    victim = i
                    break
            if victim is not None:
                break
        if victim is None:
            break
        active &= ~(1 << victim)
    remaining = list(bits(active))
    h = nx.Graph()
    h.add_nodes_from(range(len(remaining)))
    for a, i in enumerate(remaining):
        for b, j in enumerate(remaining[:a]):
            if (closed[i] >> j) & 1:
                h.add_edge(a, b)
    require(all(
        not (set(h[v]) | {v}) <= (set(h[u]) | {u})
        for v in h for u in h if v != u
    ), "Pared result still has dominated vertices")
    return h


def reproduce(source_graph6: str):
    g = nx.from_graph6_bytes(source_graph6.encode("ascii"))
    require(len(g) == 10, "Source is not order ten")
    g = pare(g)
    for _ in range(3):
        g = pare(clique(g))
    k3 = g
    k4_unpared = clique(k3)
    k4_pared = pare(k4_unpared)
    return k3, k4_unpared, k4_pared


def indexed_sources():
    raw = SOURCE.read_bytes()
    digest = hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()
    require(digest == PINNED_BLOB, "Historical v11 index changed")
    rows = {}
    for line in raw.decode("utf-8").splitlines():
        if line and not line.startswith("#"):
            f = line.split()
            require(len(f) == 6, "Malformed current census record")
            rows[int(f[0])] = f
    return rows


def verify_positive(cert: dict, rows: dict) -> None:
    index = cert["index"]
    require(index in rows, "Not an indexed original graph")
    row = rows[index]
    require(row[1] == "10" and row[2] == cert["source_graph6"]
            and row[3:] == ["-", "-", "-"], "Not a fully unclassified stiff ten-core")
    k3, k4_raw, host = reproduce(cert["source_graph6"])
    for name, actual in (("K3", k3), ("K4_unpared", k4_raw), ("K4_pared", host)):
        require(cert[name] == [len(actual), actual.number_of_edges()],
                "Saved graph sizes do not match " + name)
    graph6 = nx.to_graph6_bytes(host, header=False).strip()
    require(hashlib.sha256(graph6).hexdigest() == cert["host_sha256"],
            "Full fourth-iterate graph6 digest does not match")
    pairs = cert["pairs"]
    require(len(pairs) == 6, "Target must be O6")
    endpoints = [v for pair in pairs for v in pair]
    target = set(endpoints)
    require(len(target) == 12 and target <= set(host), "Target endpoints invalid")
    for i, (u, v) in enumerate(pairs):
        require(not host.has_edge(u, v), "Antipodal pair is adjacent")
        for a, b in pairs[:i]:
            require(all(host.has_edge(x, y) for x in (u, v) for y in (a, b)),
                    "Target is not an induced octahedron")
    images = list(base64.b64decode(cert["images_b64"], validate=True))
    require(len(images) == len(host) and set(images) == target,
            "Incomplete map or images outside target")
    require(all(images[v] == v for v in endpoints),
            "Retraction does not fix target pointwise")
    require(all(
        images[u] == images[v] or host.has_edge(images[u], images[v])
        for u, v in host.edges()
    ), "Map is not a graph morphism")
    print(
        "VERIFIED_O6", index, "K3", len(k3), "K4", len(k4_raw),
        "paredK4", len(host), "edges", host.number_of_edges(),
        "target", len(endpoints), flush=True,
    )


def main() -> None:
    data = json.loads(CERTIFICATES.read_text(encoding="utf-8"))
    require(data["schema"] == 1 and data["source"] == SOURCE.name,
            "Unexpected certificate metadata")
    certs = data["proofs"]
    require(len(certs) == 3 and len({r["index"] for r in certs}) == 3,
            "Unexpected certificate count or duplicates")
    rows = indexed_sources()
    for cert in certs:
        verify_positive(cert, rows)
    print("Verified 3 independent complete O6 fourth-iterate retractions")


if __name__ == "__main__":
    main()
