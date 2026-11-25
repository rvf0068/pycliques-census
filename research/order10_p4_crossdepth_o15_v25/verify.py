"""Four complete cross-depth P4 -> P3(McKay 260910) -> O15 certificates.

The positive proof reconstructs every ten-vertex original independently,
checks every coordinate of the archived 132-vertex isomorphisms, replays
all 7,880 edges of the previously certified nine-vertex O15 retraction,
and transports that complete projection to each P4 host.

This is a v24 -> v25 *positive* census promotion. It never concludes
convergence or divergence from failed bounded searches or mere equality
of order, size, fingerprints, or WL colors.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import sys

import networkx as nx

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses positive proof assertions")

from research.order9_260910_o15_v1.verify import (
    independently_reconstruct as historical_P3,
)
from research.order10_p4_cap_rescue_v24.verify import (
    p4_facets as independently_checked_facets,
    p4_from_graph6,
)

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PREVIOUS = ROOT / "indeterminate_order_10_v24.txt"
LATEST = ROOT / "indeterminate_order_10_v25.txt"
CURRENT = ROOT / "indeterminate_order_10.txt"
CERT = HERE / "certificates.json"
OLD_O15 = ROOT / "research/order9_260910_o15_v1/certificate.json"
P3_INDEX = ROOT / "research/order10_p3_global_v23_index/certificates.json"

# Fixed against the *merged* source histories, not copied from the mutable
# new proof certificate. All archived contents are checked independently.
V24_BLOB = "cf0ba2b44519b51565808fbe0b24d3c76c061666"
O15_BLOB = "8d97a9e8278cf67aa2c431fb2551b47547bf19f5"
P3_INDEX_BLOB = "ab5a9f1c075dfad63b111929368147884519f2a3"
HISTORICAL_P3_SHA = (
    "248ab6dc4e6bb9317ba2b271bb3e551bbdecae1e8111cf07beb8858a227513a6"
)
REMOVED = (11551790, 11552072, 11555600, 11707526)
SOURCE_G6 = {
    11551790: "IEhetr}|o",
    11552072: "IEhetvm~O",
    11555600: "IEhevi~~_",
    11707526: "IQyurzUuo",
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def git_blob(content: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(content)).encode("ascii") + b"\0" + content
    ).hexdigest()


def source_rows(path: Path) -> dict[int, str]:
    answer: dict[int, str] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        require(
            len(fields) == 6 and
            fields[1] in ("9", "10") and
            fields[-3:] == ["-", "-", "-"],
            "Malformed original census record",
        )
        index = int(fields[0])
        require(index not in answer, "Repeated McKay index")
        answer[index] = line
    require(list(answer) == sorted(answer), "Noncanonical McKay index order")
    return answer


def verify_index(cert: dict) -> None:
    """Independently derive all four deletions from the immutable v24."""
    require(git_blob(PREVIOUS.read_bytes()) == V24_BLOB,
            "Historical source ten-v24 Git blob changed")
    require(CURRENT.read_bytes() == LATEST.read_bytes(),
            "Current ten-vertex working root does not equal new v25")
    require(
        (ROOT / "indeterminate_order_9.txt").read_bytes() ==
        (ROOT / "indeterminate_order_9_v9.txt").read_bytes(),
        "Nine-vertex certified root changed",
    )
    before, after = source_rows(PREVIOUS), source_rows(LATEST)
    require(len(before) == 1056 and len(after) == 1052,
            "Wrong exact before/after original count")
    require(
        tuple(sorted(set(before) - set(after))) == REMOVED and
        all(after[index] == before[index] for index in after),
        "Changed a retained ten-v24 original or removed an unproved index",
    )
    for i in REMOVED:
        require(before[i] == f"{i} 10 {SOURCE_G6[i]} - - -",
                f"Wrong original index, graph6, or stiff core: {i}")
    require(
        tuple(sum(row.split()[1] == str(order) for row in before.values())
              for order in (9, 10)) == (430, 626) and
        tuple(sum(row.split()[1] == str(order) for row in after.values())
              for order in (9, 10)) == (430, 622),
        "The v25 transition altered nine-core dependents or wrong stiff count",
    )
    require(
        cert["schema"] == 1 and
        cert["kind"] ==
        "cross_depth_fourth_to_proven_divergent_nine_P3_O15_full_transport"
        and cert["from_snapshot"] == PREVIOUS.name
        and cert["from_git_blob"] == V24_BLOB
        and cert["to_snapshot"] == LATEST.name
        and cert["population"] == {
            "before": 1056, "after": 1052, "removed": 4,
            "unresolved_nine_pared": 430,
            "stiff_ten_before": 626, "stiff_ten_after": 622,
        },
        "Wrong new proof schema or population",
    )
    require(
        cert["global_P3_archive"] == P3_INDEX.relative_to(ROOT).as_posix()
        and cert["global_P3_git_blob"] == P3_INDEX_BLOB
        and git_blob(P3_INDEX.read_bytes()) == P3_INDEX_BLOB,
        "Historical P3 class proof provenance changed",
    )
    global_index = json.loads(P3_INDEX.read_text(encoding="utf-8"))
    source_class = [
        group for group in global_index["nontrivial_classes"]
        if group["representative"] == 11551790
    ]
    require(
        len(source_class) == 1 and
        [member["index"] for member in source_class[0]["members"]]
        == list(REMOVED) and source_class[0]["order"] == 21
        and source_class[0]["edges"] == 176,
        "The four sources do not form the certified P3 equivalence class",
    )


def canonical_pare(graph: nx.Graph) -> nx.Graph:
    """One vertex at a time, deterministic smallest-label fold."""
    graph = graph.copy()
    while True:
        closed = {u: set(graph[u]) | {u} for u in graph}
        victim = next(
            (u for u in sorted(graph)
             if any(u != v and closed[u] <= closed[v]
                    for v in graph)),
            None,
        )
        if victim is None:
            return nx.convert_node_labels_to_integers(
                graph, ordering="sorted"
            )
        graph.remove_node(victim)


def canonical_clique(graph: nx.Graph) -> nx.Graph:
    """Sorted facet mask labeling, explicitly crosschecked with bitset BK."""
    require(set(graph) == set(range(len(graph))),
            "Graph source requires canonical contiguous labels")
    facets = independently_checked_facets(graph)
    raw = nx.Graph()
    raw.add_nodes_from(range(len(facets)))
    raw.add_edges_from(
        (i, j) for i, first in enumerate(facets)
        for j in range(i+1, len(facets))
        if first & facets[j]
    )
    return raw


def canonical_stages(graph6: str) -> tuple[list[list[int]], nx.Graph]:
    graph = canonical_pare(nx.from_graph6_bytes(graph6.encode("ascii")))
    dimensions = [[len(graph), graph.number_of_edges()]]
    for step in range(1, 5):
        graph = canonical_pare(canonical_clique(graph))
        dimensions.append([len(graph), graph.number_of_edges()])
    return dimensions, graph


def host_sha(graph: nx.Graph) -> str:
    return hashlib.sha256(
        nx.to_graph6_bytes(graph, header=False).strip()
    ).hexdigest()


def verify_reference(cert: dict) -> tuple[nx.Graph, list[int], list[tuple[int, int]]]:
    require(
        cert["historical_O15_archive"] ==
        OLD_O15.relative_to(ROOT).as_posix() and
        cert["historical_O15_git_blob"] == O15_BLOB and
        git_blob(OLD_O15.read_bytes()) == O15_BLOB,
        "Historical complete O15 source proof Git blob was altered",
    )
    ref=cert["reference"]
    require(ref == {
        "index": 260910, "graph6": "HUZvvzu", "depth": 3,
        "pared_graph": [132, 7880],
        "labeled_host_sha256": HISTORICAL_P3_SHA,
        "retract_target": "O15",
    }, "Wrong certified nine-vertex reference and stage")
    historical = json.loads(OLD_O15.read_text(encoding="utf-8"))
    require(
        historical["schema"] == 1
        and historical["original_index"] == 260910
        and historical["source_graph6"] == "HUZvvzu"
        and historical["pared_depth"] == 3
        and historical["target_dimension"] == 15
        and historical["pared_graph6_sha256"] == HISTORICAL_P3_SHA,
        "Historical 260910 O15 positive certificate changed",
    )
    frozen = (ROOT / "indeterminate_order_9_v4.txt").read_text(encoding="ascii")
    require(any(row.startswith("260910 9 HUZvvzu ") for row in frozen.splitlines()),
            "Historical nine-v4 reference index or graph6 missing")
    reference = historical_P3()
    require([len(reference), reference.number_of_edges()] == [132, 7880]
            and host_sha(reference) == HISTORICAL_P3_SHA,
            "Historical 132-vertex P3 labeling or edges changed")
    images = list(base64.b64decode(historical["images_b64"], validate=True))
    pairs = [tuple(pair) for pair in historical["opposite_pairs"]]
    endpoints = [u for pair in pairs for u in pair]
    target = set(endpoints)
    require(
        len(images) == 132 and len(pairs) == 15
        and len(target) == 30 and set(images) == target
        and all(images[v] == v for v in target),
        "Historical complete O15 projection is invalid",
    )
    require(
        all(not reference.has_edge(u, v) for u, v in pairs)
        and all(reference.has_edge(u, v)
                for i, pair in enumerate(pairs)
                for later in pairs[i+1:]
                for u in pair for v in later),
        "Historical target is not the induced O15",
    )
    require(
        all(images[u] == images[v] or
            reference.has_edge(images[u], images[v])
            for u, v in reference.edges()),
        "Historical source retraction fails to preserve an edge",
    )
    return reference, images, pairs


def independent_p4_crosscheck(graph6: str, graph: nx.Graph) -> None:
    """Independent third/fourth iterates from merged PR #92 algorithms."""
    raw, pared, _, p3_dims = p4_from_graph6(graph6)
    require(p3_dims == (21, 176), "Independent source P3 dimensions differ")
    require(
        len(raw) == 132 and len(pared) == 132
        and sum(m.bit_count() for m in pared)//2 == 7880,
        "Independent P4 from the former-cap recovery gives a different graph",
    )
    other = nx.Graph()
    other.add_nodes_from(range(len(pared)))
    other.add_edges_from(
        (u, v) for u in range(len(pared))
        for v in range(u+1, len(pared)) if pared[u] & (1 << v)
    )
    m = nx.algorithms.isomorphism.GraphMatcher(
        nx.complement(graph), nx.complement(other)
    )
    require(m.is_isomorphic() and all(
        graph.has_edge(u, v) == other.has_edge(m.mapping[u], m.mapping[v])
        for u in graph for v in graph
    ), "Independent P4 algorithm or complete adjacency crosscheck disagrees")


