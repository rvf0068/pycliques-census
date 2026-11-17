"""Replay four historical divergent nine-cores and lift certificates to 167 originals.

The two special-octahedron witnesses are in RAW K^3 of nine-vertex
representatives, not an asserted iterate of any unpared order-ten graph.
The other two cores are suspensions of connected graphs with explicit
2-coaffinations, invoking Larrión--Neumann-Lara--Pizaña, On expansive
graphs (2009), Theorem 4.6. Closed-neighborhood dominated deletions
preserve K-behavior by Frías-Armenta--Neumann-Lara--Pizaña (2004).

This script never changes historical census stages or active verdicts.
Usage (after bash scripts/bootstrap_special_k3_v5.sh):
  .venv-special-k3-v5/bin/python scripts/historical_ninecore_lift_v1.py
  .venv-special-k3-v5/bin/python scripts/historical_ninecore_lift_v1.py --output proof.json
  .venv-special-k3-v5/bin/python scripts/historical_ninecore_lift_v1.py --verify proof.json
"""
from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path

import networkx as nx

import core_isomorphism_index as old_index
import special_octahedron_class_lift_v1 as previous

ROOT = Path(__file__).resolve().parents[1]
OLD_REPORT = ROOT / "reports/order10_special_octahedron_core_lift_v1/members.tsv"
THEOREM_2004 = "Frías-Armenta, Neumann-Lara, Pizaña (2004), Dismantlings and iterated clique graphs"
THEOREM_2009 = "Larrión, Neumann-Lara, Pizaña (2009), On expansive graphs, Theorem 4.6"

# The graph6 strings and original counts are independently checked against
# the byte-exact reconstituted post-v3 core-isomorphism index.
SPECS = {
    7454135: {
        "graph6": "HEnb~jl", "members": 61, "method": "special",
        "third_order": 67, "third_edges": 1674,
        "facet": [7, 11, 13, 22, 31, 41, 56],
        "antipodes": [60, 59, 55, 14, 44, 34, 10],
    },
    9678187: {
        "graph6": "HQyuzpt", "members": 37, "method": "special",
        "third_order": 57, "third_edges": 1142,
        "facet": [0, 26, 36, 41],
        "antipodes": [47, 33, 28, 2],
    },
    10768817: {
        "graph6": "HUZ~v~}", "members": 33, "method": "suspension",
        "poles": [5, 6],
        "base_vertices": [0, 1, 2, 3, 4, 7, 8],
        "coaffination_images": [1, 2, 3, 4, 0, 8, 7],
    },
    11363569: {
        "graph6": "HUzrv~}", "members": 36, "method": "suspension",
        "poles": [7, 8],
        "base_vertices": [0, 1, 2, 3, 4, 5, 6],
        "coaffination_images": [1, 2, 3, 4, 5, 6, 0],
    },
}


def raw_clique_graph(graph: nx.Graph) -> nx.Graph:
    """Independent deterministic maximal-clique intersection construction."""
    facets = sorted(
        (frozenset(f) for f in nx.find_cliques(graph)),
        key=lambda f: tuple(sorted(f)),
    )
    result = nx.Graph()
    result.add_nodes_from(range(len(facets)))
    result.add_edges_from(
        (i, j)
        for i, f in enumerate(facets)
        for j in range(i + 1, len(facets))
        if f & facets[j]
    )
    return result


def check_special(graph: nx.Graph, facet: list[int], antipodes: list[int]) -> None:
    """Validate a complete special-O_d witness, including maximality."""
    if (
        len(facet) < 3 or len(facet) != len(antipodes)
        or len(set(facet + antipodes)) != 2 * len(facet)
        or not set(facet + antipodes) <= set(graph)
    ):
        raise ValueError("Invalid octahedron witness vertices")
    if not any(set(q) == set(facet) for q in nx.find_cliques(graph)):
        raise ValueError("The privileged facet is not maximal")
    for i, a in enumerate(facet):
        if graph.has_edge(a, antipodes[i]):
            raise ValueError("Matched vertices must be nonadjacent")
        for j, b in enumerate(facet):
            if i != j and (
                not graph.has_edge(a, b)
                or not graph.has_edge(antipodes[i], antipodes[j])
                or not graph.has_edge(a, antipodes[j])
            ):
                raise ValueError("Witness is not an induced O_d")


