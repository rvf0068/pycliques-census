"""Tests for the reusable covering-certificate verifier and stage selection."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "postpasses"))
import staged
from easy_cover_certificates import verify_witness, verify_record, scan

WITNESSES = json.loads((ROOT / "postpasses" / "easy_cover_witnesses.json").read_text())


class CoverReplayTests(unittest.TestCase):
    def test_both_known_certificates(self):
        first = verify_witness(nx.from_graph6_bytes(b"ICxvExyl_"), WITNESSES["ICxvExyl_"])
        self.assertEqual(first["history"], [[28,28],[36,34],[40,24]])
        self.assertEqual(first["good_segments"], [0,2,3,5])
        second = verify_witness(nx.from_graph6_bytes(b"IEhuVquZ_"), WITNESSES["IEhuVquZ_"])
        self.assertEqual(second["history"], [[30,30],[40,40]])
        self.assertEqual((second["source_order"],second["radius"]),(18,4))
        for graph6,w in WITNESSES.items():
            g = nx.from_graph6_bytes(graph6.encode("ascii"))
            row = {"status":"DIVERGENT", "graph6":graph6, "witness":w}
            self.assertTrue(verify_record(row))
            self.assertEqual(scan(g,WITNESSES)["status"],"DIVERGENT")

    def test_corrupted_certificates_are_rejected(self):
        bad = json.loads(json.dumps(WITNESSES["ICxvExyl_"]))
        bad["deleted_edges"] = [[0,1]]
        self.assertFalse(verify_record({"status":"DIVERGENT", "graph6":"ICxvExyl_", "witness":bad}))
        bad = json.loads(json.dumps(WITNESSES["IEhuVquZ_"]))
        bad["embedding"][0] = bad["embedding"][1]
        self.assertFalse(verify_record({"status":"DIVERGENT", "graph6":"IEhuVquZ_", "witness":bad}))
        bad = json.loads(json.dumps(WITNESSES["IEhuVquZ_"]))
        bad["voltage_ones"] = []
        self.assertFalse(verify_record({"status":"DIVERGENT", "graph6":"IEhuVquZ_", "witness":bad}))
        self.assertEqual(scan(nx.cycle_graph(4),{})["status"],"INDETERMINATE")

    def test_cohort_uses_only_previous_bound120_indeterminate(self):
        source = {i:{"index":i,"graph6":"I????????"} for i in range(1,7)}
        origins = {i:f"{i} 10 I???????? - - -" for i in source}
        origins[6] = "6 9 I???????? - - -"
        homotopy = {
            1:{"is_exact":True,"is_limited":False,"spheres":{}},
            2:{"is_exact":True,"is_limited":False,"spheres":{"1":2}},
            3:{"is_exact":True,"is_limited":False,"spheres":{"1":1}},
            4:{"is_exact":True,"is_limited":False,"spheres":{"2":1}},
            5:{"is_exact":False,"is_limited":False,"spheres":{"1":1}},
            6:{"is_exact":True,"is_limited":False,"spheres":{}},
        }
        bound120 = {i:{"verdict":"INDETERMINATE"} for i in source}
        bound120[1] = {"verdict":"CONVERGENT"}
        def rows(order, stage, _source):
            self.assertEqual(order,10)
            if stage=="homotopy": return homotopy
            if stage=="bound120": return bound120
            if stage in ("c10","s1divergence"): return {}
            self.fail("Selection must not inspect its own stage")
        with (
            patch.object(staged,"census",return_value=(Path("."),source,origins)),
            patch.object(staged,"checked_records",side_effect=rows),
        ):
            selection,_ = staged.stage_selection(10,"easycovers")
            self.assertEqual(set(selection),{2,3})

    def test_cli(self):
        with (
            patch.object(sys,"argv",["staged.py","10","easycovers"]),
            patch.object(staged,"run_stage") as run,
        ):
            staged.main()
        run.assert_called_once_with(10,"easycovers")
