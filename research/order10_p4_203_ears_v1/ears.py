"""Complete fourteen-ear certificates and all-iterate homotopy corollaries.

For each indicated ten-vertex original G and unresolved nine-vertex H:
    P4(G) == P4(H) + x,  N(x) = {a,b},  a not adjacent b.
All 14 complete induced-subgraph bijections and ordinary graph
retractions are checked from the frozen original graph6 codes.

The merged general complete-ear theorem (immutable, pinned) then gives:
    Delta(P_(4+j)(G)) ~= Delta(P_(4+j)(H)) wedge S^1, all j >= 0.
In particular these 14 ten-vertex originals are not K-null. No
K-divergence status follows, since the nine-vertex sources are unresolved.
"""
from __future__ import annotations

import base64
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import sys

if sys.flags.optimize:
    raise RuntimeError("Optimized ear proof is forbidden")

import networkx as nx

from research.order10_p4_cap_rescue_v24.verify import (
    p4_from_graph6, check_bijection, constrained_matcher,
)
from research.order10_small_p4_98_v1.verify import (
    row_hash, verify_record as reconstruct_ten_p4,
)
from research.order10_p4_203_ears_v1.verify import (
    frozen, require, validated_catalog, EXPECTED_EAR_TARGETS,
)

HERE = Path(__file__).resolve().parent


def bit_vertices(mask: int):
    while mask:
        low = mask & -mask
        yield low.bit_length() - 1
        mask ^= low


def source_nine() -> dict[int, str]:
    rows = frozen("indeterminate_order_9_v9.txt").decode("ascii")
    all_rows = {}
    for line in rows.splitlines():
        if line and not line.startswith("#"):
            values = line.split()
            require(len(values) == 6 and values[1] == "9"
                    and values[3:] == ["-", "-", "-"],
                    "Unexpected frozen unresolved nine-original row")
            all_rows[int(values[0])] = values[2]
    require(len(all_rows) == 3 and
            all(i in all_rows for i in EXPECTED_EAR_TARGETS),
            "The frozen nine-v9 core inventory changed")
    return all_rows


def connected(rows: list[int]) -> bool:
    if not rows:
        return False
    found = {0}
    frontier = [0]
    while frontier:
        u = frontier.pop()
        for v in bit_vertices(rows[u]):
            if v not in found:
                found.add(v)
                frontier.append(v)
    return len(found) == len(rows)


def prove_one(row: dict, all_ten: dict[int, dict],
              nine_g6: dict[int, str],
              nine_p4: dict[int, list[int]]) -> dict:
    idx, nine_idx = row["ten_index"], row["nine_index"]
    require(idx in all_ten and nine_idx in EXPECTED_EAR_TARGETS,
            "A purported ear is not an authenticated current original")
    original = all_ten[idx]
    require(row["ten_graph6"] == original["graph6"]
            and row["nine_graph6"] == nine_g6[nine_idx]
            and row["p3_ten"] == original["p3"]
            and row["p4_ten"] == original["p4"]
            and row["ten_p4_adj_sha256"] == original["p4_adj_sha256"],
            "Ear certificate does not match the frozen original graph6")

    nine = nine_p4[nine_idx]
    _raw, ten = reconstruct_ten_p4(original)
    n = len(nine)
    require(n + 1 == len(ten)
            and row["p4_nine"] == [
                n, sum(x.bit_count() for x in nine)//2
            ] and connected(nine) and connected(ten),
            "Fourth-iterate ear target is not the specified connected graph")

    special = row["unique_degree_two_vertex"]
    require(type(special) is int and 0 <= special <= n
            and [special] == [
                u for u in range(n+1) if ten[u].bit_count() == 2
            ], "Wrong unique extra degree-two ear vertex")
    original_neighbors = list(bit_vertices(ten[special]))
    require(len(original_neighbors) == 2
            and not (ten[original_neighbors[0]] >>
                     original_neighbors[1] & 1),
            "Ear vertex does not have two anticomplete singleton sides")

    survivors = [u for u in range(n+1) if u != special]
    remap = {u: i for i, u in enumerate(survivors)}
    core = [
        sum(1 << remap[v] for v in bit_vertices(ten[u])
            if v != special) for u in survivors
    ]
    require(row["nine_to_ten_core_bijection_encoding"] ==
            "uint16_little_endian_base64",
            "Unsupported map compression or canonical vertex coordinates")
    enc = base64.b64decode(
        row["nine_to_ten_core_map_b64"], validate=True
    )
    require(len(enc) == n*2 and
            hashlib.sha256(enc).hexdigest() ==
                row["nine_to_ten_core_map_sha256"],
            "Recorded nine-to-ten complete vertex permutation changed")
    perm = list(struct.unpack("<" + "H"*n, enc))
    require(sorted(perm) == list(range(n)),
            "Nine-to-ten induced copy is not a complete bijection")

    # Edge and NONEDGE preservation on every ordered vertex pair.
    check_bijection(nine, core, perm)
    # A second independent labeled-graph algorithm verifies this exact
    # saved permutation on the complementary graph, not a different map.
    constrained_matcher(nine, core, perm)

    embedded = [survivors[perm[u]] for u in range(n)]
    require(len(set(embedded)) == n and
            special not in embedded, "Nine-core section not induced")
    inverse = {embedded[j]: j for j in range(n)}
    neighbors = sorted(inverse[v] for v in original_neighbors)
    require(neighbors == row["neighbor_images_in_nine"]
            and not (nine[neighbors[0]] >> neighbors[1] & 1),
            "The ear neighbors are not the recorded anticomplete pair")
    w = row["retraction_image_of_degree_two_vertex"]
    require(type(w) is int and 0 <= w < n
            and all(w == a or bool(nine[w] & (1 << a))
                    for a in neighbors),
            "The extra vertex has no valid pinned retraction image")
    ret = [inverse[u] if u != special else w for u in range(n+1)]
    require(all(ret[embedded[i]] == i for i in range(n)),
            "The ordinary retraction fails to fix its target")
    for u in range(n+1):
        for v in bit_vertices(ten[u]):
            if u < v:
                require(ret[u] == ret[v] or
                        bool(nine[ret[u]] & (1 << ret[v])),
                        f"Ordinary retraction sends source edge {u}-{v} "
                        "to a target nonedge")
    require(row.get("all_pairs_iso_verified") is True and
            row.get("retraction_checked_on_all_source_edges") is True,
            "Archived proof claims unexpectedly changed")
    return {
        "ten_original": idx,
        "nine_original": nine_idx,
        "ten_P4_shape": row["p4_ten"],
        "nine_P4_shape": row["p4_nine"],
        "attachment_vertex": special,
        "attachment_neighbors_in_nine_P4": neighbors,
        "retraction_image": w,
        "all_pair_isomorphism": True,
        "ordinary_retraction_all_source_edges": True,
        "complete_ear_attachment": True,
        "all_iterate_homotopy_formula_by_pinned_general_theorem": True,
        "not_K_null": True,
        "K_divergence": "UNRESOLVED",
    }


