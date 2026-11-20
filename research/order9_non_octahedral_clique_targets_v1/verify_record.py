"""Audit the archived (not fully replayed) order-9 negative-search report.

Reconstruct the exact 49-case cohort from the frozen 54-case root, independently
verify the five excluded nine-vertex divergence references (including the
nonidentically labeled isomorphism at index 250693), and check concrete
induced-O8 witnesses in the K(C_n^c) target graphs for n=12..17.

IMPORTANT: This script does NOT verify the original 48 exhaustive negative
retraction searches; their source scripts and per-copy proofs were unavailable
when this historical report was migrated. See REPORT.md and summary.json.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
from itertools import combinations
import json
from pathlib import Path

import networkx as nx

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REPORT = HERE / "summary.json"


def require(condition: bool, explanation: str) -> None:
    if not condition:
        raise ValueError(explanation)


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def clique_graph(graph: nx.Graph) -> nx.Graph:
    """Independent deterministic clique-graph construction."""
    maximal = sorted(
        (frozenset(q) for q in nx.find_cliques(graph)),
        key=lambda q: sum(1 << v for v in q),
    )
    result = nx.Graph()
    result.add_nodes_from(range(len(maximal)))
    result.add_edges_from(
        (i, j) for i, j in combinations(result.nodes, 2)
        if maximal[i] & maximal[j]
    )
    return result


def graph6(spec: str) -> nx.Graph:
    return nx.from_graph6_bytes(spec.encode("ascii"))


def source_rows() -> tuple[bytes, list[dict]]:
    raw = (ROOT / "indeterminate_order_9.txt").read_bytes()
    rows = []
    for line in raw.decode("utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        require(len(fields) == 6, "Invalid historical six-column source")
        rows.append({
            "index": int(fields[0]),
            "pared_order": int(fields[1]),
            "pared_graph6": fields[2],
            "conditional": fields[4] == "conjectured_divergent",
        })
    require(len(rows) == 54, "Historical root no longer has 54 entries")
    require(len({x["index"] for x in rows}) == 54, "Duplicate McKay index")
    require(sum(x["conditional"] for x in rows) == 36, "Wrong old conditional count")
    return raw, rows


def validate_record(data: dict) -> None:
    raw, source = source_rows()
    require(data.get("schema") == 1, "Wrong schema")
    require(data.get("historical_root") == {
        "path": "indeterminate_order_9.txt",
        "git_blob_sha": git_blob_sha(raw),
        "entries": 54,
        "conditional": 36,
    }, "Historical source identity changed")
    removed = data.get("excluded_proved_divergent")
    require(isinstance(removed, list) and len(removed) == 5, "Five proofs required")
    expected = {
        242316: (44, "HCrlvhz"),
        248687: (39, "HEher^{"),
        250693: (42, "HQqvUx}"),
        252075: (45, "HEh~dzm"),
        255141: (42, "HEnfbzm"),
    }
    source_map = {x["index"]: x for x in source}
    require(
        {x["index"]: (x["proof_pr"], x["proved_graph6"]) for x in removed}
        == expected,
        "Unexpected proved-divergent exclusion list",
    )
    for index, (_, proved_graph6) in expected.items():
        require(
            nx.is_isomorphic(
                graph6(source_map[index]["pared_graph6"]), graph6(proved_graph6)
            ),
            f"Proved target is not isomorphic to original nine-graph {index}",
        )
        require(not source_map[index]["conditional"], "Excluded a conditional case")

    eligible = [r for r in source if r["index"] not in expected]
    require(len(eligible) == 49, "Incorrect 49-case cohort")
    require(sum(r["conditional"] for r in eligible) == 36, "Incorrect conditional cohort")
    expected_cases = [
        {**r,
         "search_through_level": 2 if r["index"] == 260910 else 3,
         "level3_status": (
             "TIMEOUT_INCOMPLETE" if r["index"] == 260910
             else "NEGATIVE_REPORTED"
         )}
        for r in eligible
    ]
    require(
        data.get("cohort") == {
            "size": 49,
            "conditional": 36,
            "nonconditional": 13,
            "cases": expected_cases,
        },
        "Case records mismatch source, classification, or timeout status",
    )
    counts = data["reported_search"]
    require(counts["representative_p3"] == 22, "Wrong P3 count")
    require(counts["complete_p3_representatives"] == 21, "Wrong complete P3 count")
    require(counts["early_levels"]["target_host_checks"] == 143, "Wrong early checks")
    require(counts["early_levels"]["induced_target_vertex_sets"] == 483,
            "Wrong early induced count")
    require(counts["early_levels"]["local_domain_survivors"] == 109,
            "Wrong early local-domain count")
    require(counts["early_levels"]["positive_retractions"] == 0,
            "Reported positive incorrectly")
    p3 = counts["third_level"]
    require(p3["small_cases_covered"] == 48, "Wrong complete P3 cohort")
    require([
        (x["index"], x["induced_full_target_copies"], x["retraction_search"])
        for x in p3["kc10_cases"] if "retraction_search" in x
    ] == [(248936, 24, "EXHAUSTED"), (250814, 608, "EXHAUSTED")],
        "Altered reported complete K(C10^c) searches")
    big = counts["large_case"]
    require(big == {
        "index": 260910, "p3_vertices": 132, "p3_edges": 7880,
        "kc10_partial_induced_copies": 81,
        "search_status": "TIMEOUT_INCOMPLETE",
        "must_not_infer_no_retraction": True,
    }, "Large case must stay incomplete, never an exhaustive negative")

    # Reconstruct the target K(C_n^c) afresh. In its complement, each listed
    # eight-edge induced matching gives an induced O8 in K(C_n^c).
    witnesses = data.get("o8_complement_induced_matching_witnesses", {})
    require(set(witnesses) == {str(n) for n in range(12, 18)},
            "Expected witnesses for exactly six target cycles")
    for n in range(12, 18):
        target = clique_graph(nx.complement(nx.cycle_graph(n)))
        comp = nx.complement(target)
        pairs = witnesses[str(n)]
        require(len(pairs) == 8, f"Wrong matching size at n={n}")
        flattened = [v for uv in pairs for v in uv]
        require(len(set(flattened)) == 16, f"Matching is not vertex-disjoint at n={n}")
        require(all(comp.has_edge(u, v) for u, v in pairs),
                f"Listed nonedge is not an edge of complement, n={n}")
        require(
            comp.subgraph(flattened).number_of_edges() == 8,
            f"Target graph has extra complement edges in the O8, n={n}",
        )
    # Verify the fundamental anchor property used to exclude K(C11^c)
    # from small P3 hosts, not the original per-host anchor search itself.
    comp11 = nx.complement(clique_graph(nx.complement(nx.cycle_graph(11))))
    components = [comp11.subgraph(c).copy() for c in nx.connected_components(comp11)]
    require(sorted(map(len, components)) == [11, 11],
            "K(C11^c) complement components changed")
    require(any(nx.is_isomorphic(c, nx.cycle_graph(11)) for c in components),
            "K(C11^c) complement lacks required C11 anchor")
    # All original nine-vertex pared inputs have <=9 vertices while
    # the smallest non-octahedral targets in these families have 10.
    require(all(x["pared_order"] <= 9 for x in source),
            "Unexpected historically larger pared source")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    data = json.loads(REPORT.read_text(encoding="utf-8"))
    validate_record(data)
    if args.self_test:
        bad = copy.deepcopy(data)
        bad["cohort"]["cases"][-1]["level3_status"] = "NEGATIVE_REPORTED"
        try:
            validate_record(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("Corrupt timeout was accepted")
        bad = copy.deepcopy(data)
        bad["o8_complement_induced_matching_witnesses"]["12"][0][1] = 6
        try:
            validate_record(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid target witness was accepted")
    print(
        "RECORD AUDIT PASSED: 49 cases (36 conditional, 13 other); "
        "five proved-divergent exclusions; six induced-O8 target witnesses; "
        "260910 P3 INCOMPLETE. Original exhaustive searches NOT replayed."
    )


if __name__ == "__main__":
    main()
