"""Independent finite proof of 20 K-divergent original ten-vertex graphs.

No discovery heuristics or cached iterates are trusted. Reconstruct P2/P3
from original graph6, use independent Bron--Kerbosch and NetworkX maximal
clique enumeration, and check every pair under the archived bijections.
For the two ten-vertex references, also verify complete ordinary graph
retractions onto already proved divergent smaller graphs.
"""

from __future__ import annotations

import base64
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
CERT = HERE / "certificates.json"
V21 = ROOT / "indeterminate_order_10_v21.txt"
V22 = ROOT / "indeterminate_order_10_v22.txt"
CURRENT = ROOT / "indeterminate_order_10.txt"
V21_BLOB = "668582e463a7d5e47637a5f78663954a72867d47"

REFERENCES = {
    249436: "HEhff^{",
    249574: "HEhfvx}",
    208409: "HCZTf\\}",
    250814: "HEhuvzm",
    251902: "HEhvvzm",
    9312634: "ICQfHz\\}o",
    11262714: "ICpu}zy}W",
}
EXPECTED = {
    7959206: (249436, 3),
    9813482: (9312634, 2),
    9813863: (249574, 3),
    9815528: (208409, 3),
    10297283: (249436, 3),
    10300042: (249436, 3),
    10475768: (208409, 3),
    10477617: (208409, 3),
    10484202: (208409, 3),
    10485646: (208409, 3),
    10601010: (249436, 3),
    11405876: (249436, 3),
    11475405: (250814, 3),
    11555266: (249436, 3),
    11557504: (249436, 3),
    11558565: (249436, 3),
    11559200: (249436, 3),
    11612071: (251902, 3),
    11624622: (249436, 3),
    11657332: (11262714, 2),
}
SMALL_TARGETS = {
    9312634: ("snub", "GQyuzw"),
    11262714: (260910, "HUZvvzu"),
}
EXPECTED_COUNTS = Counter({
    249436: 10, 208409: 5, 249574: 1, 250814: 1,
    251902: 1, 9312634: 1, 11262714: 1,
})


def check(ok: bool, reason: str) -> None:
    if not ok:
        raise AssertionError(reason)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def read_rows(path: Path) -> dict[int, str]:
    result = {}
    for line in path.read_text(encoding="ascii").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        check(len(parts) == 6, f"Malformed original census row: {line}")
        i, order, g6, rule, status, label = parts
        index = int(i)
        check(index not in result, f"Duplicate McKay index: {index}")
        check((rule, status, label) == ("-", "-", "-"),
              f"Conditional original still present: {index}")
        check(int(order) in (9, 10), f"Invalid pared order: {index}")
        check(len(nx.from_graph6_bytes(g6.encode("ascii"))) == int(order),
              f"Wrong original pared graph6 order: {index}")
        result[index] = line
    check(list(result) == sorted(result), f"Unsorted original indices: {path}")
    return result


def independent_maximal_cliques(graph: nx.Graph) -> set[frozenset[int]]:
    """Pure Bron--Kerbosch with pivot; independent of nx.find_cliques."""
    result: set[frozenset[int]] = set()
    neighbors = {v: set(graph[v]) for v in graph}

    def recurse(R: frozenset[int], P: set[int], X: set[int]) -> None:
        if not P and not X:
            result.add(R)
            return
        pivot = max(P | X, key=lambda u: (len(P & neighbors[u]), -u))
        for v in sorted(P - neighbors[pivot]):
            recurse(R | {v}, P & neighbors[v], X & neighbors[v])
            P.remove(v)
            X.add(v)

    recurse(frozenset(), set(graph), set())
    return result


def clique_graph(graph: nx.Graph) -> nx.Graph:
    maximal = {frozenset(c) for c in nx.find_cliques(graph)}
    check(maximal == independent_maximal_cliques(graph),
          "Two independent maximal clique enumerators disagree")
    sets = [set(c) for c in sorted(tuple(sorted(s)) for s in maximal)]
    out = nx.Graph()
    out.add_nodes_from(range(len(sets)))
    out.add_edges_from(
        (i, j) for i, j in combinations(range(len(sets)), 2)
        if sets[i] & sets[j]
    )
    return out


