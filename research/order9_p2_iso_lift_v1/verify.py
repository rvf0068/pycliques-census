"""Independently audit v3 -> v4 (order 9) and v13 -> v14 (order 10).

This script does not call any ILP or retraction finder. It verifies
archived complete O12 proof via the historical dedicated verifier,
recomputes every exact P2-isomorphism lift using pycliques, and
independently reconstructs the base P2 isomorphism with NetworkX.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import networkx as nx

from research.order9_p2_iso_lift_v1 import screen
from research.order10_fourth_oct_v1.verify_o12 import verify_cert

ROOT = Path(__file__).resolve().parents[2]
CERT = Path(__file__).with_name("certificate.json")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def independent_pare(graph: nx.Graph) -> nx.Graph:
    host = graph.copy()
    while True:
        ns = {v: set(host[v]) | {v} for v in host}
        witness = next(
            (v for v in host if any(v != w and ns[v] <= ns[w] for w in host)),
            None,
        )
        if witness is None:
            return nx.convert_node_labels_to_integers(host)
        host.remove_node(witness)


def independent_clique_graph(graph: nx.Graph) -> nx.Graph:
    facets = [frozenset(q) for q in nx.find_cliques(graph)]
    host = nx.Graph()
    host.add_nodes_from(range(len(facets)))
    for i, qi in enumerate(facets):
        for j in range(i + 1, len(facets)):
            if qi.intersection(facets[j]):
                host.add_edge(i, j)
    return host


def independent_p2(graph6: str) -> nx.Graph:
    host = independent_pare(nx.from_graph6_bytes(graph6.encode()))
    for _ in range(2):
        host = independent_pare(independent_clique_graph(host))
    return host


def rows(path: Path) -> list[str]:
    return [line for line in path.read_text().splitlines()
            if line and not line.startswith("#")]


def verify() -> None:
    data = json.loads(CERT.read_text())
    check(data["schema"] == 1, "Wrong certificate schema")
    check(data["source_order9_blob"] == screen.NINE_V3_BLOB,
          "Wrong frozen order-nine digest")
    check(data["source_order10_blob"] == screen.V13_BLOB,
          "Wrong frozen order-ten digest")
    check(data["removed_order9"] == [248936], "Wrong nine-vertex deletion")
    removed = data["removed_order10"]
    check(len(removed) == 219 and removed == sorted(set(removed)),
          "Wrong number or order of ten-vertex positive sources")

    # Replay the archived complete, positive O12 retraction independently of
    # the ILP search. Reconstruct P4 and check all 14,298 source edges.
    archived = json.loads(
        (ROOT / "research/order10_fourth_oct_v1/o12_certificates.json").read_text()
    )
    ten = next(x for x in archived["proofs"] if x["index"] == 10223405)
    verify_cert(ten)

    a = independent_p2(screen.NINE_GRAPH6)
    b = independent_p2(screen.TEN_GRAPH6)
    check((len(a), a.number_of_edges()) == (19, 117),
          "Incorrect independent nine-vertex second iterate")
    check((len(b), b.number_of_edges()) == (19, 117),
          "Incorrect independent ten-vertex second iterate")
    check(nx.is_isomorphic(nx.complement(a), nx.complement(b)),
          "No independent base P2 isomorphism")
    # Independently re-check the pycliques-generated base isomorphism and
    # the full pointwise adjacency relation of the saved coordinates.
    aa = screen.second_pared_iterate(screen.NINE_GRAPH6)
    bb = screen.second_pared_iterate(screen.TEN_GRAPH6)
    check(aa is not None and bb is not None, "Missing pycliques P2")
    check(screen.full_isomorphism(aa, bb) is not None,
          "No public-pycliques P2 isomorphism")
    mapping = data["pared_second_iterate"]["nine_to_ten_isomorphism_on_pycliques_labels"]
    check(len(mapping) == 19 and set(mapping) == set(range(19)),
          "Incomplete base mapping")
    # Labels are reproducible for the pinned Python/NetworkX/pycliques
    # environment used by CI and PYTHONHASHSEED=0.
    check(all(aa.has_edge(i, j) == bb.has_edge(mapping[i], mapping[j])
              for i in range(19) for j in range(19)),
          "Saved base mapping is not edge/nonedge preserving")

    expected = screen.search()
    check(expected["positive_indices"] == removed,
          "Complete full-index independent P2 screen disagrees with certificate")
    check(expected["distinct_matching_pared_graph6"] ==
          sorted(set(r.split()[2] for r in data["removed_order10_rows"])),
          "Distinct positively matched source encodings differ")
    initial10 = rows(screen.V13)
    initial9 = rows(screen.NINE_V3)
    updated10 = rows(ROOT / "indeterminate_order_10_v14.txt")
    updated9 = rows(ROOT / "indeterminate_order_9_v4.txt")
    check((len(initial9), len(updated9)) == (13, 12),
          "Incorrect order-nine census counts")
    check((len(initial10), len(updated10)) == (2787, 2568),
          "Incorrect order-ten census counts")
    check((ROOT / "indeterminate_order_9.txt").read_bytes() ==
          (ROOT / "indeterminate_order_9_v4.txt").read_bytes(),
          "Authoritative order-nine root is not v4")
    check((ROOT / "indeterminate_order_10.txt").read_bytes() ==
          (ROOT / "indeterminate_order_10_v14.txt").read_bytes(),
          "Authoritative order-ten root is not v14")
    check(set(initial9) - set(updated9) == {
          row for row in initial9 if row.startswith("248936 ")},
          "Unexpected order-nine deletion")
    check(set(updated9).issubset(set(initial9)),
          "An order-nine row was added or altered")
    index_to_row = {int(row.split()[0]): row for row in initial10}
    expected_removed = {index_to_row[index] for index in removed}
    check(set(initial10) - set(updated10) == expected_removed,
          "Unexpected ten-vertex deletion")
    check(set(updated10).issubset(set(initial10)),
          "A ten-vertex row was added or altered")
    check(data["removed_order10_rows"] == [
          index_to_row[index] for index in removed],
          "Stored original graph identities differ")
    check(all(row.split()[1] == "9" and row.split()[4] == "-"
              for row in expected_removed),
          "A conditional or stiff ten-vertex case was improperly promoted")
    check(sum(row.split()[4] == "conjectured_divergent"
              for row in updated10) == 120,
          "Previously conditional status was altered")
    print("CERTIFIED_ORDER9_V4 13->12 removed=[248936]")
    print("CERTIFIED_ORDER10_V14 2787->2568 removed_positives=219")
    print("CERTIFIED_ALL_219_FULL_P2_ISOMORPHISM_REPLAYS")


if __name__ == "__main__":
    verify()
