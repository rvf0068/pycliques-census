"""Read-only replay of merged v24 proofs after ten-v25 becomes current.

Only the old verifiers' former mutable-root Path *aliases* are patched
in memory to their respective immutable source snapshots. The complete
archived certificates, graph6 files, exact maps, and mathematical checks
remain untouched. No file or historical module is edited or copied.

The archive replayers and their tests remain usable while the current
ten-vertex census advances to v25.
"""
from __future__ import annotations

import argparse
import unittest
from unittest.mock import patch

from research.order10_p4_o12_lifts_v24 import (
    verify as old_v24, test_verify as old_v24_tests,
    verify_transport as old_transport,
)
from research.order10_p4_no_octahedral_10820813_v1 import (
    verify as old_p4, test_verify as old_p4_tests,
)
from research.order10_p5_growth_10820813_v1 import (
    verify as old_p5, test_verify as old_p5_tests,
)
from research.order10_p4_reference_pilot_v24 import (
    search as old_pilot, verify_results as old_pilot_audit,
)
from research.order10_p4_cap_rescue_v24 import (
    verify as old_cap, test_verify as old_cap_tests,
)


def check_tests(module) -> None:
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise RuntimeError("Historical test replay failed: " + module.__name__)


def run(stage: str) -> None:
    # Fix only aliases, not historical files or their provenance checks.
    with (
        patch.object(old_v24, "CURRENT", old_v24.NEW),
        patch.object(old_p4, "CURRENT", old_p4.SNAPSHOT),
        patch.object(old_pilot, "CURRENT", old_pilot.SOURCE),
        patch.object(old_pilot_audit, "CURRENT", old_pilot.SOURCE),
    ):
        if stage in ("v24_lifts", "all"):
            old_v24.verify_archive()
            check_tests(old_v24_tests)
            print("PASS: frozen v24 complete O12 positive proofs", flush=True)
        if stage in ("v24_transport", "all"):
            old_transport.main()
            print("PASS: frozen v24 transported O12 full projections", flush=True)
        if stage in ("p4_obstruction", "all"):
            check_tests(old_p4_tests)
            import json
            cert = json.loads(old_p4.ARCHIVE.read_text(encoding="utf-8"))
            graph_stages = old_p4.reconstruct_all(cert)
            old_p4.verify_earlier_stages(cert, graph_stages[:4])
            old_p4.verify_result(
                cert, old_p4.enumerate_targets(graph_stages[-1])
            )
            print("PASS: frozen 10820813 P0--P4 obstruction", flush=True)
        if stage in ("p5_growth", "all"):
            check_tests(old_p5_tests)
            old_p5.verify()
            print("PASS: frozen 10820813 P5 growth / O20 witness", flush=True)
        if stage in ("p4_cap", "all"):
            # test_replay_all_26_exact_fourth_iterates invokes old_cap.verify()
            # itself. Running old_cap.verify() here a second time would
            # reconstruct all 26 expensive graphs redundantly.
            check_tests(old_cap_tests)
            print("PASS: frozen 26 recovered P4 graph certificates", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=(
        "v24_lifts", "v24_transport",
        "p4_obstruction", "p5_growth", "p4_cap", "all",
    ))
    args = parser.parse_args()
    run(args.stage)


if __name__ == "__main__":
    main()
