"""Independent proof replay for the global ten-v23 P3 equivalence index.

This module deliberately does not call classes.build(), classes.pare(),
classes.clique_graph(), classes.fingerprint(), or the custom matcher.
Its second maximal-clique enumerator is an independent bitset
Bron--Kerbosch with pivoting; complete clique sets must agree with
NetworkX at *every* reconstructed stage. Saved positive isomorphisms
are checked on all pairs and independently with GraphMatcher.
Necessary graph invariants certify separation of different classes.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

import networkx as nx

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical checks")

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "indeterminate_order_10_v23.txt"
CURRENT = ROOT / "indeterminate_order_10.txt"
ARCHIVE = Path(__file__).with_name("certificates.json")
SOURCE_BLOB = "f32ceb913b44583f472402e14c596598fef71aaa"
LIMIT_INTERMEDIATE = 110
LIMIT_FACETS = 750
SKIPPED = {11708967, 11715667, 11716441}


def check(ok: bool, reason: str) -> None:
    if not ok:
        raise AssertionError(reason)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def rows() -> dict[int, str]:
    check(git_blob(SOURCE.read_bytes()) == SOURCE_BLOB,
          "Immutable ten-v23 source was changed")
    check(CURRENT.read_bytes() == SOURCE.read_bytes(),
          "Current census root is not ten-v23")
    check((ROOT / "indeterminate_order_9.txt").read_bytes() ==
          (ROOT / "indeterminate_order_9_v9.txt").read_bytes(),
          "Nine-v9 root was changed")
    result: dict[int, str] = {}
    for row in SOURCE.read_text(encoding="ascii").splitlines():
        if not row or row.startswith("#"):
            continue
        bits = row.split()
        check(len(bits) == 6, "Malformed original census record")
        index, order, g6, rule, status, label = bits
        if order != "10":
            continue
        idx = int(index)
        check(idx not in result and (rule, status, label) == ("-", "-", "-"),
              f"Conditional/duplicate record {idx}")
        graph = nx.from_graph6_bytes(g6.encode("ascii"))
        check(len(graph) == 10, f"Bad source graph order {idx}")
        result[idx] = g6
    check(len(result) == 629 and list(result) == sorted(result),
          "Changed stiff ten-v23 cohort")
    return result


class LimitHit(Exception):
    def __init__(self, stage: int, reason: str, orders: list[int]):
        self.stage, self.reason, self.orders = stage, reason, list(orders)


class TooManyCliques(Exception):
    pass


def _bits(mask: int):
    while mask:
        bit = mask & -mask
        mask ^= bit
        yield bit.bit_length() - 1


def maximal_cliques_bk(graph: nx.Graph, *, cap: int = LIMIT_FACETS) -> list[int]:
    """Standalone pivoted Bron--Kerbosch, capped *during* enumeration."""
    n = len(graph)
    check(set(graph) == set(range(n)), "Graph vertex labels are not canonical")
    neighborhood = [
        sum(1 << v for v in graph[i])
        for i in range(n)
    ]
    results: list[int] = []

    def visit(r: int, p: int, x: int) -> None:
        if not p and not x:
            results.append(r)
            if len(results) > cap:
                raise TooManyCliques
            return
        union = p | x
        if union:
            pivot = max(_bits(union),
                        key=lambda v: (p & neighborhood[v]).bit_count())
            choices = p & ~neighborhood[pivot]
        else:
            choices = p
        for v in list(_bits(choices)):
            bit = 1 << v
            visit(r | bit, p & neighborhood[v], x & neighborhood[v])
            p &= ~bit
            x |= bit

    visit(0, (1 << n) - 1, 0)
    return sorted(results)


def maximal_cliques_nx(graph: nx.Graph, *, cap: int = LIMIT_FACETS) -> list[int]:
    """Separate NetworkX enumeration, with the same explicit hard cap."""
    facets: list[int] = []
    for clique in nx.find_cliques(graph):
        facets.append(sum(1 << v for v in clique))
        if len(facets) > cap:
            raise TooManyCliques
    return sorted(facets)


def independent_pare(graph: nx.Graph) -> nx.Graph:
    """Sequential closed-neighborhood folds implemented with integer masks."""
    n = len(graph)
    check(set(graph) == set(range(n)), "Noncanonical paring input")
    neighbors = [sum(1 << v for v in graph[u]) for u in range(n)]
    active = (1 << n) - 1
    while True:
        victim = None
        for u in _bits(active):
            closed_u = (neighbors[u] | (1 << u)) & active
            for v in _bits(active):
                if v != u and closed_u & ~((neighbors[v] | (1 << v)) & active) == 0:
                    victim = u
                    break
            if victim is not None:
                break
        if victim is None:
            break
        active &= ~(1 << victim)
    labels = list(_bits(active))
    graph2 = nx.Graph()
    graph2.add_nodes_from(range(len(labels)))
    graph2.add_edges_from(
        (i, j) for i, u in enumerate(labels)
        for j in range(i + 1, len(labels))
        if neighbors[u] & (1 << labels[j])
    )
    check(all(
        not (set(graph2[u]) | {u}) <= (set(graph2[v]) | {v})
        for u in graph2 for v in graph2 if u != v
    ), "Independent paring left a dominated vertex")
    return graph2


def independent_clique_graph(
    graph: nx.Graph, *, stage: int, orders: list[int],
) -> nx.Graph:
    """Compare two enumerators before computing the canonical clique graph."""
    try:
        nx_facets = maximal_cliques_nx(graph)
    except TooManyCliques:
        try:
            maximal_cliques_bk(graph)
        except TooManyCliques:
            raise LimitHit(stage, "maximal_clique_cap", orders) from None
        raise AssertionError("NetworkX exceeded facet cap but Bron--Kerbosch did not")
    try:
        bk_facets = maximal_cliques_bk(graph)
    except TooManyCliques as exc:
        raise AssertionError(
            "Bron--Kerbosch exceeded cap but NetworkX did not"
        ) from exc
    check(nx_facets == bk_facets,
          f"Independent maximal-clique enumerators disagree at stage {stage}")
    output = nx.Graph()
    output.add_nodes_from(range(len(bk_facets)))
    output.add_edges_from(
        (i, j)
        for i in range(len(bk_facets))
        for j in range(i + 1, len(bk_facets))
        if bk_facets[i] & bk_facets[j]
    )
    return output


def independent_p3(graph6: str) -> nx.Graph:
    graph = independent_pare(
        nx.from_graph6_bytes(graph6.encode("ascii"))
    )
    orders = [len(graph)]
    for stage in range(1, 4):
        if len(graph) > LIMIT_INTERMEDIATE:
            raise LimitHit(stage, "intermediate_order_cap", orders)
        next_graph = independent_clique_graph(
            graph, stage=stage, orders=orders,
        )
        graph = independent_pare(next_graph)
        orders.append(len(graph))
    return graph


def independent_invariant(graph: nx.Graph) -> tuple:
    """Isomorphism invariant, used only for separation of distinct classes."""
    degree = dict(graph.degree())
    local_profile = tuple(sorted(
        (degree[u], tuple(sorted(degree[v] for v in graph[u])))
        for u in graph
    ))
    return (
        len(graph), graph.number_of_edges(), local_profile,
        nx.weisfeiler_lehman_graph_hash(graph, iterations=3),
    )


def verify_pair(
    graph: nx.Graph, reference: nx.Graph, permutation: list[int],
) -> None:
    """Verify a saved complete map, then confirm with an independent matcher."""
    n = len(graph)
    check(n == len(reference) and isinstance(permutation, list)
          and sorted(permutation) == list(range(n)),
          "Non-bijective saved P3 map")
    check(all(
        graph.has_edge(i, j) == reference.has_edge(permutation[i], permutation[j])
        for i in range(n) for j in range(n)
    ), "Saved P3 map fails an edge or nonedge")
    # Constrain the independent GraphMatcher to the saved proof mapping.
    # This certifies the *specific* saved isomorphism in polynomial
    # time instead of asking VF2 to search a highly symmetric dense graph.
    # A false saved mapping still fails, rather than finding some other
    # accidental isomorphism between the two graphs.
    colored_graph = graph.copy()
    colored_reference = reference.copy()
    nx.set_node_attributes(
        colored_graph, {u: u for u in range(n)}, "certificate_vertex"
    )
    nx.set_node_attributes(
        colored_reference,
        {permutation[u]: u for u in range(n)},
        "certificate_vertex",
    )
    matcher = nx.algorithms.isomorphism.GraphMatcher(
        colored_graph, colored_reference,
        node_match=lambda a, b: (
            a["certificate_vertex"] == b["certificate_vertex"]
        ),
    )
    check(matcher.is_isomorphic() and
          matcher.mapping == {u: permutation[u] for u in range(n)},
          "Independent label-constrained GraphMatcher rejects saved mapping")


def verify_archive() -> None:
    check(ARCHIVE.is_file(), "Required positive-certificate archive is absent")
    cert = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    check(cert.get("schema") == 1 and
          cert.get("immutable_source_git_blob") == SOURCE_BLOB and
          cert.get("limits") == {
              "intermediate_order": LIMIT_INTERMEDIATE,
              "maximal_cliques": LIMIT_FACETS,
          }, "Wrong certificate schema, blob, or resource limits")

    sources = rows()
    singletons = cert["singleton_indices"]
    classes = cert["nontrivial_classes"]
    check(isinstance(singletons, list) and singletons == sorted(set(singletons)),
          "Bad singleton indices")
    check(isinstance(classes, list), "Missing classes")
    assignment: dict[int, int] = {i: i for i in singletons}
    refs: dict[int, dict[int, list[int]]] = {}
    for item in classes:
        rep, members = item["representative"], item["members"]
        check(len(members) > 1, "Archived trivial nontrivial class")
        ids = [entry["index"] for entry in members]
        check(ids == sorted(set(ids)) and ids[0] == rep
              and rep not in refs, "Incorrect class member order or representative")
        refs[rep] = {entry["index"]: entry["bijection"] for entry in members}
        for index in ids:
            check(index not in assignment, f"Duplicate class assignment: {index}")
            assignment[index] = rep

    indices = set(assignment)
    exceptions = cert["skips"]
    skipped = {entry["index"]: entry for entry in exceptions}
    check(len(skipped) == len(exceptions) and set(skipped) == SKIPPED,
          "Incorrect bounded exception identities")
    check(not indices & SKIPPED and indices | SKIPPED == set(sources),
          "Missing or repeated original McKay index in global partition")

    graphs: dict[int, nx.Graph] = {}
    independent_skips = []
    for index, g6 in sources.items():
        try:
            graphs[index] = independent_p3(g6)
        except LimitHit as exc:
            independent_skips.append({
                "index": index, "reason": exc.reason,
                "stage": exc.stage, "pared_orders": exc.orders,
            })
    check(independent_skips == exceptions,
          "Independent reconstruction disagrees about skipped cases")
    check(set(graphs) == indices and len(graphs) == 626,
          "Independent P3 reconstruction did not cover all 626 cases")

    buckets: dict[tuple, set[int]] = defaultdict(set)
    for index, graph in graphs.items():
        buckets[independent_invariant(graph)].add(assignment[index])
    # An isomorphism implies identical invariant. The archive must put
    # each complete invariant bucket in exactly ONE class; classes with
    # different buckets cannot be isomorphic. No heuristic fingerprints
    # are being treated as positive proofs.
    check(all(len(reps) == 1 for reps in buckets.values()),
          "Archive split a matching invariant bucket across classes")
    check(len(buckets) == 525 and len(set(assignment.values())) == 525,
          "Global equivalence-class count is inconsistent")

    for item in classes:
        rep = item["representative"]
        ref = graphs[rep]
        check((len(ref), ref.number_of_edges()) ==
              (item["order"], item["edges"]),
              "Archived representative graph dimensions changed")
        for entry in item["members"]:
            verify_pair(graphs[entry["index"]], ref, entry["bijection"])
    check(len(classes) == 33
          and len(singletons) == 492
          and sum(len(item["members"]) for item in classes) == 134,
          "Unexpected positive class structure")
    counts = {
        "stiff_originals": 629,
        "reconstructed": 626,
        "explicitly_skipped": 3,
        "exact_isomorphism_classes": 525,
        "nontrivial_classes": 33,
        "members_in_nontrivial_classes": 134,
        "singleton_classes": 492,
    }
    check(cert["counts"] == counts,
          "Archived total counts do not match independently reconstructed proof")
    print("PASS: independent BK/NetworkX clique enumeration and bitset paring"
          " at all reconstructed P3 stages; 626 originals, 525 exact classes,"
          " 33 nontrivial groups with 134 originals, 492 singletons,"
          " 3 explicit skips; complete vertex maps and GraphMatcher verified.")


if __name__ == "__main__":
    verify_archive()
