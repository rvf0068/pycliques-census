"""Exact rational LP-dual certificate of P4 complement domination lower bounds.

The saved weights are nonnegative integers with scale 10000. Each closed
neighborhood of the complement has weight <= 10000, and their total
weight exceeds 80000 or 90000. By the covering weak-duality argument,
any dominating set must have at least 9 or 10 vertices. The verifier
uses integer arithmetic ONLY; no LP or integer-programming solver.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import itertools
import json
import struct
import sys
from pathlib import Path

import networkx as nx

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical assertions")

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CERT = HERE / "certificate.json"
FROZEN = ROOT / "indeterminate_order_9_v7.txt"
FROZEN_BLOB = "6f1e05d6b6bb0f1b4f2638ad73a7163f26ab0345"
SOURCES = {
    251759: ("HEhvtzm", 403, 70679, 9, 80129, 9997),
    254369: ("HEjfvx}", 394, 67229, 9, 81026, 9995),
    251902: ("HEhvvzm", 461, 94642, 10, 99341, 9995),
}


def pare(graph: nx.Graph) -> nx.Graph:
    g = graph.copy()
    while True:
        closed = {v: set(g[v]) | {v} for v in g}
        victim = next(
            (
                v for v in sorted(g)
                if any(v != w and closed[v] <= closed[w] for w in g)
            ),
            None,
        )
        if victim is None:
            return g
        g.remove_node(victim)


def clique_graph(graph: nx.Graph) -> nx.Graph:
    maximal = list(nx.find_cliques(graph))
    out = nx.empty_graph(len(maximal))
    membership = {v: [] for v in graph}
    for j, clique in enumerate(maximal):
        for v in clique:
            membership[v].append(j)
    for ids in membership.values():
        out.add_edges_from(itertools.combinations(ids, 2))
    return out


def normalized(graph: nx.Graph) -> nx.Graph:
    return nx.convert_node_labels_to_integers(graph, ordering="sorted")


def edge_digest(g: nx.Graph) -> str:
    edges = sorted(
        (min(u, v), max(u, v)) for u, v in g.edges()
    )
    return hashlib.sha256(
        "\n".join(f"{u},{v}" for u, v in edges).encode("ascii")
    ).hexdigest()


def frozen_sources() -> None:
    data = FROZEN.read_bytes()
    actual = hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()
    assert actual == FROZEN_BLOB, "Frozen nine-v7 was modified"
    rows = {
        int(parts[0]): parts
        for line in data.decode("ascii").splitlines()
        if line and not line.startswith("#")
        for parts in [line.split()]
    }
    assert len(rows) == 6, "Unexpected frozen nine-v7 cohort"
    for index, (graph6, *_rest) in SOURCES.items():
        assert rows[index] == [
            str(index), "9", graph6, "-", "-", "-"
        ], f"Wrong frozen source identity for McKay {index}"


def same_graph(a: nx.Graph, b: nx.Graph) -> bool:
    return set(a) == set(b) and {
        frozenset(edge) for edge in a.edges()
    } == {
        frozenset(edge) for edge in b.edges()
    }


def build_p4(graph6: str, *, public: bool) -> nx.Graph:
    g = pare(nx.from_graph6_bytes(graph6.encode("ascii")))
    for _ in range(4):
        raw = clique_graph(g)
        if public:
            import pycliques

            returned = pycliques.clique_graph(g)
            assert returned is not None
            # Compare public clique identities directly, not via a potentially
            # pathological VF2 isomorphism check on dense symmetric graphs.
            cliques = [frozenset(c) for c in nx.find_cliques(g)]
            positions = {c: i for i, c in enumerate(cliques)}
            assert len(returned) == len(positions)
            assert all(frozenset(q) in positions for q in returned)
            public_raw = nx.relabel_nodes(
                returned, {q: positions[frozenset(q)] for q in returned}
            )
            assert same_graph(raw, public_raw), "Public K differs from independent K"
            sorted_public_raw = nx.Graph()
            sorted_public_raw.add_nodes_from(sorted(raw))
            sorted_public_raw.add_edges_from(public_raw.edges())
            public_pared = pycliques.completely_pared_graph(sorted_public_raw)
        g = pare(raw)
        if public:
            assert same_graph(g, public_pared), "Public paring differs"
    return normalized(g)


def verify(*, public: bool = False) -> None:
    frozen_sources()
    data = json.loads(CERT.read_text(encoding="utf8"))
    assert data["schema"] == 1
    assert data["scale"] == 10000
    assert data["encoding"] == "uint16_le_per_sorted_normalized_P4_host_vertex"
    assert len(data["cases"]) == 3
    assert {case["mckay_index"] for case in data["cases"]} == set(SOURCES)

    for case in data["cases"]:
        index = case["mckay_index"]
        graph6, order, edges, lower, total, max_load = SOURCES[index]
        assert case["original_graph6"] == graph6
        host = build_p4(graph6, public=public)
        assert (len(host), host.number_of_edges()) == (order, edges)
        assert edge_digest(host) == case["p4_normalized_edge_sha256"], (
            index, "P4 source labeling/digest mismatch"
        )
        raw = base64.b64decode(case["weights_b64"], validate=True)
        assert len(raw) == 2 * order
        weights = struct.unpack(f"<{order}H", raw)
        assert all(w >= 0 for w in weights)
        total_weight = sum(weights)
        assert total_weight == case["integer_weight_sum"] == total

        # N_{complement(X)}[v] = V(X) minus the open X-neighborhood of v.
        # Therefore its integer weight is W - sum_{u in N_X(v)} w[u].
        loads = [
            total_weight - sum(weights[u] for u in host[v])
            for v in host
        ]
        assert max(loads) == case["max_closed_complement_weight"] == max_load
        assert all(0 <= load <= 10000 for load in loads)
        assert (total_weight + 10000 - 1) // 10000 == lower
        print(
            f"PASS McKay={index} P4_order={order} P4_edges={edges} "
            f"dual_weight_sum={total_weight}/10000 max_load={max(loads)}/10000 "
            f"gamma_complement_at_least={lower}",
            flush=True,
        )
    print("PASS: all three exact domination lower bounds verified by integer arithmetic")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public", action="store_true")
    args = parser.parse_args()
    verify(public=args.public)


if __name__ == "__main__":
    main()
