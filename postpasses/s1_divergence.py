"""Certified S^1-case divergence search for the order-10 clique census.

Search K^2(G), K^3(G) for a divergent clockwork reduction; if neither yields a
proof, search triangular double covers for an admissible clockwork-pair map.
All positives are independently replayed before returning DIVERGENT.
Bounded negative results do *not* imply convergence or nondivergence.

A positive witness is JSON-compatible so its proof can be replayed later from
the original graph6 independently of the original search.
"""
from __future__ import annotations

import json
from collections.abc import Mapping

import networkx as nx

from pycliques.cliques import Clique, clique_graph
from pycliques.clockwork import (
    ClockworkDivergenceStatus,
    clockwork_divergence_result,
    verify_clockwork_structure,
)
from pycliques.clockwork_pairs import clockwork_coaffine_pair
from pycliques.clockwork_search import CertificateVerificationStatus
from pycliques.small import Certificate
from pycombtop.covering_divergence import (
    TriangularCoverDivergenceCertificate,
    verify_triangular_cover_divergence_certificate,
)
from pycombtop.covering_divergence_search import (
    CoveringSearchStatus,
    search_covering_divergence,
)

ITERATE_CLIQUE_BOUND = 500
ITERATE_EDGE_BOUND = 20000
CLOCKWORK_FALLBACK_ORDER = 18
CLOCKWORK_FALLBACK_CANDIDATES = 5000
COVER_SEARCH_LIMITS = {
    "max_cover_classes": 4,
    "max_cover_vertices": 40,
    "max_cover_edges": 120,
    "max_clique_vertices": 200,
    "max_clique_edges": 5000,
    "max_source_order": 24,
    "max_m": 3,
    "max_n": 0,  # Search the theorem family used for IEjdnpy^O first.
    "max_morphism_states": 100000,
    "max_morphism_assignments": 1000000,
}


def _graph6(graph: nx.Graph) -> str:
    """Encode an iteration with integer labels in its stored vertex order."""
    numbered = nx.convert_node_labels_to_integers(graph)
    return nx.to_graph6_bytes(numbered, header=False).decode("ascii").strip()


def _iterate_witness(graph: nx.Graph, depth: int, result) -> dict:
    structure = result.structure
    if structure is None or not structure.good_segments:
        raise ValueError("Cannot certify clockwork divergence without good segments")
    order = {vertex: index for index, vertex in enumerate(structure.G)}
    witness = {
        "kind": "divergent_clockwork_iterate",
        "iterate": depth,
        "iterate_graph6": _graph6(graph),
        "reduced_graph6": _graph6(structure.G),
        "crown_segments": [
            sorted(order[vertex] for vertex in segment)
            for segment in structure.B_segments
        ],
        "core_segments": [
            sorted(order[vertex] for vertex in segment)
            for segment in structure.C_segments
        ],
        "core_orders": [
            [order[vertex] for vertex in segment]
            for segment in structure.core_orders
        ],
        "good_segments": list(structure.good_segments),
    }
    if not verify_iterate_witness_from_graph(graph, witness):
        raise AssertionError("Divergent clockwork witness failed independent verification")
    return witness


def verify_iterate_witness_from_graph(iterate_graph: nx.Graph, witness: Mapping) -> bool:
    """Check a saved decomposition on the computed iterate, including its paring."""
    if witness.get("kind") != "divergent_clockwork_iterate":
        return False
    if witness.get("iterate_graph6") != _graph6(iterate_graph):
        return False
    from pycliques.clockwork import remove_dominated_vertices

    reduced = remove_dominated_vertices(iterate_graph)
    if _graph6(reduced) != witness.get("reduced_graph6"):
        return False
    reduced = nx.convert_node_labels_to_integers(reduced)
    crown = [set(seg) for seg in witness["crown_segments"]]
    core = [set(seg) for seg in witness["core_segments"]]
    orders = witness["core_orders"]
    valid, structure = verify_clockwork_structure(reduced, crown, core, orders)
    if not valid or not getattr(structure, "good_segments", None):
        return False
    return list(structure.good_segments) == witness["good_segments"]