def check_suspension(graph: nx.Graph, poles: list[int],
                     base_vertices: list[int], images: list[int]) -> None:
    """Replay the suspension and its explicit distance-at-least-two automorphism."""
    if (
        len(poles) != 2 or len(set(poles)) != 2
        or len(set(base_vertices)) != len(base_vertices)
        or set(poles).isdisjoint(base_vertices) is False
        or set(poles + base_vertices) != set(graph)
        or len(images) != len(base_vertices)
        or set(images) != set(base_vertices)
    ):
        raise ValueError("Invalid suspension or permutation")
    a, b = poles
    if graph.has_edge(a, b) or any(
        not graph.has_edge(a, v) or not graph.has_edge(b, v)
        for v in base_vertices
    ):
        raise ValueError("Invalid suspension poles")
    base = graph.subgraph(base_vertices)
    if not nx.is_connected(base):
        raise ValueError("Suspension base is not connected")
    perm = dict(zip(base_vertices, images))
    if any(v == perm[v] or base.has_edge(v, perm[v]) for v in base):
        raise ValueError("Not a 2-coaffination")
    if any(
        base.has_edge(u, v) != base.has_edge(perm[u], perm[v])
        for u in base for v in base if u < v
    ):
        raise ValueError("Proposed coaffination is not an automorphism")


def core_certificate(core_id: int, spec: dict) -> dict:
    graph = previous.decode(spec["graph6"])
    if len(graph) != 9 or not nx.is_connected(graph):
        raise ValueError("Expected a connected nine-vertex core")
    if spec["method"] == "special":
        levels = [[len(graph), graph.number_of_edges()]]
        for _ in range(3):
            graph = raw_clique_graph(graph)
            levels.append([len(graph), graph.number_of_edges()])
        if levels[-1] != [spec["third_order"], spec["third_edges"]]:
            raise ValueError("Raw K^3 graph no longer has the certified size")
        check_special(graph, spec["facet"], spec["antipodes"])
        return {
            "core_id": core_id, "core_graph6": spec["graph6"],
            "method": "special_O_d_in_raw_K3", "iterate": 3,
            "dimension": len(spec["facet"]), "raw_levels": levels,
            "facet": spec["facet"], "antipodes": spec["antipodes"],
        }
    if spec["method"] == "suspension":
        check_suspension(
            graph, spec["poles"], spec["base_vertices"],
            spec["coaffination_images"],
        )
        return {
            "core_id": core_id, "core_graph6": spec["graph6"],
            "method": "suspension_of_connected_coaffine_graph",
            "theorem": THEOREM_2009, "poles": spec["poles"],
            "base_vertices": spec["base_vertices"],
            "coaffination_images": spec["coaffination_images"],
        }
    raise ValueError("Unrecognized certificate method")


def authenticated_previous_members() -> set[int]:
    """Recompute *all* prior certificates and compare every saved report byte.

    A self-consistent but forged/stale 133-row TSV is not accepted. Replay
    the previous special-O4 witnesses, full source index and dominated folds
    using the merged, independently verified PR #19 implementation.
    """
    expected = previous.prepare()
    previous.check_saved(OLD_REPORT.parent, expected)
    with io.StringIO(expected["members.tsv"].decode("utf-8")) as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if tuple(reader.fieldnames or ()) != (
            "index", "original_graph6", "historical_pared_graph6", "core_id",
            "core_graph6", "dominated_folds", "residual_graph6",
            "residual_to_core", "certified_direct_v5",
        ):
            raise ValueError("Unexpected verified prior certificate schema")
        rows = list(reader)
    indices = [int(row["index"]) for row in rows]
    if len(indices) != 133 or len(set(indices)) != 133:
        raise ValueError("Prior certified cohort must have 133 unique members")
    return set(indices)


