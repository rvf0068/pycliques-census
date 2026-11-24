"""Positive-only P4 reference-isomorphism pilot on certified ten-v24 P3 classes.

Only P3 representatives not already proved divergent are processed. Every
P4 uses independent bitset Bron--Kerbosch, NetworkX facet crosscheck,
and integer-mask closed-neighborhood paring. Isomorphism candidates
are finally verified on every edge and nonedge; a matching fingerprint
is never a proof. Bound/timeouts are recorded as inconclusive.

Run in CI via run --shard N --shards 12, each graph in a timed subprocess.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import networkx as nx

from research.order10_p3_global_v23_index.independent_verify import (
    LimitHit,
    independent_p3,
    independent_clique_graph,
    independent_pare,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "indeterminate_order_10_v24.txt"
CURRENT = ROOT / "indeterminate_order_10.txt"
ARCHIVE = ROOT / "research/order10_p3_global_v23_index/certificates.json"
EXCLUDED = frozenset((11495390, 11533866, 11556387))
from .reference_provenance import (
    REFERENCE_G6, REFERENCE_DIMENSIONS, check_reference_provenance,
)


def check(value: bool, why: str) -> None:
    if not value:
        raise AssertionError(why)


def source_rows() -> dict[int, str]:
    check_reference_provenance()
    check(SOURCE.read_bytes() == CURRENT.read_bytes(),
          "Current root differs from certified ten-v24")
    lines = SOURCE.read_text(encoding="ascii").splitlines()
    check(lines[0].endswith("order ten, v24") and
          lines[1] == "# Remaining=1056 previous_v23=1059 newly_proved_divergent=3",
          "Missing v24 header or wrong census provenance")
    result = {}
    for line in lines:
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        check(len(parts) == 6, "Malformed six-field record")
        index, order, g6, rule, status, label = parts
        if order != "10":
            continue
        check((rule, status, label) == ("-", "-", "-"), "Conditional source")
        check(int(index) not in result and
              len(nx.from_graph6_bytes(g6.encode("ascii"))) == 10,
              "Duplicate or invalid original graph6")
        result[int(index)] = g6
    check(len(result) == 626, "Wrong ten-v24 stiff source cohort")
    return result


def representatives() -> list[tuple[int, str]]:
    data = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    check(data["immutable_source_git_blob"] ==
          "f32ceb913b44583f472402e14c596598fef71aaa",
          "Historical ten-v23 index provenance changed")
    ids = set(data["singleton_indices"]) | {
        cl["representative"] for cl in data["nontrivial_classes"]
    }
    check(len(ids) == 525 and EXCLUDED <= set(data["singleton_indices"]),
          "Unexpected frozen global P3 class partition")
    ids.difference_update(EXCLUDED)
    sources = source_rows()
    check(len(ids) == 522 and ids <= sources.keys(),
          "Incorrect certified v24 representative count")
    return [(i, sources[i]) for i in sorted(ids)]


def fourth(graph6: str) -> tuple[nx.Graph, nx.Graph, nx.Graph]:
    p3 = independent_p3(graph6)
    raw = independent_clique_graph(
        p3, stage=4, orders=[10, -1, -1, len(p3)]
    )
    p4 = independent_pare(raw)
    return p3, raw, p4


def dims(graph: nx.Graph) -> tuple[int, int]:
    return len(graph), graph.number_of_edges()


def verify_map(a: nx.Graph, b: nx.Graph, mapping: list[int]) -> None:
    n = len(a)
    check(n == len(b) == len(mapping) and
          sorted(mapping) == list(range(n)), "Not a complete bijection")
    check(all(
        a.has_edge(i, j) == b.has_edge(mapping[i], mapping[j])
        for i in range(n) for j in range(n)
    ), "False P4 graph isomorphism mapping")


def exact_isomorphism(a: nx.Graph, b: nx.Graph) -> list[int] | None:
    if dims(a) != dims(b):
        return None
    if sorted(d for _, d in a.degree) != sorted(d for _, d in b.degree):
        return None
    if nx.weisfeiler_lehman_graph_hash(a, iterations=3) != (
        nx.weisfeiler_lehman_graph_hash(b, iterations=3)
    ):
        return None
    # Complement is often far sparser than these dense fourth iterates.
    matcher = nx.algorithms.isomorphism.GraphMatcher(
        nx.complement(a), nx.complement(b)
    )
    if not matcher.is_isomorphic():
        return None
    mapping = [int(matcher.mapping[i]) for i in range(len(a))]
    verify_map(a, b, mapping)
    return mapping


def inspect(index: int, g6: str, p3_low: int, p3_high: int) -> dict:
    check_reference_provenance()
    p3 = independent_p3(g6)
    base = {
        "index": index, "graph6": g6,
        "p3": list(dims(p3)),
    }
    if not p3_low <= len(p3) <= p3_high:
        return {**base, "status": "P3_OUTSIDE_WINDOW"}
    try:
        raw = independent_clique_graph(
            p3, stage=4, orders=[10, -1, -1, len(p3)]
        )
        p4 = independent_pare(raw)
    except LimitHit as exc:
        return {**base, "status": "P4_FACET_CAP",
                "reason": exc.reason, "stage": exc.stage}
    base.update(raw_p4=list(dims(raw)), p4=list(dims(p4)))
    candidates = [
        index for index, shape in REFERENCE_DIMENSIONS.items()
        if shape == dims(p4)
    ]
    if not candidates:
        return {**base, "status": "NO_REFERENCE_DIMENSION_MATCH"}
    positives = []
    for ref in candidates:
        _r3, _raw, target = fourth(REFERENCE_G6[ref])
        check(dims(target) == REFERENCE_DIMENSIONS[ref],
              "Previously certified reference dimensions changed")
        permutation = exact_isomorphism(p4, target)
        if permutation is not None:
            positives.append({
                "reference": ref,
                "images_b64": base64.b64encode(bytes(permutation)).decode("ascii"),
                "host_sha256": hashlib.sha256(
                    nx.to_graph6_bytes(p4, header=False).strip()
                ).hexdigest(),
                "reference_sha256": hashlib.sha256(
                    nx.to_graph6_bytes(target, header=False).strip()
                ).hexdigest(),
            })
    return {
        **base, "status": "EXACT_MATCH" if positives else "CHECKED_NONMATCH",
        "candidate_references": candidates, "positives": positives,
    }


def plan(low: int, high: int) -> dict:
    originals = representatives()
    selection = []
    for idx, g6 in originals:
        graph = independent_p3(g6)
        if low <= len(graph) <= high:
            selection.append((idx, g6, len(graph)))
    return {
        "original_representatives": len(originals),
        "window": [low, high],
        "selected": selection,
    }


def run(args) -> None:
    cohort = plan(args.min_p3, args.max_p3)
    selected = cohort["selected"][args.shard::args.shards]
    records = []
    for index, graph6, p3_order in selected:
        cmd = [
            sys.executable, "-m",
            "research.order10_p4_reference_pilot_v24.search",
            "one", "--index", str(index),
            "--min-p3", str(args.min_p3),
            "--max-p3", str(args.max_p3),
        ]
        try:
            child = subprocess.run(
                cmd, capture_output=True, text=True, check=True,
                timeout=args.timeout_sec,
            )
            record = json.loads(child.stdout.strip())
            check(record["index"] == index and
                  record["graph6"] == graph6 and
                  record["p3"][0] == p3_order,
                  "Subprocess returned incorrect source identity")
        except subprocess.TimeoutExpired:
            record = {
                "index": index, "graph6": graph6,
                "p3": [p3_order], "status": "TIMEOUT",
            }
        except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Unexpected inspection failure {index}") from exc
        records.append(record)
        print("CASE", json.dumps({
            k: v for k, v in record.items()
            if k not in ("positives", "graph6")
        }, separators=(",", ":")), flush=True)
        if record["status"] == "EXACT_MATCH":
            print("POSITIVE_CERTIFICATE", json.dumps(
                record, separators=(",", ":"), sort_keys=True
            ), flush=True)
    payload = {
        "schema": 1, "source": SOURCE.name,
        "historical_p3_source": ARCHIVE.relative_to(ROOT).as_posix(),
        "settings": {
            "shards": args.shards, "shard": args.shard,
            "min_p3": args.min_p3, "max_p3": args.max_p3,
            "timeout_sec": args.timeout_sec,
        },
        "representatives": cohort["original_representatives"],
        "selected_total": len(cohort["selected"]),
        "records": records,
        "status_counts": dict(Counter(r["status"] for r in records)),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print("SUMMARY", json.dumps({
        "shard": args.shard, "selected": len(selected),
        "total_window": len(cohort["selected"]),
        "counts": payload["status_counts"],
    }, sort_keys=True), flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("plan", "one", "run"))
    ap.add_argument("--index", type=int)
    ap.add_argument("--shards", type=int, default=12)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--min-p3", type=int, default=41)
    ap.add_argument("--max-p3", type=int, default=55)
    ap.add_argument("--timeout-sec", type=int, default=24)
    ap.add_argument("--output", type=Path)
    a = ap.parse_args()
    if (a.shards < 1 or not 0 <= a.shard < a.shards
            or a.min_p3 < 1 or a.max_p3 < a.min_p3
            or a.timeout_sec < 1):
        ap.error("Invalid shard, window or timeout")
    if a.command == "plan":
        overview = plan(a.min_p3, a.max_p3)
        print(json.dumps({
            "original_representatives": overview["original_representatives"],
            "window": overview["window"],
            "window_cases": len(overview["selected"]),
            "cases_per_shard": [
                len(overview["selected"][s::a.shards])
                for s in range(a.shards)
            ],
        }, sort_keys=True))
    elif a.command == "one":
        rows = dict(representatives())
        if a.index not in rows:
            ap.error("index is not a surviving v24 P3 representative")
        print(json.dumps(
            inspect(a.index, rows[a.index], a.min_p3, a.max_p3),
            separators=(",", ":"), sort_keys=True
        ))
    else:
        if a.output is None:
            ap.error("--output required for run")
        run(a)


if __name__ == "__main__":
    main()
