"""Exact weighted edge-neighborhood covering obstruction to P4 -> O5.

For H = complement(P4(G_251902)), let C(uv) = N_H[u] union N_H[v]
for each complement edge uv. Integer weights satisfy
  W = sum_v w_v = 50893,
  max_{uv in E(H)} sum_{x in C(uv)} w_x = 9990.
Five complement edges cover total weight at most 5*9990 = 49950 < W,
so no collection of five complement edges dominates all H vertices.
A P4 -> O5 retraction requires five antipodal complement edges whose
endpoints dominate H. Hence no such ordinary retraction exists.

No optimization solver, floating-point operations, randomized search,
or resource-bounded negative test is used in the proof.
"""
from __future__ import annotations

import argparse
import base64
import json
import struct
import sys
from pathlib import Path

import networkx as nx

from research.order9_p4_domination_dual_v1.verify import (
    build_p4,
    edge_digest,
    frozen_sources,
)

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical assertions")

HERE = Path(__file__).resolve().parent
CERT = HERE / "certificate.json"


def pair_cover_bound(x: nx.Graph, weights: tuple[int, ...]) -> tuple[int, int, int]:
    """Return (weight sum, maximum edge-neighborhood weight, complement edges).

    Uses only integer operations. For each complement edge uv we sum weights
    over N_H[u] union N_H[v], counting each vertex at most once.
    """
    n = len(x)
    assert set(x) == set(range(n)), "Vertex labels must be 0, ..., n-1"
    assert len(weights) == n and all(isinstance(w, int) and w >= 0 for w in weights)
    H = nx.complement(x)
    assert H.number_of_edges() > 0
    closed = [set(H[v]) | {v} for v in H]
    maximum = 0
    for u, v in H.edges():
        load = sum(weights[t] for t in closed[u] | closed[v])
        maximum = max(maximum, load)
    return sum(weights), maximum, H.number_of_edges()


def test_self_examples() -> None:
    x = nx.octahedral_graph()
    # The complement of O3 consists of three disjoint edges. All-one
    # weights give W=6 and edge-neighborhood cap 2, hence dimension >=3.
    assert pair_cover_bound(x, (1,) * 6) == (6, 2, 3)


def verify(*, public: bool = False) -> None:
    frozen_sources()
    test_self_examples()
    c = json.loads(CERT.read_text(encoding="utf-8"))
    assert (
        c["schema"], c["mckay_index"], c["original_graph6"],
        c["pared_depth"], c["p4_order"], c["p4_edges"],
        c["complement_edges"],
    ) == (1, 251902, "HEhvvzm", 4, 461, 94642, 11388)
    assert c["weights_encoding"] == (
        "uint16_little_endian_per_normalized_p4_label"
    )
    assert c["scale"] == 10000

    x = build_p4(c["original_graph6"], public=public)
    assert (len(x), x.number_of_edges()) == (
        c["p4_order"], c["p4_edges"]
    ), "Unexpected reconstructed fourth pared iterate"
    assert edge_digest(x) == c["p4_edge_sha256"], (
        "Reconstructed normalized P4 labeling differs from saved witness"
    )
    assert c["p4_edge_sha256"] == (
        "e09bfabf7e7a2ab4af810f09c16942b6e64a9dfba9e5027f9cd62a5bee66efb1"
    )

    raw = base64.b64decode(c["weights_b64"], validate=True)
    assert len(raw) == 2 * len(x), "Wrong count of saved integer weights"
    weights = struct.unpack(f"<{len(x)}H", raw)
    weight_sum, max_load, complement_edges = pair_cover_bound(x, weights)
    assert (
        weight_sum == c["weight_sum"] == 50893
        and max_load == c["max_edge_neighborhood_union_weight"] == 9990
        and complement_edges == c["complement_edges"] == 11388
    ), "The saved dual is not the claimed exact certificate"
    assert weight_sum > 5 * max_load, (
        "Pair-neighborhood weights do not rule out five dominating edges"
    )
    minimum_pairs = (weight_sum + max_load - 1) // max_load
    assert minimum_pairs == c["minimum_octahedral_retraction_dimension"] == 6

    print(
        f"PASS McKay=251902 P4_vertices={len(x)} P4_edges={x.number_of_edges()} "
        f"complement_edges={complement_edges} pair_cover_weight={weight_sum} "
        f"max_edge_cover_weight={max_load} min_dominating_pairs={minimum_pairs} "
        f"ordinary_P4_to_O5=EXCLUDED "
        f"reconstruction={'public-and-independent' if public else 'independent'}",
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public", action="store_true")
    args = parser.parse_args()
    verify(public=args.public)


if __name__ == "__main__":
    main()
