"""Proof-only native pycliques pilot on the ten oversized third iterates.

Uses the exact 521-case P3 host builder already merged into this census
and the public pycliques API from a separately pinned monorepo checkout.
Does not build P4, modify the census, infer divergence from a resource
limit, or import any locally devised graph-specific search algorithm.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("Cannot optimize away proof-critical assertions")

import networkx as nx

from research.order10_full_nine_reference_v1 import index as sources
from research.order10_p4_203_ears_v1.verify import TEN_P3_OVERCAP, require

PYCLIQUES_SHA = "f8eb9b9f2c71d79f9394571df98155f9de568785"
MAX_STATES = 100_000
TIME_LIMIT_SECONDS = 25
SHARDS = 5


def degree_obstruction(graph: nx.Graph) -> dict:
    """A degree-preserving automorphism cannot map v to an H-neighbor."""
    H = nx.complement(graph)
    degrees = dict(H.degree())
    for v in sorted(H):
        neighbors = sorted(H[v])
        if all(degrees[w] != degrees[v] for w in neighbors):
            require(neighbors and
                    all(not graph.has_edge(v, w) and w != v
                        for w in neighbors),
                    "Complement adjacency is not authentic")
            return {
                "vertex": v,
                "complement_degree": degrees[v],
                "neighbor_complement_degrees":
                    sorted({degrees[w] for w in neighbors}),
            }
    raise AssertionError("No degree obstruction to coaffine automorphisms")


def source_catalog() -> dict[int, dict]:
    """Reconstruct every original third iterate from the frozen P3 proof."""
    hosts = sources.hosts()
    require(hosts["schema"] == 1 and len(hosts["records"]) == 521,
            "Exact historical 521-class P3 catalog changed")
    entries = {x["index"]: x for x in hosts["records"]}
    require(len(entries) == 521 and
            len(TEN_P3_OVERCAP) == 10 and
            all(i in entries for i in TEN_P3_OVERCAP),
            "Ten eligible third-stage graph identities changed")
    for i in TEN_P3_OVERCAP:
        x = entries[i]
        g = nx.from_graph6_bytes(x["p3_graph6"].encode("ascii"))
        require(list(x["p3"]) == [len(g), g.number_of_edges()],
                "Unauthenticated third-iterate dimensions")
    return entries


def independent_coaffine_check(graph: nx.Graph, f: dict) -> None:
    """Check every original vertex, edge, and image constraint."""
    require(set(f) == set(graph) and set(f.values()) <= set(graph),
            "A coaffine image has malformed domain or labels")
    for v in graph:
        require(v != f[v] and not graph.has_edge(v, f[v]),
                "Claimed coaffine morphism maps a vertex into its closed N")
    for u, v in graph.edges():
        require(f[u] == f[v] or graph.has_edge(f[u], f[v]),
                "Claimed coaffine map does not preserve a source edge")


def independent_octahedral_retraction_check(
    graph: nx.Graph, pairs: tuple, ret: dict,
) -> None:
    """Check ordinary retraction onto the exact induced O_d."""
    require(len(pairs) >= 3
            and all(len(p) == 2 and p[0] != p[1] for p in pairs),
            "Malformed octahedral antipode pairs")
    flat = [v for pair in pairs for v in pair]
    require(len(flat) == len(set(flat)) and set(flat) <= set(graph),
            "Non-induced or repeated octahedron vertices")
    require(set(ret) == set(graph) and set(ret.values()) <= set(flat),
            "Retraction map not total or image outside target")
    for p in pairs:
        require(not graph.has_edge(*p),
                "Antipodal pair is an edge of the source")
    for i, p in enumerate(pairs):
        for q in pairs[i+1:]:
            require(all(graph.has_edge(u, v) for u in p for v in q),
                    "Induced alleged O_d lacks a required cross-edge")
    require(all(ret[u] == u for u in flat),
            "Ordinary retraction does not fix every target vertex")
    for u, v in graph.edges():
        require(ret[u] == ret[v] or graph.has_edge(ret[u], ret[v]),
                "Ordinary retraction sends a source edge to a target nonedge")


def probe_one(host: dict, *, state_cap: int, seconds: float) -> dict:
    # Directly use the general algorithms already implemented in
    # pycliques; no alternative CSP or octahedral search is duplicated.
    from pycliques import (
        find_coaffine_endomorphism,
        find_octahedral_retraction_coaffine,
        verify_coaffine_endomorphism,
    )

    graph = nx.from_graph6_bytes(host["p3_graph6"].encode("ascii"))
    require([len(graph), graph.number_of_edges()] == list(host["p3"]),
            "Reconstructed P3 does not match authenticated dimensions")
    degree = degree_obstruction(graph)
    result = {
        "index": host["index"],
        "original_graph6": host["graph6"],
        "p3_graph6_sha256": __import__("hashlib").sha256(
            host["p3_graph6"].encode("ascii")
        ).hexdigest(),
        "p3": list(host["p3"]),
        "complement_components": nx.number_connected_components(
            nx.complement(graph)
        ),
        "no_coaffine_automorphism": True,
        "degree_obstruction": degree,
    }
    probe = find_coaffine_endomorphism(
        graph, backend="native", value_order="fiber",
        max_states=state_cap, time_limit=seconds,
    )
    require(probe.status.name in {"FOUND", "EXHAUSTED", "LIMIT_REACHED"},
            "Unrecognized coaffine search result")
    result["coaffine_weak_endomorphism"] = {
        "status": probe.status.name,
        "states_explored": probe.states_explored,
        "assignments_tried": probe.assignments_tried,
        "arc_revisions": probe.arc_revisions,
    }
    if probe.status.name == "FOUND":
        f = probe.endomorphism
        require(f is not None and verify_coaffine_endomorphism(graph, f),
                "Native search returned a false coaffine map")
        independent_coaffine_check(graph, f)
        result["coaffine_weak_endomorphism"]["map"] = [
            f[i] for i in range(len(graph))
        ]
    else:
        require(probe.endomorphism is None,
                "Inconclusive/negative result has an unexpected map")

    # An exact EXHAUSTED result already excludes every O_d retraction
    # via the general composition i*tau*r; don't duplicate the CSP.
    if probe.status.name == "EXHAUSTED":
        result["octahedral_retraction"] = {
            "status": "EXCLUDED_BY_EXHAUSTIVE_COAFFINE_SEARCH",
            "states_explored": 0,
        }
    else:
        octa = find_octahedral_retraction_coaffine(
            graph, backend="native", value_order="fiber",
            min_dimension=3, max_states=state_cap, time_limit=seconds,
        )
        require(octa.status.name in {
            "FOUND", "EXHAUSTED", "LIMIT_REACHED"
        }, "Unrecognized octahedral search result")
        o = {
            "status": octa.status.name,
            "states_explored": octa.states_explored,
            "assignments_tried": octa.assignments_tried,
            "arc_revisions": octa.arc_revisions,
        }
        if octa.status.name == "FOUND":
            require(octa.retraction is not None and
                    octa.antipodal_pairs is not None,
                    "Native FOUND octahedral retraction is missing")
            independent_octahedral_retraction_check(
                graph, octa.antipodal_pairs, octa.retraction,
            )
            o["dimension"] = octa.dimension
            o["antipodal_pairs"] = octa.antipodal_pairs
            o["retraction_map"] = [
                octa.retraction[i] for i in range(len(graph))
            ]
            o["implication"] = (
                "Original ten-vertex graph is K-divergent; "
                "requires a separate certified promotion"
            )
        result["octahedral_retraction"] = o
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard", type=int, required=True)
    parser.add_argument("--shards", type=int, default=SHARDS)
    parser.add_argument("--max-states", type=int, default=MAX_STATES)
    parser.add_argument("--time-limit", type=float, default=TIME_LIMIT_SECONDS)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    require(options.shards == SHARDS and 0 <= options.shard < SHARDS
            and options.max_states >= 1 and options.time_limit > 0,
            "Malformed bounded native search options")
    require(os.environ.get("PYCLIQUES_PINNED_SHA") == PYCLIQUES_SHA,
            "Exact monorepo source checkout SHA not verified")
    entries = source_catalog()
    which = sorted(TEN_P3_OVERCAP)[options.shard::SHARDS]
    reports = []
    for index in which:
        report = probe_one(entries[index], state_cap=options.max_states,
                           seconds=options.time_limit)
        reports.append(report)
        print(
            f"McKay={index} n={report['p3'][0]} "
            f"coaffine={report['coaffine_weak_endomorphism']['status']} "
            f"oct={report['octahedral_retraction']['status']}",
            flush=True,
        )
    data = {
        "schema": 1,
        "kind": "bounded_native_pycliques_coaffine_on_ten_oversized_P3",
        "monorepo_commit": PYCLIQUES_SHA,
        "full_current_p3_classes": 521,
        "oversized_p3_count": 10,
        "shard": options.shard,
        "shards": SHARDS,
        "max_states": options.max_states,
        "time_limit_seconds_per_algorithm": options.time_limit,
        "no_census_promotion": True,
        "records": reports,
    }
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(json.dumps(data, sort_keys=True, indent=2)
                              + "\n", encoding="utf-8")
    print("PASS: authenticated native pycliques P3 pilot", flush=True)


if __name__ == "__main__":
    main()
