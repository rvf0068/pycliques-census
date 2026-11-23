"""Independently certify ten-vertex P3 low-degree retraction obstructions.

A necessary condition for a t-vertex induced retract T with
max degree <= t-3 is: its vertex set S is an OPEN 2-dominating
set in the complement H=comp(X), i.e. |N_H(x) cap S| >= 2
for EVERY host vertex x (selected target vertices included).

Enumerate ALL such sets of cardinality ten, using pure Python
integer DPLL, then independently check the fixed-target unary
image condition. This verifier chooses a most-constrained
unmet row when branching, unlike the separately written C++
search. No solver seed, saved target, timeout or floating
point relaxation enters the proof.
"""
from __future__ import annotations

import argparse
import itertools
import random
import sys
from pathlib import Path

import networkx as nx

from research.order9_p3_eight_vertex_obstruction_v1.verify import (
    SOURCES,
    check,
    complement_masks,
    reconstruct_p3,
    verify_frozen_sources,
)

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical assertions")

EXPECTED = {249576: 2161, 251628: 12822, 260040: 17620}


def enumerate_open_two(
    h: tuple[int, ...], target_size: int
) -> tuple[set[int], int, int]:
    """Complete pure-integer search for all exact-size open double covers.

    Here every row has a mandatory deficit of 2, even when that
    row's vertex is itself selected (unlike an external cover).
    A bitmask denotes the selected vertices. Every branch is finite.

    Forced selections follow a row whose remaining options equal its
    deficit. A total-deficit optimistic upper bound safely prunes
    a branch if the largest possible gains of the remaining selected
    vertices cannot meet all outstanding row deficits.
    """
    n = len(h)
    check(0 < target_size <= n < 64, "Invalid finite enumeration dimension")
    full = (1 << n) - 1
    solutions: set[int] = set()
    nodes = forced = 0

    def dfs(selected: int, excluded: int) -> None:
        nonlocal nodes, forced
        nodes += 1
        if selected.bit_count() > target_size:
            return

        while True:
            undecided = full & ~(selected | excluded)
            outstanding = []
            unsatisfied = total_demand = 0
            changed = False
            for x, mask in enumerate(h):
                deficit = 2 - (mask & selected).bit_count()
                if deficit <= 0:
                    continue
                available = mask & undecided
                capacity = available.bit_count()
                if capacity < deficit:
                    return
                if capacity == deficit:
                    selected |= available
                    forced += capacity
                    changed = True
                    break
                outstanding.append(
                    (capacity - deficit, capacity, x, available, deficit)
                )
                unsatisfied |= 1 << x
                total_demand += deficit
            if selected.bit_count() > target_size:
                return
            if not changed:
                break

        slots = target_size - selected.bit_count()
        if not outstanding:
            # Every superset of an open double cover is also an open
            # double cover. Include ALL exact-size extensions, even
            # when a smaller valid cover exists.
            remaining = [
                v for v in range(n)
                if undecided >> v & 1
            ]
            if slots < 0 or len(remaining) < slots:
                return
            for choice in itertools.combinations(remaining, slots):
                solutions.add(
                    selected | sum((1 << v for v in choice))
                )
            return

        if slots <= 0:
            return

        # A chosen vertex v contributes at most one unit of
        # coverage to each deficient row adjacent to v in H.
        # Summing its maximal possible gain overcounts, so the
        # following upper bound cannot reject a real cover.
        gains = sorted(
            ((mask & unsatisfied).bit_count()
             for v, mask in enumerate(h)
             if undecided >> v & 1),
            reverse=True,
        )
        if sum(gains[:slots]) < total_demand:
            return

        # Independent C++ uses maximum total gain as branch pivot;
        # here the tightest currently deficient constraint chooses
        # the pivot's candidate set.
        _, _, _, available, _ = min(outstanding)
        candidates = []
        while available:
            bit = available & -available
            available ^= bit
            v = bit.bit_length() - 1
            candidates.append(((h[v] & unsatisfied).bit_count(), -v, v))
        pivot = max(candidates)[2]
        bit = 1 << pivot
        dfs(selected | bit, excluded)
        dfs(selected, excluded | bit)

    dfs(0, 0)
    return solutions, nodes, forced


