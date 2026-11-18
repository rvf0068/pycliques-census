"""Exhaust all direct snub retracts among 29 unresolved stiff nine-vertex cores.

A retraction onto the eight-vertex snub S must fix one induced G-v and
send v to one of the eight remaining vertices. Check all 9*8 possibilities
with the exact clique-literature graph-morphism condition (images of
adjacent vertices adjacent OR equal). Check all 9 induced deletion
graphs for isomorphism to S; never infer divergence from a retraction.

Additionally check all 29 second COMPLETELY PARED K iterates against the
second completely pared clique iterate of S. An isomorphism is a proof
of identical K-behavior (via the dominated-vertex theorem); it is not
a proof that either graph is divergent.

All historical inputs and classifications remain immutable.
"""
from __future__ import annotations

import argparse
import csv
from io import StringIO
import hashlib
import json
import os
from pathlib import Path
import tempfile

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports/order10_core9_crossref_v1/unclassified.tsv"
XREF_MANIFEST = ROOT / "reports/order10_core9_crossref_v1/manifest.json"
CLASSES = ROOT / "reports/order10_core_index_v1/classes.tsv"
CORE_MANIFEST = ROOT / "reports/order10_core_index_v1/manifest.json"
V4 = ROOT / "indeterminate_order_10_v4.txt"
OLD_CERTS = ROOT / "reports/order9_snub_retractions_v1/certificates.json"
OUTPUT = ROOT / "reports/order9_snub_retractions_v2"
SNUB_G6 = "GQyuzw"
ORIGINAL_THREE = {4929602, 4972358, 5645085}
EXPECTED_RETRACTS = {
    2317843, 3148541, 3505942, 4929602, 4952669,
    4953338, 4972358, 5601875, 5645085,
}
EXPECTED_K2_EQUIVALENCE = ORIGINAL_THREE
EXPECTED_INDUCED_ONLY = {
    5418647, 6938156, 6957324, 6974529, 7315343, 7316198,
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(StringIO(path.read_text(encoding="utf-8")), delimiter="\t"))


def decode(g6: str) -> nx.Graph:
    graph = nx.from_graph6_bytes(g6.encode("ascii"))
    return nx.convert_node_labels_to_integers(graph)


def g6(graph: nx.Graph) -> str:
    return nx.to_graph6_bytes(
        nx.convert_node_labels_to_integers(graph, ordering="sorted"),
        header=False
    ).decode("ascii").strip()


