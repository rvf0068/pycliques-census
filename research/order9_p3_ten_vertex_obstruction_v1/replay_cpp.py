"""Compile an independent C++17 certificate for the ten-target obstruction.

The C++ program rebuilds P0-P3 from the original graph6 without Python
edge lists, checks stage sizes and triangle counts, and then uses a
maximum-global-gain branching heuristic; the
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
    FROZEN,
    check,
    verify_frozen_sources,
)
from research.order9_p3_ten_vertex_obstruction_v1.verify import EXPECTED

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical assertions")

HERE = Path(__file__).resolve().parent
CPP_SOURCE = HERE / "enumerate.cpp"
RESULT = re.compile(
    r"^EXHAUSTIVE native_P3=(\d+)/(\d+) size=10 open_double_covers=(\d+) "
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
        # Read the immutable ORIGINAL graph6 rows, not Python's P3
        # adjacency. Native C++ decodes graph6, computes K and dominated
        # vertex paring three times, and verifies P0-P3 sizes and triangles.
        originals = {}
        for line in FROZEN.read_text(encoding="ascii").splitlines():
            if line and not line.startswith("#"):
                fields = line.split()
                check(len(fields) == 6, "Unexpected frozen source row")
                check(int(fields[1]) == 9, "Incorrect original order")
                originals[int(fields[0])] = fields[2]
        check(set(originals) == set(SOURCES), "Incorrect original source set")
        for idx in SOURCES:
            result = subprocess.run(
                [str(binary), str(idx), originals[idx], "10", "40"],
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
            order, edges, cover_count, survivors, states, forced, bounds = (
                int(v) for v in match.groups()
            )
            check(
                (order, edges) == SOURCES[idx]["stages"][3]
                and cover_count == EXPECTED[idx]
                and survivors == 0 and states > 0 and bounds > 0,
                f"Independent C++17 result disagrees at McKay {idx}",
            )
            print(
                f"PASS_CXX McKay={idx} native_P3={order}/{edges} "
                f"ten_open_double_covers={cover_count} "
                f"unary_survivors={survivors} "
                f"integer_states={states} forced={forced} "
                f"safe_pruning_bound_uses={bounds}",
                flush=True,
            )


if __name__ == "__main__":
    verify()
