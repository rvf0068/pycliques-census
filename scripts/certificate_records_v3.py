"""Versioned, independently replayable positive certificates for future stages.

This module does not modify or reinterpret historical v1/v2 records. It
requires a pycliques revision offering the witness verification APIs added
after the historical census pin. Store graph6 encodings and vertex *indices*,
not repr() of Clique or other non-JSON node labels.

The replay verifier checks both the local witness and (optionally) that the
stored source is an iterated, completely pared clique graph of the original.
An unsupported rule is explicitly `not_serialized`, never a claimed proof.
"""
from __future__ import annotations

import re
from typing import Any

import networkx as nx


def graph6(graph: nx.Graph) -> str:
    """Encode the graph in its current node order without depending on labels."""
    numbered = nx.convert_node_labels_to_integers(graph)
    return nx.to_graph6_bytes(numbered, header=False).decode("ascii").strip()


def decode(data: str) -> nx.Graph:
    return nx.from_graph6_bytes(data.encode("ascii"))


def _require_witness_api():
    from pycliques import retractions

    if not all(
        hasattr(retractions, attr)
        for attr in (
            "SpecialOctahedronWitness",
            "verify_special_octahedron_witness",
            "verify_retraction_witness",
        )
    ):
        raise RuntimeError(
            "Certificate records v3 require the post-census pycliques witness APIs; "
            "do not upgrade the historical v2 stage dependency in place."
        )
    return retractions


def _proven_target_identifier(target: nx.Graph) -> str | None:
    """Recognize the explicit independently established divergent targets.

    A retraction map alone does not prove divergence unless its target is
    already known divergent. Unknown reference targets need a separate
    externally verifiable target certificate and are not marked proved here.
    """
    from pycliques.named import complement_of_cycle, suspension_of_cycle

    proven_targets = (
        ("octahedral_graph", nx.octahedral_graph()),
        ("suspension_C5", suspension_of_cycle(5)),
        ("suspension_C6", suspension_of_cycle(6)),
        ("suspension_C7", suspension_of_cycle(7)),
        ("complement_C8", complement_of_cycle(8)),
    )
    for identifier, known in proven_targets:
        if nx.is_isomorphic(target, known):
            return identifier
    return None


def _source_provenance(
    origin: nx.Graph, source: nx.Graph, index: int, bound: int
) -> dict[str, Any]:
    return {
        "schema": 3,
        "origin_graph6": graph6(origin),
        "source_graph6": graph6(source),
        "iterate_index": index,
        "clique_bound": bound,
    }


