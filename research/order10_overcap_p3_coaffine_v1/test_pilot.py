"""Exact degree-obstruction and replay guard regressions."""
from __future__ import annotations

import unittest

import networkx as nx

from . import aggregate, pilot


class CoaffineTenCoreTests(unittest.TestCase):
    def test_every_one_of_the_ten_has_degree_obstruction(self):
        hosts = pilot.source_catalog()
        self.assertEqual(len(hosts), 521)
        for idx in pilot.TEN_P3_OVERCAP:
            with self.subTest(McKay=idx):
                g = nx.from_graph6_bytes(
                    hosts[idx]["p3_graph6"].encode("ascii")
                )
                result = pilot.degree_obstruction(g)
                v = result["vertex"]
                H = nx.complement(g)
                self.assertGreater(H.degree(v), 0)
                self.assertTrue(all(
                    H.degree(v) != H.degree(w) for w in H[v]
                ))

    def test_no_false_obstruction_on_octahedron(self):
        # In O3 all vertices have the same degree and an antipode
        # outside the closed neighborhood, so degree cannot prohibit
        # its genuine coaffination.
        with self.assertRaisesRegex(AssertionError, "No degree"):
            pilot.degree_obstruction(nx.octahedral_graph())

    def test_fixed_native_budget_requires_exact_numbers(self):
        good = {
            "max_states": pilot.MAX_STATES,
            "time_limit_seconds_per_algorithm": float(pilot.TIME_LIMIT_SECONDS),
        }
        aggregate.require_fixed_budget(good)
        for name, bad in (
            ("max_states", 99_999),
            ("max_states", 100_001),
            ("max_states", str(pilot.MAX_STATES)),
            ("max_states", True),
            ("time_limit_seconds_per_algorithm", 24.5),
            ("time_limit_seconds_per_algorithm", 26.0),
            ("time_limit_seconds_per_algorithm", "25"),
            ("time_limit_seconds_per_algorithm", True),
        ):
            with self.subTest(field=name, altered_value=bad):
                changed = dict(good)
                changed[name] = bad
                with self.assertRaisesRegex(AssertionError, "100000 states"):
                    aggregate.require_fixed_budget(changed)

    def test_exact_three_status_contract_for_both_native_algorithms(self):
        counters = {
            "states_explored": 0,
            "assignments_tried": 0,
            "arc_revisions": 0,
        }
        for status in ("FOUND", "EXHAUSTED", "LIMIT_REACHED"):
            with self.subTest(status=status):
                aggregate.require_solver_contract(
                    {"status": status, **counters},
                    {"status": status, **counters},
                )
        # An EXHAUSTED general search does not justify fabricating
        # an octahedral API status, whether or not the deduction holds.
        with self.assertRaisesRegex(AssertionError, "invented"):
            aggregate.require_solver_contract(
                {"status": "EXHAUSTED", **counters},
                {"status": "EXCLUDED_BY_EXHAUSTIVE_COAFFINE_SEARCH",
                 **counters},
            )
        with self.assertRaisesRegex(AssertionError, "contradicts"):
            aggregate.require_solver_contract(
                {"status": "EXHAUSTED", **counters},
                {"status": "FOUND", **counters},
            )
        with self.assertRaisesRegex(AssertionError, "counters"):
            aggregate.require_solver_contract(
                {"status": "LIMIT_REACHED", **counters},
                {"status": "LIMIT_REACHED",
                 **{**counters, "states_explored": pilot.MAX_STATES + 1}},
            )

    def test_malformed_coaffine_endomorphism_rejected(self):
        g = nx.cycle_graph(4)
        f = {v: v for v in g}
        with self.assertRaisesRegex(AssertionError, "closed"):
            pilot.independent_coaffine_check(g, f)

    def test_malformed_retraction_rejected(self):
        g = nx.octahedral_graph()
        H = nx.complement(g)
        pairs = tuple(tuple(edge) for edge in H.edges())
        self.assertEqual(len(pairs), 3)
        ret = {v: v for v in g}
        pilot.independent_octahedral_retraction_check(g, pairs, ret)
        ret[0] = 1
        with self.assertRaisesRegex(AssertionError, "does not fix"):
            pilot.independent_octahedral_retraction_check(g, pairs, ret)


if __name__ == "__main__":
    unittest.main()
