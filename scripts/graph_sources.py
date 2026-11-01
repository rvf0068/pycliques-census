"""Stable sources of connected unlabeled graphs, through order ten.

Orders 1--5 use NetworkX's graph atlas; orders 6--10 use the McKay
connected graph6 files distributed by pyg6data. Original source order
and zero-based indices must never be changed by the census runner.
"""

from collections.abc import Iterator

import networkx as nx

# OEIS A001349 / Brendan McKay's connected graph census.
EXPECTED_COUNTS = {
    1: 1,
    2: 1,
    3: 2,
    4: 6,
    5: 21,
    6: 112,
    7: 853,
    8: 11117,
    9: 261080,
    10: 11716571,
}


def connected_graphs(n: int) -> Iterator[nx.Graph]:
    if n not in EXPECTED_COUNTS:
        raise ValueError(f"unsupported connected graph order: {n}")
    if n <= 5:
        for graph in nx.graph_atlas_g():
            if graph.number_of_nodes() == n and nx.is_connected(graph):
                yield graph
    else:
        from pyg6data.lists import graph_generator

        yield from graph_generator(n, connected=True)


def graph6(graph: nx.Graph) -> str:
    return nx.to_graph6_bytes(graph, header=False).decode("ascii").strip()