def verify() -> dict:
    # The general mathematical result is already proved in the
    # independently merged theorem, NOT inferred by finite extrapolation.
    theorem = frozen("research/snub_ear_all_iterates_homotopy_v1.md")
    require(b"all-iterate complete-ear formula" in theorem
            and b"for every integer" in theorem,
            "The archived general complete-ear theorem is unavailable")
    cases, _ = validated_catalog()
    all_ten = {r["index"]: r for r in cases}
    nine_g6 = source_nine()
    archive = json.loads(frozen(
        "research/order10_p4_203_ears_v1/ear_retractions.json"
    ))
    records = archive["records"]
    require(archive.get("schema") == 1 and
            archive.get("kind") ==
                "14 complete P4 induced embeddings and ordinary graph retractions onto P4 of 2 unresolved nine-vertex graphs"
            and len(records) == 14
            and [x["ten_index"] for x in records] ==
                sorted({x["ten_index"] for x in records})
            and Counter(x["nine_index"] for x in records) ==
                {251628: 7, 260040: 7},
            "The 14 canonical complete-ear source cases changed")

    nine_p4 = {}
    for idx in EXPECTED_EAR_TARGETS:
        _raw, pared, _rounds, _p3 = p4_from_graph6(nine_g6[idx])
        require(connected(pared), "The nine-reference fourth iterate is disconnected")
        nine_p4[idx] = pared

    results = []
    for record in records:
        result = prove_one(record, all_ten, nine_g6, nine_p4)
        results.append(result)
        print(f"COMPLETE-EAR CERTIFIED: ten={result['ten_original']} "
              f"nine={result['nine_original']} P4=+one degree-2 vertex; "
              "complete bijection, ordinary retraction, permanent S1",
              flush=True)
    return {
        "schema": 1,
        "kind": "fourteen_certified_complete_ears_and_all_iterate_homotopy",
        "source_ten_indeterminate_count": 1052,
        "nine_indeterminate_count": 3,
        "ear_count": 14,
        "frozen_unresolved_nine_sources": list(EXPECTED_EAR_TARGETS),
        "all_iterates_stably_have_extra_S1": True,
        "all_14_proved_not_K_null": True,
        "new_K_divergence_verdicts": 0,
        "records": results,
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    options = parser.parse_args()
    result = verify()
    print("PASS: fourteen complete-ear isomorphisms and graph retractions "
          "from original nine- and ten-vertex graph6; no divergent "
          "classification promoted", flush=True)
    if options.output:
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(json.dumps(result, sort_keys=True, indent=2)
                                  + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
