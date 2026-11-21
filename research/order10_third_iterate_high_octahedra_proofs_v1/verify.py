"""Independently replay complete raw K³(G) -> O_d retractions.

All supplied sources are previously unclassified stiff ten-vertex graphs in
the immutable v9 working list. NetworkX and an independent bitset clique
enumerator reconstruct every iterate; every edge of each projection is
checked against its induced octahedral target.

The proof archive can grow by adding further positive maps, never by
deducing convergence from unsuccessful bounded searches.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "indeterminate_order_10_v9.txt"
CERTIFICATES = Path(__file__).with_name("certificates.json")
V9_GIT_BLOB = "704219076c6d61b595374cd129c5fa520253a089"
SEED_INDICES = (5502890, 6555024, 6946005, 6954458, 6954725, 6954734)


def require(cond: bool, message: str) -> None:
    if not cond:
        raise ValueError(message)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def source_rows() -> dict[int, list[str]]:
    raw = SOURCE.read_bytes()
    require(git_blob(raw) == V9_GIT_BLOB, "Frozen version-nine source changed")
    result = {}
    for line in raw.decode("utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        row = line.split()
        require(len(row) == 6, "Malformed historical record")
        idx = int(row[0])
        require(idx not in result, "Duplicate source index")
        result[idx] = row
    require(len(result) == 7920, "Unexpected source cohort size")
    require(
        sum(v[1] == "10" and v[3:] == ["-", "-", "-"]
            for v in result.values()) == 1393,
        "Unexpected stiff ten-core population"
    )
    return result


def independent_facets(graph: nx.Graph) -> set[int]:
    n = len(graph)
    require(set(graph) == set(range(n)), "Graph vertex labels are noncanonical")
    neighbors = [sum(1 << j for j in graph[v]) for v in range(n)]
    result: set[int] = set()

    def recur(current: int, possible: int, excluded: int) -> None:
        if not (possible or excluded):
            require(current not in result, "Duplicate independently found maximal clique")
            result.add(current)
            return
        union = possible | excluded
        pivot = max(
            (i for i in range(n) if union & (1 << i)),
            key=lambda i: (possible & neighbors[i]).bit_count(),
            default=None,
        )
        options = possible & ~(neighbors[pivot] if pivot is not None else 0)
        while options:
            bit = options & -options
            v = bit.bit_length() - 1
            recur(current | bit,
                  possible & neighbors[v],
                  excluded & neighbors[v])
            possible ^= bit
            excluded |= bit
            options ^= bit

    recur(0, (1 << n) - 1, 0)
    return result


def clique_graph(graph: nx.Graph) -> nx.Graph:
    standard = {
        sum(1 << v for v in q)
        for q in nx.find_cliques(graph)
    }
    independent = independent_facets(graph)
    require(standard == independent,
            "Two independent maximal-clique algorithms disagree")
    facets = sorted(independent)
    h = nx.Graph()
    h.add_nodes_from(range(len(facets)))
    h.add_edges_from(
        (i, j) for i, j in itertools.combinations(range(len(facets)), 2)
        if facets[i] & facets[j]
    )
    return h


def verify_certificate(record: dict, source: dict[int, list[str]]) -> dict:
    require(set(record) == {
        "index", "graph6", "iterate_sizes", "dimension",
        "opposite_pairs", "projection"
    }, "Malformed positive proof data")
    index = record["index"]
    require(type(index) is int and index in source,
            "Unknown original ten-vertex index")
    row = source[index]
    require(row[1] == "10" and row[2] == record["graph6"]
            and row[3:] == ["-", "-", "-"],
            "Proof refers to a different or conditionally classified case")
    graph = nx.from_graph6_bytes(record["graph6"].encode("ascii"))
    require(
        len(graph) == 10 and nx.is_connected(graph)
        and all(not (set(graph[u]) | {u}) <= (set(graph[v]) | {v})
                for u in graph for v in graph[u]),
        "Original graph is not a connected stiff ten-vertex core"
    )
    counts = []
    for level in range(4):
        counts.append([len(graph), graph.number_of_edges()])
        if level < 3:
            graph = clique_graph(graph)
    require(counts == record["iterate_sizes"],
            "Raw clique iteration sizes or edges differ from certificate")

    pairs = record["opposite_pairs"]
    d = record["dimension"]
    projection = record["projection"]
    require(type(d) is int and d >= 3
            and type(pairs) is list and len(pairs) == d
            and all(isinstance(pair, list) and len(pair) == 2
                    and all(type(x) is int for x in pair)
                    for pair in pairs),
            "Invalid target antipodal pairing")
    target = [x for pair in pairs for x in pair]
    target_set = set(target)
    require(len(target_set) == 2 * d and target_set <= set(graph),
            "Duplicate or missing target vertices")
    require(isinstance(projection, list)
            and len(projection) == len(graph)
            and all(type(x) is int and x in target_set for x in projection)
            and all(projection[t] == t for t in target),
            "Projection is not total or does not fix its target")
    sub = graph.subgraph(target)
    require(
        {tuple(sorted(p)) for p in nx.non_edges(sub)}
        == {tuple(sorted(p)) for p in pairs},
        "Induced target has incorrect missing pairs"
    )
    require(nx.is_isomorphic(
        sub, nx.complete_multipartite_graph(*([2] * d))
    ), "Induced target is not O_d")
    require(
        all(projection[u] == projection[v]
            or sub.has_edge(projection[u], projection[v])
            for u, v in graph.edges()),
        "The proposed retraction violates a source edge"
    )
    return {"index": index, "graph6": record["graph6"],
            "target": f"O_{d}", "stages": counts,
            "verified_source_edges": graph.number_of_edges()}


def verify(self_test=False) -> None:
    source = source_rows()
    data = json.loads(CERTIFICATES.read_text(encoding="utf-8"))
    require(set(data) == {"schema", "source", "iterate", "proofs"}
            and data["schema"] == 1
            and data["source"] == SOURCE.name
            and data["iterate"] == 3
            and type(data["proofs"]) is list,
            "Malformed proof archive metadata")
    records = data["proofs"]
    ids = [record["index"] for record in records]
    require(ids == sorted(ids) and len(ids) == len(set(ids)),
            "Proofs must be sorted and unique")
    require(set(SEED_INDICES) <= set(ids),
            "The six originally independently verified proofs are missing")
    verified = [verify_certificate(row, source) for row in records]

    if self_test:
        import copy
        altered = copy.deepcopy(records[0])
        t = altered["opposite_pairs"][0][0]
        altered["projection"][t] = altered["opposite_pairs"][0][1]
        try:
            verify_certificate(altered, source)
        except ValueError:
            pass
        else:
            raise AssertionError("Tampered target section not rejected")
        altered = copy.deepcopy(records[-1])
        altered["iterate_sizes"][3][1] += 1
        try:
            verify_certificate(altered, source)
        except ValueError:
            pass
        else:
            raise AssertionError("Mutated clique graph size not rejected")

    for item in verified:
        print(json.dumps(item, sort_keys=True))
    print(f"VERIFIED: {len(verified)} complete independent raw K³-to-O_d"
          " retractions; no unproved result promoted to classification")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    verify(parser.parse_args().self_test)
