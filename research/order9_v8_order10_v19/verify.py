"""Exact certified nine-v7 -> v8 and ten-v18 -> v19 census promotion.

The 150 removals are recomputed independently from immutable v18
nine-pared graph6 cores, not selected from the saved manifest. Every
explicit manifest vertex bijection and exact original source row is
checked, and all retained records must remain byte-for-byte identical.
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
NINE_OLD = ROOT / "indeterminate_order_9_v7.txt"
TEN_OLD = ROOT / "indeterminate_order_10_v18.txt"
NINE_NEW = ROOT / "indeterminate_order_9_v8.txt"
TEN_NEW = ROOT / "indeterminate_order_10_v19.txt"
ROOT_NINE = ROOT / "indeterminate_order_9.txt"
ROOT_TEN = ROOT / "indeterminate_order_10.txt"
MANIFEST = HERE / "promotion_manifest.json"
NINE_BLOB = "6f1e05d6b6bb0f1b4f2638ad73a7163f26ab0345"
TEN_BLOB = "9dba1f3359d6e90fbda1026d672173fa2461b460"
MCKAY = 251902
GRAPH6 = "HEhvvzm"
SOURCE_ROW = "251902 9 HEhvvzm - - -"
CERTIFICATE = "research/order9_251902_p4_o17_v1/certificate.json"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_blob(data: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()


def rows(path: Path) -> dict[int, str]:
    result: dict[int, str] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        check(len(parts) == 6, f"Malformed six-field row in {path}: {line}")
        original = int(parts[0])
        check(original not in result, f"Duplicate original McKay {original}")
        check(parts[3:] == ["-", "-", "-"], f"Conditional census row {original}")
        check(parts[1] in ("9", "10"), f"Incorrect pared graph order for {original}")
        check(
            len(nx.from_graph6_bytes(parts[2].encode("ascii"))) == int(parts[1]),
            f"Graph6/declared pared order disagreement {original}",
        )
        result[original] = line
    check(list(result) == sorted(result), f"Original McKay rows out of order: {path}")
    return result


def verify_indices() -> None:
    check(git_blob(NINE_OLD.read_bytes()) == NINE_BLOB, "Frozen v7 nine-source changed")
    check(git_blob(TEN_OLD.read_bytes()) == TEN_BLOB, "Frozen v18 ten-source changed")
    check(ROOT_NINE.read_bytes() == NINE_NEW.read_bytes(), "Nine-root does not equal v8")
    check(ROOT_TEN.read_bytes() == TEN_NEW.read_bytes(), "Ten-root does not equal v19")

    old9, new9 = rows(NINE_OLD), rows(NINE_NEW)
    old10, new10 = rows(TEN_OLD), rows(TEN_NEW)
    check(
        (len(old9), len(new9), len(old10), len(new10))
        == (6, 5, 1681, 1531),
        "Incorrect old/new census population",
    )
    check(old9[MCKAY] == SOURCE_ROW, "Unexpected original nine-core identity")
    check(set(old9) - set(new9) == {MCKAY}, "Wrong order-nine removal")
    check(set(new9) <= set(old9), "Unexpected new nine-original")
    check(
        all(new9[idx] == old9[idx] for idx in new9),
        "A retained nine-original record has been modified",
    )

    old_partition = Counter(int(row.split()[1]) for row in old10.values())
    new_partition = Counter(int(row.split()[1]) for row in new10.values())
    check(old_partition == Counter({9: 800, 10: 881}), "Unexpected v18 pared partition")
    check(new_partition == Counter({9: 650, 10: 881}), "Unexpected v19 pared partition")
    check(set(new10) <= set(old10), "New original ten-index unexpectedly appeared")
    check(
        all(new10[idx] == old10[idx] for idx in new10),
        "A retained ten-original record has been changed",
    )

    # Independently recompute exactly which original ten graphs inherit
    # McKay 251902's K-divergence. The manifest is NOT used to choose them.
    proved_graph = nx.from_graph6_bytes(GRAPH6.encode("ascii"))
    recomputed: dict[int, tuple[str, nx.Graph]] = {}
    for index, line in old10.items():
        _, pared, graph6, *_ = line.split()
        if pared != "9":
            continue
        core = nx.from_graph6_bytes(graph6.encode("ascii"))
        matcher = nx.algorithms.isomorphism.GraphMatcher(proved_graph, core)
        if matcher.is_isomorphic():
            mapping = matcher.mapping
            check(
                len(mapping) == 9 and set(mapping) == set(proved_graph)
                and set(mapping.values()) == set(core),
                f"Invalid source to ten-core mapping for {index}",
            )
            check(
                all(
                    proved_graph.has_edge(u, v)
                    == core.has_edge(mapping[u], mapping[v])
                    for u in proved_graph for v in proved_graph
                ),
                f"False nine-core isomorphism for original ten-index {index}",
            )
            recomputed[index] = (line, core)

    check(len(recomputed) == 150, "Expected 150 independently classified lifts")
    check(
        set(old10) - set(new10) == set(recomputed),
        "Unproved deletion or missing K-divergent original",
    )

    saved = json.loads(MANIFEST.read_text(encoding="utf8"))
    check(saved["schema"] == 1, "Wrong manifest schema")
    check(
        saved["previous_nine_snapshot"] == NINE_OLD.name
        and saved["previous_nine_git_blob"] == NINE_BLOB
        and saved["previous_ten_snapshot"] == TEN_OLD.name
        and saved["previous_ten_git_blob"] == TEN_BLOB,
        "Manifest does not identify exact frozen sources",
    )
    check(
        saved["removed_nine_source_row"] == SOURCE_ROW
        and saved["source_certificate"] == CERTIFICATE
        and saved["source_proof"] == "P4->O17",
        "Manifest does not link the positive retraction proof",
    )
    check(
        (saved["previous_nine_count"], saved["new_nine_count"],
         saved["previous_ten_count"], saved["new_ten_count"],
         saved["source_family_size"],
         saved["ten_pared_nine_old"], saved["ten_pared_nine_new"],
         saved["ten_pared_ten_unchanged"])
        == (6, 5, 1681, 1531, 150, 800, 650, 881),
        "Wrong promotion manifest counts",
    )
    manifest_rows = saved["removed_ten_originals"]
    check(len(manifest_rows) == 150, "Wrong number of explicit promoted records")
    seen: set[int] = set()
    for item in manifest_rows:
        index = item["original_index"]
        check(index in recomputed and index not in seen, f"Bad promoted index {index}")
        seen.add(index)
        row, core = recomputed[index]
        check(
            item["source_row"] == row
            and item["pared_core_graph6"] == row.split()[2]
            and item["source_mckay"] == MCKAY
            and item["certificate"] == CERTIFICATE
            and item["retraction"] == "P4->O17",
            f"Incorrect saved promotion provenance for {index}",
        )
        mapping = item["core_isomorphism"]
        check(
            isinstance(mapping, list)
            and len(mapping) == 9
            and sorted(mapping) == list(range(9)),
            f"Saved mapping not a bijection at {index}",
        )
        check(
            all(
                proved_graph.has_edge(u, v)
                == core.has_edge(mapping[u], mapping[v])
                for u in proved_graph for v in proved_graph
            ),
            f"Saved nine-core mapping is not an isomorphism at {index}",
        )
    check(seen == set(recomputed), "Manifest omitted or duplicated a proven lift")
    print(
        "PASS nine-v8=5 ten-v19=1531: exactly 150 disjoint "
        "McKay-251902 dependent originals promoted, all 150 explicit "
        "vertex isomorphisms checked, every retained row unchanged, "
        "frozen v7/v18 Git blobs preserved",
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--proofs", action="store_true",
        help="replay complete 461-image P4 -> O17 positive certificate",
    )
    parser.add_argument("--public", action="store_true")
    args = parser.parse_args()
    if args.public and not args.proofs:
        parser.error("--public requires --proofs")
    verify_indices()
    if args.proofs:
        from research.order9_251902_p4_o17_v1.verify import (
            verify_positive, verify_ten_lifts,
        )
        verify_positive(public=args.public)
        verify_ten_lifts()


if __name__ == "__main__":
    main()
