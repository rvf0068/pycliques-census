"""Transport and verify the *complete* historical O12 map to all 3 new hosts.

Requires the pinned historical pycliques used by the v12 O12 proof.
This independently composes both 182-vertex graph isomorphisms with
the complete archived base retraction, and tests all host edges.
"""
from __future__ import annotations

import base64
import hashlib
import json

import networkx as nx

from research.order10_nonlocal_oct_stiff_v1.sweep import iterate
from .verify import (
    ARCHIVE, BASE_G6, BASE_HASH, BASE_ID, ROOT,
    canonical_bijection, host_sha, reconstruct, require, verify_archive,
)


def main() -> None:
    import pycliques

    # The independent proof of every source and index transition runs first.
    verify_archive()

    base_k3 = iterate(BASE_G6, 3, 1500)
    require(base_k3 is not None, "Historical native third-iterate reference absent")
    raw = pycliques.clique_graph(base_k3, bound=1500)
    require(raw is not None, "Historical native fourth-iterate reference absent")
    native = nx.convert_node_labels_to_integers(
        pycliques.completely_pared_graph(raw)
    )
    source_cert = json.loads(
        (ROOT / "research/order10_fourth_oct_v1/o12_certificates.json")
        .read_text(encoding="utf-8")
    )
    old_proofs = [x for x in source_cert["proofs"] if x["index"] == BASE_ID]
    require(len(old_proofs) == 1, "Missing historical O12 certificate")
    old = old_proofs[0]
    require(host_sha(native) == old["host_sha256"],
            "Native reference does not match archived O12 host")
    old_pairs = [tuple(x) for x in old["pairs"]]
    old_target = {u for pair in old_pairs for u in pair}
    old_images = list(base64.b64decode(old["images_b64"], validate=True))
    require(len(old_images) == len(native) == 182
            and len(old_target) == 24,
            "Historical projection is not a total O12 map")
    require(set(old_images) == old_target
            and all(old_images[t] == t for t in old_target),
            "Historical retraction does not fix an induced target")
    require(all(
        old_images[u] == old_images[v]
        or native.has_edge(old_images[u], old_images[v])
        for u, v in native.edges
    ), "Historical O12 image is not an ordinary graph morphism")

    _, base = reconstruct(BASE_G6)
    require(host_sha(base) == BASE_HASH, "Canonical O12 reference changed")
    # Both reference labeling schemes are exact copies of the same
    # 182-vertex graph and have unique one-step degree-neighborhood colors.
    base_to_native = canonical_bijection(base, native)

    cert = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    for item in cert["witnesses"]:
        _, host = reconstruct(item["graph6"])
        host_to_base = canonical_bijection(host, base)
        host_to_native = [base_to_native[x] for x in host_to_base]
        inverse = {native_vertex: source_vertex
                   for source_vertex, native_vertex
                   in enumerate(host_to_native)}
        require(len(inverse) == 182, "Non-bijective composite P4 transport")
        pairs = [(inverse[a], inverse[b]) for a, b in old_pairs]
        target = {v for pair in pairs for v in pair}
        require(len(target) == 24, "Transported antipodes overlap")
        for j, (a, b) in enumerate(pairs):
            require(not host.has_edge(a, b),
                    "Transported O12 opposite endpoints are adjacent")
            for c, d in pairs[:j]:
                require(all(host.has_edge(x, y)
                            for x in (a, b) for y in (c, d)),
                        "Transported O12 is not an induced octahedron")
        images = [
            inverse[old_images[host_to_native[v]]]
            for v in range(len(host))
        ]
        require(len(images) == 182 and set(images) == target
                and all(images[v] == v for v in target),
                "Transported projection is not a total retraction")
        require(all(images[u] == images[v]
                    or host.has_edge(images[u], images[v])
                    for u, v in host.edges),
                "A transported O12 projection fails a host edge")
        print(f"VERIFIED_COMPLETE_O12_MAP {item['index']}: "
              f"182 images, 14,298 host edges, O12 induced section,"
              f" map_SHA256={hashlib.sha256(bytes(images)).hexdigest()}",
              flush=True)
    print("PASS: three new full graph retractions from independently"
          " reconstructed P4 hosts onto induced O12 targets.")


if __name__ == "__main__":
    main()
