#!/usr/bin/env python3
"""Locate the first classifier exception in a connected-graph source interval.

This diagnostic does NOT write to runs/, change any classifier setting, or alter
the provenance hash of scripts/. Run it in the same pinned Codespace environment
as the interrupted census, and record its output before updating pycliques.
"""

from __future__ import annotations

import argparse
import itertools
import subprocess
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from graph_sources import EXPECTED_COUNTS, connected_graphs, graph6  # noqa: E402
from pycliques.small import classify_clique_behavior  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--order", type=int, default=9, choices=range(6, 11))
    parser.add_argument("--start", type=int, default=250000)
    parser.add_argument("--end", type=int, default=260000, help="exclusive source index")
    parser.add_argument("--bound", type=int, default=30)
    parser.add_argument("--progress", type=int, default=1000)
    args = parser.parse_args()
    if not 0 <= args.start < args.end <= EXPECTED_COUNTS[args.order]:
        parser.error("Require 0 <= start < end <= connected-graph count")
    if args.bound < 1 or args.progress < 1:
        parser.error("bound and progress must be positive")
    checkout = ROOT / ".deps" / "pycliques-project"
    sha = subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True
    ).strip()
    print(
        f"source_commit={sha} order={args.order} "
        f"range=[{args.start},{args.end}) bound={args.bound}",
        flush=True,
    )
    source = itertools.islice(connected_graphs(args.order), args.start, args.end)
    for index, graph in enumerate(source, start=args.start):
        if (index - args.start) % args.progress == 0:
            print(f"checking index={index}", flush=True)
        try:
            classify_clique_behavior(graph, bound=args.bound)
        except Exception as exc:
            print(
                f"CLASSIFICATION ERROR order={args.order} index={index} "
                f"graph6={graph6(graph)} edges={graph.number_of_edges()}",
                flush=True,
            )
            print(f"{type(exc).__name__}: {exc}", flush=True)
            traceback.print_exc()
            return 1
    print("No exceptions in requested range.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