def frozen_sources(root: Path = ROOT) -> list[dict]:
    """Check the saved frozen cross-reference and independent index hashes."""
    xref = root / "reports/order10_core9_crossref_v1"
    core = root / "reports/order10_core_index_v1"
    xmeta = json.loads((xref / "manifest.json").read_text(encoding="utf-8"))
    imeta = json.loads((core / "manifest.json").read_text(encoding="utf-8"))
    for fname in ("unclassified.tsv", "matches.tsv", "summary.md"):
        if sha((xref / fname).read_bytes()) != xmeta["output_sha256"][fname]:
            raise ValueError("Changed historical cross-reference output")
    for fname in ("classes.tsv", "assignments.tsv"):
        if sha((core / fname).read_bytes()) != imeta["output_sha256"][fname]:
            raise ValueError("Changed historical nine-core isomorphism index")
    if xmeta["input_sha256"]["reports/order10_core_index_v1/manifest.json"] != sha(
        (core / "manifest.json").read_bytes()
    ):
        raise ValueError("Unlinked historical core index manifest")

    rows = read_tsv(xref / "unclassified.tsv")
    if len(rows) != 29:
        raise ValueError("Expected exactly 29 unresolved nine-vertex core classes")
    classes = {int(row["core_id"]): row for row in read_tsv(core / "classes.tsv")}
    assignments = {
        int(row["index"]): row
        for row in read_tsv(core / "assignments.tsv")
    }
    if len(classes) != 2439 or len(assignments) != 8533:
        raise ValueError("Original exact core-class and per-index assignment populations changed")
    remaining = {}
    for line in (root / "indeterminate_order_10_v4.txt").read_text(
        encoding="utf-8"
    ).splitlines():
        if line and not line.startswith("#"):
            fields = line.split()
            if len(fields) != 6 or int(fields[0]) in remaining:
                raise ValueError("Malformed current unresolved index")
            remaining[int(fields[0])] = fields
    if len(remaining) != 8233:
        raise ValueError("The versioned v4 unresolved population has changed")
    seen_cores = set()
    seen_members = set()
    for row in rows:
        i = int(row["core_id"])
        if i in seen_cores or i not in classes:
            raise ValueError("Invalid or missing core representative")
        seen_cores.add(i)
        c = classes[i]
        members = [int(v) for v in c["member_indices"].split(",")]
        if (
            c["core_graph6"] != row["core_graph6"]
            or int(c["core_order"]) != 9
            or int(c["members"]) != int(row["original_members"])
            or len(members) != len(set(members))
            or len(members) != int(c["members"])
            or seen_members.intersection(members)
            or min(members) != i
        ):
            raise ValueError("Invalid frozen original membership in nine-core class")
        seen_members.update(members)
        for index in members:
            assignment = assignments.get(index)
            fields = remaining.get(index)
            if (
                assignment is None or fields is None
                or int(assignment["core_id"]) != i
                or assignment["core_graph6"] != row["core_graph6"]
                or assignment["pared_order"] != "9"
                or fields[1] != "9"
                or assignment["pared_graph6"] != fields[2]
                or assignment["original_target_status"] != fields[4]
            ):
                raise ValueError(
                    f"Original {index} core assignment disagrees with independently "
                    "frozen member/class and v4 source records"
                )
        if any(
            x not in remaining
            or int(remaining[x][1]) != 9
            or remaining[x][4] != "conjectured_divergent"
            for x in members
        ) and i in EXPECTED_RETRACTS:
            raise ValueError("Snub-dependent originals were silently reclassified")
        if not nx.is_isomorphic(
            decode(row["core_graph6"]), decode(row["order9_graph6"])
        ):
            raise ValueError("Original nine-vertex entry is not isomorphic to its core")
    if sum(int(r["original_members"]) for r in rows) != 3738:
        raise ValueError("Unexpected unresolved nine-core original population")
    if len(seen_members) != 3738:
        raise ValueError("Original nine-core member indices are not a partition")
    return sorted(rows, key=lambda row: int(row["core_id"]))


def raw_K(graph: nx.Graph) -> nx.Graph:
    """An independently reconstructed maximal-clique intersection graph."""
    facets = sorted(
        (tuple(sorted(q)) for q in nx.find_cliques(graph)),
        key=lambda q: q
    )
    sets = [set(q) for q in facets]
    result = nx.Graph()
    result.add_nodes_from(range(len(facets)))
    result.add_edges_from(
        (i, j) for i in range(len(facets))
        for j in range(i + 1, len(facets))
        if sets[i].intersection(sets[j])
    )
    return result


def completely_pare(graph: nx.Graph) -> nx.Graph:
    """Deterministic CLOSED-neighborhood dominated-vertex folding only."""
    h = graph.copy()
    while True:
        closed = {v: set(h[v]) | {v} for v in h}
        pair = next(
            ((v, u) for v in sorted(h) for u in sorted(h)
             if v != u and closed[v] <= closed[u]), None
        )
        if pair is None:
            return nx.convert_node_labels_to_integers(h, ordering="sorted")
        h.remove_node(pair[0])


def pared_K2(graph: nx.Graph) -> nx.Graph:
    return completely_pare(raw_K(completely_pare(raw_K(graph))))


