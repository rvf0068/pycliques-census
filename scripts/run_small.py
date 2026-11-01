"""Classify connected graphs of orders 1..5 using the current fast classifier."""
import argparse
import csv
import os
from pathlib import Path

from graph_sources import EXPECTED_COUNTS, connected_graphs
from pycliques.small import classify_clique_behavior


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--order", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bound", type=int, default=30)
    args = parser.parse_args()
    if args.order not in range(1, 6):
        parser.error("orders 1..5 only")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".partial")
    count = 0
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        handle.write("# index\tverdict\treason\n")
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        for idx, graph in enumerate(connected_graphs(args.order)):
            result = classify_clique_behavior(graph, bound=args.bound)
            writer.writerow([idx, result.verdict.name, result.reason])
            count += 1
    if count != EXPECTED_COUNTS[args.order]:
        raise RuntimeError(f"Order {args.order}: expected {EXPECTED_COUNTS[args.order]} graphs; found {count}")
    os.replace(temporary, args.output)
    print(f"Order {args.order}: wrote {count} verdicts to {args.output}")


if __name__ == "__main__":
    main()
