"""Independent verification of 149 direct retractions from stiff ten-vertex cores.

Only full positive certificates are promoted. The verifier recomputes all
edge/nonedge checks from graph6; it does not trust the discovery procedure.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import networkx as nx

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical assertions")

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
V22 = ROOT / "indeterminate_order_10_v22.txt"
V23 = ROOT / "indeterminate_order_10_v23.txt"
CURRENT = ROOT / "indeterminate_order_10.txt"
CERT = HERE / "certificates.json"
V22_BLOB = "b066bf5b32d0c77448a0a23e10d33715aca19fc0"
REFERENCES = {
    249436: "HEhff^{",
    249574: "HEhfvx}",
    250814: "HEhuvzm",
    251759: "HEhvtzm",
    251902: "HEhvvzm",
    254369: "HEjfvx}",
}
BY_REFERENCE = Counter({
    249436: 39, 249574: 20, 250814: 26,
    251759: 26, 251902: 23, 254369: 15,
})


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def rows(path: Path) -> dict[int, str]:
    result: dict[int, str] = {}
    for raw in path.read_text(encoding="ascii").splitlines():
        if not raw or raw.startswith("#"):
            continue
        fields = raw.split()
        check(len(fields) == 6, f"Incorrect census row format: {raw}")
        index, order, graph6, rule, status, label = fields
        i = int(index)
        check(i not in result, f"Duplicate original index {i}")
        check((rule, status, label) == ("-", "-", "-"),
              f"Unexpected conditional source record: {i}")
        check(int(order) in (9, 10), f"Bad pared order {i}")
        check(len(nx.from_graph6_bytes(graph6.encode("ascii"))) == int(order),
              f"Incorrect graph6 order {i}")
        result[i] = raw
    check(list(result) == sorted(result), f"Unsorted original indices: {path}")
    return result


def check_witness(item: dict, prior_row: str) -> None:
    """Verify all ten-vertex edges, all nine-target pairs, and total projection."""
    idx, encoded = item["original_index"], item["original_graph6"]
    ref, ref_encoded = item["reference_index"], item["reference_graph6"]
    check(prior_row == f"{idx} 10 {encoded} - - -",
          f"Original McKay graph6 differs from frozen v22: {idx}")
    check(ref in REFERENCES and ref_encoded == REFERENCES[ref],
          f"Unproved or misidentified nine-vertex target: {idx}")
    source = nx.from_graph6_bytes(encoded.encode("ascii"))
    target = nx.from_graph6_bytes(ref_encoded.encode("ascii"))
    check(len(source) == 10 and len(target) == 9,
          f"Wrong graph orders for {idx}")
    check(nx.is_connected(source), f"Disconnected ten-vertex source {idx}")
    check(all(
        not ((set(source[v]) | {v}) <= (set(source[w]) | {w}))
        for v in source for w in source if v != w
    ), f"Supposed stiff ten-core has dominated vertex: {idx}")

    deleted, image = item["deleted_vertex"], item["image"]
    keep = item["target_vertices"]
    sigma = item["target_bijection"]
    check(isinstance(deleted, int) and deleted in source
          and isinstance(image, int) and image in source and image != deleted,
          f"Wrong deletion or projection image: {idx}")
    check(isinstance(keep, list) and keep == sorted(set(source) - {deleted}),
          f"Wrong induced target vertices: {idx}")
    check(isinstance(sigma, list) and len(sigma) == 9
          and sorted(sigma) == list(range(9)),
          f"Target-isomorphism bijection is not a permutation: {idx}")
    phi = dict(zip(keep, sigma))
    check(all(
        source.has_edge(a, b) == target.has_edge(phi[a], phi[b])
        for a in keep for b in keep
    ), f"Induced nine-vertex reference isomorphism fails: {idx}")
    check(nx.is_isomorphic(source.subgraph(keep), target),
          f"Independent GraphMatcher disagrees: {idx}")

    projection = {v: v for v in keep}
    projection[deleted] = image
    check(set(projection) == set(source)
          and all(projection[v] == v for v in keep),
          f"Source-to-subgraph projection is not total and split: {idx}")
    check(all(
        projection[u] == projection[v]
        or source.has_edge(projection[u], projection[v])
        for u, v in source.edges
    ), f"Graph retraction fails adjacency-or-equality: {idx}")


def verify_reference_proofs() -> None:
    """Independently replay already archived complete octahedral retractions."""
    from research.order9_three_p4_retractions_v1.verify import check_certificates
    from research.order9_two_p4_retractions_v1.verify import verify_positive
    from research.order9_251902_p4_o17_v1.verify import verify_positive as p17

    check_certificates(public=False)  # 249436, 249574, 250814
    verify_positive(251759, public=False)
    verify_positive(254369, public=False)
    p17(public=False)


def verify_archive(*, replay_sources: bool = True) -> None:
    archive = json.loads(CERT.read_text(encoding="utf-8"))
    check(archive["schema"] == 1 and archive["source_v22_git_blob"] == V22_BLOB,
          "Wrong certificate schema or immutable source blob")
    check(git_blob(V22.read_bytes()) == V22_BLOB,
          "Frozen v22 is not byte-identical to its original Git blob")
    check(CURRENT.read_bytes() == V23.read_bytes(),
          "Authoritative ten-vertex index differs from frozen v23")
    check((ROOT / "indeterminate_order_9.txt").read_bytes()
          == (ROOT / "indeterminate_order_9_v9.txt").read_bytes(),
          "The unchanged nine-v9 root was modified")
    old, new = rows(V22), rows(V23)
    check((len(old), len(new)) == (1208, 1059),
          "Wrong old/new indeterminate population")
    check((archive["previous_count"], archive["current_count"],
           archive["removed_count"]) == (1208, 1059, 149),
          "Incorrect census transition declaration")
    check(set(new) < set(old) and all(old[i] == row for i, row in new.items()),
          "Retained original index has been added or modified")
    check(Counter(int(row.split()[1]) for row in old.values())
          == Counter({9: 430, 10: 778}),
          "Unexpected frozen v22 pared-order partition")
    check(Counter(int(row.split()[1]) for row in new.values())
          == Counter({9: 430, 10: 629}),
          "Incorrect ten-v23 pared-order partition")
    check(archive["remaining_pared_order"] == {"9": 430, "10": 629},
          "Wrong archive class partition")
    check(archive["reference_proofs"] == {
        str(k): v for k, v in REFERENCES.items()
    }, "Wrong reference source identities")
    check({i for i in rows(ROOT / "indeterminate_order_9_v4.txt")
           if i not in rows(ROOT / "indeterminate_order_9_v9.txt")}
          >= set(REFERENCES),
          "A supposed divergent source remains indeterminate")
    check(archive["counts_by_reference"] ==
          {str(i): BY_REFERENCE[i] for i in sorted(BY_REFERENCE)},
          "Incorrect certified reference count")

    cases = archive["witnesses"]
    check(len(cases) == 149
          and [x["original_index"] for x in cases]
          == sorted(set(old) - set(new)),
          "Witness indices are missing, repeated or fail exact subtraction")
    distribution: Counter[int] = Counter()
    for item in cases:
        index = item["original_index"]
        check_witness(item, old[index])
        distribution[item["reference_index"]] += 1
    check(distribution == BY_REFERENCE,
          f"Incorrect retraction target distribution: {distribution}")
    if replay_sources:
        verify_reference_proofs()
    print("PASS: 149 independently checked direct retractions onto"
          " six previously proved K-divergent nine-vertex sources;"
          " immutable ten-v22=1208 -> ten-v23=1059"
          " (430 nine-core + 629 stiff ten-core), all records preserved.",
          flush=True)


if __name__ == "__main__":
    verify_archive()
