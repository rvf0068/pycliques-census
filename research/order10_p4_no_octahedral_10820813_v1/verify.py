"""Complete octahedral-retraction obstruction on P4(McKay 10820813).

This is a full finite proof of NO ORDINARY RETRACTION FROM P4 onto any
induced O_d, d >= 3; it is NOT a verdict about K-divergence or any
different target/stage.

The complement of an induced O_d is an induced matching of d edges.
An ordinary retraction fixing the target forces that matching's 2d
endpoints to dominate the host complement. Every remaining candidate
is rejected by sound singleton-domain propagation: only antipodal
target images are forbidden on source edges.

Everything is enumerated, with no heuristic, sample, time limit, or
facet cap in the *octahedral target enumeration*. P4 itself is
reconstructed independently with both BK and NetworkX clique facets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import networkx as nx

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical checks")

from research.order10_p3_global_v23_index.independent_verify import (
    independent_clique_graph,
    independent_pare,
)

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ARCHIVE = HERE / "certificates.json"
SNAPSHOT = ROOT / "indeterminate_order_10_v24.txt"
CURRENT = ROOT / "indeterminate_order_10.txt"
PILOT = ROOT / "research/order10_p4_reference_pilot_v24/results.json"
EXPECTED_COUNTS = {
    3: (387428, 22, 0, 22, 0, 0),
    4: (472762, 205024, 0, 166199, 38825, 0),
    5: (14304, 144, 0, 140, 4, 0),
    6: (491, 0, 0, 0, 0, 0),
    7: (2, 0, 0, 0, 0, 0),
    8: (0, 0, 0, 0, 0, 0),
}


def require(statement: bool, reason: str) -> None:
    if not statement:
        raise AssertionError(reason)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def bit_indices(mask: int):
    while mask:
        lowest = mask & -mask
        yield lowest.bit_length() - 1
        mask -= lowest


def shape(g: nx.Graph) -> tuple[int, int]:
    return len(g), g.number_of_edges()


def reconstruct(cert: dict) -> nx.Graph:
    """Reconstruct each completely pared stage and check immutable sources."""
    src = cert["source"]
    require(src["index"] == 10820813 and
            src["census_snapshot"] == SNAPSHOT.name and
            src["pilot_archive"] == PILOT.relative_to(ROOT).as_posix(),
            "Wrong original index or proven-source path")
    require(git_blob(SNAPSHOT.read_bytes()) == src["census_git_blob"] and
            SNAPSHOT.read_bytes() == CURRENT.read_bytes(),
            "Historical ten-v24 census snapshot changed")
    require(git_blob(PILOT.read_bytes()) == src["pilot_git_blob"],
            "Merged ten-v24 P4 pilot evidence changed")
    original_line = "10820813 10 " + src["graph6"] + " - - -"
    require(SNAPSHOT.read_text(encoding="ascii").splitlines().count(
        original_line
    ) == 1, "Original McKay index or graph6 absent from ten-v24")
    prior = json.loads(PILOT.read_text(encoding="ascii"))
    pilot_rows = [
        item for item in prior["records"] if item["index"] == src["index"]
    ]
    require(pilot_rows == [{
        "index": src["index"], "graph6": src["graph6"],
        "p3": [43, 625], "raw_p4": [223, 18159],
        "p4": [70, 1830], "status": "NO_REFERENCE_DIMENSION_MATCH",
    }], "Independent prior P4 research archive disagrees")

    g = independent_pare(nx.from_graph6_bytes(src["graph6"].encode("ascii")))
    stages = [list(shape(g))]
    raw_p4 = None
    for stage in range(1, 5):
        # Two independent maximal-clique enumerators are cross-checked
        # inside independent_clique_graph at *every* stage.
        raw = independent_clique_graph(
            g, stage=stage, orders=[row[0] for row in stages],
        )
        if stage == 4:
            raw_p4 = list(shape(raw))
        g = independent_pare(raw)
        stages.append(list(shape(g)))
    require(stages == cert["completely_pared_orders_edges"] and
            raw_p4 == cert["raw_P4"] and
            list(shape(g)) == [70, 1830],
            "Independent 4-stage reconstruction differs from proof archive")
    digest = hashlib.sha256(
        nx.to_graph6_bytes(g, header=False).strip()
    ).hexdigest()
    require(digest == cert["P4_graph6_sha256"],
            "Exact canonical labeled fourth iterate SHA-256 changed")
    return g


def neighborhood_masks(g: nx.Graph) -> tuple[list[int], list[int]]:
    """Return source-edge masks and complement-edge masks (no loops)."""
    require(set(g) == set(range(len(g))) and
            not g.is_multigraph() and not g.is_directed(),
            "P4 input is not a canonical simple graph")
    n = len(g)
    full = (1 << n) - 1
    edges = [sum(1 << v for v in g[u]) for u in range(n)]
    nonedges = [full & ~(edges[u] | (1 << u)) for u in range(n)]
    return edges, nonedges


def screen_target(
    edges: list[int],
    nonedges: list[int],
    pairs: tuple[tuple[int, int], ...],
) -> str:
    """Sound necessary condition for an ordinary retraction fixing O_d.

    Allowed image a_i means the source vertex is nonadjacent (in G) to
    antipode b_i. An outside source edge cannot map to a_i-b_i.
    Singleton propagation deletes the antipode of every forced image
    from the domains of all source neighbors. An empty domain proves
    that this fixed target cannot retract; SURVIVES is inconclusive.
    """
    n = len(edges)
    endpoints = [u for pair in pairs for u in pair]
    d = len(pairs)
    require(len(endpoints) == len(set(endpoints)) == 2 * d and
            all(0 <= u < n for u in endpoints),
            "Malformed octahedral embedding")
    position = {u: j for j, u in enumerate(endpoints)}
    domains: list[int] = []
    for u in range(n):
        if u in position:
            domains.append(1 << position[u])
        else:
            allowed = 0
            for i, (a, b) in enumerate(pairs):
                if nonedges[u] & (1 << b):
                    allowed |= 1 << (2 * i)
                if nonedges[u] & (1 << a):
                    allowed |= 1 << (2 * i + 1)
            domains.append(allowed)
            if not allowed:
                return "initial_empty"

    # First check explicit adjacent sources whose forced target images
    # are antipodal; this is a compact local impossibility witness.
    forced_groups = [0] * (2 * d)
    for u, options in enumerate(domains):
        if options.bit_count() == 1:
            forced_groups[options.bit_length() - 1] |= 1 << u
    for i in range(d):
        a_group, b_group = forced_groups[2*i:2*i+2]
        if any(edges[u] & b_group for u in bit_indices(a_group)):
            return "direct_contradiction"
        if any(edges[u] & a_group for u in bit_indices(b_group)):
            return "direct_contradiction"

    # Full iterative singleton propagation, not merely a bounded sample.
    queue = [u for u, options in enumerate(domains)
             if options.bit_count() == 1]
    while queue:
        u = queue.pop()
        p = domains[u].bit_length() - 1
        forbidden = 1 << (p ^ 1)
        for v in bit_indices(edges[u]):
            if domains[v] & forbidden:
                domains[v] &= ~forbidden
                if not domains[v]:
                    return "propagated_contradiction"
                if domains[v].bit_count() == 1:
                    queue.append(v)
    return "survives"


def enumerate_targets(g: nx.Graph) -> dict:
    """Enumerate *all* induced matchings of G-complement through d=8."""
    source, complement = neighborhood_masks(g)
    n = len(g)
    full = (1 << n) - 1
    pairs = [
        (u, v) for u in range(n)
        for v in range(u + 1, n)
        if complement[u] & (1 << v)
    ]
    require(len(pairs) == 585, "Unexpected complement size")
    closed = [complement[u] | (1 << u) for u in range(n)]
    covered_by = [closed[u] | closed[v] for u, v in pairs]
    compatible_future = [0] * len(pairs)
    for i, (a, b) in enumerate(pairs):
        incompatible = complement[a] | complement[b]
        for j in range(i + 1, len(pairs)):
            c, d = pairs[j]
            if not (incompatible & ((1 << c) | (1 << d))):
                compatible_future[i] |= 1 << j

    induced = [0] * 9
    dominating = [0] * 9
    outcomes = {
        name: [0] * 9 for name in (
            "initial_empty", "direct_contradiction",
            "propagated_contradiction", "survives",
        )
    }

    def visit(
        d: int, candidates: int, covered: int,
        chosen: tuple[int, ...],
    ) -> None:
        induced[d] += 1
        if d >= 3 and covered == full:
            dominating[d] += 1
            target = tuple(pairs[i] for i in chosen)
            outcome = screen_target(source, complement, target)
            outcomes[outcome][d] += 1
            require(outcome != "survives",
                    f"Target {target} survives; do NOT assert nonexistence")
        if d == 8:
            return
        while candidates:
            lowest = candidates & -candidates
            i = lowest.bit_length() - 1
            candidates -= lowest
            visit(d + 1, candidates & compatible_future[i],
                  covered | covered_by[i], chosen + (i,))

    visit(0, (1 << len(pairs)) - 1, 0, ())
    result = {
        "induced_O1": induced[1],
        "induced_O2": induced[2],
        "counts": {
            f"O{d}": {
                "induced": induced[d],
                "dominating": dominating[d],
                "initial_empty": outcomes["initial_empty"][d],
                "direct_contradiction": outcomes["direct_contradiction"][d],
                "propagated_contradiction":
                    outcomes["propagated_contradiction"][d],
                "survives": outcomes["survives"][d],
            }
            for d in range(3, 9)
        },
    }
    return result


def verify_result(cert: dict, result: dict) -> None:
    require(cert["schema"] == 1 and
            cert["kind"] ==
            "complete_nonexistence_of_ordinary_octahedral_retractions_from_pared_fourth_iterate",
            "Wrong complete-retraction-obstruction certificate kind")
    require(cert["complement_edges"] == 585,
            "Expected complement order/size changed")
    require(result == {
        name: cert[name] for name in ("induced_O1", "induced_O2", "counts")
    }, "Complete finite octahedral enumeration disagrees with archive")
    require(
        all(
            tuple(result["counts"][f"O{d}"][key]
                  for key in (
                      "induced", "dominating", "initial_empty",
                      "direct_contradiction", "propagated_contradiction",
                      "survives",
                  )) == EXPECTED_COUNTS[d]
            for d in EXPECTED_COUNTS
        ), "Unexpected enumerated octahedral target distribution")
    require(result["counts"]["O8"]["induced"] == 0,
            "No bound for higher dimensional induced octahedra")
    print(
        "CERTIFIED: McKay 10820813 P4 (70 vertices, 1830 edges) has NO"
        " ordinary graph retraction onto an induced O_d, d >= 3;"
        " exhaustive 387428 O3, 472762 O4, 14304 O5, 491 O6,"
        " 2 O7, 0 O8; all dominating candidates are refuted by"
        " sound singleton-domain propagation.",
        flush=True,
    )


def write_complement(g: nx.Graph, path: Path) -> None:
    # Plain sorted edge list to feed a completely separate compiled verifier.
    _source, comp = neighborhood_masks(g)
    edges = [(u, v) for u in range(len(g))
             for v in range(u+1, len(g)) if comp[u] & (1 << v)]
    path.write_text(
        f"{len(g)} {len(edges)}\n" +
        "".join(f"{u} {v}\n" for u, v in edges),
        encoding="ascii",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-complement", type=Path)
    args = parser.parse_args()
    cert = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    g = reconstruct(cert)
    if args.export_complement is not None:
        write_complement(g, args.export_complement)
    result = enumerate_targets(g)
    verify_result(cert, result)


if __name__ == "__main__":
    main()
