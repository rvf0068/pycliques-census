"""Reconstruct and independently verify two archived complete O12 retractions.

Requires pycliques-project at the pinned SHA used by the PR59 workflow.
No randomized search or cached target embedding is used to verify the maps.
"""
from __future__ import annotations
import base64
import hashlib
import json
from pathlib import Path

import networkx as nx

from research.order10_nonlocal_oct_stiff_v1.sweep import entries, iterate
from research.order10_pared_k3_33class_v1 import verify as older

CERTS = Path(__file__).with_name("o12_certificates.json")


def verify_cert(cert: dict) -> None:
    import pycliques
    index = cert["index"]
    sources = dict(entries())
    if sources.get(index) != cert["source_graph6"]:
        raise ValueError(f"Invalid immutable McKay source {index}")
    k3 = iterate(cert["source_graph6"], 3, 1500)
    if k3 is None or len(k3) != cert["k3_order"]:
        raise ValueError(f"Cannot reconstruct third iterate for {index}")
    raw = pycliques.clique_graph(k3, bound=1500)
    if raw is None or len(raw) != cert["k4_raw_order"]:
        raise ValueError(f"Cannot reconstruct fourth iterate for {index}")
    host = nx.convert_node_labels_to_integers(
        pycliques.completely_pared_graph(raw)
    )
    if (len(host), host.number_of_edges()) != (cert["k4_order"], cert["k4_edges"]):
        raise ValueError(f"Incorrect fourth pared iterate for {index}")
    graph6 = nx.to_graph6_bytes(host, header=False).decode("ascii").strip()
    if hashlib.sha256(graph6.encode("ascii")).hexdigest() != cert["host_sha256"]:
        raise ValueError(f"Full labeled fourth iterate does not match for {index}")
    pairs = [tuple(p) for p in cert["pairs"]]
    if len(pairs) != 12 or not pycliques.verify_induced_octahedron(host, pairs):
        raise ValueError(f"Invalid induced O12 for {index}")
    target = {v for pair in pairs for v in pair}
    images = list(base64.b64decode(cert["images_b64"], validate=True))
    if len(images) != len(host) or set(images) != target:
        raise ValueError(f"Retraction not total or target image invalid for {index}")
    if any(images[v] != v for v in target):
        raise ValueError(f"Retraction not identity on O12 for {index}")
    # Check every edge directly, independently of the search verifier.
    for u, v in host.edges():
        if images[u] != images[v] and not host.has_edge(images[u], images[v]):
            raise ValueError(f"Non-morphism edge {(u,v)} in certificate {index}")
    print(f"VERIFIED_O12 {index}: pared fourth iterate has "
          f"{len(host)} vertices, {host.number_of_edges()} edges")


def main() -> None:
    data = json.loads(CERTS.read_text())
    if data["schema"] != 1 or data["source"] != "indeterminate_order_10_v11.txt":
        raise ValueError("Wrong certificate schema")
    certs = data["proofs"]
    if sorted(r["index"] for r in certs) != [10223405, 10775850]:
        raise ValueError("Missing or duplicated O12 certificate")
    for cert in certs:
        verify_cert(cert)

    # This separate historical program reconstructs all 33 third pared iterates
    # with independent Bron-Kerbosch facets and checks exact isomorphism maps.
    c = older.certificate()
    if c["class_size"] != 33 or 10223405 not in older.MCKAY:
        raise ValueError("Incomplete 33-member third-iterate equivalence class")
    current = dict(entries())
    if any(current.get(i) != older.cohort()[i] for i in older.MCKAY):
        raise ValueError("A 33-family member is not in unclassified v11 stiff index")
    print("VERIFIED_THIRD_ITERATE_ISOMORPHISM_CLASS", len(older.MCKAY))


if __name__ == "__main__":
    main()