def _cover_witness(certificate: TriangularCoverDivergenceCertificate) -> dict:
    """Store enough concrete data to replay the full covering theorem verifier."""
    theorem = certificate.theorem_certificate
    if not isinstance(theorem.map, Mapping):
        raise AssertionError("Expected explicit Theorem 2.6 morphism")
    return {
        "kind": "triangular_cover_pair",
        "voltages": [
            [int(first), int(second), int(value)]
            for first, second, value in certificate.voltage_cocycle
        ],
        "m": theorem.m,
        "n": theorem.n,
        "deck_radius": certificate.deck_radius,
        "clique_bound": certificate.clique_bound,
        "clique_max_edges": certificate.clique_max_edges,
        # Map source (integer) vertices to cliques of lifted (vertex,sheet)
        # pairs. These are the exact equivariant map values, not a yes/no flag.
        "morphism": [
            [int(vertex), [[int(base), int(sheet)] for base, sheet in sorted(clique)]]
            for vertex, clique in sorted(theorem.map.items())
        ],
    }


def verify_cover_witness(graph: nx.Graph, witness: Mapping) -> bool:
    """Reconstruct and check a full triangular covering divergence certificate."""
    if witness.get("kind") != "triangular_cover_pair":
        return False
    try:
        cocycle = tuple(
            (int(first), int(second), int(value))
            for first, second, value in witness["voltages"]
        )
        voltages = {frozenset((u, v)): change for u, v, change in cocycle}
        if len(voltages) != len(cocycle):
            return False
        if set(voltages) != {frozenset(edge) for edge in graph.edges()}:
            return False
        if not all(value in (0, 1) for value in voltages.values()):
            return False
        cover = nx.Graph()
        cover.add_nodes_from((vertex, sheet) for vertex in graph for sheet in (0, 1))
        for first, second in graph.edges():
            for sheet in (0, 1):
                cover.add_edge(
                    (first, sheet),
                    (second, sheet ^ voltages[frozenset((first, second))]),
                )
        deck = {(vertex, sheet): (vertex, 1 - sheet) for vertex, sheet in cover}
        target = clique_graph(
            cover,
            bound=witness["clique_bound"],
            max_edges=witness["clique_max_edges"],
        )
        if target is None:
            return False
        target_deck = {
            clique: Clique(deck[vertex] for vertex in clique)
            for clique in target
        }
        source = clockwork_coaffine_pair(int(witness["m"]), int(witness["n"]))
        morphism = {
            int(vertex): Clique((int(u), int(sheet)) for u, sheet in vertices)
            for vertex, vertices in witness["morphism"]
        }
        theorem = Certificate(
            rule="theorem_2_6_clockwork_pair_map",
            target=target,
            target_status="proven_divergent",
            map=morphism,
            m=int(witness["m"]),
            n=int(witness["n"]),
            radius=int(witness["deck_radius"]),
            source=source.graph,
            source_coaffination=source.coaffination,
            target_coaffination=target_deck,
            theorem_base_graph=target,
        )
        certificate = TriangularCoverDivergenceCertificate(
            base_graph=graph,
            cover_graph=cover,
            projection={vertex: vertex[0] for vertex in cover},
            deck_transformation=deck,
            theorem_certificate=theorem,
            voltage_cocycle=cocycle,
            clique_bound=witness["clique_bound"],
            clique_max_edges=witness["clique_max_edges"],
            deck_radius=int(witness["deck_radius"]),
        )
        return (
            verify_triangular_cover_divergence_certificate(certificate).status
            is CertificateVerificationStatus.VERIFIED
        )
    except (KeyError, ValueError, TypeError, IndexError):
        return False