def target_isomorphism(target: nx.Graph, snub: nx.Graph) -> list[int | None] | None:
    matcher = nx.algorithms.isomorphism.GraphMatcher(target, snub)
    # Exact graph isomorphisms are small (8 vertices); choose a
    # deterministic minimum map, independent of search traversal order.
    maps = [
        tuple(mapping[v] for v in sorted(target))
        for mapping in matcher.isomorphisms_iter()
    ]
    if not maps:
        return None
    chosen = min(maps)
    output: list[int | None] = [None] * 9
    for v, image in zip(sorted(target), chosen):
        output[v] = image
    return output


def verify_retraction(graph: nx.Graph, removed: int, image: int) -> bool:
    """Check adjacency OR equality (not strict adjacency) on every edge."""
    if image == removed:
        return False
    retained = graph.subgraph([v for v in graph if v != removed])
    mapping = {v: image if v == removed else v for v in graph}
    if set(mapping.values()) != set(retained):
        return False
    return all(
        mapping[u] == mapping[v]
        or retained.has_edge(mapping[u], mapping[v])
        for u, v in graph.edges()
    )


def investigate_core(graph: nx.Graph, snub: nx.Graph) -> dict:
    if len(graph) != 9 or not nx.is_connected(graph):
        raise ValueError("Expected connected nine-vertex core")
    deletions = []
    all_retractions = []
    for removed in sorted(graph):
        target = graph.subgraph([v for v in graph if v != removed])
        isomorphism = target_isomorphism(target, snub)
        if isomorphism is None:
            continue
        possible = []
        failures = []
        for image in sorted(target):
            if verify_retraction(graph, removed, image):
                possible.append(image)
            else:
                # For a one-vertex retraction, exactly a source edge incident
                # to 'removed' must violate adjacency-or-equality.
                bad = next(
                    (v for v in sorted(graph[removed])
                     if v != image and not target.has_edge(image, v)),
                    None
                )
                if bad is None:
                    raise AssertionError("Complete retraction test lacks an obstruction")
                failures.append([image, bad])
        deletions.append({
            "removed_vertex": removed,
            "target_to_snub": isomorphism,
            "admissible_image_vertices": possible,
            "rejected_image_obstructions": failures,
        })
        all_retractions.extend([{"removed_vertex": removed, "image_vertex": u}
                                for u in possible])
    return {
        "status": ("SNUB_RETRACT" if all_retractions else
                   "INDUCED_SNUB_NO_RETRACT" if deletions else "NO_INDUCED_SNUB"),
        "deletions": deletions,
        "retractions": all_retractions,
    }


