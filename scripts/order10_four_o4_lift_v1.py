"""Verify nineteen order-ten K-divergences using two K^3 -> O4 retracts.

Four historical pared graph6 strings represent two nine-vertex isomorphism
types. Proofs replay every dominated-vertex fold at all four levels,
independently reconstruct clique graphs from maximal cliques, and check
every edge of the complete ordinary O4 retractions (edges may map to equality).
All historical results and v7 remain frozen.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
V7 = ROOT / "indeterminate_order_10_v7.txt"
V8 = ROOT / "indeterminate_order_10_v8.txt"
CURRENT = ROOT / "indeterminate_order_10.txt"
V7_BLOB = "4b41da5b49726fb64f56cbfc97c75fc5b3ced5a4"
GROUPS = {
    "HQqvUx}": (9943619, 9943624, 9944398, 9964496, 11548395, 11548997),
    "HEhutzm": (6945593, 6945998, 11589592, 11589624),
    "HEht}rl": (6938971, 6938987, 11597205),
    "HEnfbzm": (10547079, 11300525, 11300543, 11652131, 11652585, 11652613),
}

# Complete proof witnesses for the two nonisomorphic nine-vertex cores.
# A projection is represented as (source_vertex, fixed_target_image) pairs.
PROOFS = {
    "HQqvUx}": {
        "folds": [[], [], [[7, 6], [11, 5]],
                  [[21, 22], [30, 31], [35, 36], [42, 43], [9, 8], [12, 11]]],
        "sizes": [[9, 22, 9, 22], [13, 50, 13, 50],
                  [21, 141, 19, 119], [47, 794, 41, 607]],
        "target": [0, 1, 10, 11, 31, 36, 37, 39],
        "projection": [
            [0,0],[1,1],[2,0],[3,1],[4,1],[5,1],[6,1],[7,1],
            [8,1],[10,10],[11,11],[13,11],[14,11],[15,11],
            [16,11],[17,11],[18,36],[19,11],[20,11],[22,11],
            [23,1],[24,10],[25,11],[26,11],[27,1],[28,1],
            [29,1],[31,31],[32,36],[33,36],[34,36],[36,36],
            [37,37],[38,36],[39,39],[40,36],[41,36],[43,31],
            [44,31],[45,31],[46,31],
        ],
    },
    "HEnfbzm": {
        "folds": [[], [], [], []],
        "sizes": [[9,23,9,23],[16,79,16,79],
                  [23,173,23,173],[70,1728,70,1728]],
        "target": [0, 2, 13, 22, 39, 41, 49, 51],
        "projection": [
            [0,0],[1,13],[2,2],[3,2],[4,2],[5,49],[6,49],[7,49],
            [8,13],[9,13],[10,49],[11,13],[12,13],[13,13],[14,13],
            [15,13],[16,2],[17,2],[18,2],[19,2],[20,2],[21,2],
            [22,22],[23,2],[24,2],[25,2],[26,2],[27,2],[28,13],
            [29,49],[30,49],[31,49],[32,13],[33,13],[34,13],
            [35,13],[36,13],[37,49],[38,49],[39,39],[40,2],
            [41,41],[42,2],[43,2],[44,2],[45,2],[46,2],[47,2],
            [48,2],[49,49],[50,49],[51,51],[52,51],[53,49],
            [54,49],[55,49],[56,41],[57,41],[58,41],[59,41],
            [60,41],[61,41],[62,41],[63,41],[64,41],[65,41],
            [66,41],[67,41],[68,41],[69,41],
        ],
    },
}


def decode(graph6: str) -> nx.Graph:
    return nx.from_graph6_bytes(graph6.encode("ascii"))


def clique_graph(graph: nx.Graph) -> nx.Graph:
    """Reconstruct iterates deterministically, without a search verdict."""
    cliques = sorted(
        (frozenset(c) for c in nx.find_cliques(graph)),
        key=lambda q: sum(1 << v for v in q),
    )
    result = nx.Graph()
    result.add_nodes_from(range(len(cliques)))
    result.add_edges_from(
        (i, j) for i, j in combinations(range(len(cliques)), 2)
        if cliques[i] & cliques[j]
    )
    return result


def verify_core(graph6: str, proof: dict) -> dict:
    graph = decode(graph6)
    if len(proof["folds"]) != 4 or len(proof["sizes"]) != 4:
        raise ValueError("Missing iterate/fold stages")
    counts = []
    for depth in range(4):
        a, b, c, d = proof["sizes"][depth]
        if (len(graph), graph.number_of_edges()) != (a, b):
            raise ValueError("Incorrect source iterate at level " + str(depth))
        for v, w in proof["folds"][depth]:
            if (v not in graph or w not in graph or v == w
                    or not ((set(graph[v]) | {v}) <= (set(graph[w]) | {w}))):
                raise ValueError("Invalid dominated-vertex fold")
            graph.remove_node(v)
        if (len(graph), graph.number_of_edges()) != (c, d):
            raise ValueError("Incorrect pared iterate at level " + str(depth))
        counts.append([a, b, c, d])
        if depth != 3:
            graph = clique_graph(graph)
    target = proof["target"]
    projection = dict(proof["projection"])
    if (len(target) != 8 or len(set(target)) != 8
            or len(proof["projection"]) != len(graph)
            or set(projection) != set(graph)
            or set(projection.values()) != set(target)
            or any(projection[v] != v for v in target)):
        raise ValueError("Target or fixed retraction section invalid")
    target_graph = graph.subgraph(target)
    missing = list(nx.complement(target_graph).edges())
    if (len(missing) != 4
            or {u for pair in missing for u in pair} != set(target)
            or not nx.is_isomorphic(
                target_graph, nx.complete_multipartite_graph(2, 2, 2, 2)
            )):
        raise ValueError("Target is not an induced O4")
    if any(
        projection[u] != projection[v]
        and not graph.has_edge(projection[u], projection[v])
        for u, v in graph.edges()
    ):
        raise ValueError("Map violates ordinary graph morphism condition")
    return {
        "graph6": graph6, "stages": counts,
        "final_retract_source_order": len(graph),
        "final_retract_source_edges": graph.number_of_edges(),
        "o4_target": target,
        "edge_constraints_verified": graph.number_of_edges(),
    }


def frozen_v7_rows() -> list[str]:
    data = V7.read_bytes()
    digest = hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()
    if digest != V7_BLOB:
        raise ValueError("Frozen version-seven source changed")
    rows = [s for s in data.decode("utf-8").splitlines()
            if s and not s.startswith("#")]
    if len(rows) != 8124:
        raise ValueError("Unexpected version-seven population")
    found = {g: [] for g in GROUPS}
    for row in rows:
        index, order, graph6, rule, status, label = row.split(" ", 5)
        if graph6 in found:
            if (order, rule, status, label) != ("9", "-", "-", "-"):
                raise ValueError("Target row has unexpected historical status")
            found[graph6].append(int(index))
    if any(tuple(sorted(found[g])) != indices for g, indices in GROUPS.items()):
        raise ValueError("Historical original-index provenance does not match")
    return rows


def next_index_content() -> str:
    rows = frozen_v7_rows()
    excluded = {index for group in GROUPS.values() for index in group}
    remaining = [row for row in rows
                 if int(row.split(" ", 1)[0]) not in excluded]
    if (len(excluded), len(remaining)) != (19, 8105):
        raise ValueError("Incorrect 19-case census lift")
    if sum(row.split(" ")[4] == "conjectured_divergent" for row in remaining) != 4509:
        raise ValueError("A conjectural dependency has changed unexpectedly")
    return "\n".join((
        "# Order-10 unresolved after certified O4 retractions for four nine-vertex strings",
        "# Remaining=8105 previous_v7=8124 newly_proved_divergent=19",
        "# Historical stage reports and all earlier versioned lists remain unchanged.",
        "# Format: original_index pared_order pared_graph6 certificate_rule certificate_target_status certificate_target_label",
        *remaining, "",
    ))


def verify() -> dict:
    reports = {g: verify_core(g, proof) for g, proof in PROOFS.items()}
    canonical = decode("HQqvUx}")
    for label in ("HEhutzm", "HEht}rl"):
        if not nx.is_isomorphic(canonical, decode(label)):
            raise ValueError("Three recorded nine-vertex cores not isomorphic")
    if nx.is_isomorphic(canonical, decode("HEnfbzm")):
        raise ValueError("Expected two distinct nine-vertex isomorphism classes")
    expected = next_index_content()
    if V8.read_text(encoding="utf-8") != expected:
        raise ValueError("Versioned v8 index missing or changed")
    if CURRENT.read_text(encoding="utf-8") != expected:
        raise ValueError("Root index not synchronized with v8")
    return {
        "newly_proved_divergent_original_order10": 19,
        "remaining": 8105, "conditional": 4509,
        "covered": {g: list(indices) for g, indices in GROUPS.items()},
        "positive_proofs": reports,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("verify", "certificates"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify()
    if args.command == "certificates":
        if args.output is None:
            parser.error("certificates requires --output")
        args.output.write_text(
            json.dumps(result, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    print("CERTIFIED: 2 nonisomorphic nine-vertex O4-retract classes")
    print("PROVED: 19 original order-ten graphs K-divergent")
    print("REMAINING: 8105 order-ten cases (4509 conditional)")


if __name__ == "__main__":
    main()