def verify_witness(graph: nx.Graph, witness: Mapping) -> bool:
    """Replay a saved positive proof from G, without trusting its verdict."""
    kind = witness.get("kind")
    if kind == "triangular_cover_pair":
        return verify_cover_witness(graph, witness)
    if kind != "divergent_clockwork_iterate":
        return False
    depth = witness.get("iterate")
    if depth not in (2, 3):
        return False
    current = graph
    for _ in range(depth):
        current = clique_graph(
            current, bound=ITERATE_CLIQUE_BOUND, max_edges=ITERATE_EDGE_BOUND
        )
        if current is None:
            return False
    return verify_iterate_witness_from_graph(current, witness)


def scan(graph: nx.Graph) -> dict:
    """Try two direct iterates, followed by a bounded verified cover search."""
    current = graph
    iterations = []
    for level in range(1, 4):
        next_graph = clique_graph(
            current, bound=ITERATE_CLIQUE_BOUND, max_edges=ITERATE_EDGE_BOUND
        )
        if next_graph is None:
            iterations.append({
                "iterate": level, "status": "LIMIT_REACHED",
                "reason": "Clique graph construction exceeded the configured vertex/edge budget",
            })
            break
        current = next_graph
        if level == 1:
            continue
        verdict = clockwork_divergence_result(
            current,
            fallback_max_order=CLOCKWORK_FALLBACK_ORDER,
            fallback_max_candidates=CLOCKWORK_FALLBACK_CANDIDATES,
        )
        iterations.append({
            "iterate": level,
            "order": current.number_of_nodes(),
            "size": current.number_of_edges(),
            "status": verdict.status.name,
            "reason": verdict.reason,
        })
        if verdict.status is ClockworkDivergenceStatus.DIVERGENT:
            witness = _iterate_witness(current, level, verdict)
            if not verify_witness(graph, witness):
                raise AssertionError("Clockwork iterate proof failed replay")
            return {
                "status": "DIVERGENT",
                "rule": "clockwork_iterate",
                "reason": f"K^{level}(G) has a verified divergent clockwork reduction",
                "iterations": iterations,
                "witness": witness,
            }

    cover = search_covering_divergence(graph, **COVER_SEARCH_LIMITS)
    search = {
        "status": cover.status.name,
        "cover_classes_total": cover.cover_classes_total,
        "cover_classes_checked": cover.cover_classes_checked,
        "cover_candidates_checked": cover.cover_candidates_checked,
        "morphism_states": cover.morphism_states,
        "morphism_assignments": cover.morphism_assignments,
        "cover_classes_complete": cover.cover_classes_complete,
        "morphisms_complete": cover.morphisms_complete,
        "source_parameters": [list(pair) for pair in cover.configured_source_parameters],
        "limits": dict(cover.limits),
        "reasons": list(cover.reasons),
    }
    if cover.status is CoveringSearchStatus.FOUND:
        if cover.certificate is None:
            raise AssertionError("Cover search returned FOUND without a certificate")
        witness = _cover_witness(cover.certificate)
        if not verify_witness(graph, witness):
            raise AssertionError("Triangular-cover proof failed independent replay")
        return {
            "status": "DIVERGENT",
            "rule": "triangular_cover_pair",
            "reason": "Verified triangular double cover and Theorem 2.6 clockwork-pair morphism",
            "iterations": iterations,
            "cover_search": search,
            "witness": witness,
        }
    return {
        "status": "INDETERMINATE",
        "rule": "-",
        "reason": (
            "No divergence certificate in the configured iterate/cover searches; "
            "this does not imply convergence or absence of other certificates"
        ),
        "iterations": iterations,
        "cover_search": search,
        "witness": None,
    }


def verify_json_record(record: Mapping) -> bool:
    """Recheck a stored positive record against its original graph6."""
    if record.get("status") != "DIVERGENT" or not isinstance(record.get("witness"), dict):
        return False
    graph = nx.from_graph6_bytes(record["graph6"].encode("ascii"))
    return verify_witness(graph, record["witness"])
