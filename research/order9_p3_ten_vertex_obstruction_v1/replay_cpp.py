"""Compile an independent C++17 certificate for the ten-target obstruction.

The C++ solver uses a maximum-global-gain branching heuristic; the
pure Python verifier uses a most-constrained-row branching heuristic.
Both independently enumerate all valid target sets and test the
necessary fixed-target image domains. Any timeout or failed process
is INCONCLUSIVE and cannot be used to infer nonexistence.
"""
from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys
import tempfile

from research.order9_p3_eight_vertex_obstruction_v1.verify import (
    SOURCES,
    check,
    reconstruct_p3,
    verify_frozen_sources,
)
from research.order9_p3_ten_vertex_obstruction_v1.verify import EXPECTED

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical assertions")

HERE = Path(__file__).resolve().parent
CPP_SOURCE = HERE / "enumerate.cpp"
RESULT = re.compile(
    r"^EXHAUSTIVE size=10 open_double_covers=(\d+) "
    r"unary_survivors=(\d+) search_nodes=(\d+) "
    r"forced=(\d+) bound_prunes=(\d+)$"
)


def verify() -> None:
    verify_frozen_sources()
    with tempfile.TemporaryDirectory() as temporary:
        location = Path(temporary)
        binary = location / "enumerate"
        compile_run = subprocess.run(
            ["c++", "-std=c++17", "-O3", "-Wall", "-Wextra",
             str(CPP_SOURCE), "-o", str(binary)],
            capture_output=True, text=True, check=False, timeout=90,
        )
        check(compile_run.returncode == 0,
              f"C++17 compilation failed: {compile_run.stderr}")
        for idx in SOURCES:
            graph = reconstruct_p3(idx)
            source = location / f"McKay_{idx}_P3.edgelist"
            with source.open("w", encoding="ascii") as output:
                output.write(f"{len(graph)} {graph.number_of_edges()}\n")
                for u, v in graph.edges():
                    output.write(f"{u} {v}\n")
            result = subprocess.run(
                [str(binary), str(source), "10", "40"],
                capture_output=True, text=True, check=False, timeout=50,
            )
            check(
                result.returncode == 0,
                f"C++ result INCONCLUSIVE for McKay {idx}: "
                f"{result.stdout} {result.stderr}",
            )
            match = RESULT.fullmatch(result.stdout.strip())
            check(match is not None,
                  f"C++ output malformed or not exhaustive for McKay {idx}")
            cover_count, survivors, states, forced, bounds = (
                int(v) for v in match.groups()
            )
            check(
                cover_count == EXPECTED[idx]
                and survivors == 0 and states > 0 and bounds > 0,
                f"Independent C++17 result disagrees at McKay {idx}",
            )
            print(
                f"PASS_CXX McKay={idx} ten_open_double_covers={cover_count} "
                f"unary_survivors={survivors} "
                f"integer_states={states} forced={forced} "
                f"safe_pruning_bound_uses={bounds}",
                flush=True,
            )


if __name__ == "__main__":
    verify()