def pare(graph: nx.Graph) -> nx.Graph:
    """Delete smallest-index closed-neighborhood-dominated vertices."""
    graph = graph.copy()
    while True:
        victim = None
        for u in sorted(graph):
            closed_u = set(graph[u]) | {u}
            if any(u != v and closed_u <= set(graph[v]) | {v}
                   for v in sorted(graph)):
                victim = u
                break
        if victim is None:
            check(all(
                not (set(graph[u]) | {u}) <= (set(graph[v]) | {v})
                for u in graph for v in graph if u != v
            ), "A dominated vertex survived complete paring")
            return nx.convert_node_labels_to_integers(graph, ordering="sorted")
        graph.remove_node(victim)


def reconstruct(graph6: str, depth: int) -> nx.Graph:
    graph = nx.from_graph6_bytes(graph6.encode("ascii"))
    check(depth in (2, 3), "Unsupported pared iterate depth")
    for j in range(depth + 1):
        graph = pare(graph)
        if j < depth:
            graph = clique_graph(graph)
    return graph


def verify_small_retraction(index: int, item: dict) -> None:
    """Independently certify a full original-graph projection to a subgraph."""
    source = nx.from_graph6_bytes(item["source_graph6"].encode("ascii"))
    target = nx.from_graph6_bytes(item["target_graph6"].encode("ascii"))
    label = {int(k): v for k, v in item["target_bijection"].items()}
    keep = set(item["fixed_vertices"])
    check((item["source_graph6"], item["target_index"],
           item["target_graph6"]) == (REFERENCES[index], *SMALL_TARGETS[index]),
          f"Wrong small positive source identity: {index}")
    check(len(source) == 10 and keep <= set(source) and len(keep) == len(target),
          f"Invalid target vertex set: {index}")
    check(set(label) == keep and set(label.values()) == set(target),
          f"Invalid target graph isomorphism: {index}")
    check(all(
        source.has_edge(u, v) == target.has_edge(label[u], label[v])
        for u in keep for v in keep
    ), f"False induced-target isomorphism: {index}")
    outside = {int(k): v for k, v in item["outside_images"].items()}
    projection = {v: v for v in keep} | outside
    check(set(projection) == set(source) and all(v in keep for v in projection.values()),
          f"Non-total or invalid retraction: {index}")
    check(all(projection[v] == v for v in keep),
          f"Retraction does not fix its target: {index}")
    check(all(
        projection[u] == projection[v]
        or source.has_edge(projection[u], projection[v])
        for u, v in source.edges
    ), f"Retraction fails graph-morphism condition: {index}")
    print(f"PASS ten-reference {index}: complete original-graph retraction"
          f" to {item['target_index']} ({len(source)} source vertices)")


