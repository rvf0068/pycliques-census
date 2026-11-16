"""Independently verify three graph retractions onto the snub disphenoid.

The target is the induced 8-vertex subgraph G-{2}.  The retraction
maps 2 -> 1 and fixes all other vertices.  A graph morphism may send
adjacent vertices to adjacent or equal vertices, as in the clique-graph
literature. No inference of clique divergence is made.

    python scripts/verify_order9_snub_retractions.py
"""
from __future__ import annotations

import json
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
CERTS = ROOT / "reports/order9_snub_retractions_v1/certificates.json"
CROSSREF = ROOT / "reports/order10_core9_crossref_v1/matches.tsv"
CORE_INDEX = ROOT / "reports/order10_core_index_v1/classes.tsv"
ISO = ROOT / "runs/order10/core9-followup-v1/isomorphism.json"
STRUCTURE = ROOT / "runs/order10/core9-structure-v1/records"
EXPECTED = {232592: 4929602, 233586: 4972358, 244584: 5645085}
SNUB = "GQyuzw"


def decode(g6: str) -> nx.Graph:
    return nx.from_graph6_bytes(g6.encode("ascii"))


def verify_retraction_certificate(entry: dict, snub: nx.Graph) -> None:
    """Check the retraction and the explicit target-to-snub graph isomorphism."""
    graph = decode(entry["original_graph6"])
    if graph.number_of_nodes() != 9 or not nx.is_connected(graph):
        raise ValueError("The original graph must be connected of order nine")

    removed = entry["removed_vertex"]
    image = entry["image_vertex"]
    if (
        not isinstance(removed, int)
        or not isinstance(image, int)
        or removed == image
        or removed not in graph
        or image not in graph
    ):
        raise ValueError("The retraction's deleted vertex or image is invalid")
    target = graph.copy()
    target.remove_node(removed)
    if len(target) != 8:
        raise ValueError("Incorrect target order")

    # The explicitly recorded retraction fixes all target vertices.
    projection = {
        vertex: (image if vertex == removed else vertex) for vertex in graph
    }
    if set(projection.values()) != set(target):
        raise ValueError("The projection is not onto the claimed induced target")
    if any(projection[v] != v for v in target):
        raise ValueError("The projection does not fix its induced target")
    for u, v in graph.edges():
        if (
            projection[u] != projection[v]
            and not target.has_edge(projection[u], projection[v])
        ):
            raise ValueError(f"The proposed map is not a graph morphism on {u,v}")

    permutation = entry["induced_target_to_snub"]
    if (
        not isinstance(permutation, list)
        or len(permutation) != 9
        or permutation[removed] is not None
        or set(permutation[v] for v in target) != set(snub)
    ):
        raise ValueError("Invalid explicit target-to-snub bijection")
    if any(
        target.has_edge(u, v) != snub.has_edge(permutation[u], permutation[v])
        for u in target for v in target
    ):
        raise ValueError("Recorded target-to-snub map is not an isomorphism")

    # In these examples, the retraction is not the deletion of a
    # dominated vertex: the identified vertices are not adjacent.
    if graph.has_edge(removed, image):
        raise ValueError("These examples must use a nonadjacent identification")
    if not set(graph.neighbors(removed)).issubset(graph.neighbors(image)):
        raise ValueError("Open-neighborhood containment certificate is invalid")


def index_entries() -> dict[int, dict]:
    lines = CROSSREF.read_text(encoding="utf-8").splitlines()
    expected_columns = (
        "core_id", "core_graph6", "original_members", "order9_index",
        "order9_graph6", "historical_verdict", "first_positive_stage",
        "positive_rule", "positive_reason", "last_stage_examined",
        "order9_still_unresolved", "evidence_path",
    )
    if tuple(lines[0].split("\t")) != expected_columns:
        raise ValueError("Frozen cross-reference schema changed")
    entries: dict[int, dict] = {}
    for line in lines[1:]:
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) != len(expected_columns):
            raise ValueError("Malformed frozen cross-reference row")
        data = dict(zip(expected_columns, fields))
        i = int(data["order9_index"])
        if i in entries:
            raise ValueError(f"Duplicate order-nine index {i}")
        entries[i] = data
    return entries


