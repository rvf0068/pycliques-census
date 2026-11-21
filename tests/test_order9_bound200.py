"""New order-9 stage and homology-gated clockwork pilot regressions."""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import order9_bound200 as stage  # noqa: E402
import order9_clockwork_pilot as pilot  # noqa: E402


class Order9NewStageTests(unittest.TestCase):
    def test_historical_cohort_is_54_with_36_conditional(self):
        cohort, source, groups = stage.cohort()
        self.assertEqual(len(cohort), 54)
        self.assertEqual(len(source), 63)
        self.assertEqual(
            {kind: list(groups.values()).count(kind)
             for kind in ("conjectured", "nonconjectural")},
            {"conjectured": 36, "nonconjectural": 18},
        )

    def test_pilot_cases_really_have_beta1_one_at_k2(self):
        from pycliques.dominated import completely_pared_graph
        from pycliques.small import CliqueSequence

        for index, graph6 in pilot.CASES:
            original = nx.from_graph6_bytes(graph6.encode("ascii"))
            self.assertEqual(pilot.betti_one_mod2(original), 1, index)
            seq = CliqueSequence(completely_pared_graph(original), bound=200)
            k2 = seq[2]
            self.assertIsNotNone(k2)
            self.assertEqual(pilot.betti_one_mod2(k2), 1, index)

    def test_mod2_homology_filter_examples(self):
        self.assertEqual(pilot.betti_one_mod2(nx.cycle_graph(7)), 1)
        self.assertEqual(pilot.betti_one_mod2(nx.octahedral_graph()), 0)
        self.assertEqual(pilot.betti_one_mod2(nx.complete_graph(4)), 0)
        self.assertEqual(pilot.betti_one_mod2(nx.disjoint_union(
            nx.cycle_graph(3), nx.cycle_graph(4))), 1)

    def test_immutable_manifest_guard_rejects_changed_implementation(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / "stage"
            cohort = {1: {"graph6": "HCRSv\\}"}}
            original = {"schema": 1, "bound": 200}
            stage.saved_records(folder, cohort, original)
            with self.assertRaisesRegex(RuntimeError, "manifest differs"):
                stage.saved_records(folder, cohort, {"schema": 1, "bound": 201})

    def test_classify_failing_worker_is_not_a_mathematical_verdict(self):
        # Supervisor diagnostic semantics must preserve explicit errors.
        with tempfile.TemporaryDirectory() as d:
            with patch.object(stage, "WORKER", Path(d) / "missing_worker.py"):
                with contextlib.redirect_stdout(io.StringIO()):
                    out = stage.classify_one("HCZTf\\}", Path(d))
        self.assertEqual(out["status"], "ERROR")
        self.assertEqual(out["verdict"], "INDETERMINATE")
        self.assertEqual(out["bound"], 200)


if __name__ == "__main__":
    unittest.main()
