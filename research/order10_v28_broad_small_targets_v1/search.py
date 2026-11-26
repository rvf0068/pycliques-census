"""Finite exhaustive small divergent-retract pilot over ten-v28 stiff originals.

This is a *positive* discovery tool. It makes complete ordinary retraction
certificates, not convergence claims from failures. Each divergent target is
either an independently coaffine-connected-summand join, the previously proved
snub disphenoid, or the complement of C8/C9 (LNP09 Theorem 5.4).

Connected coaffine base graphs through seven vertices are enumerated from
NetworkX's exhaustive graph atlas. We form joins with O_m, dimension m>=1.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import combinations
import hashlib
import json
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("Cannot optimize away positive certificate checks")

import networkx as nx

from research.order10_p4_crossdepth_o15_v25.verify import git_blob, source_rows

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "indeterminate_order_10_v28.txt"
SOURCE_BLOB = "35bb83b56bb8b4fd453b0ba272d354dc6b42e68c"
SNUB = "GQyuzw"
SHARDS = 8


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise AssertionError(reason)


def source_records() -> dict[int, str]:
    require(git_blob(SOURCE.read_bytes()) == SOURCE_BLOB,
            "Frozen ten-v28 original source Git blob changed")
    entries = source_rows(SOURCE)
    require(len(entries) == 1043, "ten-v28 original population changed")
    stiff = {i: line.split()[2] for i, line in entries.items()
             if line.split()[1] == "10"}
    require(len(stiff) == 613 and list(stiff) == sorted(stiff),
            "Unexpected ten-v28 stiff original cohort")
    return stiff


def join(a: nx.Graph, b: nx.Graph) -> nx.Graph:
    x = nx.disjoint_union(a, b)
    x.add_edges_from((u, v) for u in range(len(a))
                     for v in range(len(a), len(a) + len(b)))
    return x


def is_coaffine(g: nx.Graph) -> list[int] | None:
    for phi in nx.algorithms.isomorphism.GraphMatcher(
        g, g
    ).isomorphisms_iter():
        if all(phi[v] != v and not g.has_edge(v, phi[v]) for v in g):
            return [phi[v] for v in range(len(g))]
    return None


def divergent_targets() -> list[dict]:
    targets = []
    for atlas_id, base in enumerate(nx.graph_atlas_g()):
        n = len(base)
        if not (4 <= n <= 7) or not nx.is_connected(base):
            continue
        base = nx.convert_node_labels_to_integers(base)
        alpha = is_coaffine(base)
        if alpha is None:
            continue
        for m in range(1, 4):
            if n + 2 * m > 9:
                continue
            octa_complement = nx.Graph()
            octa_complement.add_nodes_from(range(2 * m))
            octa_complement.add_edges_from((2 * i, 2 * i + 1)
                                           for i in range(m))
            octa = nx.complement(octa_complement)
            target = join(octa, base)
            targets.append({
                "id": f"coaffine-join-O{m}-atlas{atlas_id}",
                "kind": "connected_summand_theorem_4_6",
                "graph": target,
                "m": m,
                "base_graph6": nx.to_graph6_bytes(
                    base, header=False
                ).decode("ascii").strip(),
                "base_coaffination": alpha,
                "atlas_id": atlas_id,
            })

    # The snub is proved divergent by its permanent O24 fourth-iterate
    # retraction; complements of cycles >=8 are covered by LNP09 Thm 5.4.
    for kind, target, name in [
        ("snub_O24_permanent", nx.from_graph6_bytes(SNUB.encode("ascii")),
         "snub-disphenoid"),
        ("cycle_complement_theorem_5_4", nx.complement(nx.cycle_graph(8)),
         "complement-C8"),
        ("cycle_complement_theorem_5_4", nx.complement(nx.cycle_graph(9)),
         "complement-C9"),
    ]:
        targets.append({"id": name, "kind": kind, "graph": target})

    # Distinct descriptions of the same target are harmless, but retain
    # only one when target graphs are isomorphic to avoid repeated searches.
    unique: list[dict] = []
    for item in sorted(targets, key=lambda x: (len(x["graph"]), x["id"])):
        if not any(len(item["graph"]) == len(t["graph"])
                   and item["graph"].number_of_edges() ==
                        t["graph"].number_of_edges()
                   and nx.is_isomorphic(item["graph"], t["graph"])
                   for t in unique):
            unique.append(item)
    for t in unique:
        t["degrees"] = sorted(d for _, d in t["graph"].degree())
        t["edges"] = t["graph"].number_of_edges()
        t["order"] = len(t["graph"])
    return unique


def find_retraction(host: nx.Graph, targets: list[dict]) -> dict | None:
    vertices = tuple(sorted(host))
    by_order: dict[int, list[dict]] = defaultdict(list)
    for t in targets:
        by_order[t["order"]].append(t)

    for order in sorted(by_order):
        for selected in combinations(vertices, order):
            section = host.subgraph(selected)
            edgenum = section.number_of_edges()
            degrees = sorted(d for _, d in section.degree())
            candidates = [
                t for t in by_order[order]
                if t["edges"] == edgenum and t["degrees"] == degrees
            ]
            if not candidates:
                continue

            fixed = set(selected)
            outside = [v for v in vertices if v not in fixed]
            domains = {}
            for v in outside:
                domains[v] = [
                    t for t in selected if all(
                        t == u or host.has_edge(t, u)
                        for u in host[v] if u in fixed
                    )
                ]
            if any(not domains[v] for v in outside):
                continue
            outside.sort(key=lambda v: (len(domains[v]), v))
            assignment: dict[int, int] = {}

            def dfs(k: int) -> bool:
                if k == len(outside):
                    return True
                v = outside[k]
                for image in domains[v]:
                    if all(image == assigned or
                           host.has_edge(image, assigned)
                           for u, assigned in assignment.items()
                           if host.has_edge(u, v)):
                        assignment[v] = image
                        if dfs(k + 1):
                            return True
                        del assignment[v]
                return False

            if not dfs(0):
                continue
            projection = [v if v in fixed else assignment[v] for v in vertices]
            require(all(projection[u] == projection[v] or
                        host.has_edge(projection[u], projection[v])
                        for u, v in host.edges()),
                    "The proposed projection violates source adjacency")

            for t in candidates:
                if nx.is_isomorphic(section, t["graph"]):
                    return {
                        "target_id": t["id"],
                        "target_kind": t["kind"],
                        "target_vertices": list(selected),
                        "retraction_images": projection,
                        "target_order": order,
                        "target_edges": edgenum,
                    }
    return None


def scan_shard(shard: int) -> dict:
    require(type(shard) is int and 0 <= shard < SHARDS,
            "Invalid shard number")
    sources = source_records()
    targets = divergent_targets()
    selected = list(sources.items())[shard::SHARDS]
    out = []
    for index, original in selected:
        G = nx.from_graph6_bytes(original.encode("ascii"))
        require(len(G) == 10, "Wrong stiff ten-core")
        witness = find_retraction(G, targets)
        if witness is not None:
            witness.update({
                "original_index": index,
                "original_graph6": original,
            })
            out.append(witness)
            print(f"POSITIVE original={index} target={witness['target_id']}",
                  flush=True)
    return {
        "schema": 1,
        "kind": "ten_v28_stiff_originals_to_named_divergent_small_targets",
        "source_git_blob": SOURCE_BLOB,
        "shard": shard,
        "shards": SHARDS,
        "source_originals_checked": [i for i, _ in selected],
        "target_library_size": len(targets),
        "target_descriptions": [
            {k: v for k, v in t.items() if k not in ("graph", "degrees")}
            for t in targets
        ],
        "positives": out,
        "no_convergence_inference": True,
    }


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--shard", type=int, choices=range(SHARDS), required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = scan_shard(args.shard)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"PASS: exact small-target retraction pilot "
          f"shard={args.shard} originals={len(result['source_originals_checked'])} "
          f"positives={len(result['positives'])}", flush=True)


if __name__ == "__main__":
    main()