def serialize_result(
    original: nx.Graph, result: Any, *, bound: int = 120
) -> dict[str, Any]:
    """Record a positive witness, conditional status, or explicit absence.

    The original classification result and its reasoning are retained, but
    a `proof_status=verified_local` claim requires successful independent
    verification on the source graph. The graph-sequence link is tested by
    `verify_record(..., verify_iterate=True)` and never inferred.
    """
    retractions = _require_witness_api()
    cert = result.certificate
    record = {
        "verdict": result.verdict.name,
        "reason": result.reason,
        "certificate_rule": cert.rule if cert is not None else None,
        "certificate_target_status": (
            cert.target_status if cert is not None else None
        ),
        "proof_status": "not_serialized",
        "proof": None,
    }
    if (
        result.verdict.name not in {"DIVERGENT", "CONVERGENT"}
        or (cert is not None and cert.target_status == "conjectured_divergent")
    ):
        return record

    if (
        result.verdict.name == "DIVERGENT"
        and cert is not None
        and cert.rule == "special_octahedron"
        and cert.special_octahedron is not None
        and cert.source is not None
        and cert.iterate_index is not None
    ):
        source = cert.source
        witness = cert.special_octahedron
        if not retractions.verify_special_octahedron_witness(source, witness):
            raise ValueError("Stored special-octahedron witness is invalid")
        lookup = {v: i for i, v in enumerate(source)}
        proof = _source_provenance(original, source, cert.iterate_index, bound)
        proof.update(
            rule="special_octahedron",
            clique_indices=[lookup[v] for v in witness.clique],
            antipode_indices=[lookup[v] for v in witness.antipodes],
        )
    elif (
        result.verdict.name == "DIVERGENT"
        and cert is not None
        and cert.rule == "retracts"
        and cert.source is not None
        and cert.target is not None
        and cert.iterate_index is not None
        and isinstance(cert.map, tuple)
    ):
        source, target = cert.source, cert.target
        target_identifier = _proven_target_identifier(target)
        if cert.target_status != "proven_divergent" or target_identifier is None:
            return record  # Valid map to an unproved target is NOT a proof.
        if not retractions.verify_retraction_witness(source, target, cert.map):
            raise ValueError("Stored retraction witness is invalid")
        projection, inclusion = cert.map
        target_index = {v: i for i, v in enumerate(target)}
        source_index = {v: i for i, v in enumerate(source)}
        proof = _source_provenance(original, source, cert.iterate_index, bound)
        proof.update(
            rule="retracts",
            target_graph6=graph6(target),
            target_reference=target_identifier,
            projection=[target_index[projection[v]] for v in source],
            inclusion=[source_index[inclusion[v]] for v in target],
        )
    else:
        # The existing classifier supplies a Helly proof as an explanation
        # without a Certificate instance. Reconstruct that particular
        # iterate, test Helly, and retain the graph as a replayable witness.
        match = re.fullmatch(r"is eventually Helly \(index (\d+)\)", result.reason)
        if result.verdict.name != "CONVERGENT" or match is None:
            return record
        from pycliques.helly import is_clique_helly
        from pycliques.small import CliqueSequence
        from pycliques.dominated import completely_pared_graph

        index = int(match.group(1))
        seq = CliqueSequence(completely_pared_graph(original), bound=bound)
        source = seq[index]
        if source is None or not is_clique_helly(source):
            raise ValueError("The claimed Helly iterate cannot be independently checked")
        proof = _source_provenance(original, source, index, bound)
        proof["rule"] = "eventually_clique_helly"

    record["proof"] = proof
    if not verify_record(record, verify_iterate=False):
        raise ValueError("Serialized positive witness failed independent local replay")
    record["proof_status"] = "verified_local"
    return record


def verify_record(record: dict, *, verify_iterate: bool = True) -> bool:
    """Independently check a stored proof and optionally its iteration chain.

    On `verify_iterate=True`, the verifier recomputes the pared clique
    sequence from the stored original graph and checks graph isomorphism,
    not hash values or graph6 vertex order. Resource exhaustion is an
    exception/failure, never proof of absence.
    """
    try:
        retractions = _require_witness_api()
        proof = record["proof"]
        if not isinstance(proof, dict) or proof.get("schema") != 3:
            return False
        original = decode(proof["origin_graph6"])
        source = decode(proof["source_graph6"])
        index = proof["iterate_index"]
        bound = proof["clique_bound"]
        if not isinstance(index, int) or index < 0 or not isinstance(bound, int) or bound < 1:
            return False
        if record["verdict"] == "DIVERGENT" and proof["rule"] == "special_octahedron":
            witness = retractions.SpecialOctahedronWitness(
                clique=tuple(proof["clique_indices"]),
                antipodes=tuple(proof["antipode_indices"]),
            )
            verified = retractions.verify_special_octahedron_witness(source, witness)
        elif record["verdict"] == "DIVERGENT" and proof["rule"] == "retracts":
            target = decode(proof["target_graph6"])
            if _proven_target_identifier(target) != proof.get("target_reference"):
                return False
            projection = dict(enumerate(proof["projection"]))
            inclusion = dict(enumerate(proof["inclusion"]))
            verified = retractions.verify_retraction_witness(
                source, target, (projection, inclusion)
            )
        elif record["verdict"] == "CONVERGENT" and proof["rule"] == "eventually_clique_helly":
            from pycliques.helly import is_clique_helly

            verified = is_clique_helly(source)
        else:
            return False
        if not verified:
            return False
        if verify_iterate:
            from pycliques.dominated import completely_pared_graph
            from pycliques.small import CliqueSequence

            seq = CliqueSequence(completely_pared_graph(original), bound=bound)
            iterate = seq[index]
            if iterate is None or not nx.is_isomorphic(iterate, source):
                return False
        return True
    except (KeyError, TypeError, ValueError, IndexError, nx.NetworkXException):
        return False
