"""Exact P2-isomorphism promotion of the newly certified 9-vertex core.

The known v12 O12 certificate for ten-vertex McKay 10223405 is
independently replayed by the archived verifier. The program below
checks P2(HEhev^{) ≅ P2(ICXnRi^uo) and tests all unresolved v13
pared graph6 sources for the same certified P2 core.

All iterates and isomorphism checks use public pycliques + NetworkX;
no copied embeddings, fixed labels or graph-specific solver are needed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import networkx as nx
import pycliques

ROOT = Path(__file__).resolve().parents[2]
V13 = ROOT / "indeterminate_order_10_v13.txt"
V13_BLOB = "deca07f54c885d41011e266a03868341c054bdf6"
NINE_V3 = ROOT / "indeterminate_order_9_v3.txt"
NINE_V3_BLOB = "446cbb0be5f40b6014cdb530b1a314de95ff72b2"
NINE_GRAPH6 = "HEhev^{"
TEN_GRAPH6 = "ICXnRi^uo"


def assert_git_blob(path: Path, expected: str) -> bytes:
    raw = path.read_bytes()
    digest = hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\\0" + raw
    ).hexdigest()
    if digest != expected:
        raise AssertionError("Immutable historical index changed: " + str(path))
    return raw


def rows(raw: bytes) -> list[list[str]]:
    data = []
    for line in raw.decode("utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        columns = line.split()
        if len(columns) != 6:
            raise ValueError("Malformed six-column indeterminate source")
        data.append(columns)
    if [int(r[0]) for r in data] != sorted({int(r[0]) for r in data}):
        raise ValueError("Duplicate or nonmonotone McKay index")
    return data


def second_pared_iterate(graph6: str) -> nx.Graph | None:
    graph = pycliques.completely_pared_graph(
        nx.from_graph6_bytes(graph6.encode("ascii"))
    )
    for _ in range(2):
        next_graph = pycliques.clique_graph(graph, bound=600)
        if next_graph is None:
            return None
        graph = pycliques.completely_pared_graph(next_graph)
    return nx.convert_node_labels_to_integers(graph)


def full_isomorphism(a: nx.Graph, b: nx.Graph) -> list[int] | None:
    if len(a) != len(b) or a.number_of_edges() != b.number_of_edges():
        return None
    iso = nx.algorithms.isomorphism.GraphMatcher(
        nx.complement(a), nx.complement(b)
    )
    if not iso.is_isomorphic():
        return None
    mapping = iso.mapping
    if set(mapping) != set(a) or set(mapping.values()) != set(b):
        raise AssertionError("Incomplete exact isomorphism")
    for i in a:
        for j in a:
            if a.has_edge(i, j) != b.has_edge(mapping[i], mapping[j]):
                raise AssertionError("Invalid exact isomorphism")
    return [mapping[i] for i in range(len(a))]


def prove_base() -> tuple[nx.Graph, list[int]]:
    history = rows(assert_git_blob(NINE_V3, NINE_V3_BLOB))
    if not any(r[:3] == ["248936", "9", NINE_GRAPH6] for r in history):
        raise AssertionError("Nine-vertex source is not an unresolved v3 core")
    a = second_pared_iterate(NINE_GRAPH6)
    b = second_pared_iterate(TEN_GRAPH6)
    if a is None or b is None:
        raise AssertionError("Could not compute known second iterates")
    if (len(a), a.number_of_edges()) != (19, 117) or (
        len(b), b.number_of_edges()
    ) != (19, 117):
        raise AssertionError("Unexpected certified P2 sizes")
    witness = full_isomorphism(a, b)
    if witness is None:
        raise AssertionError("The new order-nine P2 isomorphism failed")
    print("CERTIFIED_ORDER9_248936_SECOND_ITERATE", 19, 117, witness)
    return a, witness


def search() -> dict:
    reference, witness = prove_base()
    original = rows(assert_git_blob(V13, V13_BLOB))
    if len(original) != 2787:
        raise AssertionError("Incorrect original v13 census")
    cache: dict[str, list[int] | None] = {}
    hits = []
    skipped = []
    for row in original:
        index, n, g6 = int(row[0]), int(row[1]), row[2]
        if n not in (9, 10):
            raise ValueError("Unexpected order in v13")
        if g6 not in cache:
            candidate = second_pared_iterate(g6)
            if candidate is None:
                cache[g6] = None
            else:
                cache[g6] = full_isomorphism(candidate, reference)
        bijection = cache[g6]
        if bijection is None:
            # A bounded second iterate is never a negative divergence result.
            continue
        hits.append(index)
    if len(hits) != len(set(hits)):
        raise AssertionError("Duplicated certified graph indices")
    if not hits:
        raise AssertionError("Expected at least one ten-vertex consequence")
    print("CERTIFIED_P2_LIFT_COUNT", len(hits),
          "nine_base", NINE_GRAPH6, "ten_base", TEN_GRAPH6,
          "distinct_pared_graph6", sum(v is not None for v in cache.values()))
    print("CERTIFIED_P2_LIFT_INDICES", json.dumps(hits, separators=(",", ":")))
    return {"schema": 1, "v13_blob": V13_BLOB,
            "base_nine_index": 248936,
            "base_ten_index": 10223405,
            "base_p2_map": witness,
            "positive_indices": hits,
            "distinct_matching_pared_graph6": sorted(
                key for key, value in cache.items() if value is not None
            ),
            "source_count": len(original),
            "unresolved_count_after": len(original) - len(hits)}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("scan", "verify"))
    p.add_argument("--output", type=Path)
    opts = p.parse_args()
    certificate = search()
    if opts.output:
        opts.output.parent.mkdir(parents=True, exist_ok=True)
        opts.output.write_text(
            json.dumps(certificate, indent=2, sort_keys=True) + "\n",
            encoding="utf-8"
        )
    if opts.action == "verify":
        if not opts.output:
            raise ValueError("verify requires --output")
        generated = json.loads(opts.output.read_text())
        if generated != certificate:
            raise AssertionError("Saved independently generated cohort differs")
    print("P2_LIFT_SCAN_SUCCESS")


if __name__ == "__main__":
    main()
