"""Isolated structural probe of an unresolved nine-vertex pared core.

No classification verdict is returned. A verified induced divergent
clockwork is an *observation*, not a proof of divergence of its host.
The GF(2) b1 of the flag complex is exact; a connected triangular
double cover requires b1 > 0, but b1 > 0 is not a divergence theorem.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import resource
import sys

import networkx as nx
from pycliques.coaffinations import coaffinations
from pycliques.clockwork_search import find_induced_clockwork_subgraphs
from pycliques.small import CliqueSequence

CLIQUE_BOUND = 120
MAX_CLIQUES = 512
CLOCKWORK_CANDIDATES = 96
COAFFINATIONS_CAP = 16


def encode(g: nx.Graph) -> str:
    h = nx.convert_node_labels_to_integers(g)
    return nx.to_graph6_bytes(h, header=False).decode("ascii").strip()


def betti1_mod2(graph: nx.Graph) -> tuple[int, int, int]:
    """Exact dim H_1(Delta(G); F_2) via triangle-boundary GF(2) rank.

    Every 2-simplex is a triangle, so higher-dimensional faces do not
    affect H_1. This does not assert an integral or homotopy type.
    """
    vertices = list(graph)
    edges = sorted(tuple(sorted(edge)) for edge in graph.edges())
    positions = {edge: j for j, edge in enumerate(edges)}
    pivots: dict[int, int] = {}
    triangles = 0
    for u in vertices:
        for v in graph[u]:
            if u >= v:
                continue
            for w in graph[u].keys() & graph[v].keys():
                if v >= w:
                    continue
                triangles += 1
                vector = (
                    (1 << positions[(u, v)])
                    ^ (1 << positions[(u, w)])
                    ^ (1 << positions[(v, w)])
                )
                while vector:
                    pivot = vector.bit_length() - 1
                    if pivot not in pivots:
                        pivots[pivot] = vector
                        break
                    vector ^= pivots[pivot]
    connected_components = nx.number_connected_components(graph)
    b1 = len(edges) - len(vertices) + connected_components - len(pivots)
    if b1 < 0:
        raise AssertionError("Negative first Betti number: GF(2) rank error")
    return b1, triangles, len(pivots)


def clique_sample(graph: nx.Graph, limit: int = MAX_CLIQUES) -> dict:
    """Count maximal cliques exactly or report a rigorous lower bound.

    Never extrapolate from a truncated enumeration. The observed clique-size
    histogram is a partial prefix, not a distribution, when truncated.
    """
    if limit < 1:
        raise ValueError("Clique limit must be positive")
    hist = Counter()
    count = 0
    for complete in nx.find_cliques(graph):
        count += 1
        if count > limit:
            return {
                "exact": False,
                "maximal_cliques_at_least": count,
                "maximal_cliques_exact": None,
                "partial_size_histogram": dict(sorted(hist.items())),
            }
        hist[len(complete)] += 1
    return {
        "exact": True,
        "maximal_cliques_at_least": count,
        "maximal_cliques_exact": count,
        "partial_size_histogram": dict(sorted(hist.items())),
    }


def coaffination_observation(graph: nx.Graph) -> dict:
    matches = []
    for tau in coaffinations(graph, 2):
        if len(matches) >= COAFFINATIONS_CAP:
            break
        # Record an explicit map so a candidate can be independently checked.
        matches.append([int(tau[v]) for v in sorted(graph)])
    return {
        "examples": matches,
        "searched_at_most": COAFFINATIONS_CAP + 1,
        "complete": len(matches) < COAFFINATIONS_CAP,
    }


def clockwork_candidates(graph: nx.Graph, iterate: int) -> dict:
    """Bounded induced-only search. It cannot certify the host's divergence."""
    result = find_induced_clockwork_subgraphs(
        graph, max_order=10, max_candidates=CLOCKWORK_CANDIDATES,
        max_results=1, divergent_only=True, iterate_index=iterate,
        recognition_max_order=10, recognition_max_candidates=256,
    )
    return {
        "status": result.status.name,
        "candidates_checked": result.candidates_checked,
        "candidates_total": result.candidates_total,
        "witnesses": [
            {
                "vertices": sorted(int(v) for v in witness.vertices),
                "induced_graph6": encode(witness.graph),
                "divergent": witness.divergent,
                "reason": witness.behavior_reason,
            }
            for witness in result.witnesses
        ],
        "conclusion": "induced_observation_only_not_host_divergence",
    }


def inspect(graph6: str, expected_iterates: list[dict] | None = None) -> dict:
    graph = nx.from_graph6_bytes(graph6.encode("ascii"))
    if graph.number_of_nodes() != 9 or not nx.is_connected(graph):
        raise ValueError("Expected a connected nine-vertex pared core")
    sequence = CliqueSequence(graph, bound=CLIQUE_BOUND)
    results = []
    for step in range(4):
        g = sequence[step]
        if g is None:
            raise ValueError(f"Stored core9 benchmark implies G_{step} exists")
        g6 = encode(g)
        b1, triangles, rank = betti1_mod2(g)
        degrees = sorted(d for _, d in g.degree())
        complement = nx.complement(g)
        row = {
            "index": step, "graph6": g6,
            "order": len(g), "edges": g.number_of_edges(),
            "degree_sequence": degrees,
            "complement_component_orders": sorted(
                len(part) for part in nx.connected_components(complement)
            ),
            "triangles": triangles,
            "triangle_boundary_rank_mod2": rank,
            "betti1_mod2": b1,
            "connected_triangular_double_cover_possible": b1 > 0,
            "nontriangle_edges": sum(
                not (set(g[u]) & set(g[v])) for u, v in g.edges()
            ),
            "wl3_hash": nx.weisfeiler_lehman_graph_hash(g, iterations=3),
            "maximal_cliques": clique_sample(g),
        }
        if step in (0, 1):
            row["divergent_induced_clockwork"] = clockwork_candidates(g, step)
        if step == 0:
            row["coaffination_radius2"] = coaffination_observation(g)
        results.append(row)
    if expected_iterates is not None:
        past = {row["index"]: row for row in expected_iterates}
        for row in results:
            old = past.get(row["index"])
            if not old or (
                old.get("pared_order") != row["order"]
                or old.get("pared_edges") != row["edges"]
            ):
                raise ValueError(
                    f"Reconstructed G_{row['index']} differs from frozen benchmark"
                )
        if past.get(4, {}).get("status") != "clique_bound_exceeded":
            raise ValueError("Historical benchmark did not stop at G_4")
    return {
        "input_graph6": graph6,
        "scope": "structural_diagnostics_only",
        "max_clique_sample": MAX_CLIQUES,
        "clique_sequence_bound": CLIQUE_BOUND,
        "iterates": results,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit(
            "Usage: core9_structure_worker.py GRAPH6 EXPECTED_ITERATES_JSON RESULT_FILE"
        )
    graph6, expected_file, output_file = sys.argv[1:]
    old = json.loads(Path(expected_file).read_text(encoding="utf-8"))
    record = inspect(graph6, old)
    Path(output_file).write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