def verify_all(certificates: dict) -> dict:
    if (
        certificates.get("schema") != 1
        or certificates.get("snub_graph6") != SNUB
        or certificates.get("source") != str(CROSSREF.relative_to(ROOT))
        or certificates.get("second_iterates") != str(ISO.relative_to(ROOT))
    ):
        raise ValueError("Retraction certificate metadata disagrees with frozen sources")
    entries = certificates.get("certificates")
    if not isinstance(entries, list) or len(entries) != 3:
        raise ValueError("Exactly three order-nine retractions are required")
    crossref = index_entries()
    snub = decode(SNUB)
    if (len(snub), snub.number_of_edges()) != (8, 18):
        raise ValueError("Wrong snub disphenoid reference graph")
    if not any(
        fields[:3] == ["2317572", "8", SNUB]
        for line in CORE_INDEX.read_text(encoding="utf-8").splitlines()[1:]
        if (fields := line.split("\t"))
    ):
        raise ValueError("Snub disphenoid is not the reference in the committed core index")

    found: set[int] = set()
    for entry in entries:
        i = entry["order9_index"]
        if i in found or EXPECTED.get(i) != entry["core_id"]:
            raise ValueError("Duplicate or unexpected graph index")
        found.add(i)
        source = crossref[i]
        if (
            int(source["core_id"]) != entry["core_id"]
            or int(source["original_members"]) != entry["original_members"]
            or source["order9_graph6"] != entry["original_graph6"]
            or source["core_graph6"] != entry["core_graph6"]
            or source["historical_verdict"] != "INDETERMINATE"
        ):
            raise ValueError(f"Original graph does not match frozen census index {i}")
        verify_retraction_certificate(entry, snub)

    if found != set(EXPECTED):
        raise ValueError("Missing required nine-vertex graph")

    # Cross-check the separately verified equality of the second iterates.
    # This confirms the mathematical remark in the accompanying report,
    # rather than assuming isomorphism just from a hash/fingerprint.
    saved = json.loads(ISO.read_text(encoding="utf-8"))
    if (
        saved.get("iterate_index") != 2
        or saved.get("left_core") != 4929602
        or {record["right_core"] for record in saved["comparisons"]}
            != {4972358, 5645085}
    ):
        raise ValueError("Unexpected saved G2 comparison cohort")
    left = decode(json.loads(
        (STRUCTURE / "04929602.json").read_text(encoding="utf-8")
    )["iterates"][2]["graph6"])
    for comparison in saved["comparisons"]:
        right_id = comparison["right_core"]
        right = decode(json.loads(
            (STRUCTURE / f"{right_id:08d}.json").read_text(encoding="utf-8")
        )["iterates"][2]["graph6"])
        mapping = comparison.get("mapping")
        if (
            comparison.get("isomorphic") is not True
            or not isinstance(mapping, list)
            or len(mapping) != len(left)
            or set(mapping) != set(right)
            or any(
                left.has_edge(u, v) != right.has_edge(mapping[u], mapping[v])
                for u in left for v in left
            )
        ):
            raise ValueError(f"G2 certificate failed replay for core {right_id}")

    return {
        "retractions_checked": len(entries),
        "snub_graph6": SNUB,
        "order9_indices": sorted(found),
        "core_ids": sorted(EXPECTED.values()),
        "verified_g2_isomorphism_pairs": 2,
        "original_ten_vertex_members_represented": sum(
            entry["original_members"] for entry in entries
        ),
    }


def main() -> None:
    report = verify_all(json.loads(CERTS.read_text(encoding="utf-8")))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
