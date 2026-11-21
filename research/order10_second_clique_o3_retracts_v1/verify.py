"""Replay twelve exact K^2(G) -> O_3 graph retractions for order-ten cores.

The previous v8 source is immutable; a positive map is a complete edge-by-edge
certificate. No unsuccessful search is used to infer K-behavior.
Requires NetworkX 3.6.1; does not use pycliques or optimization solvers.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "indeterminate_order_10_v8.txt"
RECORD = Path(__file__).with_name("certificates.json")
SOURCE_GIT_BLOB = "b8d36442ae3c4cda702900b7cbc74d8be45f7072"
IDS = (
    10298587, 10582171, 10592280, 11031164, 11031734, 11106678,
    11551444, 11566611, 11585214, 11599630, 11602159, 11624876,
)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def frozen_rows() -> dict[int, list[str]]:
    source = SOURCE.read_bytes()
    require(git_blob(source) == SOURCE_GIT_BLOB,
            "Historical version-eight snapshot changed")
    result: dict[int, list[str]] = {}
    for line in source.decode("utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        cells = line.split()
        require(len(cells) == 6, "Malformed frozen source entry")
        key = int(cells[0])
        require(key not in result, "Duplicate frozen McKay index")
        result[key] = cells
    require(len(result) == 7932, "Unexpected frozen v8 population")
    require(sum(row[1] == "10" for row in result.values()) == 2357,
            "Unexpected frozen stiff ten-core population")
    require(sum(row[4] == "conjectured_divergent" for row in result.values())
            == 4509, "Conditional references unexpectedly changed")
    return result


def maximal_cliques_bitset(g: nx.Graph) -> set[int]:
    """Independent maximal-clique algorithm, with no NetworkX clique search."""
    n = len(g)
    require(set(g) == set(range(n)), "Vertices must be labeled 0..n-1")
    neighbors = [sum(1 << j for j in g[i]) for i in range(n)]
    found: set[int] = set()

    def visit(clique: int, possible: int, excluded: int) -> None:
        if not (possible or excluded):
            require(clique not in found, "Duplicated independently found facet")
            found.add(clique)
            return
        union = possible | excluded
        pivot = max(
            (i for i in range(n) if (union >> i) & 1),
            key=lambda i: (possible & neighbors[i]).bit_count(),
            default=None,
        )
        choices = possible & ~(neighbors[pivot] if pivot is not None else 0)
        while choices:
            bit = choices & -choices
            vertex = bit.bit_length() - 1
            visit(clique | bit,
                  possible & neighbors[vertex],
                  excluded & neighbors[vertex])
            possible ^= bit
            excluded |= bit
            choices ^= bit

    visit(0, (1 << n) - 1, 0)
    return found


def clique_graph(g: nx.Graph) -> nx.Graph:
    """Canonical K(G) labeling: facets in increasing integer-mask order."""
    facets = sorted(
        (frozenset(q) for q in nx.find_cliques(g)),
        key=lambda q: sum(1 << v for v in q),
    )
    expected = {sum(1 << v for v in facet) for facet in facets}
    require(expected == maximal_cliques_bitset(g),
            "Independent and NetworkX maximal-clique enumerators disagree")
    h = nx.Graph()
    h.add_nodes_from(range(len(facets)))
    h.add_edges_from(
        (i, j) for i, j in itertools.combinations(range(len(facets)), 2)
        if facets[i] & facets[j]
    )
    return h


def verify_certificate(record: dict, source: dict[int, list[str]]) -> dict:
    require(
        isinstance(record, dict)
        and set(record) == {
            "index", "graph6", "k1_vertices", "k1_edges", "k2_vertices",
            "k2_edges", "target", "projection"
        }, "Certificate field set invalid"
    )
    index = record["index"]
    require(type(index) is int and index in source,
            "Unknown certified McKay index")
    historical = source[index]
    require(
        historical[1] == "10"
        and historical[2] == record["graph6"]
        and historical[3:] == ["-", "-", "-"],
        "Proof must refer to a previously unclassified stiff ten-core"
    )
    g = nx.from_graph6_bytes(record["graph6"].encode("ascii"))
    require(
        len(g) == 10 and nx.is_connected(g)
        and all(
            not (set(g[v]) | {v}) <= (set(g[u]) | {u})
            for v in g for u in g[v]
        ),
        "Input is not a stiff connected ten-vertex graph"
    )

    first = clique_graph(g)
    second = clique_graph(first)
    require(
        (len(first), first.number_of_edges())
        == (record["k1_vertices"], record["k1_edges"])
        and (len(second), second.number_of_edges())
        == (record["k2_vertices"], record["k2_edges"]),
        "Reconstructed clique-iterate size differs from certificate"
    )

    target = record["target"]
    projection = record["projection"]
    require(
        isinstance(target, list) and len(target) == 6
        and all(type(u) is int for u in target)
        and sorted(set(target)) == target
        and set(target) <= set(second)
        and isinstance(projection, list)
        and len(projection) == len(second)
        and all(type(u) is int and u in target for u in projection)
        and all(projection[t] == t for t in target),
        "Invalid induced section or total projection"
    )
    sub = second.subgraph(target)
    nonedges = list(nx.non_edges(sub))
    require(
        len(nonedges) == 3
        and len({x for edge in nonedges for x in edge}) == 6
        and nx.is_isomorphic(sub, nx.complete_multipartite_graph(2, 2, 2)),
        "Target does not induce O_3"
    )
    require(
        all(
            projection[u] == projection[v]
            or sub.has_edge(projection[u], projection[v])
            for u, v in second.edges()
        ),
        "Projection does not preserve source adjacency or equality"
    )
    return {
        "index": index, "graph6": historical[2],
        "clique_graph_order": len(first),
        "second_clique_graph_order": len(second),
        "second_clique_graph_edges_checked": second.number_of_edges(),
        "target_opposite_pairs": sorted(tuple(sorted(p)) for p in nonedges),
        "status": "K_DIVERGENT_CERTIFIED",
    }


def verify(self_test: bool = False) -> None:
    source = frozen_rows()
    data = json.loads(RECORD.read_text(encoding="utf-8"))
    require(
        set(data) == {"schema", "source", "graph", "target", "certificates"}
        and data["schema"] == 1
        and data["source"] == SOURCE.name
        and data["target"] == "O_3"
        and data["graph"] == "raw second clique graph K^2(G)"
        and isinstance(data["certificates"], list)
        and len(data["certificates"]) == len(IDS),
        "Malformed standalone research record"
    )
    records = data["certificates"]
    require(tuple(rec["index"] for rec in records) == IDS,
            "Unexpected or duplicate set of newly proved originals")
    verified = [verify_certificate(rec, source) for rec in records]
    if self_test:
        changed = json.loads(json.dumps(records[0]))
        changed["projection"][changed["target"][0]] = changed["target"][1]
        try:
            verify_certificate(changed, source)
        except ValueError:
            pass
        else:
            raise AssertionError("Mutation of the fixed section went undetected")
        changed = json.loads(json.dumps(records[0]))
        changed["k2_edges"] += 1
        try:
            verify_certificate(changed, source)
        except ValueError:
            pass
        else:
            raise AssertionError("Mutation of the clique graph went undetected")
        changed = json.loads(json.dumps(records[0]))
        changed["graph6"] = "I????????"
        try:
            verify_certificate(changed, source)
        except ValueError:
            pass
        else:
            raise AssertionError("Mutation of the original input went undetected")
    for item in verified:
        print(json.dumps(item, sort_keys=True))
    print("VERIFIED: 12 independent raw K^2 -> O_3 retractions; "
          "no census files changed by this verifier.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    verify(parser.parse_args().self_test)
