"""Independent 83-graph P2 isomorphism proof and immutable ten-v21 census audit.

No pycliques dependency or saved graph iterates are used. Original graph6
strings are decoded independently. Each maximal-clique stage is independently
checked against a second Bron--Kerbosch enumerator, dominated-vertex folds
are checked directly, and every saved P2 bijection is verified on ALL pairs.
"""

from __future__ import annotations

from collections import Counter
from itertools import combinations
import hashlib
import json
from pathlib import Path
import sys

import networkx as nx

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical assertions")

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
V20 = ROOT / "indeterminate_order_10_v20.txt"
V21 = ROOT / "indeterminate_order_10_v21.txt"
CURRENT = ROOT / "indeterminate_order_10.txt"
NINE_CURRENT = ROOT / "indeterminate_order_9.txt"
NINE_V9 = ROOT / "indeterminate_order_9_v9.txt"
CERT = HERE / "certificates.json"
FROZEN_V20 = "89f8f18bd236e6d7fa1e7ca928aa5418af061de4"
PROVED_COUNTS = {249436: 11, 249574: 9, 250814: 18,
                 251759: 20, 251902: 14, 253650: 4, 254369: 7}

# Immutable identities, independent of the new certificate manifest.
# The historically merged positive verifiers additionally authenticate
# the P4 host, antipodal target, and every vertex of its full projection.
PROVED_SOURCES = {
    249436: ("HEhff^{", "research/order9_three_p4_retractions_v1/REPORT.md"),
    249574: ("HEhfvx}", "research/order9_three_p4_retractions_v1/REPORT.md"),
    250814: ("HEhuvzm", "research/order9_three_p4_retractions_v1/REPORT.md"),
    251759: ("HEhvtzm", "research/order9_251759_p4_o15_v1/certificate.json"),
    251902: ("HEhvvzm", "research/order9_251902_p4_o17_v1/certificate.json"),
    253650: ("HEjer~{", "research/order9_253650_o12_v1/certificate.json"),
    254369: ("HEjfvx}", "research/order9_254369_p4_o13_v1/certificate.json"),
}


def verify_archived_source_retractions() -> None:
    """Independently replay seven historically certified P4 -> O_d proofs.

    The preexisting verifiers reconstruct P4 from the original graph6,
    authenticate the host, and check every edge under a total retraction
    fixing an induced octahedral target. They do NOT merely grep reports.
    Unrelated historical ten-vertex lifts are omitted from this replay.
    """
    from research.order9_three_p4_retractions_v1.verify import (
        check_certificates as check_three,
    )
    from research.order9_two_p4_retractions_v1.verify import (
        verify_positive as check_two,
    )
    from research.order9_251902_p4_o17_v1.verify import (
        verify_positive as check_251902,
    )
    from research.order9_253650_o12_v1.verify import (
        verify as check_253650,
    )

    check_three(public=False)  # 249436, 249574, 250814
    check_two(251759, public=False)
    check_two(254369, public=False)
    check_251902(public=False)
    check_253650(public=False)




