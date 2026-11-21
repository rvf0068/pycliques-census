"""Replay five exact fourth-pared-iterate isomorphisms and lift the O12 map.

Positive-only proof; no Weisfeiler-Lehman signatures or negative search
outcomes are used. All graph mappings are checked on every vertex pair and
every edge. Reconstructs each complete clique/paring sequence independently.
"""
from __future__ import annotations

import base64
import hashlib
import json
import sys
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from research.order10_fourth_oct_v1.verify_o6 import reproduce
from research.order10_nonlocal_oct_stiff_v1.sweep import entries, iterate

DIRECTORY = Path(__file__).parent
CERTS = DIRECTORY / "extra5_isomorphisms.json"
O12 = DIRECTORY / "o12_certificates.json"


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def host_hash(graph: nx.Graph) -> str:
    return hashlib.sha256(nx.to_graph6_bytes(graph, header=False).strip()).hexdigest()


def check_bijection(g: nx.Graph, h: nx.Graph, images: list[int]) -> None:
    need(len(g) == len(h) == len(images), "Incomplete graph isomorphism")
    need(sorted(images) == list(range(len(g))), "Not a bijection")
    # Verify both adjacency and non-adjacency, not just a WL fingerprint.
    for a in range(len(g)):
        for b in range(a + 1, len(g)):
            need(g.has_edge(a, b) == h.has_edge(images[a], images[b]),
                 "Claimed graph-isomorphism map is invalid")


def main() -> None:
    import pycliques

    data = json.loads(CERTS.read_text(encoding="utf-8"))
    need(data["schema"] == 1 and data["base"] == 10223405, "Wrong certificate base")
    proofs = data["proofs"]
    expected_indices = [11251181, 11425747, 11509851, 11556261, 11599112]
    need([x["index"] for x in proofs] == expected_indices,
         "Unexpected additional-family indices")
    sources = dict(entries())
    base_g6 = sources[10223405]

    # Independently reconstruct a second deterministic labeled realization
    # of the positive fourth core, checking every fold and maximal clique
    # (both NetworkX and separate bitset Bron-Kerbosch).
    base_k3, base_raw, base = reproduce(base_g6)
    need((len(base), base.number_of_edges()) == (182, 14298),
         "Wrong independent base core")
    need(host_hash(base) == data["base_local_sha256"], "Wrong base local graph6")

    # Reconstruct the *other* published labeled host with pycliques;
    # this is the host carrying the original archived complete O12 map.
    base_k3_native = iterate(base_g6, 3, 1500)
    need(base_k3_native is not None, "Native base K3 over bound")
    base_k4_native = pycliques.clique_graph(base_k3_native, bound=1500)
    need(base_k4_native is not None, "Native base K4 over bound")
    native = nx.convert_node_labels_to_integers(
        pycliques.completely_pared_graph(base_k4_native)
    )
    o12_all = json.loads(O12.read_text(encoding="utf-8"))["proofs"]
    o12_cert = next(p for p in o12_all if p["index"] == 10223405)
    native_digest = hashlib.sha256(
        nx.to_graph6_bytes(native, header=False).strip()
    ).hexdigest()
    need(native_digest == o12_cert["host_sha256"], "Native labeled O12 host differs")
    need((len(native), native.number_of_edges()) == (182, 14298),
         "Native base size differs")

    # Construct and explicitly verify exact bridge from independent base
    # labeling to original native labeled certificate host.
    match = nx.algorithms.isomorphism.GraphMatcher(
        nx.complement(base), nx.complement(native)
    )
    need(match.is_isomorphic(), "Local positive base is not native positive base")
    base_to_native = [int(match.mapping[v]) for v in range(len(base))]
    check_bijection(base, native, base_to_native)

    native_images = list(base64.b64decode(o12_cert["images_b64"], validate=True))
    native_pairs = [tuple(p) for p in o12_cert["pairs"]]
    native_target = {v for pair in native_pairs for v in pair}
    need(len(native_target) == 24 and len(native_images) == len(native),
         "Invalid archived native O12 map")
    need(all(native_images[v] == v for v in native_target),
         "Native map does not fix its target")

    for cert in proofs:
        index = cert["index"]
        need(sources.get(index) == cert["source_graph6"],
             f"Graph6 identity not pinned for {index}")
        k3, raw, host = reproduce(cert["source_graph6"])
        for name, graph in (("K3", k3), ("K4_unpared", raw), ("K4_pared", host)):
            need([len(graph), graph.number_of_edges()] == cert[name],
                 f"Unexpected {name} graph for {index}")
        need(host_hash(host) == cert["host_sha256"], f"Wrong host graph6 {index}")
        extra_to_base = list(base64.b64decode(cert["to_base_b64"], validate=True))
        check_bijection(host, base, extra_to_base)
        # Compose the two independently checked isomorphisms.
        extra_to_native = [base_to_native[v] for v in extra_to_base]
        check_bijection(host, native, extra_to_native)
        inverse_native = {v: u for u, v in enumerate(extra_to_native)}
        need(len(inverse_native) == len(host), "Non-bijective composed transport")
        transported_pairs = [
            (inverse_native[a], inverse_native[b]) for a, b in native_pairs
        ]
        transported_target = {v for pair in transported_pairs for v in pair}
        need(len(transported_target) == 24, "Transported O12 endpoints overlap")
        for i, (a, b) in enumerate(transported_pairs):
            need(not host.has_edge(a, b), "Transported antipodes are adjacent")
            for c, d in transported_pairs[:i]:
                need(all(host.has_edge(u, v) for u in (a, b) for v in (c, d)),
                     "Transported target is not induced O12")

        # Explicitly exhibit and check the complete O12 projection on the
        # new graph, rather than merely appealing to a transitive claim.
        images = [
            inverse_native[native_images[extra_to_native[v]]]
            for v in range(len(host))
        ]
        need(set(images) == transported_target, "Wrong transported image set")
        need(all(images[v] == v for v in transported_target),
             "Transported retraction does not fix target")
        need(all(images[u] == images[v] or host.has_edge(images[u], images[v])
                 for u, v in host.edges()),
             "Transported O12 map fails an original edge")
        print(f"VERIFIED_EXTRA_O12 {index}: {len(host)} host vertices, "
              f"{host.number_of_edges()} source edges and complete projection")

    print("VERIFIED_FIVE_ADDITIONAL_FOURTH_ISOMORPHISMS", len(proofs))


if __name__ == "__main__":
    main()
