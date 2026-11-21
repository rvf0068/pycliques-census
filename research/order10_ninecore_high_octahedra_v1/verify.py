"""Replay two high-dimensional octahedral retractions and their 351 class lifts.

Proof-only, independent of pycliques. Rebuild raw K^3 with two independent
maximal-clique enumerators and check every edge of each total retraction.
For the lift, verify every frozen v9 pared-core string via exact isomorphism.

No bounded-search negative can affect a classification.
Requires networkx==3.6.1.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
V9 = ROOT / "indeterminate_order_10_v9.txt"
CORES = ROOT / "reports/order10_core_index_v1/classes.tsv"
CERTIFICATES = Path(__file__).with_name("certificates.json")
V9_BLOB = "704219076c6d61b595374cd129c5fa520253a089"
CORE_BLOB = "9c1559191231a7c61d95955d14f41a22e4565f79"
EXPECTED = {5418647: (5, 116), 6974529: (6, 235)}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def historical_rows() -> tuple[dict[int, list[str]], dict[int, list[str]]]:
    source = V9.read_bytes()
    classes = CORES.read_bytes()
    require(git_blob(source) == V9_BLOB, "Frozen v9 snapshot changed")
    require(git_blob(classes) == CORE_BLOB, "Frozen core-isomorphism index changed")
    records: dict[int, list[str]] = {}
    for line in source.decode("utf-8").splitlines():
        if line and not line.startswith("#"):
            row = line.split()
            require(len(row) == 6, "Malformed historical census row")
            i = int(row[0])
            require(i not in records, "Duplicate McKay index")
            records[i] = row
    require(len(records) == 7920, "Unexpected v9 population")
    grouped: dict[int, list[str]] = {}
    for line in classes.decode("utf-8").splitlines()[1:]:
        if line:
            parts = line.split("\t")
            require(len(parts) == 6, "Malformed historical core class")
            key = int(parts[0])
            require(key not in grouped, "Duplicate core class")
            grouped[key] = parts
    return records, grouped


def bitset_maximal_cliques(graph: nx.Graph) -> set[int]:
    """Independent Bron-Kerbosch-with-pivot implementation."""
    n = len(graph)
    require(set(graph) == set(range(n)), "Graph labels are not consecutive")
    adjacency = [sum(1 << v for v in graph[x]) for x in range(n)]
    found: set[int] = set()

    def search(r: int, p: int, x: int) -> None:
        if not (p or x):
            require(r not in found, "Duplicate maximal clique from independent solver")
            found.add(r)
            return
        pool = p | x
        pivot = max(
            (j for j in range(n) if (pool >> j) & 1),
            key=lambda j: (p & adjacency[j]).bit_count(),
            default=None,
        )
        candidates = p & ~(adjacency[pivot] if pivot is not None else 0)
        while candidates:
            bit = candidates & -candidates
            v = bit.bit_length() - 1
            search(r | bit, p & adjacency[v], x & adjacency[v])
            p ^= bit
            x |= bit
            candidates ^= bit

    search(0, (1 << n) - 1, 0)
    return found


def clique_graph(graph: nx.Graph) -> nx.Graph:
    """Use canonical integer-bitmask ordering for all facet vertices."""
    ordinary = {
        sum(1 << v for v in q) for q in nx.find_cliques(graph)
    }
    independent = bitset_maximal_cliques(graph)
    require(ordinary == independent,
            "NetworkX and independent bitset clique enumeration disagree")
    facets = sorted(independent)
    h = nx.Graph()
    h.add_nodes_from(range(len(facets)))
    # The facet intersection condition is *exact*, with no graph6 cache.
    h.add_edges_from(
        (i, j) for i, j in itertools.combinations(range(len(facets)), 2)
        if facets[i] & facets[j]
    )
    return h


def verify_projection(graph: nx.Graph, rec: dict) -> dict:
    opposite = rec["opposite_pairs"]
    d = rec["dimension"]
    projection = rec["projection"]
    require(type(d) is int and d >= 3
            and type(opposite) is list and len(opposite) == d
            and all(isinstance(pair, list) and len(pair) == 2
                    and all(type(t) is int for t in pair) for pair in opposite),
            "Malformed octahedron opposite pairs")
    target = [t for pair in opposite for t in pair]
    target_set = set(target)
    require(
        len(target_set) == 2 * d
        and target_set <= set(graph)
        and isinstance(projection, list)
        and len(projection) == len(graph)
        and all(type(v) is int and v in target_set for v in projection)
        and all(projection[t] == t for t in target),
        "The projection does not fix the induced octahedron"
    )
    expected_nonedges = {tuple(sorted(p)) for p in opposite}
    target_graph = graph.subgraph(target)
    actual_nonedges = {tuple(sorted(p)) for p in nx.non_edges(target_graph)}
    require(expected_nonedges == actual_nonedges,
            "Induced target does not have precisely the prescribed missing edges")
    require(nx.is_isomorphic(
        target_graph, nx.complete_multipartite_graph(*([2] * d))
    ), "Target does not induce O_d")
    require(
        all(projection[u] == projection[v]
            or target_graph.has_edge(projection[u], projection[v])
            for u, v in graph.edges()),
        "A source edge is neither preserved nor collapsed to equality"
    )
    return {"dimension": d, "target": sorted(target),
            "opposite_pairs": opposite, "checked_edges": graph.number_of_edges()}


def replay_core(rec: dict) -> dict:
    require(set(rec) == {
        "index", "graph6", "members", "iterate_sizes", "dimension",
        "opposite_pairs", "projection"
    }, "Unexpected or missing certificate fields")
    idx = rec["index"]
    require(type(idx) is int and idx in EXPECTED,
            "Unknown representative core index")
    dimension, represented = EXPECTED[idx]
    require(rec["dimension"] == dimension and rec["members"] == represented,
            "Core dimension or class-size mismatch")
    g = nx.from_graph6_bytes(rec["graph6"].encode("ascii"))
    require(
        len(g) == 9 and nx.is_connected(g)
        and all(
            not (set(g[v]) | {v}) <= (set(g[u]) | {u})
            for v in g for u in g[v]),
        "Input is not a connected stiff nine-vertex core"
    )
    counts = []
    for level in range(4):
        counts.append([len(g), g.number_of_edges()])
        if level < 3:
            g = clique_graph(g)
    require(counts == rec["iterate_sizes"],
            "Independently reconstructed clique-iterate sizes differ")
    proof = verify_projection(g, rec)
    return {"core_id": idx, "graph6": rec["graph6"],
            "iterate_sizes": counts, **proof}


def verify(self_test: bool = False) -> None:
    rows, classes = historical_rows()
    document = json.loads(CERTIFICATES.read_text(encoding="utf-8"))
    require(set(document) == {"schema", "baseline", "core_table", "proofs"}
            and document["schema"] == 1
            and document["baseline"] == V9.name
            and document["core_table"] == "reports/order10_core_index_v1/classes.tsv"
            and isinstance(document["proofs"], list),
            "Malformed positive-proof record")
    records = document["proofs"]
    require([rec["index"] for rec in records] == list(EXPECTED),
            "Unexpected number or order of proved nine-cores")

    lifted = set()
    proofs = []
    for rec in records:
        proof = replay_core(rec)
        core_id = rec["index"]
        old_class = classes.get(core_id)
        require(old_class is not None and old_class[1] == "9"
                and old_class[2] == rec["graph6"]
                and int(old_class[3]) == rec["members"],
                "Frozen class reference differs from proof representative")
        ids = [int(v) for v in old_class[5].split(",")]
        require(len(ids) == rec["members"] == len(set(ids)),
                "Class does not contain the expected distinct originals")
        canonical = nx.from_graph6_bytes(rec["graph6"].encode("ascii"))
        for index in ids:
            require(index not in lifted, "Two positive classes overlap")
            source = rows.get(index)
            require(source is not None and source[1] == "9"
                    and source[3:] == ["-", "-", "-"],
                    "A claimed class member is not currently unclassified")
            other = nx.from_graph6_bytes(source[2].encode("ascii"))
            require(nx.is_isomorphic(canonical, other),
                    "Frozen pared graph is not isomorphic to its target core")
            lifted.add(index)
        proof["lifted_originals"] = len(ids)
        proofs.append(proof)

    require(len(lifted) == 351, "Unexpected combined certified population")

    if self_test:
        import copy
        altered = copy.deepcopy(records[0])
        target = altered["opposite_pairs"][0][0]
        altered["projection"][target] = altered["opposite_pairs"][0][1]
        try:
            replay_core(altered)
        except ValueError:
            pass
        else:
            raise AssertionError("Broken fixed section escaped verification")
        altered = copy.deepcopy(records[1])
        altered["iterate_sizes"][3][1] += 1
        try:
            replay_core(altered)
        except ValueError:
            pass
        else:
            raise AssertionError("Incorrect K³ edge count escaped verification")

    for item in proofs:
        print(json.dumps(item, sort_keys=True))
    print("VERIFIED: two exact raw K³ retractions to O5 and O6,"
          " 351 currently unresolved original ten-vertex graphs;"
          " all historical census files unchanged.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    verify(parser.parse_args().self_test)