def check(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def git_blob(data: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()


def read_rows(path: Path) -> dict[int, str]:
    result: dict[int, str] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        check(len(parts) == 6, f"Malformed six-column census row: {line}")
        index, order, g6, rule, status, label = parts
        ix = int(index)
        check(ix not in result, f"Duplicate census McKay index {ix}")
        check((rule, status, label) == ("-", "-", "-"),
              f"Conditional entry should be retained, not promoted: {ix}")
        check(int(order) in (9, 10), f"Unexpected pared order for {ix}")
        G = nx.from_graph6_bytes(g6.encode("ascii"))
        check(len(G) == int(order), f"Wrong graph6 order for {ix}")
        result[ix] = line
    check(list(result) == sorted(result), f"Index not strictly sorted: {path}")
    return result


def independent_maximal_cliques(G: nx.Graph) -> set[frozenset[int]]:
    """Bron--Kerbosch enumeration distinct from NetworkX find_cliques."""
    result: set[frozenset[int]] = set()
    neighbors = {v: set(G[v]) for v in G}

    def recurse(R: frozenset[int], P: set[int], X: set[int]) -> None:
        if not P and not X:
            result.add(R)
            return
        pivot = max(P | X, key=lambda u: (len(P & neighbors[u]), -u))
        for v in sorted(P - neighbors[pivot]):
            recurse(R | {v}, P & neighbors[v], X & neighbors[v])
            P.remove(v)
            X.add(v)

    recurse(frozenset(), set(G), set())
    return result


def canon_clique_graph(G: nx.Graph) -> nx.Graph:
    nx_cliques = {frozenset(c) for c in nx.find_cliques(G)}
    check(nx_cliques == independent_maximal_cliques(G),
          "Independent maximal-clique enumerators disagree")
    cliques = sorted(tuple(sorted(c)) for c in nx_cliques)
    sets = [set(c) for c in cliques]
    H = nx.Graph()
    H.add_nodes_from(range(len(cliques)))
    H.add_edges_from(
        (a, b) for a, b in combinations(range(len(cliques)), 2)
        if not sets[a].isdisjoint(sets[b])
    )
    return H


def canon_pare(G: nx.Graph) -> nx.Graph:
    """Sequential smallest-index dominated-vertex deletion and audit."""
    H = G.copy()
    while True:
        removal = None
        for v in sorted(H):
            Nv = set(H[v]) | {v}
            for w in sorted(H):
                if v != w and Nv <= (set(H[w]) | {w}):
                    removal = v
                    break
            if removal is not None:
                break
        if removal is None:
            break
        H.remove_node(removal)
    check(
        all(
            not (set(H[v]) | {v}) <= (set(H[w]) | {w})
            for v in H for w in H if v != w
        ),
        "Paring left a dominated vertex",
    )
    return nx.convert_node_labels_to_integers(H, ordering="sorted")


def independently_reconstruct_p2(graph6: str, expected_order: int) -> nx.Graph:
    G = nx.from_graph6_bytes(graph6.encode("ascii"))
    check(len(G) == expected_order, f"Unexpected source order: {graph6}")
    for j in range(3):
        G = canon_pare(G)
        if j < 2:
            G = canon_clique_graph(G)
    return G


def verify_archive() -> None:
    manifest = json.loads(CERT.read_text(encoding="utf-8"))
    check(manifest["schema"] == 1, "Unsupported certificate schema")
    check(manifest["source_v20_blob"] == FROZEN_V20,
          "Certificate cites a wrong frozen v20 Git blob")
    check((manifest["source_v20_count"], manifest["certified_v21_count"])
          == (1311, 1228), "Unexpected manifest population")
    check(git_blob(V20.read_bytes()) == FROZEN_V20,
          "Immutable ten-v20 snapshot was modified")
    check(CURRENT.read_bytes() == V21.read_bytes(),
          "Working ten-vertex index differs from certified v21")
    check(NINE_CURRENT.read_bytes() == NINE_V9.read_bytes(),
          "Nine-v9 working root unexpectedly changed")

    old, new = read_rows(V20), read_rows(V21)
    check((len(old), len(new)) == (1311, 1228),
          "Unexpected old/new populations")
    check(set(new) <= set(old), "New unproved index appeared")
    check(all(new[i] == old[i] for i in new),
          "An unchanged six-field original record was modified")
    check(Counter(int(row.split()[1]) for row in old.values())
          == Counter({9: 430, 10: 881}),
          "Wrong ten-v20 nine-core/stiff-core partition")
    check(Counter(int(row.split()[1]) for row in new.values())
          == Counter({9: 430, 10: 798}),
          "Wrong ten-v21 nine-core/stiff-core partition")

    sources = manifest["source_proofs"]
    check(len(sources) == 7 and
          {s["index"] for s in sources} == set(PROVED_COUNTS),
          "Incorrect proved divergent reference set")
    reference_graphs: dict[int, nx.Graph] = {}
    for source in sources:
        ix, graph6, rel = source["index"], source["g6"], source["proof"]
        check((graph6, rel) == PROVED_SOURCES[ix],
              f"Wrong identity or certificate path for proved source: {ix}")
        check((ROOT / rel).is_file(),
              f"Archived source divergence proof missing: {rel}")
        check(graph6 in (ROOT / rel).read_text(encoding="utf8"),
              f"Source proof does not identify the original graph6: {ix}")
        # Historical source graph identity is independently authenticated
        # against frozen old nine-vertex source index files.
        historic = [
            ROOT / f"indeterminate_order_9_v{k}.txt"
            for k in range(4, 9)
        ]
        check(any(
            f"{ix} 9 {graph6} - - -" in path.read_text(encoding="ascii").splitlines()
            for path in historic
        ), f"Proved nine-vertex source identity absent from history: {ix}")
        reference_graphs[ix] = independently_reconstruct_p2(graph6, 9)

    # The seven divergence premises must pass their saved *positive*
    # projection verifiers before any new ten-vertex record is promoted.
    verify_archived_source_retractions()

    records = manifest["matches"]
    check(len(records) == 83 and
          len({item["original_index"] for item in records}) == 83,
          "Duplicate or missing P2 positive certificates")
    check([item["original_index"] for item in records]
          == sorted(item["original_index"] for item in records),
          "Certificate entries are not sorted")
    check({item["original_index"] for item in records}
          == set(old) - set(new),
          "Exact census difference does not match positive certificates")
    counts: Counter[int] = Counter()
    for item in records:
        ix, graph6, ref = (
            item["original_index"], item["original_graph6"],
            item["source_index"]
        )
        check(ref in reference_graphs, f"Unproved source reference: {ix}")
        check(old[ix] == f"{ix} 10 {graph6} - - -",
              f"Wrong immutable original McKay record: {ix}")
        G = independently_reconstruct_p2(graph6, 10)
        R = reference_graphs[ref]
        mapping = item["p2_bijection"]
        n = len(G)
        check(n == len(R) == item["p2_order"]
              and G.number_of_edges() == R.number_of_edges()
              == item["p2_edges"],
              f"Wrong reconstructed P2 dimensions: {ix}")
        check(isinstance(mapping, list) and
              sorted(mapping) == list(range(n)),
              f"Invalid P2 vertex bijection: {ix}")
        check(all(
            G.has_edge(u, v) == R.has_edge(mapping[u], mapping[v])
            for u in G for v in G
        ), f"P2 certificate fails independent edge/nonedge audit: {ix}")
        # Distinct independent isomorphism algorithm cross-check.
        check(nx.is_isomorphic(G, R),
              f"NetworkX GraphMatcher contradicts saved mapping: {ix}")
        counts[ref] += 1

    check(dict(counts) == PROVED_COUNTS,
          f"Unexpected exact per-reference promotion counts: {counts}")
    print(
        "PASS: 83 exact P2 source isomorphisms; seven archived K-divergent "
        "nine-sources; immutable ten-v20 1311 -> certified ten-v21 1228; "
        "430 nine-core and 798 stiff ten-core originals remain; "
        "all saved bijections checked on every ordered pair.",
        flush=True,
    )


if __name__ == "__main__":
    verify_archive()
