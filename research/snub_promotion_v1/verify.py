"""Independent positive-only audit of snub-dependent order-nine and ten promotions.

This verifier uses NetworkX only, not pycliques' classifier or saved projection.
Each accepted index gets a concrete finite proof built from induced isomorphism,
graph retraction, valid closed-neighborhood folds, a triangle-free edge removal,
or an admissible local-bridge inverse cutpoint extension.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
from collections import Counter
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
SNUB = nx.from_graph6_bytes(b"GQyuzw")
FROZEN = {
    9: ("indeterminate_order_9_v2.txt", "indeterminate_order_9_v3.txt",
        "0a18b1a67434e0995e768b175878a5875bff7de1", 49, 36, 13),
    10: ("indeterminate_order_10_v10.txt", "indeterminate_order_10_v11.txt",
         "35acbd4efbe6fd6816ff0b5c749b8b20b4455d1e", 7219, 4389, 2830),
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def rows(raw: bytes) -> dict[int, tuple[str, ...]]:
    data: dict[int, tuple[str, ...]] = {}
    for line in raw.decode().splitlines():
        if not line or line.startswith("#"):
            continue
        fields = tuple(line.split())
        require(len(fields) == 6, "Expected six columns")
        index = int(fields[0])
        require(index not in data, f"Duplicate McKay index {index}")
        data[index] = fields
    require(list(data) == sorted(data), "McKay indices are not sorted")
    return data


def pare(graph: nx.Graph) -> tuple[nx.Graph, list[tuple[int, int]]]:
    """Delete only closed-neighborhood dominated vertices; record every fold."""
    h = graph.copy()
    folds: list[tuple[int, int]] = []
    while True:
        closed = {x: set(h[x]) | {x} for x in h}
        pair = next(
            ((x, y) for x in sorted(h) for y in sorted(h)
             if x != y and closed[x] <= closed[y]),
            None,
        )
        if pair is None:
            return h, folds
        x, y = pair
        folds.append((x, y))
        h.remove_node(x)


def induced_snub_retraction(graph: nx.Graph) -> dict | None:
    """Exhaustively search all 8-vertex induced snubs and outside projections."""
    if len(graph) < 8:
        return None
    nodes = sorted(graph)
    for eight in itertools.combinations(nodes, 8):
        target = graph.subgraph(eight)
        if target.number_of_edges() != 18 or not nx.is_isomorphic(target, SNUB):
            continue
        fixed = set(eight)
        outside = [v for v in nodes if v not in fixed]
        domains: dict[int, list[int]] = {}
        for v in outside:
            domains[v] = [
                t for t in eight if all(
                    t == w or target.has_edge(t, w)
                    for w in graph[v] if w in fixed
                )
            ]
        if any(not choices for choices in domains.values()):
            continue
        outside.sort(key=lambda v: (len(domains[v]), v))
        assignment: dict[int, int] = {}

        def solve(i: int) -> bool:
            if i == len(outside):
                return True
            v = outside[i]
            for t in domains[v]:
                if all(
                    t == assignment[u] or target.has_edge(t, assignment[u])
                    for u in assignment if graph.has_edge(u, v)
                ):
                    assignment[v] = t
                    if solve(i + 1):
                        return True
                    del assignment[v]
            return False

        if solve(0):
            projection = {v: (v if v in fixed else assignment[v]) for v in nodes}
            require(
                all(
                    projection[u] == projection[v]
                    or target.has_edge(projection[u], projection[v])
                    for u, v in graph.edges
                ),
                "Retraction violates a host edge",
            )
            require(all(projection[v] == v for v in eight),
                    "Projection must fix its induced target")
            return {"target": list(eight),
                    "outside_images": sorted(assignment.items())}
    return None


def proof_by_retraction_or_fold(graph: nx.Graph) -> dict | None:
    pared, folds = pare(graph)
    witness = induced_snub_retraction(pared)
    if witness is not None:
        return {"folds": folds, "retraction": witness}
    return None


def proof_nontriangle_edge(graph: nx.Graph, *, allow_inverse: bool = True) -> dict | None:
    for u, v in graph.edges():
        if set(graph[u]) & set(graph[v]):
            continue
        target = graph.copy()
        target.remove_edge(u, v)
        proof = proof_by_retraction_or_fold(target)
        if proof is None and allow_inverse:
            pared, folds = pare(target)
            nested = proof_inverse_cutpoint(pared, allow_nontriangle=False)
            if nested is not None:
                proof = {"folds": folds, "inverse_cutpoint_subproof": nested}
        if proof is not None:
            return {"removed_triangle_free_edge": [u, v], "subproof": proof}
    return None


def proof_inverse_cutpoint(graph: nx.Graph, *, allow_nontriangle: bool = True) -> dict | None:
    """Verify an admissible vertex split followed by triangle-free removal."""
    for w in sorted(graph):
        neighborhood = graph.subgraph(list(graph[w]))
        if len(neighborhood) < 2:
            continue
        components = list(nx.connected_components(neighborhood))
        if len(components) < 2:
            continue
        rest = components[1:]
        for k in range(len(rest)):
            for choice in itertools.combinations(range(len(rest)), k):
                left = set(components[0])
                for j in choice:
                    left.update(rest[j])
                right = set(graph[w]) - left
                if not right:
                    continue
                u, v = max(graph) + 1, max(graph) + 2
                ext = graph.copy()
                ext.remove_node(w)
                ext.add_edges_from((u, x) for x in left)
                ext.add_edges_from((v, x) for x in right)
                ext.add_edge(u, v)
                no_edge = ext.copy()
                no_edge.remove_edge(u, v)
                # The added edge must be a local bridge: other paths length >= 4.
                if nx.has_path(no_edge, u, v) and nx.shortest_path_length(
                    no_edge, u, v
                ) < 4:
                    continue
                require(not (set(ext[u]) & set(ext[v])),
                        "Added edge is contained in a triangle")
                proof = proof_by_retraction_or_fold(no_edge)
                if proof is None and allow_nontriangle:
                    proof = proof_nontriangle_edge(no_edge, allow_inverse=False)
                if proof is not None:
                    return {
                        "cutpoint": w, "partition": [sorted(left), sorted(right)],
                        "added_edge": [u, v], "subproof": proof,
                    }
    return None


def prove(row: tuple[str, ...]) -> dict | None:
    _, _, graph6, rule, status, label = row
    require(status == "conjectured_divergent" and label == "snub_disphenoid",
            "This verifier accepts snub-dependent entries only")
    graph = nx.from_graph6_bytes(graph6.encode("ascii"))
    require(nx.is_connected(graph), "Pared core must be connected")
    if rule == "reference":
        if nx.is_isomorphic(graph, SNUB):
            return {"rule": rule}
    elif rule == "retracts":
        witness = induced_snub_retraction(graph)
        if witness is not None:
            return {"rule": rule, "witness": witness}
    elif rule == "non_triangle_edge":
        witness = proof_nontriangle_edge(graph)
        if witness is not None:
            return {"rule": rule, "witness": witness}
    elif rule == "inverse_cutpoint_extension":
        witness = proof_inverse_cutpoint(graph)
        if witness is not None:
            return {"rule": rule, "witness": witness}
    return None


def verify_order(order: int) -> dict:
    src_name, dest_name, sha, expected_old, removed, remaining = FROZEN[order]
    source = (ROOT / src_name).read_bytes()
    require(blob_sha(source) == sha, f"Frozen {src_name} was modified")
    old = rows(source)
    new_data = (ROOT / dest_name).read_bytes()
    current = (ROOT / f"indeterminate_order_{order}.txt").read_bytes()
    require(new_data == current, "Current root must equal new version")
    new = rows(new_data)
    require((len(old), len(new)) == (expected_old, remaining),
            "Unexpected source/new population")
    removed_rows = {idx: row for idx, row in old.items() if idx not in new}
    require(len(removed_rows) == removed, "Unexpected removal count")
    require(
        all(row[4:] == ("conjectured_divergent", "snub_disphenoid")
            for row in removed_rows.values()),
        "Only snub-dependent indices may be removed",
    )
    require(all(idx in old and old[idx] == row for idx, row in new.items()),
            "Retained rows changed their contents")
    require(
        set(old) - set(new) == {
            idx for idx, row in old.items()
            if row[4:] == ("conjectured_divergent", "snub_disphenoid")
        },
        "Did not remove exactly the snub-dependent cohort",
    )
    missing = []
    for idx, row in removed_rows.items():
        witness = prove(row)
        if witness is None:
            missing.append((idx, row))
    require(not missing, f"Missing {len(missing)} independent snub proofs: "
            + repr(missing[:30]))
    return {
        "order": order, "old": len(old), "new": len(new),
        "proven_divergent": removed,
        "rules": dict(sorted(Counter(row[3] for row in removed_rows.values()).items())),
        "distinct_proved_core_graphs": len({row[2] for row in removed_rows.values()}),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--order", type=int, choices=(9, 10))
    args = parser.parse_args()
    orders = (args.order,) if args.order else (9, 10)
    for order in orders:
        print(verify_order(order), flush=True)


if __name__ == "__main__":
    main()
