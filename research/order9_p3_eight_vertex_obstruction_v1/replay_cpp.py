"""Compile a separately implemented C++17 eight-cover enumerator and compare.

The independent Python verifier proves the minimum exceeds seven before
this C++ solver enumerates exact eight-vertex covers. Timeouts, missing
C++ compilers and any malformed result fail the run: none can certify NO.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from research.order9_p3_eight_vertex_obstruction_v1.verify import (
    SOURCES,
    check,
    reconstruct_p3,
    search_at_most,
    complement_masks,
    verify_frozen_sources,
)

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical assertions")

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "enumerate.cpp"
PATTERN = re.compile(
    r"^EXHAUSTED size=8 coverings=(\d+) "
    r"degree_4_5_candidates=(\d+) states=(\d+) "
    r"forced=(\d+) integer_bound_prunes=(\d+)$"
)


def verify_native() -> None:
    verify_frozen_sources()
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        binary = directory / "enumerate"
        compiled = subprocess.run(
            ["c++", "-O3", "-std=c++17", "-Wall", "-Wextra",
             str(SOURCE), "-o", str(binary)],
            capture_output=True, text=True, check=False, timeout=90,
        )
        check(
            compiled.returncode == 0,
            f"Independent C++17 compilation failed: {compiled.stderr}",
        )
        for idx, case in SOURCES.items():
            graph = reconstruct_p3(idx)
            below8, _ = search_at_most(complement_masks(graph), 7)
            check(below8 is None, "Native replay requires proved minimum >=8")
            filename = directory / f"P3_{idx}.edgelist"
            with filename.open("w", encoding="ascii") as stream:
                stream.write(f"{len(graph)} {graph.number_of_edges()}\n")
                for u, v in graph.edges():
                    stream.write(f"{u} {v}\n")
            completed = subprocess.run(
                [str(binary), str(filename), "8", "30"],
                capture_output=True, text=True, check=False, timeout=40,
            )
            check(
                completed.returncode == 0,
                f"C++ search failed/inconclusive for {idx}: "
                f"{completed.stdout} {completed.stderr}",
            )
            match = PATTERN.fullmatch(completed.stdout.strip())
            check(match is not None,
                  f"Malformed/incomplete C++ proof result at {idx}")
            covers, pattern, states, forced, bound_prunes = map(
                int, match.groups()
            )
            check(
                covers == len(case["eight_covers"])
                and pattern == 0 and states > 0 and bound_prunes > 0,
                f"Independent C++ outcome disagrees with exact Python at {idx}",
            )
            print(
                f"PASS_CXX McKay={idx} eight_covers={covers} "
                f"snub_degree_pattern_candidates={pattern} "
                f"exhaustive_integer_nodes={states} forced={forced} "
                f"safe_deficit_bound_prunes={bound_prunes}",
                flush=True,
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    verify_native()


if __name__ == "__main__":
    main()
