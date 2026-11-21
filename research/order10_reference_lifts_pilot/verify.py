"""Independently replay 27 new P2-isomorphism K-divergence certificates.

The saved mappings are between independently reconstructed, sequentially
pared and relabeled NetworkX clique iterates; each is checked against every
ordered vertex pair (edges *and* nonedges). Optional --public checks the
same graphs by the pinned public pycliques algorithm, and --full reruns
the entire 2,568-source positive-only screen with no P2 cutoff.

All prior snapshots and source-retraction certificates remain immutable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
CERT = Path(__file__).with_name("certificate.json")
OLD = ROOT / "indeterminate_order_10_v14.txt"
NEW = ROOT / "indeterminate_order_10_v15.txt"
CURRENT = ROOT / "indeterminate_order_10.txt"
V14_BLOB = "3ee92e02891b3046059241d4a2304794b0e34380"


def check(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def rows(raw: bytes) -> dict[int, list[str]]:
    out = {}
    for line in raw.decode("utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        check(len(fields) == 6, "Unexpected six-column census record")
        index = int(fields[0])
        check(index not in out, "Duplicate census McKay index")
        out[index] = fields
    check(list(out) == sorted(out), "Census indices not ordered")
    return out


def independent_pare(graph: nx.Graph) -> nx.Graph:
    host = graph.copy()
    while True:
        neighborhoods = {v: set(host[v]) | {v} for v in host}
        dominated = next(
            (v for v in host
             if any(v != w and neighborhoods[v] <= neighborhoods[w] for w in host)),
            None,
        )
        if dominated is None:
            return nx.convert_node_labels_to_integers(host)
        host.remove_node(dominated)


def independent_clique_graph(graph: nx.Graph) -> nx.Graph:
    maximal = [frozenset(clique) for clique in nx.find_cliques(graph)]
    out = nx.Graph()
    out.add_nodes_from(range(len(maximal)))
    out.add_edges_from(
        (i, j) for i, a in enumerate(maximal)
        for j in range(i + 1, len(maximal))
        if a.intersection(maximal[j])
    )
    return out


def independent_p2(graph6: str) -> nx.Graph:
    graph = independent_pare(nx.from_graph6_bytes(graph6.encode("ascii")))
    for _ in range(2):
        graph = independent_pare(independent_clique_graph(graph))
    return graph


def check_reference_sources() -> None:
    snub = nx.from_graph6_bytes(b"GQyuzw")
    suspension = nx.from_graph6_bytes(b"HUzrv~}")
    check((len(snub), snub.number_of_edges()) == (8, 18),
          "Wrong snub reference")
    check((len(suspension), suspension.number_of_edges()) == (9, 28),
          "Wrong historical suspension reference")
    historical = rows((ROOT / "indeterminate_order_9_v2.txt").read_bytes())
    later = rows((ROOT / "indeterminate_order_9_v3.txt").read_bytes())
    check(historical[180476][2] == "GQyuzw" and 180476 not in later,
          "Snub source is not the certified v3 removal")
    base = suspension.subgraph(range(7))
    check(nx.is_isomorphic(base, nx.complement(nx.cycle_graph(7))),
          "Suspension base is not the complement of C7")
    check(not suspension.has_edge(7, 8) and
          all(suspension.has_edge(v, p)
              for v in range(7) for p in (7, 8)),
          "Wrong suspension pole adjacencies")
    # Independently check the explicit cyclic coaffination used by the
    # archived historical divergence certificate for HUzrv~}.
    phi = {v: (v + 1) % 7 for v in range(7)}
    check(
        all(not base.has_edge(v, phi[v]) for v in base)
        and all(base.has_edge(u, v) == base.has_edge(phi[u], phi[v])
                for u in base for v in base),
        "Historical C7-complement coaffination fails",
    )


def verify(*, full: bool = False, public: bool = False) -> None:
    raw_old = OLD.read_bytes()
    check(git_blob(raw_old) == V14_BLOB, "Frozen v14 input changed")
    raw_new = NEW.read_bytes()
    check(raw_new == CURRENT.read_bytes(), "Authoritative root must equal v15")
    old, new = rows(raw_old), rows(raw_new)
    data = json.loads(CERT.read_text(encoding="utf-8"))
    check(data["schema"] == 1 and data["source_version"] == "v14",
          "Unexpected certificate version")
    check(data["snub_reference"] == "GQyuzw", "Wrong snub reference")
    check(data["suspension_reference"] == "HUzrv~}", "Wrong suspension reference")
    certificates = data["positive"]
    indices = [row["index"] for row in certificates]
    check(indices == sorted(set(indices)) and len(indices) == 27,
          "Incorrect or duplicated 27-member positive cohort")
    check(sum(row["reference"] == "snub" for row in certificates) == 26
          and sum(row["reference"] == "suspension" for row in certificates) == 1,
          "Incorrect 26 + 1 reference partition")
    check((len(old), len(new)) == (2568, 2541),
          "Unexpected v14 or v15 population")
    check(set(old) - set(new) == set(indices), "Deletion cohort differs")
    check(all(old[i] == row for i, row in new.items()),
          "An existing census record was modified")
    check(all(old[i][1] == "10" and old[i][3:] == ["-", "-", "-"]
              for i in indices),
          "Only unconditional stiff ten-vertex rows may be promoted")
    check(sum(row[4] == "conjectured_divergent" for row in new.values()) == 120,
          "The 120 conditional records must be preserved")
    check_reference_sources()

    reference = {
        "snub": independent_p2(data["snub_reference"]),
        "suspension": independent_p2(data["suspension_reference"]),
    }
    check(
        (len(reference["snub"]), reference["snub"].number_of_edges()) == (20, 136),
        "Unexpected P2 snub signature",
    )
    check(
        (len(reference["suspension"]),
         reference["suspension"].number_of_edges()) == (51, 1176),
        "Unexpected P2 suspension signature",
    )

    for item in certificates:
        i = item["index"]
        graph6 = old[i][2]
        check(item["source_pared_g6"] == graph6,
              f"Changed original/paired graph6 for McKay {i}")
        candidate = independent_p2(graph6)
        target = reference[item["reference"]]
        check(
            (len(candidate), candidate.number_of_edges()) ==
            (item["p2_order"], item["p2_edges"]),
            f"Incorrect independent P2 signature for {i}",
        )
        coordinates = item["p2_iso"]
        check(
            len(coordinates) == len(candidate) == len(target)
            and set(coordinates) == set(range(len(target))),
            f"Incomplete P2 isomorphism map for {i}",
        )
        check(
            all(candidate.has_edge(u, v) ==
                target.has_edge(coordinates[u], coordinates[v])
                for u in candidate for v in candidate),
            f"Saved P2 isomorphism fails a vertex-pair check for {i}",
        )
        if public:
            import pycliques

            graph = pycliques.completely_pared_graph(
                nx.from_graph6_bytes(graph6.encode("ascii"))
            )
            for _ in range(2):
                graph = pycliques.clique_graph(graph)
                check(graph is not None, f"Public pycliques K undefined: {i}")
                graph = pycliques.completely_pared_graph(graph)
            check(nx.is_isomorphic(graph, candidate),
                  f"Public pycliques and independent P2 disagree: {i}")

    if full:
        from research.order10_reference_lifts_pilot import screen

        found = []
        total = 0
        incomplete = 0
        for shard in range(8):
            # Unbounded P2 construction: no dropped source OR reference is
            # permitted in a complete positive-cohort certificate.
            result = screen.scan(shard, 8, 2, None)
            found.extend(row["index"] for row in result["positive"])
            total += result["processed_original_indices"]
            incomplete += result["bound_exhausted_distinct_core_graph6"]
            check(not result["exceptions"], f"Search exceptions in shard {shard}")
        check(total == 2568 and incomplete == 0,
              "The full second-iterate scan must cover all 2568 sources")
        check(sorted(found) == indices, "Full scan and saved positives disagree")

    print("CERTIFIED_ORDER10_V15 2568->2541 removed_27")
    print("CERTIFIED_27_EXACT_P2_MAPS SNUB=26 SUSPENSION=1")
    print("PRESERVED_120_CONDITIONAL_CASES")
    if public:
        print("PUBLIC_PYCLIQUES_P2_RECONSTRUCTION_PASS")
    if full:
        print("FULL_2568_SOURCE_SCAN_EXACTLY_27_POSITIVES")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--public", action="store_true")
    args = parser.parse_args()
    verify(full=args.full, public=args.public)
