"""Solver-independent positive-map replay and bounded-pilot aggregation.

Every FOUND map is checked on all edges and its stable-image retraction
is checked without trusting solver claims. Coaffine join factors may
certify expansivity by [LNP09, Theorems 3.6 or 4.6]. If no positive
complete witness is present, no behavior classification is inferred.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("Cannot optimize away positive proof checks")

import networkx as nx

from research.order10_p4_crossdepth_o15_v25.verify import git_blob, source_rows
from research.order10_overcap_p3_coaffine_v1.pilot import source_catalog
from research.order10_five_p3_native_v1.search import (
    MONOREPO_SHA, RUNTIME_VERSIONS,
)

ROOT = Path(__file__).resolve().parents[2]
LATEST = ROOT / "indeterminate_order_10_v28.txt"
LATEST_BLOB = "35bb83b56bb8b4fd453b0ba272d354dc6b42e68c"
ORIGINALS = (11505012, 11595632, 11709142)
ORDERS = ("label", "fiber")
MAX_STATES = 3_000_000
SECONDS = 150


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def audit_source(index: int, source: dict, G: nx.Graph) -> None:
    require(git_blob(LATEST.read_bytes()) == LATEST_BLOB,
            "Frozen ten-v28 original-source Git blob differs")
    row = source_rows(LATEST).get(index)
    require(index in ORIGINALS and row ==
            f'{index} 10 {source["graph6"]} - - -',
            "Original graph6 is missing from certified ten-v28")
    require(source["index"] == index
            and [len(G), G.number_of_edges()] == list(source["p3"])
            and nx.to_graph6_bytes(G, header=False).decode("ascii").strip()
                == source["p3_graph6"],
            "Canonical historical P3 graph6 or dimensions changed")


def power_map(f: list[int], n: int) -> list[int]:
    """Exponentiate a finite vertex map in O(N log n), even for huge n."""
    require(type(n) is int and n >= 1, "Invalid power exponent")
    out = list(range(len(f)))
    base = list(f)
    while n:
        if n & 1:
            out = [base[v] for v in out]
        n //= 2
        if n:
            base = [base[v] for v in base]
    return out


def audit_positive_map(G: nx.Graph, f: list[int]) -> dict:
    n = len(G)
    require(set(G) == set(range(n)) and len(f) == n
            and all(type(a) is int and 0 <= a < n for a in f),
            "Coaffine complete map is malformed")
    require(all(v != f[v] and not G.has_edge(v, f[v]) for v in G),
            "Coaffine vertex constraint fails")
    require(all(f[u] == f[v] or G.has_edge(f[u], f[v])
                for u, v in G.edges()),
            "Coaffine weak endomorphism fails original source edge")

    S = set(range(n))
    depth = 0
    while True:
        next_S = {f[v] for v in S}
        require(next_S <= S, "Iterated image is not a nested set")
        if next_S == S:
            break
        S = next_S
        depth += 1
        require(depth < n, "Unexpected transient depth on a finite map")
    require(set(f[v] for v in S) == S,
            "Endomorphism is not bijective on its eventual image")
    Y = G.subgraph(S).copy()
    require(all(Y.has_edge(u, v) == Y.has_edge(f[u], f[v])
                for u in S for v in S),
            "Stable-image restriction is not a graph automorphism")

    unseen = set(S)
    cycles = []
    while unseen:
        start = min(unseen)
        cycle = []
        u = start
        while u in unseen:
            unseen.remove(u)
            cycle.append(u)
            u = f[u]
        require(u == start, "Stable image did not partition into cycles")
        cycles.append(cycle)
    period = math.lcm(*(len(c) for c in cycles))
    exponent = period * max(1, (depth + period - 1) // period)
    retraction = power_map(f, exponent)
    require(set(retraction) == S and
            all(retraction[v] == v for v in S),
            "Power of the map is not the exact idempotent retraction")
    require(all(retraction[u] == retraction[v] or
                G.has_edge(retraction[u], retraction[v])
                for u, v in G.edges()),
            "Exact powered retraction fails a source edge")

    # Complement components of Y determine the canonical join factors.
    # The stable coaffination permutes these components; group them into
    # orbits to obtain invariant coaffine summands.
    H = nx.complement(Y)
    components = sorted(
        (frozenset(c) for c in nx.connected_components(H)),
        key=lambda c: (len(c), min(c)),
    )
    membership = {v: i for i, c in enumerate(components) for v in c}
    require(len(membership) == len(S), "Missing complement component")
    perm = []
    for C in components:
        indices = {membership[f[v]] for v in C}
        require(len(indices) == 1, "Coaffination does not permute complement components")
        perm.append(next(iter(indices)))
    require(sorted(perm) == list(range(len(components))),
            "Complement-component map is not a permutation")
    groups = []
    pending = set(range(len(components)))
    while pending:
        start = min(pending)
        i = start
        inds = []
        while i in pending:
            pending.remove(i)
            inds.append(i)
            i = perm[i]
        require(i == start, "Component orbit unexpectedly has a tail")
        group = set().union(*(components[j] for j in inds))
        require(set(f[v] for v in group) == group
                and all(v != f[v] and not Y.has_edge(v, f[v]) for v in group),
                "Proposed join summand is not coaffine invariant")
        groups.append(group)
    require(set().union(*groups) == S, "Join factor partition incomplete")
    for i, A in enumerate(groups):
        for B in groups[i + 1:]:
            require(all(G.has_edge(u, v) for u in A for v in B),
                    "Proposed Zykov-summand cross-edge absent")

    connected = [nx.is_connected(Y.subgraph(A)) for A in groups]
    theorem = None
    if len(groups) >= 3:
        theorem = "Larrion--Neumann-Lara--Pizana 2009 Theorem 3.6"
    elif len(groups) >= 2 and any(connected):
        theorem = "Larrion--Neumann-Lara--Pizana 2009 Theorem 4.6"
    return {
        "stable_order": len(S),
        "stable_edges": Y.number_of_edges(),
        "transient_depth": depth,
        "restriction_cycle_lengths": dict(Counter(str(len(c)) for c in cycles)),
        "idempotent_retraction_power": exponent,
        "ordinary_retraction_verified_on_all_edges": True,
        "complement_component_sizes": sorted(len(c) for c in components),
        "coaffine_component_orbit_factor_sizes": sorted(len(c) for c in groups),
        "connected_coaffine_factors": sum(connected),
        "expansive_witness": {
            "proved": theorem is not None,
            "theorem": theorem,
            "original_divergence_by_retraction_and_paring":
                theorem is not None,
        },
    }


def verify_record(row: dict, sources: dict[int, dict]) -> dict:
    i = row["original_index"]
    require(i in ORIGINALS and row.get("schema") == 1
            and row.get("kind") ==
                "bounded_native_three_oversized_p3_coaffine_pilot"
            and row.get("value_order") in ORDERS,
            "Wrong pilot source or schema")
    src = sources[i]
    G = nx.from_graph6_bytes(src["p3_graph6"].encode("ascii"))
    audit_source(i, src, G)
    require(row["original_graph6"] == src["graph6"]
            and row["p3_dimensions"] == list(src["p3"])
            and row["p3_graph6_sha256"] ==
                hashlib.sha256(src["p3_graph6"].encode("ascii")).hexdigest()
            and row["monorepo_pinned_revision"] == MONOREPO_SHA
            and row["installed_solver_source_blobs_verified"] is True
            and row["dependency_versions"] == RUNTIME_VERSIONS
            and row["max_states"] == MAX_STATES
            and row["time_limit_seconds"] == SECONDS
            and row["bounded_search_does_not_certify_nondivergence"] is True,
            "Search input or pinned solver provenance has changed")
    status = row["coaffine_status"]
    require(status in ("FOUND", "EXHAUSTED", "LIMIT_REACHED")
            and all(type(row[k]) is int and row[k] >= 0
                    for k in ("states_explored", "assignments_tried",
                              "arc_revisions"))
            and row["states_explored"] <= MAX_STATES,
            "Invalid native search status or counters")
    if status == "FOUND":
        require(isinstance(row.get("complete_coaffine_map"), list)
                and isinstance(row.get("positive_analysis"), dict),
                "A FOUND result must archive the complete positive map")
        audited = audit_positive_map(G, row["complete_coaffine_map"])
        require(audited == row["positive_analysis"],
                "Positive stable-image analysis differs on independent replay")
    else:
        require("complete_coaffine_map" not in row
                and "positive_analysis" not in row,
                "Limited or exhausted search must not claim a positive map")
        audited = None
    return {
        "index": i,
        "value_order": row["value_order"],
        "status": status,
        "states_explored": row["states_explored"],
        "positive_analysis": audited,
    }


def verify_batch(directory: Path) -> dict:
    paths = sorted(directory.glob("three-p3-coaffine-*.json"))
    require(len(paths) == 6, "Exactly six native result artifacts required")
    sources = source_catalog()
    seen = set()
    outcomes = []
    for path in paths:
        row = json.loads(path.read_text(encoding="utf-8"))
        result = verify_record(row, sources)
        key = (result["index"], result["value_order"])
        require(key not in seen, "Duplicated result or missing matrix case")
        seen.add(key)
        outcomes.append(result)
    require(seen == {(i, order) for i in ORIGINALS for order in ORDERS},
            "Missing native value ordering or source original")
    positives = [x for x in outcomes if x["status"] == "FOUND"]
    divergent = sorted(set(
        x["index"] for x in positives
        if x["positive_analysis"]["expansive_witness"]["proved"]
    ))
    return {
        "schema": 1,
        "kind": "solver_independent_three_oversized_p3_native_coaffine_audit",
        "three_originals": list(ORIGINALS),
        "six_matrix_cases_audited": True,
        "search_bound": {"states": MAX_STATES, "seconds": SECONDS},
        "status_counts": dict(Counter(x["status"] for x in outcomes)),
        "positive_maps_independently_checked": len(positives),
        "complete_expansive_retract_positive_originals": divergent,
        "requires_separate_permanent_positive_certification_and_promotion": True,
        "no_negative_conclusion_from_bounded_search": True,
        "records": outcomes,
    }


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--directory", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    data = verify_batch(args.directory)
    args.output.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status_counts": data["status_counts"],
        "positive_maps": data["positive_maps_independently_checked"],
        "expansive_retract_indices":
            data["complete_expansive_retract_positive_originals"],
    }, sort_keys=True), flush=True)
    print("PASS: six bounded native coaffine searches independently audited",
          flush=True)


if __name__ == "__main__":
    main()