def prepare(root: Path = ROOT) -> dict[str, bytes]:
    rows = frozen_sources(root)
    snub = decode(SNUB_G6)
    snub2 = pared_K2(snub)
    if (len(snub2), snub2.number_of_edges()) != (20, 136):
        raise ValueError("Unexpected independently reconstructed snub K^2")
    old = json.loads((root / "reports/order9_snub_retractions_v1/certificates.json").read_text())
    if {x["core_id"] for x in old["certificates"]} != ORIGINAL_THREE:
        raise ValueError("Old three certified snub retractions do not match")
    records = []
    buckets = {"SNUB_RETRACT": [], "INDUCED_SNUB_NO_RETRACT": [], "NO_INDUCED_SNUB": []}
    K2_matches = []
    for row in rows:
        i = int(row["core_id"])
        graph = decode(row["core_graph6"])
        record = {
            "core_id": i,
            "core_graph6": row["core_graph6"],
            "order9_index": int(row["order9_index"]),
            "order9_graph6": row["order9_graph6"],
            "original_order10_members": int(row["original_members"]),
            **investigate_core(graph, snub),
        }
        g2 = pared_K2(graph)
        record["pared_K2_order"] = len(g2)
        record["pared_K2_edges"] = g2.number_of_edges()
        map2 = None
        if len(g2) == len(snub2) and g2.number_of_edges() == snub2.number_of_edges():
            matcher = nx.algorithms.isomorphism.GraphMatcher(g2, snub2)
            if matcher.is_isomorphic():
                map2 = [matcher.mapping[j] for j in range(len(g2))]
        record["pared_K2_to_snub_pared_K2"] = map2
        if map2 is not None:
            K2_matches.append(i)
        buckets[record["status"]].append(i)
        records.append(record)

    if (
        set(buckets["SNUB_RETRACT"]) != EXPECTED_RETRACTS
        or set(buckets["INDUCED_SNUB_NO_RETRACT"]) != EXPECTED_INDUCED_ONLY
        or len(buckets["NO_INDUCED_SNUB"]) != 14
        or set(K2_matches) != EXPECTED_K2_EQUIVALENCE
    ):
        raise ValueError("Independent exhaustive retraction/second-iterate audit changed")

    newly = EXPECTED_RETRACTS - ORIGINAL_THREE
    total = sum(r["original_order10_members"] for r in records if r["core_id"] in EXPECTED_RETRACTS)
    added = sum(r["original_order10_members"] for r in records if r["core_id"] in newly)
    old_total = sum(r["original_order10_members"] for r in records if r["core_id"] in ORIGINAL_THREE)
    induced_only = sum(r["original_order10_members"] for r in records if r["core_id"] in EXPECTED_INDUCED_ONLY)
    if (total, added, old_total, induced_only) != (1222, 710, 512, 811):
        raise ValueError("Certified member classes have unexpected sizes")
    for original in old["certificates"]:
        record = next(r for r in records if r["core_id"] == original["core_id"])
        if not any(
            pair["removed_vertex"] == original["removed_vertex"]
            and pair["image_vertex"] == original["image_vertex"]
            for pair in record["retractions"]
        ):
            raise ValueError("Old three retraction certificates failed independent recovery")

    cert = {
        "schema": 2,
        "scope": "ALL 29 unresolved stiff nine-vertex cores from frozen post-v3 index",
        "snub_graph6": SNUB_G6,
        "old_retract_core_ids": sorted(ORIGINAL_THREE),
        "new_retract_core_ids": sorted(newly),
        "same_pared_K2_as_snub": sorted(K2_matches),
        "counts": {
            "core_classes": 29, "snub_retract_cores": 9,
            "induced_snub_without_retract_cores": 6,
            "no_induced_snub_cores": 14,
            "snub_retract_original_order10_members": total,
            "newly_identified_original_order10_members": added,
            "previous_original_order10_members": old_total,
            "induced_without_retract_order10_members": induced_only,
        },
        "no_new_clique_behavior_verdicts": True,
        "records": records,
    }
    report = [
        "# Exhaustive snub retractions of all 29 unresolved nine-vertex cores",
        "",
        "This is an exact finite investigation of **graph retractions**",
        "and second completely pared clique-iterate isomorphisms.",
        "**It is not a new clique-divergence classification.**",
        "Divergence of the snub disphenoid remains a conjecture.",
        "",
        "The snub S has graph6 `GQyuzw`. A retraction onto S inside a",
        "nine-vertex graph must delete one vertex v, identify it with",
        "one of eight remaining vertices u, and fix the rest.",
        "The checker tests all 9*8 possibilities, first verifying the",
        "induced eight-vertex graph is isomorphic to S, then every source edge",
        "under adjacency **or equality**. Negative local obstructions",
        "are recorded for each impossible image.",
        "",
        "| Core ID | Nine-vertex index | Original ten-graph members | Retraction v to u | Pared K² matches snub? |",
        "|---:|---:|---:|---|---|",
    ]
    for record in records:
        if record["status"] != "SNUB_RETRACT":
            continue
        first = record["retractions"][0]
        report.append(
            f"| {record['core_id']} | {record['order9_index']} | "
            f"{record['original_order10_members']} | "
            f"{first['removed_vertex']} to {first['image_vertex']} | "
            f"{'YES' if record['pared_K2_to_snub_pared_K2'] is not None else 'no'} |"
        )
    report.extend([
        "",
        f"**Nine snub-retracting cores represent {total:,} original ten-vertex graphs.**",
        f"The six newly identified classes contribute **{added:,}** originals;",
        f"the previous three contribute **{old_total:,}**.",
        "",
        f"Six more cores (representing **{induced_only:,}** originals)",
        "contain an induced snub but have **no graph retraction** to it.",
        "The other 14 cores contain **no induced snub**. These negative",
        "statements are exhaustive within the 29 nine-vertex core classes.",
        "",
        "## Stronger dynamical relationship for three cores",
        "",
        "For cores 4929602, 4972358, and 5645085, the checker",
        "independently constructs the full second completely pared",
        "clique iterates and explicit graph isomorphisms to the second",
        "completely pared clique iterate of S (20 vertices, 136 edges).",
        "By the dominated-vertex dismantling theorem, the K-convergence",
        "versus K-divergence behavior of **each of these three cores**",
        "is the same as that of S. The same conclusion applies to the",
        "**512 original ten-vertex graphs** which dismantle to those cores.",
        "This is an unconditional **equivalence of behavior**, not a",
        "proof of divergence for either side.",
        "",
        "For the other six snub-retracting cores, the retraction gives",
        "only the implication: **if S is K-divergent, so is the core**.",
        "There is no converse implied by an arbitrary graph retraction.",
        "",
        "References: Frías-Armenta--Neumann-Lara--Pizaña (2004),",
        "*Dismantlings and iterated clique graphs*; and the standard",
        "retraction/divergence theorem in clique-graph dynamics.",
        "",
        "## Reproduction",
        "",
        "After preparing an environment with NetworkX from the existing",
        "pinned monorepo checkout:",
        "",
        "```bash",
        ".venv-special-k3-v5/bin/python scripts/core9_snub_retractions_v2.py verify",
        ".venv-special-k3-v5/bin/python -m unittest discover -s tests -p 'test_core9_snub_retractions_v2.py' -v",
        "```",
        "",
        "The verifier recomputes every positive and negative finite search,",
        "each explicit isomorphism, all three second-iterate isomorphisms,",
        "and exactly reproduces all committed files. All past census and",
        "previous three-graph certificate files remain untouched.",
        "",
    ])
    output = {
        "certificates.json": (json.dumps(cert, sort_keys=True, indent=2) + "\n").encode(),
        "summary.md": ("\n".join(report)).encode("utf-8"),
    }
    manifest = {
        "schema": 2, "stage": "order9_snub_retractions_v2",
        "originals_before": 3738, "new_positive_originals": added,
        "inputs_sha256": {
            "unclassified.tsv": sha((root / "reports/order10_core9_crossref_v1/unclassified.tsv").read_bytes()),
            "classes.tsv": sha((root / "reports/order10_core_index_v1/classes.tsv").read_bytes()),
            "old_certificates.json": sha((root / "reports/order9_snub_retractions_v1/certificates.json").read_bytes()),
            "indeterminate_order_10_v4.txt": sha((root / "indeterminate_order_10_v4.txt").read_bytes()),
        },
        "outputs_sha256": {key: sha(value) for key, value in sorted(output.items())},
    }
    output["manifest.json"] = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    return {str(Path("reports/order9_snub_retractions_v2") / key): value
            for key, value in output.items()}


def verify(root: Path = ROOT) -> None:
    for name, data in prepare(root).items():
        file = root / name
        if not file.is_file() or file.read_bytes() != data:
            raise ValueError(f"Missing, modified or stale snub certificate: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "verify", "report"))
    args = parser.parse_args()
    payload = prepare()
    if args.action == "build":
        for name, data in payload.items():
            file = ROOT / name
            file.parent.mkdir(parents=True, exist_ok=True)
            if file.exists() and file.read_bytes() != data:
                raise ValueError(f"Refusing to overwrite a changed prior certificate: {name}")
            file.write_bytes(data)
    if args.action != "report":
        verify()
    if args.action == "report":
        print(payload["reports/order9_snub_retractions_v2/summary.md"].decode())
    else:
        print("29 cores checked; 9 retract onto the snub (6 new); "
              "1222 represented originals; three exact pared K² equivalences.")


if __name__ == "__main__":
    main()
