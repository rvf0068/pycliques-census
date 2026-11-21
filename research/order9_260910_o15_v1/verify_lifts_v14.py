"""Independently replay new 260910-based divergences without trusting search.

Read complete saved reference isomorphisms, ordinary retractions, and
second-pared-iterate isomorphisms. For each candidate check every edge
(and every nonedge for isomorphism), verify the frozen original graph6,
and replay the independently verified O15 source proof.

Optional --full reruns the complete pinned-public-pycliques 2568-row
source scan and insists that the saved positive cohort is exact, with
no bound or error omissions. This never changes census indexes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import networkx as nx
import pycliques

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
CERT = Path(__file__).with_name("lift_v14_certificate.json")
V14 = ROOT / "indeterminate_order_10_v14.txt"
SOURCE_BLOB = "3ee92e02891b3046059241d4a2304794b0e34380"
PR63_MATCHES = {
    9696790, 9784367, 10030716, 10374306, 10375764, 10494971,
    10496278, 10585242, 10625349, 11267123, 11267623, 11268005,
    11292105, 11411161, 11416793, 11495314, 11496350, 11497535,
    11599615, 11606773, 11608187, 11608188, 11609491, 11612099,
    11634539, 11638625, 11698302,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def exact_iso_check(
    graph: nx.Graph, target: nx.Graph, mapping: dict,
    label: str,
) -> None:
    require(set(mapping) == set(graph) and set(mapping.values()) == set(target),
            f"Incomplete/duplicate map in {label}")
    require(all(
        graph.has_edge(u, v) == target.has_edge(mapping[u], mapping[v])
        for u in graph for v in graph
    ), f"Isomorphism not adjacency/nonadjacency preserving in {label}")


def map_lists(items) -> dict[int, int]:
    result = dict(items)
    require(len(result) == len(items) and all(
        type(k) is int and type(v) is int for k, v in items
    ), "Duplicate or noninteger map entries")
    return result


def verify(*, full: bool = False) -> None:
    from research.order9_260910_o15_v1.verify import (
        verify as independently_replay_o15,
    )
    from research.order9_f45_o9_v1.verify import (
        independent_clique_graph, independent_pare,
    )

    independently_replay_o15()

    v14 = V14.read_bytes()
    require(git_blob(v14) == SOURCE_BLOB, "Frozen v14 index changed")
    rows = {}
    for line in v14.decode("utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        require(len(fields) == 6, "Malformed v14 row")
        n = int(fields[0])
        require(n not in rows, "Duplicate v14 original index")
        rows[n] = fields
    require(len(rows) == 2568 and list(rows) == sorted(rows),
            "Incorrect v14 source cohort")

    proof = json.loads(CERT.read_text())
    require(proof["schema"] == 1 and proof["reference_original_index"] == 260910,
            "Invalid certificate metadata")
    require(proof["reference_g6"] == "HUZvvzu",
            "Wrong divergent reference graph")
    require(proof["source_v14_git_blob"] == SOURCE_BLOB,
            "Certificate source digest differs")
    positive = proof["positive"]
    ids = [x["index"] for x in positive]
    require(ids == sorted(set(ids)) and len(ids) == 80,
            "Expected exactly 80 unique ordered positive McKay indices")
    require(set(ids).isdisjoint(PR63_MATCHES),
            "Positive source overlaps prior PR63 v15 deletions")
    require(Counter(x["kind"] for x in positive) ==
            Counter({"reference": 62, "retraction": 14, "P2_iso": 4}),
            "Incorrect positive mechanism counts")

    reference = nx.from_graph6_bytes(b"HUZvvzu")
    public_p2_reference = None
    independent_p2_reference = None
    for item in positive:
        index = item["index"]
        require(index in rows, f"McKay {index} absent from v14")
        row = rows[index]
        require(row[3:] == ["-", "-", "-"],
                f"Claim for {index} improperly conditional")
        require(item["source_g6"] == row[2] and item["source_order"] == int(row[1]),
                f"Wrong original source identity for {index}")
        graph = nx.from_graph6_bytes(item["source_g6"].encode("ascii"))
        require(len(graph) == item["source_order"],
                f"Corrupt source graph at {index}")
        kind = item["kind"]
        if kind == "reference":
            exact_iso_check(graph, reference,
                            map_lists(item["map"]), str(index))
        elif kind == "retraction":
            r = map_lists(item["projection"])
            i = map_lists(item["inclusion"])
            require(set(r) == set(graph) and set(r.values()) <= set(reference),
                    f"Non-total or out-of-target projection {index}")
            require(set(i) == set(reference) and
                    len(set(i.values())) == len(reference),
                    f"Noninjective inclusion {index}")
            require(all(r[i[u]] == u for u in reference),
                    f"Projection doesn't retract {index}")
            require(all(
                graph.has_edge(i[u], i[v]) == reference.has_edge(u, v)
                for u in reference for v in reference
            ), f"Noninduced target inclusion {index}")
            require(all(
                r[u] == r[v] or reference.has_edge(r[u], r[v])
                for u, v in graph.edges()
            ), f"Projection is not a graph morphism {index}")
            require(pycliques.verify_retraction_witness(
                graph, reference, (r, i)
            ), f"Public pycliques rejects retraction {index}")
        elif kind == "P2_iso":
            def p2(g: nx.Graph, *, public: bool) -> nx.Graph:
                if public:
                    h = pycliques.completely_pared_graph(g)
                    for _ in range(2):
                        h = pycliques.clique_graph(h)
                        require(h is not None, "Unexpected K2 build limit")
                        h = pycliques.completely_pared_graph(h)
                else:
                    h = independent_pare(g)
                    for _ in range(2):
                        h = independent_pare(independent_clique_graph(h))
                return nx.convert_node_labels_to_integers(h)

            if public_p2_reference is None:
                public_p2_reference = p2(reference, public=True)
                independent_p2_reference = p2(reference, public=False)
                require(nx.is_isomorphic(
                    public_p2_reference, independent_p2_reference
                ), "Independent and public reference P2 disagree")
            public_source = p2(graph, public=True)
            independent_source = p2(graph, public=False)
            require(nx.is_isomorphic(public_source, independent_source),
                    f"Independent source P2 reconstruction disagrees at {index}")
            require(
                (len(public_source), public_source.number_of_edges()) ==
                (item["p2_order"], item["p2_edges"]),
                f"P2 size/edge mismatch {index}"
            )
            exact_iso_check(public_source, public_p2_reference,
                            map_lists(item["map"]), str(index))
        else:
            raise AssertionError(f"Unknown proof mechanism {kind} on {index}")
        print("CERTIFIED", index, kind, flush=True)

    if full:
        scanner = ROOT / "research/order9_260910_o15_v1/lift_v14_screen.py"
        with tempfile.TemporaryDirectory() as temp:
            found = []
            checked = 0
            skipped = []
            for shard in range(8):
                out = Path(temp) / f"shard{shard}.json"
                subprocess.run([
                    sys.executable, str(scanner),
                    "--shards", "8", "--shard", str(shard),
                    "--output", str(out)
                ], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
                result = json.loads(out.read_text())
                require(result["shard"] == shard and result["shards"] == 8,
                        "Wrong shard metadata")
                checked += result["processed"]
                found.extend(result["positive"])
                skipped.extend(result["skipped_P2_bound"])
            require(checked == 2568 and not skipped,
                    "The full exact P2 scan was incomplete")
            found.sort(key=lambda x: x["index"])
            require(found == positive,
                    "Full public-pycliques scan differs from saved proof maps")
            print("FULL_2568_SOURCE_POSITIVE_SET_VERIFIED")

    print("CERTIFIED_80_NEW_ORDER10_DIVERGENCES 62 reference 14 retracts 4 P2")
    print("SOURCE_MCKAY_260910_O15_PROOF_REPLAYED")
    print("NO_OVERLAP_WITH_PR63_V15_OR_F45_CONDITIONAL_COHORT")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    verify(full=args.full)
