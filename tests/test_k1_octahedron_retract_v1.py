"""Independent regression checks for K(G)->O3 divergence and v6 census."""
from __future__ import annotations
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
import networkx as nx

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import k1_octahedron_retract_v1 as stage


class K1OctahedronRetractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload=stage.generate()
        cls.cert=json.loads(cls.payload[stage.DIR+"/certificates.json"])

    def test_independent_explicit_retraction(self):
        h,facets=stage.first_clique_graph(stage.EXPECTED_G6)
        self.assertEqual((len(h),h.number_of_edges()),(17,87))
        self.assertEqual(len(facets),17)
        stage.verify_map(h,stage.REFERENCE_SECTION,stage.REFERENCE_PROJECTION)
        self.assertTrue(nx.is_isomorphic(
            h.subgraph(stage.REFERENCE_SECTION),stage.O3()
        ))
        self.assertEqual(
            [sorted(i for i in range(10) if facet&(1<<i))
             for k,facet in enumerate(facets) if k in stage.REFERENCE_SECTION],
            [sorted(i for i in range(10) if facets[k]&(1<<i))
             for k in range(17) if k in stage.REFERENCE_SECTION],
        )

    def test_reject_bad_section_or_projection(self):
        h,_=stage.first_clique_graph(stage.EXPECTED_G6)
        broken=stage.REFERENCE_PROJECTION.copy()
        broken[stage.REFERENCE_SECTION[0]]=1
        with self.assertRaisesRegex(ValueError,"retraction"):
            stage.verify_map(h,stage.REFERENCE_SECTION,broken)
        broken=stage.REFERENCE_PROJECTION.copy()
        broken[2]=3
        with self.assertRaises(ValueError):
            stage.verify_map(h,stage.REFERENCE_SECTION,broken)
        with self.assertRaisesRegex(ValueError,"induce"):
            stage.verify_map(h,[0,1,2,3,4,5],stage.REFERENCE_PROJECTION)

    def test_exhaustive_search_counts_and_only_one_new_positive(self):
        self.assertEqual(self.cert["screen_statistics"]["active_classes"],2424)
        self.assertEqual(self.cert["screen_statistics"]["candidate_hosts"],40)
        self.assertEqual(self.cert["screen_statistics"]["all_induced_sections"],3972)
        self.assertEqual(
            [c["index"] for c in self.cert["positive_certificates"]],
            [11634099],
        )
        source=self.cert["positive_certificates"][0]
        self.assertEqual(source["graph6"],stage.EXPECTED_G6)
        h,_=stage.first_clique_graph(source["graph6"])
        stage.verify_map(h,source["section"],source["projection"])

    def test_old_and_new_populations_and_exact_delta(self):
        old=[line for line in (ROOT/stage.OLD).read_text().splitlines()
             if line and not line.startswith("#")]
        updated=[line for line in
                 self.payload[stage.NEW].decode().splitlines()
                 if line and not line.startswith("#")]
        self.assertEqual((len(old),len(updated)),(8224,8223))
        self.assertEqual(set(old)-set(updated),{
            next(x for x in old if x.startswith("11634099 "))
        })
        self.assertEqual(set(updated)-set(old),set())

    def test_bad_historical_dependency_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            untrusted=Path(temp)/"modified.py"
            untrusted.write_text("print('forged')\n")
            with patch.object(stage,"PRIOR_SCRIPT",str(untrusted)):
                with self.assertRaises((ValueError,FileNotFoundError)):
                    stage.old_data()

    def test_committed_artifacts_match_independent_reconstruction(self):
        stage.verify()


if __name__=="__main__":
    unittest.main()
