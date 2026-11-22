"""Certify exact nine-v6 -> v7 and ten-v17 -> v18 census promotion.

The standalone audit reconstructs every nine-core isomorphism from frozen
graph6 rows, checks all 344 promoted original indices, compares every retained
row byte-for-byte, checks immutable Git blob hashes, and proves no extra
classification changed. The optional --proofs independently replays all three
full octahedral projections from merged PR #73.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import networkx as nx

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical assertions")

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
NINE_OLD = ROOT / "indeterminate_order_9_v6.txt"
TEN_OLD = ROOT / "indeterminate_order_10_v17.txt"
NINE_NEW = ROOT / "indeterminate_order_9_v7.txt"
TEN_NEW = ROOT / "indeterminate_order_10_v18.txt"
ROOT_NINE = ROOT / "indeterminate_order_9.txt"
ROOT_TEN = ROOT / "indeterminate_order_10.txt"
MANIFEST = HERE / "promotion_manifest.json"
FROZEN_NINE_BLOB = "48ed753696a2ff3e509c11fc550c64ddb500d675"
FROZEN_TEN_BLOB = "57b97f4b0d4e0b66c2cfc9748826911a55a19e60"
PROVED = {
    249436: ("HEhff^{", 10, 141),
    249574: ("HEhfvx}", 12, 82),
    250814: ("HEhuvzm", 14, 121),
}


def check(value: bool, explanation: str) -> None:
    if not value:
        raise AssertionError(explanation)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def read_rows(path: Path) -> dict[int, str]:
    result = {}
    for line in path.read_text(encoding="utf8").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        check(len(fields) == 6, f"Bad row in {path}: {line}")
        index = int(fields[0])
        check(index not in result, f"Duplicate original index in {path}: {index}")
        check(fields[3:] == ["-", "-", "-"], f"Conditional row in {path}: {line}")
        result[index] = line
    check(list(result) == sorted(result), f"Unsorted McKay original index in {path}")
    return result


def graph(graph6: str) -> nx.Graph:
    result = nx.from_graph6_bytes(graph6.encode("ascii"))
    check(len(result) in (9, 10), f"Incorrect graph6 order: {graph6}")
    return result


def verify_indices() -> None:
    check(
        git_blob(NINE_OLD.read_bytes()) == FROZEN_NINE_BLOB,
        "Immutable nine-v6 source was modified",
    )
    check(
        git_blob(TEN_OLD.read_bytes()) == FROZEN_TEN_BLOB,
        "Immutable ten-v17 source was modified",
    )
    check(
        ROOT_NINE.read_bytes() == NINE_NEW.read_bytes(),
        "Current order-nine root differs from frozen v7",
    )
    check(
        ROOT_TEN.read_bytes() == TEN_NEW.read_bytes(),
        "Current order-ten root differs from frozen v18",
    )

    old9, new9 = read_rows(NINE_OLD), read_rows(NINE_NEW)
    old10, new10 = read_rows(TEN_OLD), read_rows(TEN_NEW)
    check(
        (len(old9), len(new9), len(old10), len(new10))
        == (9, 6, 2025, 1681),
        "Wrong current or historical unresolved count",
    )

    missing9 = set(old9) - set(new9)
    check(missing9 == set(PROVED), "Wrong order-nine removals")
    check(
        all(old9[idx] == new9[idx] for idx in new9),
        "An order-nine retained record was modified",
    )
    for index, (g6, _, _) in PROVED.items():
        check(
            old9[index] == f"{index} 9 {g6} - - -",
            f"Incorrect frozen original nine-source record: {index}",
        )

    manifest = json.loads(MANIFEST.read_text(encoding="utf8"))
    check(manifest["schema"] == 1, "Wrong promotion manifest schema")
    check(
        manifest["previous_order9"] == NINE_OLD.name
        and manifest["previous_order9_git_blob"] == FROZEN_NINE_BLOB
        and manifest["previous_order10"] == TEN_OLD.name
        and manifest["previous_order10_git_blob"] == FROZEN_TEN_BLOB,
        "Manifest historical source mismatch",
    )
    check(
        (manifest["remaining_order9"], manifest["remaining_order10"])
        == (6, 1681),
        "Wrong manifest destination population",
    )
    check(
        manifest["remaining_pared_order10"] == {"9": 800, "10": 881},
        "Wrong manifest pared partition",
    )

    old_core_count = Counter(int(row.split()[1]) for row in old10.values())
    new_core_count = Counter(int(row.split()[1]) for row in new10.values())
    check(old_core_count == {9: 1144, 10: 881}, "Wrong v17 source core partition")
    check(new_core_count == {9: 800, 10: 881}, "Wrong v18 destination partition")

    # Independently determine every lift. Neither the saved manifest nor the
    # previously certified lift counts are used to decide membership.
    sources = {
        index: graph(g6)
        for index, (g6, _, _) in PROVED.items()
    }
    independently_derived: dict[int, tuple[int, str]] = {}
    families = Counter()
    for index, source_row in old10.items():
        fields = source_row.split()
        if fields[1] != "9":
            continue
        candidate = graph(fields[2])
        hits = []
        for reference_index, source in sources.items():
            matcher = nx.algorithms.isomorphism.GraphMatcher(source, candidate)
            if not matcher.is_isomorphic():
                continue
            mapping = matcher.mapping
            check(
                len(mapping) == 9 and set(mapping) == set(source)
                and set(mapping.values()) == set(candidate),
                f"Non-bijection from source core: {index}",
            )
            check(
                all(
                    source.has_edge(u, v)
                    == candidate.has_edge(mapping[u], mapping[v])
                    for u in source for v in source
                ),
                f"False computed core isomorphism: {index}",
            )
            hits.append(reference_index)
        check(len(hits) <= 1, f"Original {index} belongs to multiple source cores")
        if hits:
            reference_index = hits[0]
            independently_derived[index] = (reference_index, source_row)
            families[reference_index] += 1

    check(
        families == Counter({
            index: count for index, (_, _, count) in PROVED.items()
        }),
        f"Wrong certified family sizes: {families}",
    )
    check(len(independently_derived) == 344, "Expected 344 proved ten-vertex originals")
    check(
        set(old10) - set(new10) == set(independently_derived),
        "Unproved deletion or missed ten-v17 dependent graph",
    )
    check(
        all(new10[index] == old10[index] for index in new10),
        "A retained ten-v17 record has been changed",
    )

    promoted = manifest["promoted_order9"]
    check(
        len(promoted) == 3 and {
            entry["index"] for entry in promoted
        } == set(PROVED),
        "Wrong nine-vertex promotion manifest",
    )
    for entry in promoted:
        index = entry["index"]
        g6, dimension, _ = PROVED[index]
        check(
            entry["source_row"] == old9[index]
            and entry["retraction"] == f"P4 -> O{dimension}"
            and entry["certificate"]
            == "research/order9_three_p4_retractions_v1/certificate.json",
            f"Incorrect nine-source certificate metadata {index}",
        )

    saved = manifest["removed_order10"]
    check(len(saved) == 344, "Wrong manifest removed-record count")
    saved_indices: set[int] = set()
    for entry in saved:
        index = entry["original_index"]
        check(index not in saved_indices, f"Duplicate removed original {index}")
        saved_indices.add(index)
        check(index in independently_derived, f"Unproved original in manifest: {index}")
        reference_index, source_row = independently_derived[index]
        check(
            entry["core_index"] == reference_index
            and entry["source_row"] == source_row
            and entry["core_graph6"] == source_row.split()[2]
            and entry["proof_target"] == f"O{PROVED[reference_index][1]}"
            and entry["proof"] == "research/order9_three_p4_retractions_v1/certificate.json",
            f"Incorrect manifest positive proof identity {index}",
        )
    check(saved_indices == set(independently_derived), "Manifest omits dependent originals")
    check(
        manifest["ten_proof_classes"] == {
            f"nine_core_{index}": count
            for index, (_, _, count) in PROVED.items()
        },
        "Wrong family class totals",
    )
    print(
        "PASS: nine-v7=6, ten-v18=1681; 3 independently proved nine-cores, "
        "344 exact disjoint ten-original consequences; "
        "all retained rows unchanged, historical v6/v17 preserved",
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--proofs", action="store_true",
        help="also replay full positive fourth-iterate projections and lifts"
    )
    parser.add_argument(
        "--public", action="store_true",
        help="also validate positive proofs with public pycliques"
    )
    args = parser.parse_args()
    if args.public and not args.proofs:
        parser.error("--public requires --proofs")
    verify_indices()
    if args.proofs:
        from research.order9_three_p4_retractions_v1 import verify as witness
        witness.check_certificates(public=args.public)
        witness.check_ten_lifts()


if __name__ == "__main__":
    main()
