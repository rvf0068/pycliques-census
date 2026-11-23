"""Exact obstruction to nine-vertex max-degree-six P3 retracts.

Every nine-vertex induced retract of maximum degree at most six has
an external double-cover target set in the complement. Enumerate ALL
nine-element covers without assuming that smaller covers do not exist,
then screen every candidate against its required fixed-target images.

No bounded search, SAT solver, saved embedding or homology assumption is
used to classify the candidate sets. Failure of the unary target-image
condition is an exact impossibility proof for that specified target.
"""
from __future__ import annotations

import itertools
from pathlib import Path
import pickle
import random
import sys

import networkx as nx

from research.order9_p3_eight_vertex_obstruction_v1.verify import (
    SOURCES, check, complement_masks, reconstruct_p3, verify_frozen_sources,
)

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical assertions")

EXPECTED = {
    249576: (30, 0, 0),
    251628: (297, 109, 0),
    260040: (343, 122, 0),
}


def covers_of_exact_size(h: tuple[int, ...], size: int) -> tuple[list[tuple[int, ...]], int]:
    """Exhaustive integer DPLL; works even if smaller covers exist."""
    n = len(h)
    full = (1 << n) - 1
    covers: set[tuple[int, ...]] = set()
    nodes = 0

    def recurse(selected: int, excluded: int) -> None:
        nonlocal nodes
        nodes += 1
        if selected.bit_count() > size:
            return
        while True:
            undecided = full & ~(selected | excluded)
            unsat = 0
            need2 = 0
            total_demand = 0
            forced = False
            for x in range(n):
                bit = 1 << x
                if selected & bit:
                    continue
                have = (h[x] & selected).bit_count()
                if have >= 2:
                    continue
                missing = 2 - have
                possible = h[x] & undecided
                remaining = possible.bit_count()
                if excluded & bit:
                    if remaining < missing:
                        return
                    if remaining == missing:
                        selected |= possible
                        forced = True
                        break
                elif remaining < missing:
                    selected |= bit
                    forced = True
                    break
                unsat |= bit
                total_demand += missing
                if missing == 2:
                    need2 |= bit
            if selected.bit_count() > size:
                return
            if not forced:
                break

        undecided = full & ~(selected | excluded)
        if unsat == 0:
            # Any superset of a valid external cover is also valid.
            # Enumerate all exact-size completions of this branch; this
            # remains valid when a smaller external cover exists.
            slots = size - selected.bit_count()
            available = [v for v in range(n) if undecided >> v & 1]
            if slots < 0 or len(available) < slots:
                return
            for extension in itertools.combinations(available, slots):
                mask = selected | sum(1 << v for v in extension)
                cover = tuple(v for v in range(n) if mask >> v & 1)
                check(len(cover) == size, "Incorrect extended target size")
                covers.add(cover)
            return
        slots = size - selected.bit_count()
        if slots <= 0 or not undecided:
            return
        candidates = []
        for v in range(n):
            if not (undecided >> v & 1):
                continue
            potential = (
                ((h[v] | (1 << v)) & unsat).bit_count()
                + int(bool(need2 >> v & 1))
            )
            candidates.append(
                (potential * 128 + (h[v] & unsat).bit_count(), potential, v)
            )
        candidates.sort(reverse=True)
        if sum(gain for _, gain, _ in candidates[:slots]) < total_demand:
            return
        bit = 1 << candidates[0][2]
        recurse(selected | bit, excluded)
        recurse(selected, excluded | bit)

    recurse(0, 0)
    for target in covers:
        mask = sum(1 << v for v in target)
        check(
            all((mask >> x & 1) or (h[x] & mask).bit_count() >= 2
                for x in range(n)),
            "Enumerated target violates external double domination",
        )
    return sorted(covers), nodes


def can_extend_target_neighborhoods(
    graph: nx.Graph, selected: tuple[int, ...]
) -> tuple[bool, int | None]:
    """Exact unary necessary condition for a retraction fixing target."""
    target = set(selected)
    closed = {v: (set(graph[v]) & target) | {v} for v in target}
    for x in graph:
        if x in target:
            continue
        adjacent_to_target = set(graph[x]) & target
        if not any(adjacent_to_target <= closed[y] for y in target):
            return False, x
    return True, None


def verify_small_exact_k() -> None:
    """Direct combinations independently check branches with smaller covers."""
    rng = random.Random(1137)
    tested = 0
    for n in range(4, 10):
        for _ in range(12):
            graph = nx.gnp_random_graph(
                n, 0.2 + 0.6 * rng.random(), seed=rng.randrange(10**8)
            )
            h = complement_masks(graph)
            for k in range(2, min(5, n) + 1):
                enumerated, _ = covers_of_exact_size(h, k)
                direct = [
                    target for target in itertools.combinations(range(n), k)
                    if all(
                        x in target or sum((h[x] >> u) & 1 for u in target) >= 2
                        for x in range(n)
                    )
                ]
                check(enumerated == direct,
                      "Nine-target DPLL disagrees with brute-force oracle")
                tested += 1
    print(f"PASS exact-size enumeration brute-force tests={tested}", flush=True)


def verify() -> None:
    verify_frozen_sources()
    verify_small_exact_k()
    for idx in SOURCES:
        host = reconstruct_p3(idx)
        h = complement_masks(host)
        covers, nodes = covers_of_exact_size(h, 9)
        check(len(covers) == EXPECTED[idx][0],
              f"Incorrect complete nine-cover enumeration for {idx}")
        eligible = [
            selected for selected in covers
            if max(dict(host.subgraph(selected).degree()).values()) <= 6
        ]
        check(len(eligible) == EXPECTED[idx][1],
              f"Incorrect number of degree-eligible nine-vertex targets {idx}")
        unary_survivors = [
            selected for selected in eligible
            if can_extend_target_neighborhoods(host, selected)[0]
        ]
        check(len(unary_survivors) == EXPECTED[idx][2] == 0,
              f"An induced nine-vertex target survived unary obstruction at {idx}")
        print(
            f"PROVED McKay={idx} P3={len(host)}/{host.number_of_edges()} "
            f"all_nine_external_double_covers={len(covers)} "
            f"max_degree_le_six_candidates={len(eligible)} "
            f"target_neighborhood_compatible_candidates={len(unary_survivors)} "
            f"exhaustive_DPLL_nodes={nodes} "
            f"no_retraction_to_9_vertex_max_degree_le_six=YES",
            flush=True,
        )


if __name__ == "__main__":
    verify()
