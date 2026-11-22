"""Independent proof replay: three fourth-pared-iterate octahedral retractions.

The certificates store an entire projection on each labeled P4 host, not just
an induced O_d. Default replay uses only NetworkX; --public runs pycliques'
separate positive witness verifiers. The 344 order-ten lifts are checked
against the frozen v17 census by independent graph isomorphism.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import itertools
import json
import sys
from pathlib import Path

import networkx as nx

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical assertions")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CERT = HERE / "certificate.json"
SOURCES = {249436: "HEhff^{", 249574: "HEhfvx}", 250814: "HEhuvzm"}
DIMENSIONS = {249436: 10, 249574: 12, 250814: 14}
LIFTS = {249436: 141, 249574: 82, 250814: 121}


def pare(graph: nx.Graph) -> nx.Graph:
    h = graph.copy()
    while True:
        closed = {v: set(h[v]) | {v} for v in h}
        victim = next(
            (v for v in sorted(h) if any(
                v != w and closed[v] <= closed[w] for w in h
            )), None
        )
        if victim is None:
            return h
        h.remove_node(victim)


def clique_graph(graph: nx.Graph) -> nx.Graph:
    cliques = list(nx.find_cliques(graph))
    out = nx.empty_graph(len(cliques))
    membership = {v: [] for v in graph}
    for j, clique in enumerate(cliques):
        for v in clique:
            membership[v].append(j)
    for indices in membership.values():
        out.add_edges_from(itertools.combinations(indices, 2))
    return out


def edge_digest(graph: nx.Graph) -> str:
    edges = sorted((min(u, v), max(u, v)) for u, v in graph.edges())
    payload = "\n".join(f"{u},{v}" for u, v in edges).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def frozen_rows(name: str) -> dict[int, list[str]]:
    rows: dict[int, list[str]] = {}
    for line in (ROOT / name).read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        assert len(parts) == 6, (name, line)
        index = int(parts[0])
        assert index not in rows, (name, index)
        rows[index] = parts
    return rows


def check_certificates(*, public: bool = False) -> None:
    data = json.loads(CERT.read_text(encoding="utf-8"))
    assert data["schema"] == 1
    assert data["target_image_encoding"] == (
        "uint8_sorted_target_ordinal_per_sorted_host_label"
    )
    cases = data["cases"]
    assert len(cases) == 3 and {d["mckay_index"] for d in cases} == set(SOURCES)
    nine = frozen_rows("indeterminate_order_9_v6.txt")
    assert len(nine) == 9

    for row in cases:
        index = row["mckay_index"]
        graph6 = SOURCES[index]
        assert nine[index] == [str(index), "9", graph6, "-", "-", "-"]
        assert (row["source_graph6"], row["pared_depth"]) == (graph6, 4)

        host = pare(nx.from_graph6_bytes(graph6.encode("ascii")))
        assert len(row["orders"]) == len(row["edges"]) == 5
        for level in range(5):
            assert (len(host), host.number_of_edges()) == (
                row["orders"][level], row["edges"][level]
            ), (index, level)
            if level != 4:
                host = pare(clique_graph(host))

        assert edge_digest(host) == row["p4_edge_sha256"], index
        pairs = [tuple(pair) for pair in row["antipodal_pairs"]]
        target = {v for pair in pairs for v in pair}
        dimension = DIMENSIONS[index]
        assert len(pairs) == dimension and len(target) == 2 * dimension
        assert target <= set(host)
        assert {frozenset(pair) for pair in pairs} == {
            frozenset(edge)
            for edge in nx.complement(host.subgraph(target)).edges()
        }, f"Invalid induced O{dimension} at {index}"

        ordered_target = sorted(target)
        images = base64.b64decode(row["images_b64"], validate=True)
        assert len(images) == len(host) and all(
            image < len(ordered_target) for image in images
        )
        projection = dict(zip(
            sorted(host),
            (ordered_target[i] for i in images),
            strict=True,
        ))
        assert set(projection) == set(host)
        assert set(projection.values()) == target
        assert all(projection[v] == v for v in target)
        assert all(
            projection[u] == projection[v]
            or host.has_edge(projection[u], projection[v])
            for u, v in host.edges()
        ), f"Graph-morphism failure for McKay {index}"

        if public:
            import pycliques
            assert pycliques.verify_induced_octahedron(host, pairs)
            assert pycliques.verify_retraction_witness(
                host, host.subgraph(target),
                (projection, {v: v for v in target}),
            )
        print(
            f"PASS McKay={index} P4_order={len(host)} P4_edges={host.number_of_edges()} "
            f"retraction=O{dimension} full_projection={len(projection)}",
            flush=True,
        )


def check_ten_lifts() -> None:
    data = json.loads(CERT.read_text(encoding="utf-8"))
    references = {
        d["mckay_index"]: nx.from_graph6_bytes(d["source_graph6"].encode("ascii"))
        for d in data["cases"]
    }
    ten = frozen_rows("indeterminate_order_10_v17.txt")
    assert len(ten) == 2025
    family: dict[int, list[int]] = {index: [] for index in references}
    nine_pared = 0
    for original, row in ten.items():
        assert row[3:] == ["-", "-", "-"]
        if row[1] != "9":
            continue
        nine_pared += 1
        core = nx.from_graph6_bytes(row[2].encode("ascii"))
        for index, reference in references.items():
            matcher = nx.algorithms.isomorphism.GraphMatcher(reference, core)
            if matcher.is_isomorphic():
                iso = matcher.mapping
                assert len(iso) == 9 and set(iso) == set(reference)
                assert set(iso.values()) == set(core)
                assert all(
                    reference.has_edge(u, v)
                    == core.has_edge(iso[u], iso[v])
                    for u in reference for v in reference
                ), f"False ten-vertex core isomorphism: {original}"
                family[index].append(original)

    assert nine_pared == 1144
    for index, originals in family.items():
        assert len(originals) == LIFTS[index], (index, len(originals))
        assert len(originals) == len(set(originals))
        print(f"PASS ten-vertex family McKay={index} originals={len(originals)}")
    all_indices = [x for values in family.values() for x in values]
    assert len(all_indices) == len(set(all_indices)) == 344
    print("PASS 344 distinct ten-vertex originals; frozen v17 unchanged")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public", action="store_true")
    parser.add_argument("--only-certificates", action="store_true")
    args = parser.parse_args()
    check_certificates(public=args.public)
    if not args.only_certificates:
        check_ten_lifts()


if __name__ == "__main__":
    main()
