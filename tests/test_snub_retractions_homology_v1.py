"""Regressions for exact snub non-special retraction and homology census."""
from pathlib import Path
import sys
import unittest

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from snub_retractions_homology_v1 import (
    SNUB, compute, constrained_retraction, full_betti, octahedron,
    raw_clique_graph, snub_iterates, validate_retraction,
)


class ExactSnubRetractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = compute()

    def test_homology_and_coverage(self):
        rows = self.result["results"]
        # JSON records ordinary beta_0=1. Reduced beta_0=0.
        self.assertEqual(len(rows),4)
        self.assertEqual([r["order"] for r in rows],[8,12,20,56])
        for row in rows[:3]:
            self.assertEqual(
                {k:v for k,v in row["homology"]["betti_mod2"].items() if v},
                {"0":1,"2":1},
            )
            self.assertTrue(row["homology"]["complete"])
            self.assertTrue(all(
                x["status"]=="EXHAUSTED"
                for x in row["retraction_tests"]["exhaustive"].values()
            ))
        h3=rows[-1]["homology"]
        self.assertFalse(h3["complete"])
        self.assertEqual(h3["betti_mod2"],{"0":1,"1":0,"2":0,"3":0})
        self.assertEqual(h3["faces_by_dimension"]["4"],365272)
        self.assertEqual(h3["boundary_rank"]["3"],11979)
        self.assertEqual(h3["boundary_rank"]["4"],73389)

    def test_k3_complete_pattern_search(self):
        row=self.result["results"][3]["retraction_tests"]
        o=row["octahedra"]
        self.assertEqual(o["O5_induced_targets"],2128)
        self.assertEqual(o["O5_retractions_found"],0)
        self.assertEqual(o["O6_induced_targets"],0)
        cc=row["cycle_complements"]
        self.assertEqual(cc["C14c_induced_targets"],27982)
        self.assertEqual(cc["C15c_induced_targets"],20)
        self.assertEqual(cc["C14c_retractions_found"],0)
        self.assertEqual(cc["C15c_retractions_found"],0)
        self.assertFalse(any(int(n)>=16 for n in cc["chordless_cycles_by_length"]))

    def test_actual_early_target_exhaustion(self):
        targets=self.result["results"][2]["retraction_tests"]["exhaustive"]
        self.assertEqual(targets["O_3"]["status"],"EXHAUSTED")
        self.assertGreater(targets["O_3"]["distinct_targets"],0)
        self.assertEqual(targets["Susp(C_5)"]["status"],"EXHAUSTED")
        self.assertEqual(targets["C_8^c"]["status"],"EXHAUSTED")
        self.assertEqual(targets["C_10^c"]["status"],"EXHAUSTED")

    def test_positive_solver_and_equality_of_vertex_images(self):
        target=octahedron(3)
        status,map_,states=constrained_retraction(target,set(target))
        self.assertEqual(status,"FOUND")
        self.assertTrue(validate_retraction(target,set(target),map_))
        extended=target.copy()
        extended.add_node(6)
        # Distinct nonadjacent vertices 6 and 0 have the same open neighborhood.
        extended.add_edges_from((6,w) for w in target[0])
        status,map_,states=constrained_retraction(extended,set(target))
        self.assertEqual(status,"FOUND")
        self.assertEqual(map_[6],0)
        self.assertTrue(validate_retraction(extended,set(target),map_))
        map_[6]=2
        self.assertFalse(validate_retraction(extended,set(target),map_))

    def test_homology_of_target_cycle_complements(self):
        # Check the exact sphere/wedge dimension restrictions without
        # relying only on the general independence-complex-of-cycle theorem.
        values = {
            5:{"1":1},6:{"1":2},7:{"1":1},8:{"2":1},
            9:{"2":2},10:{"2":1},11:{"3":1},
            12:{"3":2},13:{"3":1},14:{"4":1},
            15:{"4":2},
        }
        for n,expected in values.items():
            with self.subTest(n=n):
                homology=full_betti(nx.complement(nx.cycle_graph(n)))
                reduced={k:v for k,v in homology["betti_mod2"].items()
                         if int(k)>0 and v}
                self.assertEqual(reduced,expected)


if __name__ == "__main__":
    unittest.main()
