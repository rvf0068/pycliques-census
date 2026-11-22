"""Unseeded O17 rediscovery from graph6 by dual-guided vertex ordering.

No saved antipodal pair, projection, or target image is passed to the
public native coaffine solver. The only search guidance is an integer
vertex weight vector discovered from a *separate* edge-neighborhood dual.
A positive result is checked afresh by public pycliques witness verifiers.
"""
from __future__ import annotations

import base64
import struct
import sys

import networkx as nx
import pycliques as pc

from research.order9_251902_p4_o17_v1.verify import (
    ORDERS, SOURCE, read_certificate, reconstruct,
)

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical assertions")


def main() -> None:
    saved = read_certificate()
    graph = reconstruct()
    raw = base64.b64decode(saved["discovery"]["weights_b64"], validate=True)
    assert len(raw) == 2 * len(graph) == 2 * ORDERS[-1]
    weights = struct.unpack(f"<{len(graph)}H", raw)

    # Low weight first, then high host degree, then the numeric label.
    # All ties are deterministic. This is an unseeded discovery order,
    # not a supplied octahedral target or retraction.
    order = sorted(
        graph, key=lambda v: (weights[v], -graph.degree[v], v)
    )
    ordered = nx.Graph()
    ordered.add_nodes_from(order)
    ordered.add_edges_from(graph.edges())
    assert set(ordered) == set(graph)
    assert nx.utils.edges_equal(ordered.edges(), graph.edges())

    print(f"Explicit native C++17 executable: {pc.build_coaffine_native()}", flush=True)
    result = pc.find_octahedral_retraction_coaffine(
        ordered,
        backend="native",
        min_dimension=6,
        max_states=10000,
        time_limit=60,
    )
    assert result.status is pc.RetractionSearchStatus.FOUND, (
        "Unseeded native search incomplete or failed",
        result.status.name, result.states_explored
    )
    assert result.dimension == 17, ("Unexpected target dimension", result.dimension)
    assert result.antipodal_pairs is not None
    assert result.retraction is not None
    assert result.inclusion is not None
    target = set(v for pair in result.antipodal_pairs for v in pair)
    assert len(target) == 34
    assert pc.verify_induced_octahedron(ordered, result.antipodal_pairs)
    assert pc.verify_retraction_witness(
        ordered, ordered.subgraph(target),
        (result.retraction, result.inclusion),
    )
    print(
        "PASS_UNSEEDED_NATIVE_COAFFINE_DISCOVERY "
        f"McKay=251902 P4={len(graph)} target=O17 "
        f"states={result.states_explored} all_images_checked={len(result.retraction)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
