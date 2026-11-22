"""Certify exact nine-v8 -> v9 and ten-v19 -> v20 census promotion.

All 220 deleted ten-original core isomorphisms are independently computed
using NetworkX from frozen original graph6 input rows. Exact saved 9-vertex
bijections are checked only AFTER independently deriving the removal set.
Every unchanged original row and every historical Git blob is validated.
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
NINE_OLD = ROOT / "indeterminate_order_9_v8.txt"
TEN_OLD = ROOT / "indeterminate_order_10_v19.txt"
NINE_NEW = ROOT / "indeterminate_order_9_v9.txt"
TEN_NEW = ROOT / "indeterminate_order_10_v20.txt"
ROOT_NINE = ROOT / "indeterminate_order_9.txt"
ROOT_TEN = ROOT / "indeterminate_order_10.txt"
MANIFEST = HERE / "promotion_manifest.json"
FROZEN_NINE_BLOB = "446d7ddba6bdb7f4738730f7de0386bea6546df7"
FROZEN_TEN_BLOB = "cf8047698eb63f8b80ed7104f8cc4307d093fc09"
PROVED = {
    251759: ("HEhvtzm", 15, 129),
    254369: ("HEjfvx}", 13, 91),
}


def check(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError(reason)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def read_rows(path: Path) -> dict[int, str]:
    result: dict[int, str] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        check(len(fields) == 6, f"Malformed census row in {path}: {line}")
        index = int(fields[0])
        check(index not in result, f"Duplicate McKay index {index} in {path}")
        check(fields[1] in ("9", "10"), f"Unexpected pared-order field {index}")
        check(fields[3:] == ["-", "-", "-"], f"Conditional census record {index}")
        graph = nx.from_graph6_bytes(fields[2].encode("ascii"))
        check(len(graph) == int(fields[1]), f"Wrong original core order for {index}")
        result[index] = line
    check(list(result) == sorted(result), f"McKay indices not ascending: {path}")
    return result


def exact_isomorphism(source: nx.Graph, target: nx.Graph) -> dict[int, int] | None:
    matcher = nx.algorithms.isomorphism.GraphMatcher(source, target)
    if not matcher.is_isomorphic():
        return None
    mapping = matcher.mapping
    check(
        len(mapping) == len(source) == len(target) == 9
        and set(mapping) == set(source)
        and set(mapping.values()) == set(target),
        "GraphMatcher returned a non-bijection",
    )
    check(
        all(
            source.has_edge(u, v) == target.has_edge(mapping[u], mapping[v])
            for u in source for v in source
        ),
        "GraphMatcher mapping failed complete adjacency check",
    )
    return mapping


def verify_indices() -> None:
    check(git_blob(NINE_OLD.read_bytes()) == FROZEN_NINE_BLOB,
          "Immutable nine-v8 source was changed")
    check(git_blob(TEN_OLD.read_bytes()) == FROZEN_TEN_BLOB,
          "Immutable ten-v19 source was changed")
    check(ROOT_NINE.read_bytes() == NINE_NEW.read_bytes(),
          "Mutable nine-root is not identical to certified v9")
    check(ROOT_TEN.read_bytes() == TEN_NEW.read_bytes(),
          "Mutable ten-root is not identical to certified v20")

    old9, new9 = read_rows(NINE_OLD), read_rows(NINE_NEW)
    old10, new10 = read_rows(TEN_OLD), read_rows(TEN_NEW)
    check(
        (len(old9), len(new9), len(old10), len(new10)) == (5, 3, 1531, 1311),
        "Unexpected current and historical original populations",
    )
    check(set(old9) - set(new9) == set(PROVED),
          "New nine-v9 index did not remove exactly the proved originals")
    check(set(new9) <= set(old9), "Unexpected new nine-vertex index")
    check(all(new9[i] == old9[i] for i in new9),
          "Unmodified nine-v8 source record was altered")
    check(set(new10) <= set(old10), "New, unproved ten-vertex original appeared")
    check(all(new10[i] == old10[i] for i in new10),
          "Unmodified ten-v19 source record was altered")
    for index, (g6, _, _) in PROVED.items():
        check(old9[index] == f"{index} 9 {g6} - - -",
              f"Wrong immutable nine-v8 positive source identity {index}")

    old_part = Counter(int(r.split()[1]) for r in old10.values())
    new_part = Counter(int(r.split()[1]) for r in new10.values())
    check(old_part == Counter({9: 650, 10: 881}),
          "Wrong frozen ten-v19 pared-core partition")
    check(new_part == Counter({9: 430, 10: 881}),
          "Wrong promoted ten-v20 pared-core partition")

    sources = {
        index: nx.from_graph6_bytes(g6.encode("ascii"))
        for index, (g6, _, _) in PROVED.items()
    }
    recomputed: dict[int, tuple[int, str, dict[int, int]]] = {}
    family_counts: Counter[int] = Counter()
    for original, row in old10.items():
        _, pared_order, graph6, *_ = row.split()
        if pared_order != "9":
            continue
        candidate = nx.from_graph6_bytes(graph6.encode("ascii"))
        hits = []
        for index, source in sources.items():
            mapping = exact_isomorphism(source, candidate)
            if mapping is not None:
                hits.append((index, mapping))
        check(len(hits) <= 1, f"Proved source families overlap at {original}")
        if hits:
            index, mapping = hits[0]
            family_counts[index] += 1
            recomputed[original] = (index, row, mapping)

    check(
        family_counts == Counter({idx: count for idx, (_, _, count) in PROVED.items()}),
        f"Wrong independently recomputed source family sizes: {family_counts}",
    )
    check(len(recomputed) == 220, "Expected exactly 220 ten-v19 source dependents")
    check(set(old10) - set(new10) == set(recomputed),
          "One or more ten-v20 removals lack a positive source or were omitted")

    manifest = json.loads(MANIFEST.read_text(encoding="utf8"))
    check(manifest["schema"] == 1, "Wrong promotion manifest schema")
    check(
        manifest["previous_nine_snapshot"] == NINE_OLD.name
        and manifest["previous_nine_git_blob"] == FROZEN_NINE_BLOB
        and manifest["previous_ten_snapshot"] == TEN_OLD.name
        and manifest["previous_ten_git_blob"] == FROZEN_TEN_BLOB,
        "Manifest does not specify correct immutable source blobs",
    )
    check(
        (manifest["previous_nine_count"], manifest["new_nine_count"],
         manifest["previous_ten_count"], manifest["new_ten_count"],
         manifest["removed_ten_count"], manifest["ten_pared_nine_old"],
         manifest["ten_pared_nine_new"], manifest["ten_pared_ten_unchanged"])
        == (5, 3, 1531, 1311, 220, 650, 430, 881),
        "Manifest has wrong promotion population or pared-core partition",
    )
    proofs = manifest["source_proofs"]
    check(len(proofs) == 2 and len({p["mckay_index"] for p in proofs}) == 2,
          "Manifest source proofs not unique")
    for item in proofs:
        index = item["mckay_index"]
        check(index in PROVED, f"Unknown positive original source {index}")
        g6, dimension, count = PROVED[index]
        check(
            item["source_row"] == old9[index]
            and item["certificate"]
            == f"research/order9_{index}_p4_o{dimension}_v1/certificate.json"
            and item["retraction"] == f"P4->O{dimension}"
            and item["ten_originals"] == count,
            f"Incorrect positive-source provenance for {index}",
        )

    saved = manifest["removed_ten_originals"]
    check(len(saved) == 220, "Manifest lacks exact 220 original records")
    seen: set[int] = set()
    for item in saved:
        index = item["original_index"]
        check(index not in seen and index in recomputed,
              f"Missing, extra or duplicate removed original {index}")
        seen.add(index)
        reference, row, mapping = recomputed[index]
        g6, dimension, _ = PROVED[reference]
        check(
            item["source_row"] == row
            and item["pared_core_graph6"] == row.split()[2]
            and item["source_mckay"] == reference
            and item["certificate"] ==
            f"research/order9_{reference}_p4_o{dimension}_v1/certificate.json"
            and item["retraction"] == f"P4->O{dimension}",
            f"Incorrect saved original proof identity {index}",
        )
        m = item["core_isomorphism"]
        check(isinstance(m, list) and len(m) == 9 and
              sorted(m) == list(range(9)),
              f"Invalid saved nine-vertex bijection {index}")
        source = sources[reference]
        target = nx.from_graph6_bytes(row.split()[2].encode("ascii"))
        check(
            all(
                source.has_edge(u, v) == target.has_edge(m[u], m[v])
                for u in source for v in source
            ),
            f"Saved exact nine-core mapping fails adjacency check {index}",
        )
    check(seen == set(recomputed),
          "Promotion manifest missing or duplicating a classified original")

    print(
        "PASS: nine-v9=3 ten-v20=1311; "
        "K-divergent nine-McKay 251759 and 254369 removed; "
        "129+91=220 disjoint ten-originals independently recomputed; "
        "every saved source mapping and retained record checked; "
        "immutable nine-v8 and ten-v19 source blobs unchanged",
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proofs", action="store_true",
                        help="also replay complete 403- and 394-image retractions")
    parser.add_argument("--public", action="store_true")
    args = parser.parse_args()
    if args.public and not args.proofs:
        parser.error("--public requires --proofs")
    verify_indices()
    if args.proofs:
        from research.order9_two_p4_retractions_v1.verify import (
            PROVED as POSITIVES,
            verify_positive,
            verify_ten_lifts,
        )
        check(set(POSITIVES) == set(PROVED), "Positive proof source set changed")
        for index in PROVED:
            verify_positive(index, public=args.public)
        verify_ten_lifts()


if __name__ == "__main__":
    main()
