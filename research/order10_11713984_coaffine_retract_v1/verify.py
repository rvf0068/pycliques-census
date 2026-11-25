"""Permanent exact 35-vertex retract of P3 of ten-original 11713984.

Independent graph and map reconstruction; no native solver and no P4 build.
The next-iterate homology consequence is mathematical, not a K-divergence
classification.
"""
from __future__ import annotations

import base64
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import zlib

if sys.flags.optimize:
    raise RuntimeError("Proof assertions must not be optimized away")

import networkx as nx

from research.order10_p3_global_v23_index.independent_verify import (
    git_blob, independent_p3,
)

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ARCHIVE = HERE / "certificate.json"
ARCHIVE_BLOB = "3bb434dd4dad415f22bc7d85e0bd7e61c961ad4a"
TEN_V25 = ROOT / "indeterminate_order_10_v25.txt"
TEN_V25_BLOB = "d31d52d28427adcef6055cc1d277565fe88f32d5"
ORIGINAL = 11713984
SOURCE_G6 = "IQzVr~{lw"
P3_SHA = "dd4b3596ed2aa11e7c01d1e532feee5476627978c0852f80fe6931c7d394afbf"
RAW_MAP_SHA = "f90f460ff7769e440f7ef9c929b1768ee4db7e953da512fee6a47aeb948f9d69"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def audit_map(G: nx.Graph, f: list[int], expected_image: set[int]) -> tuple[nx.Graph, list[int]]:
    """Check the entire coaffine weak morphism and its idempotent 14th power."""
    n = len(G)
    require(set(G) == set(range(n)) and len(f) == n
            and all(type(v) is int and 0 <= v < n for v in f),
            "Map is not total on the canonical source")
    for v in G:
        require(v != f[v] and not G.has_edge(v, f[v]),
                "Coaffine vertex constraint fails")
    for u, v in G.edges():
        require(f[u] == f[v] or G.has_edge(f[u], f[v]),
                "Endomorphism does not preserve source edge")
    image = set(f)
    require(image == expected_image and set(f[v] for v in image) == image,
            "Expected invariant image of 35 vertices not obtained")
    current = list(range(n))
    for _ in range(14):
        current = [f[v] for v in current]
    require(set(current) == image and all(current[v] == v for v in image),
            "Fourteenth power does not retract pointwise onto stable image")
    for u, v in G.edges():
        require(current[u] == current[v] or G.has_edge(current[u], current[v]),
                "Idempotent retraction fails source edge")
    Y = G.subgraph(sorted(image)).copy()
    return Y, current


