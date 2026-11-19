"""Prove a new K-divergent stiff ten-graph by an O3 retract of K(G).

For every currently indeterminate stiff ten-vertex graph G in versioned
v5, independently enumerate maximal cliques, construct K(G), and look
for arbitrary graph retractions K(G)->O3 (not merely special octahedra).
A target is an induced 6-vertex octahedron O3 = complement of 3K2.
A graph retraction fixes that induced target pointwise, mapping edges
to edges OR equal vertices.

The unique positive among the stiff ten-vertex v5 originals is
McKay index 11634099, graph6 IEjer^{lo. K(G) has 17 vertices;
its full 17-entry map onto an induced O3 is stored and verified.
Neumann-Lara's Retraction Theorem and known K-divergence of O3
give an unconditional divergence certificate for G.

This is independent of the earlier nine-vertex suspension retracts.
All previous reports, sources, proofs and classifications stay frozen.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import networkx as nx

import direct_divergent_ninecore_retracts_v1 as old

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "indeterminate_order_10_v5.txt"
PREVIOUS_VERIFIER = ROOT / "scripts/direct_divergent_ninecore_retracts_v1.py"
OLD_SOURCE_GIT_BLOB = "52d71a90a60b0f714bdbb4bc2aef4fdb857f49e2"
OLD_SCRIPT_GIT_BLOB = "5abeb042f66668b59858ca28aeae14447abb5349"
OUT = "research/order10_first_clique_octahedron_retract_v1"
NEW_LIST = "indeterminate_order_10_v6.txt"
EXPECTED_ID = 11634099
EXPECTED_G6 = "IEjer^{lo"
EXPECTED_TARGET = (1, 5, 9, 10, 14, 15)
EXPECTED_MAP = (14, 1, 5, 15, 14, 5, 1, 10, 1, 9, 10, 10, 9, 10, 14, 15, 14)
MAX_STATES = 200_000


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def raw_clique_graph(G: nx.Graph) -> tuple[nx.Graph, list[frozenset[int]]]:
    """Exact K(G) with deterministic INTEGER-BITMASK facet ordering."""
    facets = sorted(
        (frozenset(q) for q in nx.find_cliques(G)),
        key=lambda q: sum(1 << v for v in q),
    )
    K = nx.Graph()
    K.add_nodes_from(range(len(facets)))
    K.add_edges_from(
        (i, j) for i, j in itertools.combinations(K, 2)
        if facets[i] & facets[j]
    )
    return K, facets


def verify_oct_retraction(
    H: nx.Graph, target: tuple[int, ...], projection: tuple[int, ...]
) -> None:
    """Independent exact six-vertex induced O3 and total morphism test."""
    if (
        len(target) != 6
        or tuple(sorted(target)) != target
        or len(set(target)) != 6
        or not set(target) <= set(H)
        or len(projection) != len(H)
        or set(projection) != set(target)
        or any(projection[u] != u for u in target)
    ):
        raise ValueError("Invalid induced octahedron section/retraction equation")
    T = H.subgraph(target)
    if not nx.is_isomorphic(T, nx.complete_multipartite_graph(2, 2, 2)):
        raise ValueError("The six fixed vertices do not induce O3")
    if any(
        projection[u] != projection[v]
        and not T.has_edge(projection[u], projection[v])
        for u, v in H.edges()
    ):
        raise ValueError("A source clique-graph edge violates weak morphism")


def induced_octahedra(K: nx.Graph):
    """Enumerate all O3 vertex subsets by three independent nonedges.

    An O3 is precisely six vertices with only three missing edges,
    forming a perfect matching. Enumerating triples in the complement
    avoids searching C(n,6) arbitrary dense source subgraphs.
    """
    missing = sorted(nx.non_edges(K))
    for i, first in enumerate(missing):
        for j in range(i + 1, len(missing)):
            second = missing[j]
            four = set(first + second)
            if len(four) != 4 or any(
                not K.has_edge(u, v) for u in first for v in second
            ):
                continue
            for k in range(j + 1, len(missing)):
                third = missing[k]
                six = four | set(third)
                if len(six) != 6:
                    continue
                if any(
                    not K.has_edge(u, v) for u in four for v in third
                ):
                    continue
                target = tuple(sorted(six))
                if K.subgraph(target).number_of_edges() != 12:
                    raise AssertionError("Incorrect alleged induced O3")
                yield target


def bounded_retraction(
    K: nx.Graph, target: tuple[int, ...]
) -> tuple[tuple[int, ...] | None, int, bool]:
    """Find an exact retraction or exhaust this finite embedding.

    The only possible maps fix target vertices; every other vertex's
    domain is derived from all target-adjacent source constraints.
    Search counts are bounded; a reached limit is NOT a negative result.
    """
    T = set(target)
    fixed = {v: v for v in target}
    domains = {}
    for v in K:
        if v in T:
            continue
        possible = [
            w for w in target
            if all(
                w == t or K.has_edge(w, t)
                for t in K[v] if t in T
            )
        ]
        if not possible:
            return None, 0, False
        domains[v] = possible
    outside = sorted(domains, key=lambda v: (len(domains[v]), v))
    assignment = fixed.copy()
    count = 0
    limited = False

    def rec(k: int) -> bool:
        nonlocal count, limited
        count += 1
        if count > MAX_STATES:
            limited = True
            return False
        if k == len(outside):
            return True
        v = outside[k]
        for w in domains[v]:
            if all(
                w == assignment[u] or K.has_edge(w, assignment[u])
                for u in K[v] if u in assignment
            ):
                assignment[v] = w
                if rec(k + 1):
                    return True
                del assignment[v]
        return False

    if rec(0):
        projection = tuple(assignment[v] for v in range(len(K)))
        verify_oct_retraction(K, target, projection)
        return projection, count, False
    return None, count, limited


def frozen_sources(root: Path = ROOT) -> list[dict]:
    if git_blob((root / "indeterminate_order_10_v5.txt").read_bytes()) != OLD_SOURCE_GIT_BLOB:
        raise ValueError("The verified v5 unresolved graph population was altered")
    if git_blob((root / "scripts/direct_divergent_ninecore_retracts_v1.py").read_bytes()) != OLD_SCRIPT_GIT_BLOB:
        raise ValueError("The previous exact nine-retraction verifier was altered")
    old.verify(root)
    rows = []
    for line in (root / "indeterminate_order_10_v5.txt").read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        if len(fields) != 6:
            raise ValueError("Malformed v5 unresolved source row")
        if fields[1] == "10":
            rows.append({"original_index": int(fields[0]), "graph6": fields[2]})
    if len(rows) != 2394 or len({r["original_index"] for r in rows}) != 2394:
        raise ValueError("Expected 2,394 unique stiff ten-vertex v5 sources")
    return sorted(rows, key=lambda r: r["original_index"])


def verify_oct_divergence() -> None:
    """K(O3) is O4, and O_d iterates have unbounded dimension."""
    O3 = nx.complete_multipartite_graph(2, 2, 2)
    K_O3, _ = raw_clique_graph(O3)
    O4 = nx.complete_multipartite_graph(2, 2, 2, 2)
    if not nx.is_isomorphic(K_O3, O4):
        raise ValueError("The standard octahedron divergence base step failed")


def investigate(root: Path = ROOT) -> tuple[list[dict], dict]:
    sources = frozen_sources(root)
    verify_oct_divergence()
    positives = []
    totals = {
        "stiff_ten_sources_scanned": len(sources),
        "induced_O3_candidates_in_first_clique_graphs": 0,
        "sources_with_induced_O3": 0,
        "csp_limit_reached": 0,
        "positive_induced_O3_retractions": 0,
    }
    for row in sources:
        G = nx.from_graph6_bytes(row["graph6"].encode("ascii"))
        if len(G) != 10 or not nx.is_connected(G):
            raise ValueError("Invalid stiff source")
        K, facets = raw_clique_graph(G)
        has_candidate = False
        positive = None
        for target in induced_octahedra(K):
            totals["induced_O3_candidates_in_first_clique_graphs"] += 1
            has_candidate = True
            projection, states, limited = bounded_retraction(K, target)
            if limited:
                totals["csp_limit_reached"] += 1
            if projection is None:
                continue
            # Report the first deterministic valid target only, but
            # DO NOT use an unverified negative to infer convergence.
            positive = {
                "original_index": row["original_index"],
                "original_graph6": row["graph6"],
                "clique_graph_order": len(K),
                "clique_graph_edges": K.number_of_edges(),
                "full_source_facets": [
                    sorted(q) for q in facets
                ],
                "target_O3_vertices": list(target),
                "retraction": list(projection),
                "source_morphism_states": states,
                "proof": "K(G) retracts to induced O3; O3 is K-divergent",
                "new_status": "CERTIFIED_DIVERGENT",
            }
            totals["positive_induced_O3_retractions"] += 1
            break
        if has_candidate:
            totals["sources_with_induced_O3"] += 1
        if positive is not None:
            positives.append(positive)
    if (
        len(positives) != 1
        or positives[0]["original_index"] != EXPECTED_ID
        or positives[0]["original_graph6"] != EXPECTED_G6
        or tuple(positives[0]["target_O3_vertices"]) != EXPECTED_TARGET
        or tuple(positives[0]["retraction"]) != EXPECTED_MAP
        or positives[0]["clique_graph_order"] != 17
        or positives[0]["clique_graph_edges"] != 87
        or totals["csp_limit_reached"] != 0
    ):
        raise ValueError(f"Unexpected independent first-K O3 source results: {positives}; {totals}")
    return positives, totals


def generate(root: Path = ROOT) -> dict[str, bytes]:
    positives, counts = investigate(root)
    removed = {x["original_index"] for x in positives}
    entries = [
        line for line in (root / "indeterminate_order_10_v5.txt").read_text().splitlines()
        if line and not line.startswith("#")
    ]
    remaining = [
        line for line in entries if int(line.split()[0]) not in removed
    ]
    if len(entries) != 8224 or len(remaining) != 8223 or len(removed) != 1:
        raise ValueError("The current sixth unresolved index has an incorrect population")
    v6 = "\n".join([
        "# Current order-10 unresolved after v5 and a proved first-K octahedron retraction",
        "# Remaining=8223 previous_v5=8224 new_certified_divergent=1",
        "# Historical files and proofs remain frozen; negative limited-family probes imply no convergence.",
        "# Format: original_index pared_order pared_graph6 certificate_rule certificate_target_status certificate_target_label",
        *remaining,
        "",
    ]).encode()
    report = "\n".join([
        "# First-clique-graph octahedron retraction: one new divergent ten-graph",
        "",
        "The stiff connected original ten-vertex graph of McKay index",
        "11634099 (graph6 IEjer^{lo) has precisely 17 maximal cliques,",
        "so its first clique graph K(G) has 17 vertices and 87 edges.",
        "The induced vertices 1,5,9,10,14,15 of K(G) form O3,",
        "the complement of 3 disjoint edges.",
        "The missing pairs are (1,15), (5,10), (9,14).",
        "The exact total retraction of K(G) onto these vertices,",
        "in independently sorted integer-bitmask facet labeling, is:",
        "",
        "14,1,5,15,14,5,1,10,1,9,10,10,9,10,14,15,14",
        "",
        "It fixes its induced O3 target pointwise and every source",
        "edge maps to a target edge OR a single vertex. The",
        "certificate includes all 17 maximal cliques of the original",
        "ten-vertex graph and checks each edge. Since K(O3) is O4",
        "and iterated octahedral dimensions increase, O3 is",
        "K-divergent. Neumann-Lara's Retraction Theorem implies",
        "K(G) is K-divergent, hence G itself is K-divergent.",
        "",
        "The independent complete screen of 2,394 previously",
        "indeterminate stiff ten-vertex originals examines all",
        "induced O3 subgraphs in their first clique graphs and",
        "retraction constraints with no configured CSP limit reached.",
        "Other negative cases remain K-behavior indeterminate.",
        "",
        f"Sources examined: {counts['stiff_ten_sources_scanned']}",
        f"Induced O3 candidates: {counts['induced_O3_candidates_in_first_clique_graphs']}",
        f"Source graphs containing O3: {counts['sources_with_induced_O3']}",
        "New positive divergence certificates: 1",
        "",
        "The new versioned indeterminate_order_10_v6.txt contains",
        "8,223 original graphs: 2,092 with a snub eight-core;",
        "3,738 with an unresolved nine-core; and 2,393 with",
        "a stiff ten-core. Earlier v3/v4/v5 lists, certificates",
        "and reports are completely unchanged.",
        "",
        "Reproduction with Python and NetworkX 3.6.1:",
        "  python scripts/first_clique_octahedron_retract_v1.py verify",
        "  python -m unittest discover -s tests -p test_first_clique_octahedron_retract_v1.py -v",
        "",
    ]).encode()
    cert = {
        "schema": 1,
        "scope": "all 2394 still-unresolved stiff ten graphs, first raw clique iterate",
        "target_family": "ordinary graph retractions onto induced O3",
        "negative_result_never_implies_K_convergence": True,
        "counts": counts,
        "new_divergent": positives,
    }
    out = {
        "certificate.json": (json.dumps(cert, sort_keys=True, indent=2) + "\n").encode(),
        "summary.md": report,
    }
    manifest = {
        "schema": 1,
        "stage": "order10_first_clique_octahedron_retract_v1",
        "old_v5_sha256": digest((root / "indeterminate_order_10_v5.txt").read_bytes()),
        "new_v6_sha256": digest(v6),
        "outputs_sha256": {name: digest(data) for name, data in sorted(out.items())},
    }
    out["manifest.json"] = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    payload = {
        str(Path(OUT) / name): data for name, data in out.items()
    }
    payload[NEW_LIST] = v6
    return payload


def verify(root: Path = ROOT) -> None:
    for name, expected in generate(root).items():
        path = root / name
        if not path.is_file() or path.read_bytes() != expected:
            raise ValueError(f"Missing or changed first-iterate divergent certificate: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "build", "verify"))
    args = parser.parse_args()
    files = generate()
    if args.action == "plan":
        print("One new K-divergent stiff ten-graph: 11634099. Updated unresolved v6: 8223.")
        return
    if args.action == "build":
        for name, data in files.items():
            path = ROOT / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and path.read_bytes() != data:
                raise ValueError(f"Refusing to overwrite existing distinct proof: {name}")
            path.write_bytes(data)
    verify()
    print("VERIFIED first-K O3 retraction for 11634099, new v6 remaining 8223.")


if __name__ == "__main__":
    main()
