"""Independent exact P4 isomorphism certificates for three new ten-v24 divergences.

The finder used an unrelated NetworkX-only construction and explicit
backtracking. This verifier instead uses the frozen v23 independent
bitset Bron--Kerbosch and bitset-fold reconstruction, crosschecking
NetworkX maximal-clique enumeration at every stage. It reconstructs
the complete canonical 182-vertex bijections and checks all pairs.
The certified divergence reference has a historical full O12 map.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import networkx as nx

from research.order10_p3_global_v23_index.independent_verify import (
    independent_clique_graph, independent_pare,
)

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses positive-certificate checks")

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "indeterminate_order_10_v23.txt"
NEW = ROOT / "indeterminate_order_10_v24.txt"
CURRENT = ROOT / "indeterminate_order_10.txt"
ARCHIVE = HERE / "certificates.json"
V23_BLOB = "f32ceb913b44583f472402e14c596598fef71aaa"
INDICES = (11495390, 11533866, 11556387)
SOURCE_COUNTS = (1059, 1056)
SOURCE_ORDERS = (430, 629)
TARGET_ORDERS = (430, 626)
BASE_ID = 10223405
BASE_G6 = "ICXnRi^uo"
BASE_HASH = "da0b402b388157e9982f200079b870423bd7eda3725511f097a6fe76b23dacfe"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def source_rows(file: Path) -> dict[int, str]:
    result = {}
    for record in file.read_text(encoding="ascii").splitlines():
        if not record or record.startswith("#"):
            continue
        fields = record.split()
        require(len(fields) == 6, "Malformed census row")
        original, order, graph6, *status = fields
        index = int(original)
        require(index not in result, "Repeated original McKay index")
        require(order in ("9", "10") and status == ["-", "-", "-"],
                "Unexpected conditional census row")
        require(len(nx.from_graph6_bytes(graph6.encode("ascii"))) == 10
                if order == "10" else True,
                "Wrong graph6 source order")
        result[index] = record
    require(list(result) == sorted(result), "Index records not sorted")
    return result


def verify_index_change(cert: dict) -> None:
    require(git_blob(SOURCE.read_bytes()) == V23_BLOB,
            "Frozen ten-v23 source changed")
    require(CURRENT.read_bytes() == NEW.read_bytes(),
            "Current ten-vertex root is not ten-v24")
    require((ROOT / "indeterminate_order_9.txt").read_bytes() ==
            (ROOT / "indeterminate_order_9_v9.txt").read_bytes(),
            "Nine-v9 historical root unexpectedly changed")
    require(cert["schema"] == 1 and cert["from_git_blob"] == V23_BLOB
            and cert["from_snapshot"] == SOURCE.name
            and cert["to_snapshot"] == NEW.name,
            "Bad index transition metadata")
    prior, current = source_rows(SOURCE), source_rows(NEW)
    require((len(prior), len(current)) == SOURCE_COUNTS,
            "Wrong old/new index population")
    require(set(prior) - set(current) == set(INDICES),
            "The v24 advancement does not remove precisely three proofs")
    require(all(current[i] == prior[i] for i in current),
            "A retained source record was modified")
    require(all(prior[i].split()[1] == "10" for i in INDICES),
            "One proved original is not a stiff ten-core")
    require(tuple(sum(row.split()[1] == str(order)
                      for row in prior.values()) for order in (9, 10))
            == SOURCE_ORDERS, "Wrong frozen ten-v23 partition")
    require(tuple(sum(row.split()[1] == str(order)
                      for row in current.values()) for order in (9, 10))
            == TARGET_ORDERS, "Wrong ten-v24 partition")
    return None


def reconstruct(graph6: str) -> tuple[list[tuple[int, int]], nx.Graph]:
    graph = independent_pare(nx.from_graph6_bytes(graph6.encode("ascii")))
    dimensions = [(len(graph), graph.number_of_edges())]
    for depth in range(1, 5):
        raw = independent_clique_graph(graph, stage=depth,
                                       orders=[n for n, _ in dimensions])
        graph = independent_pare(raw)
        dimensions.append((len(graph), graph.number_of_edges()))
    return dimensions, graph


def host_sha(graph: nx.Graph) -> str:
    return hashlib.sha256(
        nx.to_graph6_bytes(graph, header=False).strip()
    ).hexdigest()


def canonical_bijection(source: nx.Graph, reference: nx.Graph) -> list[int]:
    """Compute every image using canonical joint WL color refinement.

    These three pairs have 182 *distinct* stable colors after one
    neighborhood-refinement step, hence the map is uniquely specified
    without an exponential isomorphism search. All edges/nonedges
    are checked separately; color agreement alone is never a proof.
    """
    n = len(source)
    require(n == len(reference) == 182, "Unexpected source or base order")
    colors = [source.degree[u] for u in range(n)] + [
        reference.degree[u] for u in range(n)
    ]
    palette = {key: pos for pos, key in enumerate(sorted(set(colors)))}
    colors = [palette[x] for x in colors]
    linked = [
        set(source[u]) for u in range(n)
    ] + [
        {n + v for v in reference[u]} for u in range(n)
    ]
    labels = [
        (colors[u], tuple(sorted(colors[v] for v in linked[u])))
        for u in range(2 * n)
    ]
    palette = {key: pos for pos, key in enumerate(sorted(set(labels)))}
    refined = [palette[label] for label in labels]
    a, b = refined[:n], refined[n:]
    require(len(set(a)) == len(set(b)) == n and sorted(a) == sorted(b),
            "Not a bijection of unique jointly refined colors")
    reference_color_to_vertex = {color: vertex for vertex, color
                                 in enumerate(b)}
    permutation = [reference_color_to_vertex[color] for color in a]
    verify_full_bijection(source, reference, permutation)
    return permutation


def verify_full_bijection(source: nx.Graph, reference: nx.Graph,
                          permutation: list[int]) -> None:
    n = len(source)
    require(len(reference) == n and len(permutation) == n
            and sorted(permutation) == list(range(n)),
            "Invalid full P4 permutation")
    require(all(
        source.has_edge(u, v) == reference.has_edge(
            permutation[u], permutation[v])
        for u in range(n) for v in range(n)
    ), "Complete P4 graph isomorphism fails on an edge or nonedge")
    # Independent VF2 cross-check of the *specific* saved proof map:
    colored_source, colored_reference = source.copy(), reference.copy()
    nx.set_node_attributes(colored_source, {u: u for u in range(n)}, "label")
    nx.set_node_attributes(
        colored_reference,
        {permutation[u]: u for u in range(n)}, "label",
    )
    matcher = nx.algorithms.isomorphism.GraphMatcher(
        colored_source, colored_reference,
        node_match=lambda a, b: a["label"] == b["label"],
    )
    require(matcher.is_isomorphic()
            and matcher.mapping == {u: permutation[u] for u in range(n)},
            "Independent label-constrained GraphMatcher disagrees")


def verify_reference_provenance(cert: dict) -> None:
    base = cert["reference"]
    require(base == {
        "mckay": BASE_ID, "graph6": BASE_G6,
        "pared_fourth": [182, 14298],
        "canonical_host_sha256": BASE_HASH,
        "published_o12_archive":
            "research/order10_fourth_oct_v1/o12_certificates.json",
        "target_dimension": 12,
    }, "Wrong previously certified K-divergent reference")
    historical = json.loads(
        (ROOT / base["published_o12_archive"]).read_text(encoding="utf-8")
    )
    old = [p for p in historical["proofs"] if p["index"] == BASE_ID]
    require(historical["schema"] == 1 and len(old) == 1
            and old[0]["source_graph6"] == BASE_G6
            and old[0]["depth"] == 4 and old[0]["k4_order"] == 182
            and old[0]["k4_edges"] == 14298 and
            len(old[0]["pairs"]) == 12 and
            len({x for pair in old[0]["pairs"] for x in pair}) == 24,
            "Prior full O12 certificate has changed")
    # The preexisting v12 replay checks its complete retraction.
    # This proof rechecks the exact P4 isomorphism to that known source.


def verify_archive() -> None:
    cert = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    verify_index_change(cert)
    verify_reference_provenance(cert)
    third = json.loads(
        (ROOT / "research/order10_p3_global_v23_index/certificates.json")
        .read_text(encoding="utf-8")
    )
    require(third["immutable_source_git_blob"] == V23_BLOB,
            "Global v23 isomorphism index provenance changed")
    singletons = set(third["singleton_indices"])
    require(set(INDICES).issubset(singletons),
            "A new proof would duplicate a known P3 equivalence lift")
    require([item["index"] for item in cert["witnesses"]] == list(INDICES),
            "Missing or duplicated P4 positive certificates")
    base_sizes, base = reconstruct(BASE_G6)
    require(base_sizes == [
        (10, 26), (15, 65), (19, 117), (37, 503), (182, 14298)
    ] and host_sha(base) == BASE_HASH,
            "Independently reconstructed divergent P4 source differs")
    previous = source_rows(SOURCE)
    for item in cert["witnesses"]:
        i, g6 = item["index"], item["graph6"]
        require(previous[i] == f"{i} 10 {g6} - - -",
                "Incorrect frozen McKay source identity")
        sizes, host = reconstruct(g6)
        require([list(x) for x in sizes] == item["stages"]
                and host_sha(host) == item["host_sha256"],
                f"Full P4 reconstruction or digest differs for {i}")
        permutation = canonical_bijection(host, base)
        require(hashlib.sha256(bytes(permutation)).hexdigest()
                == item["canonical_map_sha256"],
                f"Full deterministic P4 map has changed for {i}")
        print(f"VERIFIED_P4_O12_LIFT {i}: P4=182 vertices/14298 edges,"
              " explicit 182-coordinate bijection checked on every pair",
              flush=True)
    print("PASS: three new K-divergent ten-vertex graphs proved by"
          " explicit exact P4 lifts of the previously certified O12 source;"
          " immutable ten-v23=1059 -> ten-v24=1056", flush=True)


if __name__ == "__main__":
    verify_archive()
