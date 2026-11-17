"""Certified order-10 original-member transfer from K3 special-O4 core witnesses.

A special O4 in the third *pared* clique iterate proves K-divergence
of its nine-vertex core. This versioned postpass independently verifies
the positive special-octahedron witness, the pre-existing exact-isomorphism
core index, and *for each of the 133 original order-ten graphs* an explicit
closed-neighborhood-dominated deletion sequence and a core isomorphism.

The logical step from a dismantling to preservation of K-dynamics uses the
published theorem of Frias-Armenta, Neumann-Lara and Pizana, "Dismantlings
and iterated clique graphs", Discrete Mathematics 282 (2004).
Do not claim an O4 witness at K^3 of the UNPARED original graph.

Never modify historical census results or the frozen v2-v5 stages.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import tempfile
from collections import defaultdict
from pathlib import Path

import networkx as nx

import core_isomorphism_index as old_index
import special_octahedra_k3_v5 as v5

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(__file__).resolve()
INDEX = ROOT / "reports/order10_core_index_v1"
OUTPUT = ROOT / "reports/order10_special_octahedron_core_lift_v1"
V5 = ROOT / "runs/order10/special-octahedra-k3-v5"
SCHEMA = 1
THEOREM = (
    "M. E. Frias-Armenta, V. Neumann-Lara, M. A. Pizana, "
    "Dismantlings and iterated clique graphs, Discrete Mathematics 282 (2004)"
)
THEOREM_URL = "https://www.sciencedirect.com/science/article/pii/S0012365X04000561"


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def decode(graph6: str) -> nx.Graph:
    return nx.from_graph6_bytes(graph6.encode("ascii"))


def numbered_g6(graph: nx.Graph) -> str:
    numbered = nx.convert_node_labels_to_integers(graph, ordering="sorted")
    return nx.to_graph6_bytes(numbered, header=False).decode("ascii").strip()


def read_tsv(path: Path, header: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if tuple(reader.fieldnames or ()) != header:
            raise ValueError(f"Invalid frozen TSV columns: {path}")
        rows = list(reader)
        if any(None in row or any(v is None for v in row.values()) for row in rows):
            raise ValueError(f"Malformed frozen TSV: {path}")
    return rows


def write_tsv(header: tuple[str, ...], rows: list[dict]) -> bytes:
    out = io.StringIO(newline="")
    writer = csv.DictWriter(
        out, fieldnames=header, delimiter="\t", lineterminator="\n"
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return out.getvalue().encode("utf-8")


def saved_core_index() -> tuple[dict[int, dict], dict[int, dict]]:
    """Validate frozen class/index inputs before accepting any assignments."""
    meta = json.loads((INDEX / "manifest.json").read_text(encoding="utf-8"))
    for filename in ("classes.tsv", "assignments.tsv", "summary.md"):
        if file_sha(INDEX / filename) != meta["output_sha256"][filename]:
            raise ValueError(f"Frozen core index file was altered: {filename}")
    if file_sha(old_index.HISTORICAL) != meta["historical_sha256"]:
        raise ValueError("Historical census differs from frozen core-index source")
    if file_sha(old_index.ACTIVE) != meta["post_v3_sha256"]:
        raise ValueError("Post-v3 census differs from frozen core-index source")
    class_rows = read_tsv(
        INDEX / "classes.tsv",
        ("core_id", "core_order", "core_graph6", "members",
         "conjectured_members", "member_indices"),
    )
    assignment_rows = read_tsv(
        INDEX / "assignments.tsv",
        ("index", "pared_order", "pared_graph6", "core_id",
         "core_order", "core_graph6", "class_size", "original_target_status"),
    )
    classes = {int(row["core_id"]): row for row in class_rows}
    assignments = {int(row["index"]): row for row in assignment_rows}
    if (
        len(classes) != len(class_rows)
        or len(assignments) != len(assignment_rows)
        or len(assignments) != meta["originals_remaining"]
        or len(classes) != meta["distinct_cores"]
    ):
        raise ValueError("Frozen core index has duplicates or missing records")
    return classes, assignments


def v5_positive() -> list[dict]:
    """Validate every positive v5 certificate and the completed-source cohort."""
    v5.require_stage()
    totals = v5.summary()
    if (
        totals["pending_unique"] or totals["timeouts"] or totals["errors"]
        or totals["clique_bound_exceeded"]
        or totals["completed_unique"] != totals["imported_unique"]
    ):
        raise ValueError("V5 source census must be completed without limitations")
    positives: list[dict] = []
    for group in v5.imported_groups():
        encoded = group["graph6"]
        record = v5.read(v5.path_for(encoded, "records"))
        cert = record.get("divergence_certificate")
        if cert is None:
            continue
        # Recompute K^3 of the original pared core and verify its witness,
        # rather than trusting the v5 report or a positive status label.
        source = v5.verify_import(encoded)
        v5.verify_record(record, encoded, source)
        if (
            cert.get("rule") != "special_octahedron"
            or cert.get("iterate_index") != 3
            or cert.get("dimension") != 4
            or cert.get("target_kind") != "octahedra:4"
            or cert.get("conclusion") != "proven_divergent"
        ):
            raise ValueError("Unexpected positive certificate in this O4 postpass")
        positives.append({
            "graph6": encoded,
            "representative_index": record["index"],
            "indices": group["indices"],
            "record_sha256": file_sha(v5.path_for(encoded, "records")),
        })
    if (
        len(positives) != totals["certified_divergent_unique"]
        or sum(len(item["indices"]) for item in positives)
        != totals["certified_divergent_indices"]
    ):
        raise ValueError("V5 report and independently replayed positives differ")
    return sorted(positives, key=lambda row: row["representative_index"])


def closed(graph: nx.Graph, vertex: int) -> set[int]:
    return set(graph[vertex]) | {vertex}


def dominated_pair(graph: nx.Graph) -> tuple[int, int] | None:
    """Choose the lexicographically first valid fold; never guess a fold."""
    for vertex in sorted(graph):
        for dominator in sorted(graph):
            if vertex != dominator and closed(graph, vertex) <= closed(graph, dominator):
                return vertex, dominator
    return None


def witness_folds(original: nx.Graph) -> tuple[nx.Graph, list[list[int]]]:
    graph = original.copy()
    folds: list[list[int]] = []
    while (pair := dominated_pair(graph)) is not None:
        vertex, dominator = pair
        folds.append([vertex, dominator])
        graph.remove_node(vertex)
    return graph, folds


def isomorphism_map(graph: nx.Graph, target: nx.Graph) -> list[list[int]]:
    matcher = nx.algorithms.isomorphism.GraphMatcher(graph, target)
    if not matcher.is_isomorphic():
        raise ValueError("Pared original does not match its assigned core class")
    return [[int(u), int(v)] for u, v in sorted(matcher.mapping.items())]


def validate_member(
    row: dict, *, original_graph6: str, historical_graph6: str,
    representative: nx.Graph
) -> None:
    """Replay every fold and the edge-preserving vertex bijection."""
    graph = decode(original_graph6)
    if len(graph) != 10 or not nx.is_connected(graph):
        raise ValueError("Expected a connected original ten-vertex census graph")
    if row["original_graph6"] != original_graph6:
        raise ValueError("Original graph6 no longer agrees with initial census")
    if row["historical_pared_graph6"] != historical_graph6:
        raise ValueError("Historical pared graph6 does not match original index")
    seen: set[int] = set()
    for vertices in row["dominated_folds"]:
        if (
            not isinstance(vertices, list) or len(vertices) != 2
            or any(type(v) is not int for v in vertices)
        ):
            raise ValueError("Malformed dominated-vertex fold witness")
        vertex, dominator = vertices
        if (
            vertex not in graph or dominator not in graph
            or vertex == dominator or vertex in seen
            or not closed(graph, vertex) <= closed(graph, dominator)
        ):
            raise ValueError("Invalid closed-neighborhood containment in fold")
        seen.add(vertex)
        graph.remove_node(vertex)
    if dominated_pair(graph) is not None:
        raise ValueError("Claimed core is not stiff")
    if numbered_g6(graph) != row["residual_graph6"]:
        raise ValueError("Folded graph6 is inconsistent with the fold sequence")
    if not nx.is_isomorphic(graph, decode(historical_graph6)):
        raise ValueError("Fold witness differs from saved original pared graph")
    mapping_data = row["residual_to_core"]
    if (
        not isinstance(mapping_data, list)
        or len(mapping_data) != len(graph)
        or any(
            not isinstance(pair, list) or len(pair) != 2
            or any(type(v) is not int for v in pair)
            for pair in mapping_data
        )
    ):
        raise ValueError("Malformed exact core-isomorphism witness")
    mapping = dict(mapping_data)
    if (
        len(mapping) != len(graph)
        or set(mapping) != set(graph)
        or len(set(mapping.values())) != len(representative)
        or set(mapping.values()) != set(representative)
        or len(graph) != len(representative)
    ):
        raise ValueError("Core bijection has wrong vertex sets")
    if any(
        graph.has_edge(x, y) != representative.has_edge(mapping[x], mapping[y])
        for x in graph for y in graph if x < y
    ):
        raise ValueError("Core bijection does not preserve adjacency")


def result_inputs() -> dict[str, str]:
    """Hash historical sources, positive certificates and every V5 record."""
    paths = {
        "script_sha256": SCRIPT,
        "v5_script_sha256": v5.SCRIPT,
        "v3_script_sha256": v5.v3.SCRIPT,
        "v2_script_sha256": v5.v2.SCRIPT,
        "v5_manifest_sha256": V5 / "manifest.json",
        "v5_pin_sha256": v5.PIN,
        "historical_sha256": old_index.HISTORICAL,
        "active_v3_sha256": old_index.ACTIVE,
        "original_census_summary_sha256": ROOT / "runs/order10/initial/summary.json",
        "original_census_manifest_sha256": ROOT / "runs/order10/initial/manifest.json",
        "core_index_manifest_sha256": INDEX / "manifest.json",
        "core_index_classes_sha256": INDEX / "classes.tsv",
        "core_index_assignments_sha256": INDEX / "assignments.tsv",
    }
    output = {k: file_sha(v) for k, v in paths.items()}
    h = hashlib.sha256()
    for path in sorted((V5 / "records").glob("*.json")):
        h.update(f"{path.name}\t{file_sha(path)}\n".encode("ascii"))
    output["all_v5_records_sha256"] = h.hexdigest()
    return output


def prepare() -> dict[str, bytes]:
    classes, assignments = saved_core_index()
    historical = old_index.load_rows(old_index.HISTORICAL)
    original_by_index = old_index.original_graph6_by_index()
    positives = v5_positive()

    by_class: dict[int, list[dict]] = defaultdict(list)
    direct_indices: dict[int, set[int]] = defaultdict(set)
    for positive in positives:
        idx = positive["representative_index"]
        assignment = assignments.get(idx)
        if assignment is None:
            raise ValueError(f"Positive graph6 lacks a frozen core assignment: {idx}")
        core_id = int(assignment["core_id"])
        if core_id not in classes:
            raise ValueError("Positive v5 result refers to unknown core")
        representative = decode(classes[core_id]["core_graph6"])
        if not nx.is_isomorphic(decode(positive["graph6"]), representative):
            raise ValueError("Positive v5 graph6 is not in the assigned core class")
        for member_idx in positive["indices"]:
            other = assignments.get(member_idx)
            if other is None or int(other["core_id"]) != core_id:
                raise ValueError("Exact duplicate v5 indices disagree on core class")
            if member_idx in direct_indices[core_id]:
                raise ValueError("Duplicate direct positive index")
            direct_indices[core_id].add(member_idx)
        by_class[core_id].append(positive)

    if not by_class:
        raise ValueError("No verified positive K3 special-octahedron examples")

    class_rows = []
    member_rows = []
    for core_id, examples in sorted(by_class.items()):
        group = classes[core_id]
        core_g6 = group["core_graph6"]
        representative = decode(core_g6)
        member_indices = [int(k) for k in group["member_indices"].split(",")]
        if (
            int(group["members"]) != len(member_indices)
            or len(set(member_indices)) != len(member_indices)
            or min(member_indices) != core_id
            or int(group["core_order"]) != 9
            or not nx.is_connected(representative)
        ):
            raise ValueError("Invalid nine-vertex frozen core class")
        class_rows.append({
            "core_id": core_id,
            "core_graph6": core_g6,
            "original_members": len(member_indices),
            "direct_v5_members": len(direct_indices[core_id]),
            "lifted_only_members": len(member_indices) - len(direct_indices[core_id]),
            "positive_graph6_encodings": ",".join(
                sorted(example["graph6"] for example in examples)
            ),
            "witness_level": 3,
            "octahedron": "O_4",
        })
        for idx in member_indices:
            a = assignments.get(idx)
            old = historical.get(idx)
            raw = original_by_index.get(idx)
            if (
                a is None or old is None or raw is None
                or int(a["core_id"]) != core_id
                or a["core_graph6"] != core_g6
                or int(a["pared_order"]) != old.order
                or a["pared_graph6"] != old.graph6
                or int(a["class_size"]) != len(member_indices)
                or old.target_status != a["original_target_status"]
            ):
                raise ValueError(f"Frozen assignment/source mismatch: {idx}")
            original = decode(raw)
            residual, folds = witness_folds(original)
            witness = {
                "index": idx,
                "original_graph6": raw,
                "historical_pared_graph6": old.graph6,
                "core_id": core_id,
                "core_graph6": core_g6,
                "dominated_folds": folds,
                "residual_graph6": numbered_g6(residual),
                "residual_to_core": isomorphism_map(residual, representative),
                "certified_direct_v5": idx in direct_indices[core_id],
            }
            validate_member(
                witness, original_graph6=raw,
                historical_graph6=old.graph6,
                representative=representative,
            )
            member_rows.append(witness)
    member_rows.sort(key=lambda row: row["index"])
    count = sum(row["original_members"] for row in class_rows)
    direct = sum(row["direct_v5_members"] for row in class_rows)
    if (
        count != len(member_rows) or len({x["index"] for x in member_rows}) != count
        or direct != sum(len(item["indices"]) for item in positives)
    ):
        raise ValueError("Incomplete or overlapping original-member lift")

    class_header = (
        "core_id", "core_graph6", "original_members", "direct_v5_members",
        "lifted_only_members", "positive_graph6_encodings",
        "witness_level", "octahedron",
    )
    member_header = (
        "index", "original_graph6", "historical_pared_graph6", "core_id",
        "core_graph6", "dominated_folds", "residual_graph6",
        "residual_to_core", "certified_direct_v5",
    )
    bytes_map: dict[str, bytes] = {}
    bytes_map["classes.tsv"] = write_tsv(class_header, class_rows)
    tsv_members = []
    for witness in member_rows:
        row = dict(witness)
        row["dominated_folds"] = json.dumps(row["dominated_folds"], separators=(",", ":"))
        row["residual_to_core"] = json.dumps(row["residual_to_core"], separators=(",", ":"))
        row["certified_direct_v5"] = str(row["certified_direct_v5"]).lower()
        tsv_members.append(row)
    bytes_map["members.tsv"] = write_tsv(member_header, tsv_members)

    body = [
        "# Certified order-ten divergence via special-O4 core classes",
        "",
        "This is a **positive-certificate extension**, not a fresh search of every",
        "original ten-vertex graph. Every recorded source graph is verified",
        "against the initial order-ten census and supplied with an explicit",
        "dominated-vertex deletion transcript and a vertex bijection to a",
        "certified nine-vertex core.",
        "",
        "| Core ID | Core graph6 | Class members | Direct v5 | Lifted by dismantling |",
        "|---:|---|---:|---:|---:|",
    ]
    for row in class_rows:
        body.append(
            f"| {row['core_id']} | `{row['core_graph6']}` | {row['original_members']} "
            f"| {row['direct_v5_members']} | {row['lifted_only_members']} |"
        )
    body += [
        "",
        f"**Total: {count} original indices, including {direct} directly",
        f"positive v5 indices and {count-direct} additional indices lifted",
        "by the published dominated-vertex theorem.**",
        "",
        f"The {len(positives)} positive exact-graph6 records all have",
        "independently replayed special-`O_4` witnesses at the third",
        "completely pared clique iterate. Their graphs fall into the two",
        "isomorphism classes listed above.",
        "",
        "## Proof scope",
        "",
        "For an original ten-vertex graph `X`, each recorded fold",
        "deletes a vertex `v` whose closed neighborhood is contained in",
        "that of an identified dominator `u`. The stored bijection",
        "identifies the final stiff graph with the certified nine-vertex",
        "representative `C`. The dismantling theorem of Frías-Armenta,",
        "Neumann-Lara and Pizaña ensures `X` and `C` have identical",
        "K-convergence/divergence behavior. The special octahedron in",
        "`K^3(C)` proves `C` K-divergent, hence `X` K-divergent.",
        "",
        "**The certificate does not assert that the unpared original",
        "graph itself contains a special octahedron in its third iterate.**",
        "The level-3 statement is about the completely pared core sequence.",
        "The negative results for other cores do not imply convergence.",
        "",
        f"Reference: [{THEOREM}]({THEOREM_URL}).",
        "",
        "## Reproduction",
        "",
        "`members.tsv` contains all original graph6 encodings, explicit",
        "dominated folds, their resulting graph6, and verified vertex maps",
        "onto the class representative. `classes.tsv` identifies the",
        "positive isomorphism classes. `manifest.json` freezes inputs,",
        "algorithms, evidence and output hashes.",
        "",
        "```bash",
        ".venv-special-k3-v5/bin/python scripts/special_octahedron_class_lift_v1.py verify",
        "```",
        "",
    ]
    bytes_map["summary.md"] = ("\n".join(body)).encode("utf-8")

    manifest = {
        "schema": SCHEMA,
        "stage": "order10_special_octahedron_core_lift_v1",
        "method": "independent_v5_special_witness_and_explicit_closed_neighborhood_fold_chain",
        "theorem": THEOREM, "theorem_url": THEOREM_URL,
        "classes": len(class_rows),
        "positive_graph6_records": len(positives),
        "original_members_certified": count,
        "direct_v5_original_indices": direct,
        "additional_lifted_original_indices": count-direct,
        "inputs_sha256": result_inputs(),
        "outputs_sha256": {
            name: sha(blob) for name, blob in sorted(bytes_map.items())
        },
    }
    bytes_map["manifest.json"] = (
        json.dumps(manifest, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    return bytes_map


def check_saved(destination: Path, expected: dict[str, bytes]) -> None:
    if not destination.is_dir():
        raise ValueError(f"Missing verified class-lift report: {destination}")
    files = {path.name for path in destination.iterdir()}
    if files != set(expected):
        raise ValueError("Class-lift report files differ from frozen output set")
    for name, blob in expected.items():
        if (destination / name).read_bytes() != blob:
            raise ValueError(f"Class-lift report was modified or stale: {name}")


def build(destination: Path, expected: dict[str, bytes]) -> None:
    if destination.exists():
        check_saved(destination, expected)
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".certified-core-lift-", dir=destination.parent
    ) as tmp:
        staged = Path(tmp) / "ready"
        staged.mkdir()
        for name, blob in expected.items():
            (staged / name).write_bytes(blob)
        os.replace(staged, destination)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "verify", "report"))
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    prepared = prepare()
    if args.action == "build":
        build(args.output, prepared)
        print(f"Built/verified immutable class-lift report: {args.output}")
    else:
        check_saved(args.output, prepared)
        print(f"Independently verified immutable class-lift report: {args.output}")
    if args.action == "report":
        print(prepared["summary.md"].decode("utf-8"))
    else:
        meta = json.loads(prepared["manifest.json"])
        print(json.dumps({
            k: meta[k] for k in (
                "classes", "positive_graph6_records",
                "original_members_certified", "direct_v5_original_indices",
                "additional_lifted_original_indices"
            )
        }, sort_keys=True))


if __name__ == "__main__":
    main()