def certified_method_totals(proofs: list[dict]) -> dict[str, int]:
    """Summarize verified core proofs; never trust separate literal totals."""
    totals = {
        "special_raw_K3_originals": 0,
        "suspension_coaffine_originals": 0,
    }
    methods = {
        "special_O_d_in_raw_K3": "special_raw_K3_originals",
        "suspension_of_connected_coaffine_graph": "suspension_coaffine_originals",
    }
    for proof in proofs:
        method = proof["method"]
        size = proof["original_members"]
        if method not in methods or type(size) is not int or size < 1:
            raise ValueError("Invalid verified core proof method or class size")
        totals[methods[method]] += size
    return totals


def certify() -> dict:
    # Reconstruct, not merely hash-check, the entire previously frozen index.
    classes, assignments = previous.saved_core_index()
    originals = old_index.original_graph6_by_index()
    historical = old_index.load_rows(old_index.HISTORICAL)
    old_members = authenticated_previous_members()

    proofs = []
    members = []
    for core_id, spec in sorted(SPECS.items()):
        group = classes.get(core_id)
        if (
            group is None or group["core_graph6"] != spec["graph6"]
            or int(group["members"]) != spec["members"]
            or int(group["core_order"]) != 9
        ):
            raise ValueError("Frozen core class mismatches independently pinned witness")
        indices = [int(x) for x in group["member_indices"].split(",")]
        if (
            len(indices) != spec["members"] or len(set(indices)) != len(indices)
            or min(indices) != core_id
        ):
            raise ValueError("Malformed or overlapping core class membership")
        proof = core_certificate(core_id, spec)
        proof["original_members"] = len(indices)
        proofs.append(proof)
        representative = previous.decode(spec["graph6"])
        for index in sorted(indices):
            assignment = assignments.get(index)
            old = historical.get(index)
            raw = originals.get(index)
            if (
                assignment is None or old is None or raw is None
                or int(assignment["core_id"]) != core_id
                or assignment["pared_graph6"] != old.graph6
                or assignment["original_target_status"] != old.target_status
            ):
                raise ValueError(f"Invalid historical source assignment: {index}")
            residual, folds = previous.witness_folds(previous.decode(raw))
            member = {
                "index": index,
                "original_graph6": raw,
                "historical_pared_graph6": old.graph6,
                "core_id": core_id,
                "core_graph6": spec["graph6"],
                "dominated_folds": folds,
                "residual_graph6": previous.numbered_g6(residual),
                "residual_to_core": previous.isomorphism_map(residual, representative),
            }
            previous.validate_member(
                member, original_graph6=raw,
                historical_graph6=old.graph6, representative=representative,
            )
            members.append(member)

    members.sort(key=lambda row: row["index"])
    unique = {row["index"] for row in members}
    if len(members) != 167 or len(unique) != 167 or unique & old_members:
        raise ValueError("Certificate lift must add exactly 167 distinct originals")
    if len(old_members | unique) != 300:
        raise ValueError("The six certified nine-core classes must cover 300 originals")
    method_totals = certified_method_totals(proofs)
    if sum(method_totals.values()) != len(members):
        raise ValueError("Certificate proof subtotals disagree with member cohort")
    return {
        "schema": 1,
        "scope": "four additional order-nine core classes from frozen post-v3 order-ten census",
        "theorem_dismantling": THEOREM_2004,
        "certified_originals_new": len(members),
        "certified_originals_previous": len(old_members),
        "certified_originals_total": len(old_members | unique),
        **method_totals,
        "core_proofs": proofs,
        "members": members,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write a fresh immutable JSON proof index")
    parser.add_argument("--verify", type=Path, help="Recompute and verify a saved JSON proof index")
    args = parser.parse_args()
    if args.output and args.verify:
        parser.error("--output and --verify are mutually exclusive")
    payload = (json.dumps(certify(), indent=2, sort_keys=True) + "\n").encode()
    if args.verify:
        if args.verify.read_bytes() != payload:
            raise ValueError("Saved certificate differs from independently replayed evidence")
        print(f"Verified independently replayed proof index: {args.verify}")
    elif args.output:
        if args.output.exists() and args.output.read_bytes() != payload:
            raise FileExistsError("Refusing to overwrite a mismatched existing certificate")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(payload)
        print(f"Saved 167 independently checked original-graph certificates: {args.output}")
    else:
        info = json.loads(payload)
        info.pop("members")
        print(json.dumps(info, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
