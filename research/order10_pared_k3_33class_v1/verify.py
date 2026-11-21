#!/usr/bin/env python3
"""Exact McKay-indexed 33-member common pared K³ isomorphism certificate.

Full graph-isomorphism bijections are checked on every pair, not inferred
from the WL fingerprint. Two distinct maximal-clique algorithms independently
reconstruct the iterates. No change to the census K-behavior verdicts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "indeterminate_order_10_v10.txt"
SOURCE_BLOB = "35acbd4efbe6fd6816ff0b5c749b8b20b4455d1e"
MCKAY = (
    7002338, 7030796, 7031264, 7064223, 7499920, 7509538,
    7510278, 7510456, 7957279, 9825078, 9989894, 10223405,
    10291196, 10298597, 10301482, 10302853, 10437931, 10582804,
    11248724, 11250419, 11273494, 11283020, 11319041, 11424291,
    11495896, 11548017, 11549318, 11551459, 11554628, 11567352,
    11576268, 11588567, 11598573,
)
EXPECTED_P3 = (37, 503)


def require(truth: bool, what: str) -> None:
    if not truth:
        raise ValueError(what)


def cohort() -> dict[int, str]:
    raw = SOURCE.read_bytes()
    sha = hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()
    require(sha == SOURCE_BLOB, "Source McKay-10 v10 archive changed")
    data = {}
    for line in raw.decode().splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        require(len(parts) == 6, "Malformed source row")
        if int(parts[0]) in MCKAY:
            i = int(parts[0])
            require(i not in data, "Duplicated original McKay index")
            require(parts[1] == "10" and parts[3:] == ["-", "-", "-"],
                    "One source was already classified or not stiff")
            data[i] = parts[2]
    require(len(data) == 33 and len(set(MCKAY)) == 33,
            "Incomplete or duplicate McKay class")
    return data


def bits(mask: int):
    while mask:
        b = mask & -mask
        yield b.bit_length()-1
        mask ^= b


def bk_cliques(g: nx.Graph) -> list[int]:
    """Independent integer-bitset Bron–Kerbosch maximal cliques."""
    n = len(g)
    require(set(g) == set(range(n)), "Noncanonical graph labels")
    neighbors = [sum(1 << j for j in g[i]) for i in range(n)]
    found = []

    def rec(r: int, p: int, x: int) -> None:
        if not (p | x):
            found.append(r)
            return
        pivot = max(bits(p | x), key=lambda u: (p & neighbors[u]).bit_count())
        for v in list(bits(p & ~neighbors[pivot])):
            b = 1 << v
            rec(r | b, p & neighbors[v], x & neighbors[v])
            p &= ~b
            x |= b

    rec(0, (1 << n) - 1, 0)
    return sorted(found)


def clique_graph(g: nx.Graph) -> nx.Graph:
    expected = bk_cliques(g)
    actual = sorted(sum(1 << v for v in q) for q in nx.find_cliques(g))
    require(expected == actual, "Independent maximal-clique algorithms disagree")
    h = nx.Graph()
    h.add_nodes_from(range(len(expected)))
    h.add_edges_from((i,j) for i,j in combinations(range(len(expected)),2)
                     if expected[i] & expected[j])
    return h


def pare(g: nx.Graph) -> tuple[nx.Graph, list[list[int]], list[int]]:
    h = g.copy()
    steps = []
    while True:
        neighborhoods = {v: set(h[v]) | {v} for v in h}
        pair = next(
            ((u,v) for u in sorted(h) for v in sorted(h)
             if u != v and neighborhoods[u] <= neighborhoods[v]),
            None,
        )
        if pair is None:
            break
        steps.append([int(pair[0]), int(pair[1])])
        h.remove_node(pair[0])
    labels = sorted(h)
    h = nx.convert_node_labels_to_integers(h, ordering="sorted")
    for u in h:
        for v in h:
            require(u == v or not ((set(h[u]) | {u}) <= (set(h[v]) | {v})),
                    "A dominated vertex remained after complete paring")
    return h, steps, labels


def reconstruct(graph6: str):
    g = nx.from_graph6_bytes(graph6.encode("ascii"))
    require(len(g) == 10 and nx.is_connected(g), "Not a ten-vertex connected graph")
    record = []
    for level in range(4):
        before = [len(g), g.number_of_edges()]
        g, folds, retained = pare(g)
        require(level != 0 or not folds, "Original McKay core was not stiff")
        record.append({"level": level, "raw": before,
                       "pared": [len(g), g.number_of_edges()],
                       "folds": folds, "retained": retained})
        if level < 3:
            g = clique_graph(g)
    require((len(g),g.number_of_edges()) == EXPECTED_P3,
            "Unexpected pared third-iterate size")
    return g, record


def exact_isomorphism(a: nx.Graph,b: nx.Graph) -> list[int]:
    gm = nx.algorithms.isomorphism.GraphMatcher(a,b)
    witness = next(gm.isomorphisms_iter(), None)
    require(witness is not None, "Claimed isomorphism does not exist")
    pi = [int(witness[i]) for i in range(len(a))]
    check_bijection(a,b,pi)
    return pi


def check_bijection(a: nx.Graph,b: nx.Graph,pi: list[int]) -> None:
    require(len(pi) == len(a) == len(b), "Map is incomplete")
    require(sorted(pi) == list(range(len(b))), "Map is not a bijection")
    require(all(
        a.has_edge(u,v) == b.has_edge(pi[u], pi[v])
        for u,v in combinations(range(len(a)),2)
    ), "Map fails an edge or a nonedge")


def certificate() -> dict:
    sources = cohort()
    rep, rep_stages = reconstruct(sources[MCKAY[0]])
    members = []
    for index in MCKAY:
        g6 = sources[index]
        g, stages = reconstruct(g6)
        pi = exact_isomorphism(g,rep)
        members.append({
            "mckay_index": index, "graph6": g6,
            "third_iterate": stages[-1]["pared"],
            "stages": stages, "to_representative": pi
        })
    require(len(members) == 33, "Missing source graph")
    return {"schema":1, "source_blob_sha1": SOURCE_BLOB,
            "representative_mckay_index": MCKAY[0],
            "representative_stages": rep_stages,
            "class_size":33, "members": members}


def verify(saved: dict) -> None:
    require(saved == certificate(), "Saved certificate differs from computed maps")
    rep, _ = reconstruct(cohort()[MCKAY[0]])
    for member in saved["members"]:
        g,_ = reconstruct(member["graph6"])
        check_bijection(g, rep, member["to_representative"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", type=Path)
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    cert = certificate()
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(json.dumps(cert,indent=2,sort_keys=True)+"\n")
    if args.verify:
        verify(json.loads(args.verify.read_text()))
    if args.self_test:
        changed = json.loads(json.dumps(cert))
        changed["members"][1]["to_representative"][0] = -1
        try:
            verify(changed)
        except ValueError:
            pass
        else:
            raise AssertionError("Tampered map survived independent verification")
    print("VERIFIED_JSON "+json.dumps({
        "representative":MCKAY[0],
        "isomorphic_original_McKay_indices": list(MCKAY),
        "pared_K3_vertices":37,"pared_K3_edges":503,
        "originals_in_unclassified_v10":len(MCKAY),
        "new_K_divergence_classifications":0
    },sort_keys=True))


if __name__ == "__main__":
    main()
