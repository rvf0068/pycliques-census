"""Positive-only bounded raw K³ octahedral retraction screen of v9 stiff ten-cores.

This *exploratory* program discovers possible full retraction maps and
verifies every positive map before printing PROOF_JSON. Timeouts, missing
patterns and negative results are NOT clique-behavior classifications.
No modified census verdict, no homology computation, no pycliques dependency.
Requires networkx==3.6.1.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import time
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "indeterminate_order_10_v9.txt"
SOURCE_SHA1 = "704219076c6d61b595374cd129c5fa520253a089"


def rows() -> list[tuple[int, str]]:
    raw = SOURCE.read_bytes()
    digest = hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()
    if digest != SOURCE_SHA1:
        raise ValueError("Frozen source v9 snapshot changed")
    result: list[tuple[int, str]] = []
    for row in raw.decode("utf-8").splitlines():
        if not row or row.startswith("#"):
            continue
        f = row.split()
        if len(f) != 6:
            raise ValueError("Malformed six-column historical source")
        if f[1] == "10" and f[3:] == ["-", "-", "-"]:
            result.append((int(f[0]), f[2]))
    if len(result) != 1393:
        raise ValueError("Unexpected current nonconditional ten-stiff population")
    return result


def clique_graph(graph: nx.Graph, max_facets: int = 125,
                 max_seconds: float = 20.0) -> nx.Graph:
    """Bound facet generation *before* allocating the next clique graph."""
    deadline = time.monotonic() + max_seconds
    facets: list[int] = []
    for q in nx.find_cliques(graph):
        if time.monotonic() > deadline:
            raise TimeoutError("Clique construction exceeded its deadline")
        facets.append(sum(1 << v for v in q))
        if len(facets) > max_facets:
            raise OverflowError("Next clique graph exceeds vertex cap")
    facets.sort()
    h = nx.Graph()
    h.add_nodes_from(range(len(facets)))
    for i, j in itertools.combinations(range(len(facets)), 2):
        if time.monotonic() > deadline:
            raise TimeoutError("Facet intersection construction timed out")
        if facets[i] & facets[j]:
            h.add_edge(i, j)
    return h


def verify_positive(h: nx.Graph, matching: list[tuple[int, int]],
                    projection: list[int]) -> None:
    d = len(matching)
    target = [v for edge in matching for v in edge]
    if d < 3 or len(set(target)) != 2 * d:
        raise ValueError("Incorrect opposite pairs")
    if len(projection) != len(h) or set(projection) != set(target):
        raise ValueError("Incomplete projection")
    if any(projection[v] != v for v in target):
        raise ValueError("Projection does not fix induced target")
    sub = h.subgraph(target)
    observed = {tuple(sorted(pair)) for pair in nx.non_edges(sub)}
    expected = {tuple(sorted(pair)) for pair in matching}
    if observed != expected or not nx.is_isomorphic(
        sub, nx.complete_multipartite_graph(*([2] * d))
    ):
        raise ValueError("Target is not an induced O_d")
    if any(
        projection[u] != projection[v]
        and not sub.has_edge(projection[u], projection[v])
        for u, v in h.edges()
    ):
        raise ValueError("Non-morphism projection edge")


class Search:
    def __init__(self, h: nx.Graph, dimension: int, max_patterns: int,
                 seconds: float):
        self.h = h
        self.n = len(h)
        self.d = dimension
        self.max_patterns = max_patterns
        self.seconds = seconds
        self.started = time.monotonic()
        self.deadline = self.started + seconds
        self.limit_hit = False
        self.full = (1 << self.n) - 1
        self.h_neigh = [
            sum(1 << v for v in h[i]) for i in range(self.n)
        ]
        self.c_neigh = [
            self.full & ~(1 << i | self.h_neigh[i])
            for i in range(self.n)
        ]
        self.edges = [
            (i, j) for i in range(self.n)
            for j in range(i + 1, self.n)
            if self.c_neigh[i] & (1 << j)
        ]
        self.compat = []
        for k, (a, b) in enumerate(self.edges):
            if time.monotonic() > self.deadline:
                self.limit_hit = True
                break
            forbidden = self.c_neigh[a] | self.c_neigh[b] | (1 << a) | (1 << b)
            bitmask = 0
            for l in range(k + 1, len(self.edges)):
                if l % 128 == 0 and time.monotonic() > self.deadline:
                    self.limit_hit = True
                    break
                x, y = self.edges[l]
                if not (forbidden & ((1 << x) | (1 << y))):
                    bitmask |= 1 << l
            self.compat.append(bitmask)
            if self.limit_hit:
                break
        self.covers = [
            self.c_neigh[a] | self.c_neigh[b] | (1 << a) | (1 << b)
            for a, b in self.edges
        ]
        self.patterns = 0
        self.found = None
        self.nodes = 0
        self.visits = 0

    def solve(self, matching: list[tuple[int, int]],
              covered_target: int) -> list[int] | None:
        target = [v for edge in matching for v in edge]
        outside = [
            v for v in range(self.n)
            if not (covered_target & (1 << v))
        ]
        opposite = {u: v for u, v in matching}
        opposite.update({v: u for u, v in matching})
        domains = [
            sum(
                1 << j for j, t in enumerate(target)
                if self.c_neigh[x] & (1 << opposite[t])
            )
            for x in outside
        ]
        if any(not a for a in domains):
            return None
        neighbors = [
            sum(
                1 << j for j, y in enumerate(outside)
                if x != y and self.h_neigh[x] & (1 << y)
            )
            for x in outside
        ]
        visit_count = 0

        def backtrack(d: list[int]) -> list[int] | None:
            nonlocal visit_count
            visit_count += 1
            self.nodes += 1
            if visit_count > 2500 or time.monotonic() > self.deadline:
                self.limit_hit = True
                return None
            pending = [
                i for i, domain in enumerate(d)
                if domain.bit_count() == 1
            ]
            while pending:
                if time.monotonic() > self.deadline:
                    self.limit_hit = True
                    return None
                i = pending.pop()
                bit = d[i]
                forbidden = 1 << ((bit.bit_length() - 1) ^ 1)
                remain = neighbors[i]
                while remain:
                    last = remain & -remain
                    j = last.bit_length() - 1
                    remain ^= last
                    new = d[j] & ~forbidden
                    if new != d[j]:
                        if not new:
                            return None
                        d[j] = new
                        if new.bit_count() == 1:
                            pending.append(j)
            idx = min(
                (i for i, m in enumerate(d) if m.bit_count() > 1),
                key=lambda i: d[i].bit_count(),
                default=None,
            )
            if idx is None:
                result = list(range(self.n))
                for i, v in enumerate(outside):
                    result[v] = target[d[i].bit_length() - 1]
                return result
            options = d[idx]
            while options:
                bit = options & -options
                options ^= bit
                nxt = d.copy()
                nxt[idx] = bit
                positive = backtrack(nxt)
                if positive is not None:
                    return positive
                if self.limit_hit:
                    return None
            return None

        return backtrack(domains)

    def visit(self, matching, choices, covered_target, covered_neighborhood):
        if self.found is not None or self.limit_hit:
            return
        self.visits += 1
        if time.monotonic() > self.deadline:
            self.limit_hit = True
            return
        if len(matching) == self.d:
            self.patterns += 1
            if self.patterns > self.max_patterns:
                self.limit_hit = True
                return
            if covered_neighborhood != self.full:
                return
            projection = self.solve(matching, covered_target)
            if projection is not None:
                verify_positive(self.h, matching, projection)
                self.found = {
                    "opposite_pairs": matching,
                    "projection": projection,
                }
            return
        needed = self.d - len(matching)
        while choices and not self.limit_hit and self.found is None:
            if time.monotonic() > self.deadline:
                self.limit_hit = True
                return
            bit = choices & -choices
            choices ^= bit
            edge = bit.bit_length() - 1
            reduced = choices & self.compat[edge]
            if reduced.bit_count() < needed - 1:
                continue
            a, b = self.edges[edge]
            self.visit(
                matching + [(a, b)], reduced,
                covered_target | (1 << a) | (1 << b),
                covered_neighborhood | self.covers[edge],
            )

    def run(self):
        if self.limit_hit:
            return None
        self.visit([], (1 << len(self.edges)) - 1, 0, 0)
        return self.found


def scan_batch(batch: int, batches: int, seconds: float,
               output: Path | None) -> None:
    todo = rows()[batch::batches]
    positives = []
    counts = {
        "input": len(todo), "examined": 0, "skipped_large": 0,
        "skipped_error": 0, "positive": 0, "bounded": 0
    }
    for idx, g6 in todo:
        counts["examined"] += 1
        sizes = []
        try:
            g = nx.from_graph6_bytes(g6.encode("ascii"))
            for level in range(4):
                sizes.append([len(g), g.number_of_edges()])
                if level < 3:
                    if len(g) > 125:
                        raise OverflowError("intermediate clique graph too large")
                    g = clique_graph(g)
            if len(g) > 125:
                raise OverflowError("Third clique graph exceeds vertex cap")
            found = None
            bounded = False
            for d in (7, 6, 5, 4):
                s = Search(g, d, 150000, seconds)
                result = s.run()
                bounded |= s.limit_hit
                if result is not None:
                    found = {
                        "index": idx, "graph6": g6,
                        "iterate_sizes": sizes, "dimension": d, **result
                    }
                    verify_positive(
                        g, [tuple(p) for p in result["opposite_pairs"]],
                        result["projection"],
                    )
                    positives.append(found)
                    counts["positive"] += 1
                    print(
                        "PROOF_JSON " + json.dumps(
                            found, separators=(",", ":"), sort_keys=True
                        ),
                        flush=True,
                    )
                    break
            counts["bounded"] += bounded
        except OverflowError:
            counts["skipped_large"] += 1
        except TimeoutError:
            counts["bounded"] += 1
        except Exception as e:
            counts["skipped_error"] += 1
            print(
                "ERROR_JSON " + json.dumps(
                    {"index": idx, "graph6": g6, "error": repr(e)}
                ), flush=True
            )
        if counts["examined"] % 25 == 0:
            print(
                "PROGRESS_JSON " + json.dumps(
                    {"batch": batch, "index": idx, **counts},
                    sort_keys=True,
                ), flush=True
            )
    summary = {"batch": batch, "batches": batches, **counts}
    print("SUMMARY_JSON " + json.dumps(summary, sort_keys=True), flush=True)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(
                {"summary": summary, "proofs": positives},
                indent=2, sort_keys=True,
            ) + "\n", encoding="utf-8"
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, required=True)
    ap.add_argument("--batches", type=int, default=8)
    ap.add_argument("--seconds", type=float, default=0.8)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    if args.batches < 1 or not 0 <= args.batch < args.batches:
        raise ValueError("Invalid batch assignment")
    scan_batch(args.batch, args.batches, args.seconds, args.output)


if __name__ == "__main__":
    main()
