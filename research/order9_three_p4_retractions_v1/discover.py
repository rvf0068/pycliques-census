"""Unseeded deterministic degree-order rediscovery with merged pycliques PR36.

No certificate pairs or projection maps are used by this search. It creates
each fourth completely pared clique iterate from original graph6 and invokes
the public native coaffine CSP, verifying the resulting retraction independently.
"""
from __future__ import annotations

import json
from pathlib import Path
import networkx as nx
import pycliques as pc
from verify import SOURCES, clique_graph, edge_digest, pare

HERE = Path(__file__).resolve().parent
EXPECTED = {249436: (353, 49491, 10, "ascending"),
            249574: (306, 40622, 12, "ascending"),
            250814: (222, 21487, 14, "descending")}


def main() -> None:
    if not __debug__:
        raise RuntimeError("Optimized Python bypasses proof-critical assertions")
    saved = json.loads((HERE / "certificate.json").read_text("utf-8"))
    print(f"Native executable: {pc.build_coaffine_native()}", flush=True)

    for index, (order, edges, dimension, direction) in EXPECTED.items():
        g = pare(nx.from_graph6_bytes(SOURCES[index].encode("ascii")))
        for _ in range(4):
            g = pare(clique_graph(g))
        assert (len(g), g.number_of_edges()) == (order, edges)
        record = next(x for x in saved["cases"] if x["mckay_index"] == index)
        assert edge_digest(g) == record["p4_edge_sha256"]

        if direction == "ascending":
            sorted_vertices = sorted(g, key=lambda v: (g.degree[v], v))
        else:
            sorted_vertices = sorted(g, key=lambda v: (-g.degree[v], v))

        # Graph insertion order is the search order used by PR36's native solver.
        ordered = nx.Graph()
        ordered.add_nodes_from(sorted_vertices)
        ordered.add_edges_from(g.edges())
        result = pc.find_octahedral_retraction_coaffine(
            ordered, backend="native",
            min_dimension=3,
            max_states=20000,
            time_limit=40,
        )
        assert result.status is pc.RetractionSearchStatus.FOUND, (
            index, result.status.name, result.states_explored
        )
        assert result.dimension == dimension, (index, result.dimension)
        assert result.retraction is not None and result.antipodal_pairs is not None
        target = ordered.subgraph(
            v for pair in result.antipodal_pairs for v in pair
        )
        assert pc.verify_induced_octahedron(ordered, result.antipodal_pairs)
        assert pc.verify_retraction_witness(
            ordered, target, (result.retraction, result.inclusion)
        )
        print(
            f"PASS rediscovery McKay={index} P4={order} "
            f"target=O{dimension} states={result.states_explored} "
            f"vertex_order={direction}",
            flush=True,
        )


if __name__ == "__main__":
    main()