def is_open_two_cover(h: tuple[int, ...], selected: int) -> bool:
    return all((mask & selected).bit_count() >= 2 for mask in h)


def unary_neighborhood_possible(
    h: tuple[int, ...], selected: int
) -> bool:
    """Necessary for a retraction fixing this exact induced target.

    If x is outside S and r(x)=y in S then N_X(x) cap S
    must lie in N_X[y] cap S, equivalently
    N_H(y) cap S subset N_H(x) cap S.
    """
    for x, mask in enumerate(h):
        if selected >> x & 1:
            continue
        nonedges_to_target = mask & selected
        possible = False
        targets = selected
        while targets:
            bit = targets & -targets
            targets ^= bit
            y = bit.bit_length() - 1
            if not ((h[y] & selected) & ~nonedges_to_target):
                possible = True
                break
        if not possible:
            return False
    return True


def verify_brute_small() -> None:
    rng = random.Random(11938)
    cases = 0
    for n in range(4, 10):
        for _ in range(12):
            g = nx.gnp_random_graph(
                n, rng.random(), seed=rng.randrange(1 << 24)
            )
            h = complement_masks(g)
            for k in range(2, min(4, n) + 1):
                got, _, _ = enumerate_open_two(h, k)
                expected = {
                    sum(1 << v for v in target)
                    for target in itertools.combinations(range(n), k)
                    if all(
                        sum((h[x] >> v) & 1 for v in target) >= 2
                        for x in range(n)
                    )
                }
                check(got == expected,
                      "DPLL missed an exact-size open double cover on a small graph")
                cases += 1
    print(f"PASS direct exhaustive small-graph oracle: {cases} cases", flush=True)


def verify(*, public: bool = False) -> None:
    verify_frozen_sources()
    verify_brute_small()
    for idx in SOURCES:
        host = reconstruct_p3(idx, public=public)
        h = complement_masks(host)
        covers, nodes, forced = enumerate_open_two(h, 10)
        check(
            len(covers) == EXPECTED[idx],
            f"Unexpected complete ten-cover count for {idx}: {len(covers)}",
        )
        check(
            all(s.bit_count() == 10 and is_open_two_cover(h, s) for s in covers),
            f"Invalid independently enumerated open double cover for {idx}",
        )
        survivors = [s for s in covers if unary_neighborhood_possible(h, s)]
        check(not survivors,
              f"Ten-vertex target survives unary retraction test for {idx}")

        # Independently verify equivalence of the bitset unary filter
        # and the actual host-graph closed-neighborhood test on
        # deterministic candidate samples.
        rng = random.Random(idx)
        samples = rng.sample(sorted(covers), min(32, len(covers)))
        for chosen in samples:
            target = {v for v in range(len(h)) if chosen >> v & 1}
            closed = {y: (set(host[y]) & target) | {y} for y in target}
            direct = all(
                any(
                    (set(host[x]) & target) <= closed[y]
                    for y in target
                )
                for x in host if x not in target
            )
            check(
                direct == unary_neighborhood_possible(h, chosen),
                f"Independent unary condition mismatch at McKay {idx}",
            )
        print(
            f"PROVED McKay={idx} original_graph6={SOURCES[idx]['graph6']} "
            f"P3={len(host)}/{host.number_of_edges()} "
            f"all_ten_open_double_covers={len(covers)} "
            f"ten_fixed_target_unary_survivors=0 "
            f"integer_nodes={nodes} forced_selections={forced} "
            f"public_clique_graph_paring_replay={public}",
            flush=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public", action="store_true")
    args = parser.parse_args()
    verify(public=args.public)


if __name__ == "__main__":
    main()
