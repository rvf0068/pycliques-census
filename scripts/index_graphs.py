"""Create a reproducible source-index-to-graph6 inventory for one order."""
import argparse
import csv
import os
from pathlib import Path
from graph_sources import EXPECTED_COUNTS, connected_graphs, graph6


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--order", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".partial")
    count = 0
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["index", "graph6", "vertices", "edges"])
        for index, graph in enumerate(connected_graphs(args.order)):
            writer.writerow([index, graph6(graph), graph.number_of_nodes(), graph.number_of_edges()])
            count += 1
    if count != EXPECTED_COUNTS[args.order]:
        raise RuntimeError(f"Order {args.order}: expected {EXPECTED_COUNTS[args.order]} graphs, got {count}")
    os.replace(temporary, args.output)
    print(f"Order {args.order}: indexed {count} connected graphs")


if __name__ == "__main__":
    main()
