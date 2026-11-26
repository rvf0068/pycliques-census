"""Independent replay of ALL positive small-target graph retractions.

The verifier never accepts a positive from a target name alone: it checks
the induced target against a *separately reconstructed* coaffine join or
published divergent named graph, checks the explicit base coaffination,
and checks every source edge and pointwise fixation. Negative results
have no mathematical clique-behavior significance.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("Cannot optimize away positive graph-retraction checks")

import networkx as nx

from research.order10_p4_crossdepth_o15_v25.verify import (
    git_blob, source_rows,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "indeterminate_order_10_v28.txt"
SOURCE_BLOB = "35bb83b56bb8b4fd453b0ba272d354dc6b42e68c"
SHARDS = 8


def require(condition: bool, explanation: str) -> None:
    if not condition:
        raise AssertionError(explanation)


def source_originals() -> dict[int, str]:
    require(git_blob(SOURCE.read_bytes()) == SOURCE_BLOB,
            "Historical ten-v28 source Git blob modified")
    allrows = source_rows(SOURCE)
    require(len(allrows) == 1043, "Wrong ten-v28 original population")
    result = {i: row.split()[2] for i, row in allrows.items()
              if row.split()[1] == "10"}
    require(len(result) == 613 and list(result) == sorted(result),
            "Wrong stiff ten-vertex source universe")
    return result


def checked_target(record: dict) -> nx.Graph:
    kind = record["kind"]
    if kind == "connected_summand_theorem_4_6":
        m = record["m"]
        base = nx.from_graph6_bytes(
            record["base_graph6"].encode("ascii")
        )
        alpha = record["base_coaffination"]
        require(type(m) is int and 1 <= m <= 3
                and 4 <= len(base) <= 7
                and type(record["atlas_id"]) is int
                and nx.is_connected(base)
                and len(alpha) == len(base)
                and sorted(alpha) == list(range(len(base))),
                "Malformed connected coaffine summand")
        require(all(alpha[v] != v and
                    not base.has_edge(v, alpha[v]) for v in base),
                "Connected base automorphism is not coaffine")
        require(all(base.has_edge(u, v) ==
                    base.has_edge(alpha[u], alpha[v])
                    for u in base for v in base),
                "Connected base coaffination is not an automorphism")

        target = nx.Graph()
        target.add_nodes_from(range(2*m+len(base)))
        target.add_edges_from(
            (u, v) for u in range(2*m)
            for v in range(u + 1, 2*m) if u // 2 != v // 2
        )
        target.add_edges_from(
            (u + 2*m, v + 2*m) for u, v in base.edges()
        )
        target.add_edges_from(
            (u, v + 2*m) for u in range(2*m) for v in base
        )
        alpha_total = [v ^ 1 for v in range(2*m)] + [
            2*m + alpha[v] for v in base
        ]
        require(all(alpha_total[v] != v and
                    not target.has_edge(v, alpha_total[v])
                    for v in target),
                "Combined Zykov join map is not coaffine")
        require(all(target.has_edge(u,v) ==
                    target.has_edge(alpha_total[u],alpha_total[v])
                    for u in target for v in target),
                "Combined Zykov join map is not an automorphism")
        require(len(target) <= 9, "Not a proper small target")
    elif kind == "cycle_complement_theorem_5_4":
        ident = record["id"]
        require(ident in ("complement-C8", "complement-C9"),
                "Invalid divergent cycle-complement target")
        n = 8 if ident == "complement-C8" else 9
        target = nx.complement(nx.cycle_graph(n))
    elif kind == "snub_O24_permanent":
        require(record["id"] == "snub-disphenoid",
                "Wrong snub source tag")
        target = nx.from_graph6_bytes(b"GQyuzw")
    else:
        raise AssertionError("Target divergence theorem is not known")
    require(record["order"] == len(target)
            and record["edges"] == target.number_of_edges(),
            "Target order or edge count does not match target theorem")
    return target


def verify_positive(item: dict, universe: dict, descriptions: dict) -> dict:
    index = item["original_index"]
    require(index in universe
            and item["original_graph6"] == universe[index],
            "Positive original McKay source differs from frozen ten-v28")
    G = nx.from_graph6_bytes(universe[index].encode("ascii"))
    require(len(G) == 10 and nx.is_connected(G),
            "Positive host is not a connected ten-core")
    target_id = item["target_id"]
    require(target_id in descriptions
            and item["target_kind"] == descriptions[target_id]["kind"],
            "Positive target has no independently authenticated theorem")
    target = checked_target(descriptions[target_id])
    fixed = item["target_vertices"]
    retraction = item["retraction_images"]
    require(isinstance(fixed, list)
            and len(fixed) == len(target)
            and fixed == sorted(set(fixed))
            and set(fixed) <= set(G)
            and isinstance(retraction, list)
            and len(retraction) == len(G)
            and all(type(v) is int and v in fixed for v in retraction),
            "Incomplete fixed target or retraction projection")
    require(item["target_order"] == len(target)
            and item["target_edges"] == target.number_of_edges(),
            "Wrong induced retraction target dimensions")
    section = G.subgraph(fixed)
    require(nx.is_isomorphic(section, target),
            "The certified divergent target is not induced in the host")
    require(all(retraction[v] == v for v in fixed),
            "Ordinary retraction is not the identity on target")
    require(all(retraction[u] == retraction[v]
                or G.has_edge(retraction[u], retraction[v])
                for u, v in G.edges()),
            "Ordinary retraction fails a source edge")
    return {
        "index": index,
        "target_id": target_id,
        "target_kind": item["target_kind"],
        "fixed_target_order": len(fixed),
        "source_edges_verified": G.number_of_edges(),
        "target_retraction_complete": True,
        "original_K_divergent": True,
    }


def verify_batch(folder: Path) -> dict:
    sources = source_originals()
    paths = sorted(folder.glob("small-target-shard-*.json"))
    require(len(paths) == SHARDS,
            "Need exactly eight independent archived source shards")
    seen = set()
    target_descriptions = None
    positives = []
    for path in paths:
        content = json.loads(path.read_text(encoding="utf-8"))
        shard = content["shard"]
        require(content.get("schema") == 1
                and content.get("kind") ==
                    "ten_v28_stiff_originals_to_named_divergent_small_targets"
                and content.get("source_git_blob") == SOURCE_BLOB
                and content.get("shards") == SHARDS
                and type(shard) is int and 0 <= shard < SHARDS,
                "Unexpected native small-target discovery protocol")
        if target_descriptions is None:
            target_descriptions = content["target_descriptions"]
        require(content["target_descriptions"] == target_descriptions
                and content["target_library_size"] == len(target_descriptions),
                "Disagreement in the shared small-target source library")
        expected = list(sources)[shard::SHARDS]
        require(content["source_originals_checked"] == expected,
                "Shards did not cover the full stiff-original population")
        keys = [row["original_index"] for row in content["positives"]]
        require(keys == sorted(set(keys))
                and set(keys) <= set(expected),
                "Repeated or incorrectly assigned positive original")
        seen.update(expected)
        positives.extend(content["positives"])
    require(len(seen) == 613 and seen == set(sources),
            "Incomplete stiff ten-v28 source scan")
    descriptions = {}
    for item in target_descriptions:
        require(item["id"] not in descriptions,
                "Duplicate target name")
        checked_target(item)
        descriptions[item["id"]] = item
    checked = [verify_positive(row, sources, descriptions)
               for row in positives]
    require(len(checked) == len({r["index"] for r in checked}),
            "An original has multiple competing certificates")
    return {
        "schema": 1,
        "kind": "certified_small_divergent_retracts_in_current_ten_v28",
        "source_git_blob": SOURCE_BLOB,
        "stiff_originals_completely_scanned": 613,
        "named_target_isomorphism_types": len(descriptions),
        "complete_positive_retractions": len(checked),
        "divergent_originals": sorted(r["index"] for r in checked),
        "positive_by_target": dict(Counter(r["target_id"] for r in checked)),
        "no_convergence_inference_from_absence": True,
        "complete_positive_proofs": checked,
    }


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--directory", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = verify_batch(args.directory)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "checked": result["stiff_originals_completely_scanned"],
        "targets": result["named_target_isomorphism_types"],
        "positives": result["complete_positive_retractions"],
        "originals": result["divergent_originals"],
    }, sort_keys=True), flush=True)
    print("PASS: every archived positive small-target retract "
          "independently checked on every host edge", flush=True)


if __name__ == "__main__":
    main()