def verify_archived_positive_octahedron(
    original: int, original_graph6: str, depth: int,
    dimension: int, host: nx.Graph, certificate: Path,
) -> None:
    """Replay archived O_d using all source images; never just check text."""
    saved = json.loads(certificate.read_text(encoding="utf-8"))
    check(saved["schema"] == 1 and saved["source_graph6"] == original_graph6
          and saved["pared_depth"] == depth,
          f"Wrong archived source certificate: {original}")
    check((saved["host_order"], saved["host_edges"], saved["target_dimension"])
          == (len(host), host.number_of_edges(), dimension),
          f"Wrong archived iterate dimensions: {original}")
    graph6_host = nx.to_graph6_bytes(host, header=False).decode("ascii").strip()
    digest = hashlib.sha256(graph6_host.encode("ascii")).hexdigest()
    check(digest == saved["pared_graph6_sha256"],
          f"Wrong archived P{depth} host graph fingerprint: {original}")
    pairs = [tuple(p) for p in saved["opposite_pairs"]]
    nodes = {v for pair in pairs for v in pair}
    check(len(pairs) == dimension and len(nodes) == 2 * dimension
          and nodes <= set(host), f"Wrong archived antipodal pairs: {original}")
    missing = nx.complement(host.subgraph(nodes))
    check(missing.number_of_edges() == dimension
          and all(d == 1 for _, d in missing.degree())
          and {frozenset(pair) for pair in pairs}
          == {frozenset(edge) for edge in missing.edges()},
          f"Archived target is not O_{dimension}: {original}")
    images = list(base64.b64decode(saved["images_b64"], validate=True))
    check(set(host) == set(range(len(host))) and len(images) == len(host)
          and set(images) == nodes and all(images[v] == v for v in nodes),
          f"Archived full projection is invalid: {original}")
    check(all(
        images[u] == images[v] or host.has_edge(images[u], images[v])
        for u, v in host.edges
    ), f"Archived projection does not preserve a source edge: {original}")
    print(f"PASS nine-source {original}: P{depth} -> O{dimension},"
          f" all {len(host)} images and all {host.number_of_edges()} edges")


def verify_reference_divergence() -> None:
    """Check the existing full positive witnesses for six nine-sources.

    The snub (GQyuzw) has a separately certified K4 -> O24 theorem
    archived in the pycliques-project monorepo; that established theorem
    is the only external source-positive premise of this v22 audit.
    """
    from research.order9_three_p4_retractions_v1.verify import check_certificates
    from research.order9_251902_p4_o17_v1.verify import verify_positive
    from research.order9_f45_o9_v1.verify import (
        explicit_f45,
        independent_p4,
    )
    from research.order9_260910_o15_v1.verify import independently_reconstruct

    check_certificates(public=False)  # 249436, 249574, 250814
    verify_positive(public=False)  # 251902

    # The old archived O9 positive source uses an independently specified
    # F45, not a graph built from the graph6 string in this new manifest.
    # Explicitly identify the original McKay 208409 graph6 with that F45
    # construction before transporting its K-divergence theorem.
    raw_f45 = nx.from_graph6_bytes(REFERENCES[208409].encode("ascii"))
    explicit = explicit_f45()
    matcher = nx.algorithms.isomorphism.GraphMatcher(raw_f45, explicit)
    check(matcher.is_isomorphic(), "McKay 208409 graph6 is not F45")
    sigma = matcher.mapping
    check(all(
        raw_f45.has_edge(u, v) ==
        explicit.has_edge(sigma[u], sigma[v])
        for u in raw_f45 for v in raw_f45
    ), "McKay 208409 to explicit F45 bijection fails a vertex pair")
    old_nine = (ROOT / "indeterminate_order_9_v4.txt").read_text(
        encoding="ascii"
    )
    check(
        f"208409 9 {REFERENCES[208409]} - - -" in old_nine.splitlines(),
        "Original McKay 208409 identity not found in frozen nine-v4",
    )
    verify_archived_positive_octahedron(
        208409, REFERENCES[208409], 4, 9, independent_p4(),
        ROOT / "research/order9_f45_o9_v1/certificate.json",
    )
    verify_archived_positive_octahedron(
        260910, "HUZvvzu", 3, 15, independently_reconstruct(),
        ROOT / "research/order9_260910_o15_v1/certificate.json",
    )
    # Require the exact historical snub-positive source identity.
    from research.snub_promotion_v1.verify import SNUB
    check(nx.to_graph6_bytes(SNUB, header=False).decode("ascii").strip()
          == "GQyuzw", "Historical proved snub reference was changed")


