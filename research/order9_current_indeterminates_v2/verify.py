#!/usr/bin/env python3
"""Reconcile historical order-nine McKay indices against existing proofs.

Positive-proofs only. No Betti numbers and no new search verdicts.
The 54-row historical snapshot is authenticated by Git's object hash.
Both exact original McKay indices and graph isomorphism are mandatory.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys

import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_BLOB = "4f210949dad5e7350fc0185c34738e2bf46f9012"
REMOVED = {
    242316: ("HCrlvhz", "HCrlvhz", "PR44", "O5"),
    248687: ("HEher^{", "HEher^{", "PR39", "O4"),
    250693: ("HEhutzm", "HQqvUx}", "PR42", "O4"),
    252075: ("HEh~dzm", "HEh~dzm", "PR45", "O6"),
    255141: ("HEnfbzm", "HEnfbzm", "PR42", "O4"),
}
OTHER_PROVED_NINE_SEEDS = (
    "HEht}pl", "HEht~bl", "HEnb~jl", "HQyuzpt",
    "HUZ~v~}", "HUzrv~}",
)
EXPLICIT_250693_ISOMORPHISM = (4, 2, 3, 0, 1, 5, 6, 7, 8)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def parsed_rows(raw: bytes) -> list[tuple[str, list[str]]]:
    lines = raw.decode("utf-8").splitlines()
    records = [(l, l.split()) for l in lines if l and not l.startswith("#")]
    require(all(len(f) == 6 and f[0].isdigit() for _, f in records),
            "Malformed indexed six-column input")
    numbers = [int(f[0]) for _, f in records]
    require(numbers == sorted(set(numbers)), "Not strictly McKay-index ordered")
    return records


def graph6(text: str) -> nx.Graph:
    graph = nx.from_graph6_bytes(text.encode("ascii"))
    require(nx.is_connected(graph), "Disconnected McKay graph")
    return graph


def assert_stiff(graph: nx.Graph, index: int) -> None:
    neighborhoods = {v: set(graph[v]) | {v} for v in graph}
    for u in graph:
        for v in graph:
            require(u == v or not neighborhoods[u] <= neighborhoods[v],
                    f"McKay {index} is not stiff ({u} dominated by {v})")


def check_permutation(source: nx.Graph, target: nx.Graph,
                      permutation: tuple[int, ...]) -> None:
    n = len(source)
    require(len(target) == n
            and sorted(permutation) == list(range(n)),
            "Invalid explicit isomorphism permutation")
    require(all(
        source.has_edge(u, v)
        == target.has_edge(permutation[u], permutation[v])
        for u in range(n) for v in range(u + 1, n)
    ), "Explicit witness is not a graph isomorphism")


def validate_transition(v1: bytes, v2: bytes, current: bytes,
                        initial: bytes) -> dict:
    require(git_blob(v1) == HISTORICAL_BLOB,
            "Historical 54-case Git object hash changed")
    require(current == v2, "Current order-nine root is not v2")
    old = parsed_rows(v1)
    new = parsed_rows(v2)
    original = {int(f[0]): f for _, f in parsed_rows(initial)}
    require(len(old) == 54 and len(new) == 49,
            "Wrong old/new order-nine populations")
    require(sum(f[4] == "conjectured_divergent" for _, f in old) == 36,
            "Historical conditional cohort changed")
    require(sum(f[4] == "conjectured_divergent" for _, f in new) == 36,
            "New conditional cohort changed")
    require(sum(f[4] == "-" for _, f in new) == 13,
            "New unconditional indeterminate cohort changed")
    expected = [line for line, fields in old
                if int(fields[0]) not in REMOVED]
    require([line for line, _ in new] == expected,
            "Rows were changed, reordered or deleted without a proof")
    old_by_id = {int(f[0]): f for _, f in old}
    seeds = {name: graph6(name) for name in
             set(OTHER_PROVED_NINE_SEEDS)
             | {proof[1] for proof in REMOVED.values()}}
    for index, (original_g6, proved_g6, _pr, _oct) in REMOVED.items():
        fields = old_by_id[index]
        require(
            fields[1:] == ["9", original_g6, "-", "-", "-"],
            f"McKay {index} did not have the expected historic status",
        )
        require(index in original
                and original[index][1:3] == ["9", original_g6],
                f"McKay {index} does not agree with the original indexed census")
        source = graph6(original_g6)
        assert_stiff(source, index)
        target = seeds[proved_g6]
        if index == 250693:
            check_permutation(source, target,
                              EXPLICIT_250693_ISOMORPHISM)
        require(nx.is_isomorphic(source, target),
                f"Wrong independently certified target for McKay {index}")
    for _, fields in new:
        if fields[1] != "9":
            continue
        g = graph6(fields[2])
        require(not any(
            len(h) == len(g) and nx.is_isomorphic(g, h)
            for h in seeds.values()
        ), f"Retained already proved divergent McKay index {fields[0]}")
    return {
        "source": "indeterminate_order_9_v1.txt",
        "remaining": len(new),
        "removed_mckay_indices": sorted(REMOVED),
        "conditional_unchanged": 36,
        "otherwise_indeterminate": 13,
        "all_retained_rows_exact": True,
        "no_known_proved_nine_seed_in_remaining_nine_cores": True,
    }


def replay_existing_positive_proofs() -> None:
    # These are independent archived *existing* retraction certificates.
    sys.path.insert(0, str(ROOT / "scripts"))
    import core9_242316_o5_divergence_v1 as p5
    import core9_252075_o6_divergence_v1 as p6
    import core9_o4_divergence_v1 as p4
    import order10_four_o4_lift_v1 as o4

    require(p5.GRAPH6 == REMOVED[242316][0]
            and p5.INDEX == 242316, "242316 source/identity changed")
    require(p6.GRAPH6 == REMOVED[252075][0]
            and p6.INDEX == 252075, "252075 source/identity changed")
    p5.verify_projection(p5.reconstruct()[-1])
    p6.verify_projection(p6.reconstruct()[-1])
    p4.positive_second_graph()
    for name in ("HQqvUx}", "HEnfbzm"):
        o4.verify_core(name, o4.PROOFS[name])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    v1 = (ROOT / "indeterminate_order_9_v1.txt").read_bytes()
    v2 = (ROOT / "indeterminate_order_9_v2.txt").read_bytes()
    current = (ROOT / "indeterminate_order_9.txt").read_bytes()
    initial = (ROOT / "runs/order9/initial/order9/"
               "indeterminate_order_9.txt").read_bytes()
    result = validate_transition(v1, v2, current, initial)
    replay_existing_positive_proofs()
    if args.self_test:
        for label, old, new, active in (
            ("deleted extra row", v1, v2.replace(b"260910 9 ", b"260911 9 "), current),
            ("wrong current root", v1, v2, v1),
            ("wrong historical index", v1.replace(b"242316 9 ", b"242317 9 "), v2, current),
        ):
            try:
                validate_transition(old, new, active, initial)
            except ValueError:
                pass
            else:
                raise AssertionError("Failed to reject " + label)
    print(result)


if __name__ == "__main__":
    main()
