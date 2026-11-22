"""Independently certify complete P4 octahedral retractions for two nine-v8 cores.

Proved-positive cases:
  McKay 251759 (HEhvtzm): P4 -> O15 (403-source-vertex projection)
  McKay 254369 (HEjfvx}): P4 -> O13 (394-source-vertex projection)

The independent reconstruction and morphism checks use only NetworkX.
The optional --public mode compares all four iteration stages with
pinned public pycliques and validates the same full positive witness.

Checks exact 129 and 91 original ten-v19 lift families with no overlap.
No resource-limited negative claim or source-index promotion is made.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import networkx as nx

from research.order9_p4_domination_dual_v1.verify import (
    pare, clique_graph, normalized, edge_digest, build_p4, same_graph,
)

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical assertions")

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
NINE = ROOT / "indeterminate_order_9_v8.txt"
TEN = ROOT / "indeterminate_order_10_v19.txt"
NINE_GIT_BLOB = "446d7ddba6bdb7f4738730f7de0386bea6546df7"
TEN_GIT_BLOB = "cf8047698eb63f8b80ed7104f8cc4307d093fc09"
PROVED = {
    251759: {
        "graph6": "HEhvtzm",
        "orders": (9, 13, 21, 43, 403),
        "edges": (23, 52, 150, 701, 70679),
        "p4_sha256": "577c3026d1dbb08eab41ec971d03418b3e3201032ca312b7686ea02a2ba4b6f5",
        "dimension": 15,
        "dependent_originals": 129,
        "certificate": ROOT / "research/order9_251759_p4_o15_v1/certificate.json",
        "seed": 73,
    },
    254369: {
        "graph6": "HEjfvx}",
        "orders": (9, 13, 17, 40, 394),
        "edges": (24, 54, 99, 626, 67229),
        "p4_sha256": "552af5cc777ee202f0938844f735f487de06245e9dda9dc51801ced67438b5f7",
        "dimension": 13,
        "dependent_originals": 91,
        "certificate": ROOT / "research/order9_254369_p4_o13_v1/certificate.json",
        "seed": 19,
    },
}


def check(condition: bool, explanation: str) -> None:
    if not condition:
        raise AssertionError(explanation)


def git_blob(data: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()


def rows(path: Path, blob: str, expected_rows: int) -> dict[int, str]:
    raw = path.read_bytes()
    check(git_blob(raw) == blob, f"Frozen original census source changed: {path.name}")
    result: dict[int, str] = {}
    for line in raw.decode("ascii").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        check(len(fields) == 6, f"Malformed six-field census row: {line}")
        index = int(fields[0])
        check(index not in result, f"Repeated original McKay index {index}")
        check(fields[3:] == ["-", "-", "-"], f"Conditional row {index}")
        check(fields[1] in ("9", "10"), f"Invalid pared order {index}")
        result[index] = line
    check(len(result) == expected_rows, f"Wrong immutable census population: {path.name}")
    check(list(result) == sorted(result), f"Unsorted McKay index: {path.name}")
    return result


def reconstruct(index: int, *, public: bool = False) -> nx.Graph:
    case = PROVED[index]
    graph = pare(nx.from_graph6_bytes(case["graph6"].encode("ascii")))
    for depth, (n, m) in enumerate(zip(case["orders"], case["edges"], strict=True)):
        check((len(graph), graph.number_of_edges()) == (n, m),
              f"Wrong P{depth} host for {index}")
        if depth < 4:
            graph = pare(clique_graph(graph))
    host = normalized(graph)
    check(set(host) == set(range(case["orders"][-1])), f"Wrong P4 labeling {index}")
    check(
        edge_digest(host) == case["p4_sha256"],
        f"Wrong exact labeled P4 graph SHA-256: {index}",
    )
    if public:
        other = build_p4(case["graph6"], public=True)
        check(same_graph(host, other), f"Public/independent P4 mismatch: {index}")
    return host


def verify_positive(index: int, *, public: bool = False) -> None:
    case = PROVED[index]
    c = json.loads(case["certificate"].read_text(encoding="ascii"))
    check(
        (c["schema"], c["original_mckay"], c["original_graph6"], c["pared_depth"])
        == (1, index, case["graph6"], 4),
        f"Wrong positive certificate identity: {index}",
    )
    check(
        (tuple(c["iterate_orders"]), tuple(c["iterate_edges"]))
        == (case["orders"], case["edges"]),
        f"Wrong stated P0-P4 stage sizes: {index}",
    )
    check(
        (c["p4_order"], c["p4_edges"], c["p4_normalized_edge_sha256"])
        == (case["orders"][-1], case["edges"][-1], case["p4_sha256"]),
        f"Wrong full P4 graph identity: {index}",
    )
    check(c["target_dimension"] == case["dimension"],
          f"Wrong O_d dimension for {index}")
    check(
        c["projection_encoding"]
        == "uint8_target_ordinal_per_sorted_normalized_p4_host_label",
        f"Unknown projection encoding: {index}",
    )
    host = reconstruct(index, public=public)
    pairs = [tuple(p) for p in c["antipodal_pairs"]]
    check(len(pairs) == case["dimension"], f"Wrong antipodal pairing {index}")
    target = {v for a, b in pairs for v in (a, b)}
    check(len(target) == 2 * len(pairs) and target <= set(host),
          f"Repeated or missing antipodes: {index}")
    check(c["target_order"] == sorted(target), f"Wrong target-order table {index}")
    missing = nx.complement(host.subgraph(target))
    check(
        missing.number_of_edges() == case["dimension"]
        and {frozenset(edge) for edge in missing.edges()}
        == {frozenset(pair) for pair in pairs},
        f"Saved targets do not induce an O_d: {index}",
    )

    packed = base64.b64decode(c["projection_images_b64"], validate=True)
    check(len(packed) == len(host), f"Incomplete full projection array: {index}")
    order = sorted(target)
    check(all(t < len(order) for t in packed), f"Out-of-range target ordinal: {index}")
    projection = {v: order[packed[v]] for v in host}
    check(set(projection.values()) == target, f"Non-surjective projection: {index}")
    check(all(projection[v] == v for v in target), f"Target not pointwise fixed {index}")
    check(
        all(
            projection[u] == projection[v]
            or host.has_edge(projection[u], projection[v])
            for u, v in host.edges()
        ),
        f"An original P4 edge is not preserved: {index}",
    )

    discovery = c["discovery"]
    check(discovery["seed"] == case["seed"]
          and discovery["observed_states"] > 0,
          f"Incorrect unseeded-search provenance: {index}")
    if public:
        import pycliques as pc
        check(pc.verify_induced_octahedron(host, pairs),
              f"Public induced-O_d verification failed: {index}")
        check(
            pc.verify_retraction_witness(
                host, host.subgraph(target),
                (projection, {v: v for v in target}),
            ),
            f"Public full-retraction verification failed: {index}",
        )
    print(
        f"PROVED McKay={index} original_graph6={case['graph6']} "
        f"P4_vertices={len(host)} P4_edges={host.number_of_edges()} "
        f"ordinary_retraction_to=O{case['dimension']} "
        f"all_{len(host)}_images=PASS all_edges=PASS "
        f"public_replay={public}",
        flush=True,
    )


def verify_ten_lifts() -> None:
    nine = rows(NINE, NINE_GIT_BLOB, 5)
    ten = rows(TEN, TEN_GIT_BLOB, 1531)
    for index, case in PROVED.items():
        check(nine[index] == f"{index} 9 {case['graph6']} - - -",
              f"McKay nine-v8 graph6 identity mismatch: {index}")
    sources = {
        index: nx.from_graph6_bytes(case["graph6"].encode("ascii"))
        for index, case in PROVED.items()
    }
    families = Counter()
    promoted: dict[int, int] = {}
    core9 = core10 = 0
    for original, row in ten.items():
        _, pared_order, g6, *_ = row.split()
        core = nx.from_graph6_bytes(g6.encode("ascii"))
        check(len(core) == int(pared_order),
              f"Wrong pared order for original ten-vertex {original}")
        if pared_order == "10":
            core10 += 1
            continue
        core9 += 1
        matched = []
        for index, source in sources.items():
            matcher = nx.algorithms.isomorphism.GraphMatcher(source, core)
            if matcher.is_isomorphic():
                mapping = matcher.mapping
                check(len(mapping) == 9 and set(mapping) == set(source)
                      and set(mapping.values()) == set(core),
                      f"Invalid nine-vertex core bijection: {original}")
                check(
                    all(
                        source.has_edge(u, v)
                        == core.has_edge(mapping[u], mapping[v])
                        for u in source for v in source
                    ),
                    f"False nine-core isomorphism: {original}",
                )
                matched.append(index)
        check(len(matched) <= 1, f"Overlapping classified families: {original}")
        if matched:
            promoted[original] = matched[0]
            families[matched[0]] += 1

    check((core9, core10) == (650, 881), "Wrong frozen v19 pared-core partition")
    check(
        families == Counter({
            index: case["dependent_originals"] for index, case in PROVED.items()
        }),
        f"Incorrect families of ten-original K-divergences: {families}",
    )
    check(len(promoted) == 220, "Expected exactly 220 distinct original ten-lifts")
    print(
        "PROVED_TEN_DEPENDENTS McKay251759=129 McKay254369=91 "
        "total_distinct=220 frozen_v19_exact_core_isomorphisms=PASS",
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public", action="store_true")
    args = parser.parse_args()
    for index in PROVED:
        verify_positive(index, public=args.public)
    verify_ten_lifts()


if __name__ == "__main__":
    main()