def verify_positive(
    record: dict,
    reference: nx.Graph,
    images: list[int],
    pairs: list[tuple[int, int]],
) -> None:
    index = record["index"]
    require(
        index in SOURCE_G6 and record["graph6"] == SOURCE_G6[index]
        and record["target_dimension"] == 15
        and record["reference_p3_sha256"] == HISTORICAL_P3_SHA,
        "Wrong McKay source or target dimension in positive record",
    )
    stages, source = canonical_stages(record["graph6"])
    require(stages == record["stages"] and stages[-1] == [132, 7880]
            and host_sha(source) == record["pared_fourth_sha256"],
            f"Nonreproducible complete fourth clique iterate for {index}")
    independent_p4_crosscheck(record["graph6"], source)

    encoded = base64.b64decode(record["bijection_b64"], validate=True)
    require(
        len(encoded) == 132
        and hashlib.sha256(encoded).hexdigest() ==
            record["bijection_sha256"],
        f"Missing complete pinned 132-image isomorphism for {index}",
    )
    mapping = list(encoded)
    require(sorted(mapping) == list(range(132)),
            "Saved coordinate map is not a bijection")
    require(all(
        source.has_edge(u, v) ==
        reference.has_edge(mapping[u], mapping[v])
        for u in source for v in source),
        f"Complete 132-vertex P4-to-P3 isomorphism failed for {index}",
    )
    # Independently confirm the specific saved permutation with a
    # GraphMatcher using labels, on the sparse complement graphs.
    left, right = nx.complement(source), nx.complement(reference)
    nx.set_node_attributes(left, {u: u for u in left}, "proof_label")
    nx.set_node_attributes(
        right, {mapping[u]: u for u in source}, "proof_label",
    )
    matcher = nx.algorithms.isomorphism.GraphMatcher(
        left, right,
        node_match=lambda a, b: a["proof_label"] == b["proof_label"]
    )
    require(
        matcher.is_isomorphic() and
        matcher.mapping == {u: mapping[u] for u in source},
        "Independent complement-graph matcher rejects explicit map",
    )

    inverse = {v: u for u, v in enumerate(mapping)}
    transported_pairs = [
        (inverse[a], inverse[b]) for a, b in pairs
    ]
    target = {u for pair in transported_pairs for u in pair}
    retract = {u: inverse[images[mapping[u]]] for u in source}
    require(
        len(target) == 30 and set(retract.values()) == target
        and all(retract[u] == u for u in target),
        "Transported O15 projection is not a pointwise-fixed retraction",
    )
    require(all(
        not source.has_edge(a, b) for a, b in transported_pairs
    ) and all(
        source.has_edge(u, v)
        for i, pair in enumerate(transported_pairs)
        for next_pair in transported_pairs[i+1:]
        for u in pair for v in next_pair
    ), "Transported image is not an induced O15")
    require(all(
        retract[u] == retract[v] or
        source.has_edge(retract[u], retract[v])
        for u, v in source.edges()
    ), "Transported full ordinary retraction does not respect a host edge")
    print(
        f"CERTIFIED_DIVERGENCE_MCKAY_{index}: "
        "P4 original (132,7880) EXACTLY isomorphic to "
        "P3(McKay 260910); complete transported ordinary "
        "P4 -> O15 retraction independently verified",
        flush=True,
    )


def verify_archive() -> None:
    cert=json.loads(CERT.read_text(encoding="utf-8"))
    verify_index(cert)
    reference, images, pairs = verify_reference(cert)
    records = cert["positives"]
    require(
        [record["index"] for record in records] == list(REMOVED)
        and len(records) == 4,
        "Saved positive set does not equal the v25 deletion set",
    )
    for record in records:
        verify_positive(record, reference, images, pairs)
    print(
        "CERTIFIED ten-v24 -> ten-v25 exact positive promotion:"
        " four complete P4 -> P3(McKay 260910) isomorphisms and"
        " transported P4 -> O15 retractions; 1056 -> 1052"
        " ten-vertex originals, 430 nine-pared and 622 stiff;",
        flush=True,
    )


if __name__ == "__main__":
    verify_archive()
