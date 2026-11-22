"""Independently certify McKay 251902 P4 -> O17 and 150 ten-v18 lifts.

The saved certificate includes every image of a 461-vertex retraction,
not merely antipodal target pairs. Reconstruction, graph morphology,
pointwise fixation and the 150 ten-vertex dependencies use only NetworkX.
Optional --public checks public pycliques' independent witness routines.
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

from research.order9_p4_domination_dual_v1.verify import (
    build_p4,
    clique_graph,
    edge_digest,
    frozen_sources,
    normalized,
    pare,
    same_graph,
)

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical assertions")

ROOT = Path(__file__).resolve().parents[2]
CERT = Path(__file__).resolve().parent / "certificate.json"
SOURCE = "HEhvvzm"
MCKAY = 251902
ORDERS = (9, 12, 18, 41, 461)
EDGES = (24, 45, 114, 641, 94642)
P4_SHA256 = "e09bfabf7e7a2ab4af810f09c16942b6e64a9dfba9e5027f9cd62a5bee66efb1"


def read_certificate() -> dict:
    saved = json.loads(CERT.read_text(encoding="utf-8"))
    assert (saved["schema"], saved["mckay_index"], saved["source_graph6"],
            saved["pared_depth"]) == (1, MCKAY, SOURCE, 4)
    assert (tuple(saved["iterate_orders"]), tuple(saved["iterate_edges"])) == (
        ORDERS, EDGES
    )
    assert (saved["host_order"], saved["host_edges"],
            saved["host_edge_sha256"]) == (461, 94642, P4_SHA256)
    assert saved["image_encoding"] == (
        "uint8_target_ordinal_per_sorted_normalized_p4_host_label"
    )
    assert saved["target_dimension"] == 17
    return saved


def reconstruct(*, public: bool = False) -> nx.Graph:
    """Rebuild all five iterates, independently checking each intermediate size."""
    frozen_sources()  # Check immutable original-nine-v7 McKay identities.
    graph = pare(nx.from_graph6_bytes(SOURCE.encode("ascii")))
    for j, (vertices, edges) in enumerate(zip(ORDERS, EDGES, strict=True)):
        assert (len(graph), graph.number_of_edges()) == (
            vertices, edges
        ), ("Invalid labeled Pj iterate", j)
        if j != 4:
            graph = pare(clique_graph(graph))
    host = normalized(graph)
    assert (len(host), host.number_of_edges()) == ORDERS[-1:] + EDGES[-1:]
    assert edge_digest(host) == P4_SHA256, "Exact P4 labeling or edges changed"

    if public:
        # Public pycliques is separately checked at every stage, using
        # explicit maximal-clique identities instead of a dense VF2 search.
        public_host = build_p4(SOURCE, public=True)
        assert same_graph(host, public_host), "Independent/public P4 mismatch"
    return host


def verify_positive(*, public: bool = False) -> None:
    saved = read_certificate()
    host = reconstruct(public=public)
    pairs = [tuple(map(int, pair)) for pair in saved["antipodal_pairs"]]
    assert len(pairs) == 17
    target = {v for pair in pairs for v in pair}
    assert len(target) == 34 and target <= set(host)
    target_order = sorted(target)
    assert saved["target_order"] == target_order
    missing = nx.complement(host.subgraph(target))
    assert missing.number_of_edges() == 17
    assert {frozenset(edge) for edge in missing.edges()} == {
        frozenset(pair) for pair in pairs
    }, "Target does not induce O17"

    images = base64.b64decode(saved["images_b64"], validate=True)
    assert len(images) == len(host), "Incomplete full-projection array"
    assert all(value < len(target_order) for value in images)
    projection = {
        v: target_order[images[v]]
        for v in sorted(host)
    }
    assert set(projection) == set(host) and set(projection.values()) == target
    assert all(projection[v] == v for v in target), "Target fixation fails"
    assert all(
        projection[u] == projection[v]
        or host.has_edge(projection[u], projection[v])
        for u, v in host.edges()
    ), "Projection fails adjacency preservation"

    if public:
        import pycliques

        assert pycliques.verify_induced_octahedron(host, pairs)
        assert pycliques.verify_retraction_witness(
            host, host.subgraph(target),
            (projection, {v: v for v in target}),
        )

    print(
        "PROVED_MCKAY_251902_K_DIVERGENT "
        "P4_ORDER=461 P4_EDGES=94642 P4_TO_O17=PASS "
        "ALL_461_PROJECTION_IMAGES_VERIFIED "
        + ("PUBLIC_PYCLIQUES=PASS" if public else "INDEPENDENT_NETWORKX=PASS"),
        flush=True,
    )


def verify_ten_lifts() -> None:
    """Independently find all remaining ten-v18 pared-nine source copies."""
    source = nx.from_graph6_bytes(SOURCE.encode("ascii"))
    frozen = ROOT / "indeterminate_order_10_v18.txt"
    lines = [
        line for line in frozen.read_text(encoding="ascii").splitlines()
        if line and not line.startswith("#")
    ]
    assert len(lines) == 1681
    hits = []
    nine_core_count = 0
    for line in lines:
        index, pared_order, g6, *cert = line.split()
        assert cert == ["-", "-", "-"], "Conditional ten-v18 record"
        if pared_order != "9":
            assert pared_order == "10"
            continue
        nine_core_count += 1
        core = nx.from_graph6_bytes(g6.encode("ascii"))
        matcher = nx.algorithms.isomorphism.GraphMatcher(source, core)
        if not matcher.is_isomorphic():
            continue
        mapping = matcher.mapping
        assert len(mapping) == 9 and set(mapping) == set(source)
        assert set(mapping.values()) == set(core)
        assert all(
            source.has_edge(a, b) == core.has_edge(mapping[a], mapping[b])
            for a in source for b in source
        ), f"Wrong ten-vertex core isomorphism at {index}"
        hits.append(int(index))

    assert nine_core_count == 800
    assert len(hits) == len(set(hits)) == 150
    print(
        "PROVED_150_TEN_ORIGINAL_DEPENDENTS "
        "EXACT_FROZEN_V18_CORE_ISOMORPHISMS=150 "
        "PARED_NINE_SURVIVORS_CHECKED=800",
        flush=True,
    )


def verify_ordering_metadata() -> None:
    """Verify dual weights used to order the unseeded discovery (not the proof)."""
    saved = read_certificate()
    meta = saved["discovery"]
    assert meta["method"] == "native_coaffine_degree_tiebreak_and_edge_cover_dual_weights"
    assert meta["weights_scale"] == 10000
    assert meta["weights_encoding"] == "uint16_little_endian_per_normalized_p4_host_vertex"
    raw = base64.b64decode(meta["weights_b64"], validate=True)
    assert len(raw) == 2 * ORDERS[-1]
    weights = struct.unpack(f"<{ORDERS[-1]}H", raw)
    assert len(weights) == 461 and sum(weights) == 50893
    print("PASS: deterministic integer dual-weight discovery metadata", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public", action="store_true")
    parser.add_argument("--no-lifts", action="store_true")
    args = parser.parse_args()
    verify_positive(public=args.public)
    verify_ordering_metadata()
    if not args.no_lifts:
        verify_ten_lifts()


if __name__ == "__main__":
    main()