def verify_archive() -> None:
    cert = json.loads(CERT.read_text(encoding="utf-8"))
    check(cert["schema"] == 1 and cert["immutable_v21_blob"] == V21_BLOB,
          "Wrong archive schema or source index SHA")
    check((cert["previous_count"], cert["new_count"]) == (1228, 1208),
          "Incorrect claimed census sizes")
    check(git_blob(V21.read_bytes()) == V21_BLOB,
          "Frozen ten-v21 snapshot was modified")
    check(CURRENT.read_bytes() == V22.read_bytes(),
          "Current working ten-index differs from frozen v22")
    nine_root = ROOT / "indeterminate_order_9.txt"
    nine_v9 = ROOT / "indeterminate_order_9_v9.txt"
    check(nine_root.read_bytes() == nine_v9.read_bytes(),
          "Nine-v9 current index unexpectedly changed")

    old, new = read_rows(V21), read_rows(V22)
    check((len(old), len(new)) == (1228, 1208),
          "Wrong ten-v21/ten-v22 populations")
    check(set(new) <= set(old)
          and all(old[index] == row for index, row in new.items()),
          "Unproved removal, insertion or modification of a retained record")
    check(Counter(int(row.split()[1]) for row in old.values())
          == Counter({9: 430, 10: 798}), "Wrong frozen ten-v21 partition")
    check(Counter(int(row.split()[1]) for row in new.values())
          == Counter({9: 430, 10: 778}), "Wrong promoted ten-v22 partition")

    retractions = cert["certified"]
    check([r["index"] for r in retractions] == [9312634, 11262714],
          "Wrong ten-reference positive certificates")
    for entry in retractions:
        verify_small_retraction(entry["index"], entry["value"])
    verify_reference_divergence()

    cases = cert["matches"]
    check(len(cases) == len(EXPECTED) == 20
          and [x["original_index"] for x in cases] == sorted(EXPECTED),
          "Missing, repeated, or unsorted positive certificates")
    check({x["original_index"] for x in cases} == set(old) - set(new),
          "The exact removed original indices do not equal the certificates")

    ref_graphs: dict[tuple[int, int], nx.Graph] = {}
    counts: Counter[int] = Counter()
    for item in cases:
        index, ref, depth = (item["original_index"], item["reference_index"],
                             item["pared_depth"])
        check((ref, depth) == EXPECTED[index] and
              item["reference_graph6"] == REFERENCES[ref],
              f"Wrong archived source identity/depth: {index}")
        check(old[index] == f"{index} 10 {item['original_graph6']} - - -",
              f"Original McKay record changed: {index}")
        reference = (ref, depth)
        if reference not in ref_graphs:
            ref_graphs[reference] = reconstruct(REFERENCES[ref], depth)
        R = ref_graphs[reference]
        G = reconstruct(item["original_graph6"], depth)
        mapping = item["bijection"]
        n = len(G)
        check((n, G.number_of_edges(), len(R), R.number_of_edges())
              == (item["pared_order"], item["pared_edges"],
                  item["pared_order"], item["pared_edges"]),
              f"Wrong P{depth} source dimensions: {index}")
        check(isinstance(mapping, list) and sorted(mapping) == list(range(n)),
              f"Bad saved P{depth} permutation: {index}")
        check(all(
            G.has_edge(u, v) == R.has_edge(mapping[u], mapping[v])
            for u in G for v in G
        ), f"Saved P{depth} bijection fails an edge/nonedge: {index}")
        check(nx.is_isomorphic(G, R),
              f"Independent GraphMatcher disagrees: {index}")
        counts[ref] += 1
    check(counts == EXPECTED_COUNTS, f"Unexpected reference counts: {counts}")
    print(
        "PASS: 20 new ten-original K-divergences: 18 exact P3 and two "
        "exact P2 bijections; seven reference families; 2 complete "
        "small source retractions; six locally replayed nine-source "
        "octahedral positive proofs and previously certified snub; "
        "immutable ten-v21=1228 -> ten-v22=1208 "
        "(430 nine-core + 778 stiff ten-core), all retained rows unchanged.",
        flush=True,
    )


if __name__ == "__main__":
    verify_archive()