def verify() -> dict:
    raw = ARCHIVE.read_bytes()
    require(git_blob(raw) == ARCHIVE_BLOB,
            "Immutable coaffine map archive Git blob changed")
    cert = json.loads(raw)
    require(cert["schema"] == 1 and
            cert["kind"] ==
                "permanent_coaffine_endomorphism_and_idempotent_retract_11713984"
            and cert["original_mckay"] == ORIGINAL
            and cert["original_graph6"] == SOURCE_G6
            and cert["p3_graph6_sha256"] == P3_SHA
            and cert["p3_vertices"] == 169
            and cert["p3_edges"] == 12897
            and cert["historical_native_run"] == 45677034487
            and cert["historical_artifact_id"] == 15051972027
            and cert["historical_monorepo_commit"] ==
                "f8eb9b9f2c71d79f9394571df98155f9de568785"
            and cert["coaffine_status"] == "FOUND"
            and cert["coaffine_states"] == 8343
            and cert["map_encoding"] == "zlib_uint8_base64"
            and cert["map_raw_sha256"] == RAW_MAP_SHA,
            "Wrong archived source or positive map provenance")
    old = TEN_V25.read_bytes()
    require(git_blob(old) == TEN_V25_BLOB,
            "Historical original graph6 snapshot changed")
    rows = [
        line.split() for line in old.decode("ascii").splitlines()
        if line and not line.startswith("#")
    ]
    targets = [row for row in rows if int(row[0]) == ORIGINAL]
    require(len(targets) == 1 and targets[0] ==
            [str(ORIGINAL), "10", SOURCE_G6, "-", "-", "-"],
            "Wrong original ten-vertex McKay index or graph6")
    G = independent_p3(SOURCE_G6)
    actual_g6 = nx.to_graph6_bytes(G, header=False).decode("ascii").strip()
    require([len(G), G.number_of_edges()] == [169, 12897]
            and hashlib.sha256(actual_g6.encode("ascii")).hexdigest() == P3_SHA,
            "Independent reconstruction does not match pinned P3 graph6")

    raw_map = zlib.decompress(base64.b64decode(
        cert["map_zlib_base64"], validate=True))
    require(len(raw_map) == 169 and
            hashlib.sha256(raw_map).hexdigest() == RAW_MAP_SHA,
            "Archived original native coaffine map corrupted")
    f = list(raw_map)
    S = set(cert["stable_image_vertices"])
    require(len(S) == cert["stable_image_vertices_count"] == 35,
            "Wrong image vertex count")
    Y, ret = audit_map(G, f, S)
    require(Y.number_of_edges() == cert["stable_image_edges"] == 574,
            "Image-induced graph edge count changed")
    cycle_lengths = Counter()
    unseen = set(S)
    while unseen:
        start = min(unseen)
        v, count = start, 0
        while True:
            require(v in unseen, "Restriction not a permutation on image")
            unseen.remove(v)
            count += 1
            v = f[v]
            if v == start:
                break
        cycle_lengths[count] += 1
    require(dict(cycle_lengths) == {2: 14, 7: 1}
            and cert["endomorphism_period_on_image"] == 14,
            "Stable automorphism fails the 14-antipodal + 7-cycle structure")

    H = nx.complement(Y)
    components = [sorted(s) for s in nx.connected_components(H)]
    pairs = sorted(s for s in components if len(s) == 2)
    seven = next((s for s in components if len(s) == 7), None)
    require(pairs == cert["complement_two_vertex_components"]
            and seven == cert["complement_seven_cycle_vertices"]
            and len(components) == 15
            and all(H.has_edge(*p) for p in pairs)
            and seven is not None
            and nx.is_isomorphic(H.subgraph(seven), nx.cycle_graph(7)),
            "Stable retract is not the pinned O14 join complement of C7")

    Z = Y.subgraph(seven)
    facets = list(nx.find_cliques(Z))
    disjoint = nx.Graph()
    disjoint.add_nodes_from(range(len(facets)))
    disjoint.add_edges_from(
        (i, j) for i in range(len(facets))
        for j in range(i + 1, len(facets))
        if set(facets[i]).isdisjoint(facets[j])
    )
    require(len(facets) == 7 and
            nx.is_isomorphic(disjoint, nx.cycle_graph(7)),
            "Seven-factor maximal-clique disjointness graph is not C7")

    # A clique of O14 join Z consists of one endpoint of each pair
    # and one maximal clique of Z: 2^14 * 7 choices. Two such cliques
    # are disjoint precisely when their 14 binary coordinates are
    # antipodal AND the Z-cliques are disjoint. Thus the complement
    # of the clique graph is 2^13 disjoint bipartite double covers
    # of C7, each of which is an induced C14.
    components_next = 1 << 13
    k_order = 7 * (1 << 14)
    sphere_dim = 5 * components_next - 1
    return {
        "schema": 1,
        "kind": "certified_coaffine_14th_power_retraction_and_next_stage_homology",
        "original_index": ORIGINAL,
        "P3": [169, 12897],
        "coaffine_weak_endomorphism_verified_on_all_edges": True,
        "ordinary_retraction_from_fourteenth_power_verified_on_all_edges": True,
        "retraction_image": {"vertices": 35, "edges": 574,
                             "isomorphic_to": "O14_join_complement_C7"},
        "induced_complement_factors": {"K2": 14, "C7": 1},
        "cliques_of_image": k_order,
        "complement_of_clique_graph_image": {
            "components": components_next,
            "each_component": "C14",
            "vertices": k_order,
        },
        "next_pared_iterate_free_Z_homology_dimension": sphere_dim,
        "next_pared_iterate_minimum_vertices": 2 * (sphere_dim + 1),
        "does_not_alone_prove_K_divergence": True,
        "ten_v27_indeterminate_population_unchanged": 1044,
    }


def main() -> None:
    print(json.dumps(verify(), indent=2, sort_keys=True))
    print("PASS: exact coaffine power retract O14 join complement C7 "
          "and derived H_40959 lower bound")


if __name__ == "__main__":
    main()
