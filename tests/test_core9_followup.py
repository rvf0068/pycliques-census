"""Regression tests for certified targeted order-nine core follow-ups."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import core9_followup as followup
import core9_followup_worker as worker


class Core9TargetedFollowupTests(unittest.TestCase):
    def test_exact_8_cover_5_bound_selection(self):
        previous, saved, tasks = followup.cohort()
        self.assertEqual(len(previous), 29)
        self.assertEqual(len(saved), 29)
        covers = [i for kind, i in tasks if kind == "cover"]
        larger = [i for kind, i in tasks if kind == "bound"]
        self.assertEqual(len(covers), 8)
        self.assertEqual(len(larger), 5)
        self.assertFalse(set(covers) & set(larger))
        self.assertEqual(larger, sorted([10760192,6914104,6938971,6946361,6962151]))
        self.assertEqual(covers, sorted([
            2317843,3148541,3505942,4952669,4953338,5601875,6938156,7315343
        ]))

    def test_three_second_iterates_have_real_explicit_isomorphisms(self):
        _, prior, _ = followup.cohort()
        iso = followup.compute_iso(prior)
        self.assertEqual(iso["left_core"], 4929602)
        self.assertEqual([r["right_core"] for r in iso["comparisons"]], [
            4972358,5645085,
        ])
        self.assertTrue(all(r["isomorphic"] for r in iso["comparisons"]))
        followup.verify_iso(iso, prior)
        corrupted = json.loads(json.dumps(iso))
        first = corrupted["comparisons"][0]["mapping"]
        first[0], first[1] = first[1], first[0]
        with self.assertRaisesRegex(ValueError, "mapping"):
            followup.verify_iso(corrupted, prior)
        corrupted = json.loads(json.dumps(iso))
        corrupted["comparisons"][1]["isomorphic"] = False
        corrupted["comparisons"][1]["mapping"] = None
        with self.assertRaisesRegex(ValueError, "nonisomorphism"):
            followup.verify_iso(corrupted, prior)

    def test_record_contract_never_promotes_unsupported_positive(self):
        previous, _, tasks = followup.cohort()
        cover_id = next(i for kind,i in tasks if kind=="cover")
        bound_id = next(i for kind,i in tasks if kind=="bound")
        prefix = {"scope": "nine_vertex_core_only"}
        no_cover = {
            **prefix, "kind":"cover", "core_id":cover_id,
            "input_graph6":previous[cover_id]["graph6"],
            "status": "EXHAUSTED", "proof_status":"none",
            "witness":None,
            "search":{"limits":worker.COVER_LIMITS,"search_status":"EXHAUSTED"},
        }
        followup.validate_record(no_cover,"cover",cover_id,previous)
        with self.assertRaisesRegex(ValueError, "witness replay"):
            followup.validate_record({
                **no_cover,"status":"DIVERGENT","proof_status":"verified",
                "witness":{},"search":{"limits":worker.COVER_LIMITS,"search_status":"FOUND"},
            },"cover",cover_id,previous)

        no_bound = {
            **prefix, "kind":"bound","core_id":bound_id,
            "input_graph6":previous[bound_id]["graph6"],
            "status":"BOUND_EXCEEDED","clique_bound":worker.BOUND,
            "verdict":"INDETERMINATE","raw_verdict":"INDETERMINATE",
            "proof_status":"not_serialized","proof":None,
        }
        followup.validate_record(no_bound,"bound",bound_id,previous)
        with self.assertRaisesRegex(ValueError,"positive proof"):
            followup.validate_record({
                **no_bound,"status":"DIVERGENT","verdict":"DIVERGENT",
                "raw_verdict":"DIVERGENT","proof_status":"verified_chain",
                "proof":{},
            },"bound",bound_id,previous)
        with self.assertRaisesRegex(ValueError,"Bound failure"):
            followup.validate_record({
                **no_bound, "raw_verdict":"DIVERGENT",
            },"bound",bound_id,previous)

    def test_verify_missing_stage_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/"new_followup"
            with patch.object(followup,"OUTPUT",target):
                with self.assertRaisesRegex(ValueError, "No targeted follow-up"):
                    followup.ensure_manifest({"stage":"test"},create=False)
            self.assertFalse(target.exists())

    def test_only_bounded_result_on_cover_search_miss(self):
        from unittest.mock import Mock
        from pycombtop.covering_divergence_search import CoveringSearchStatus
        mock = Mock()
        mock.status = CoveringSearchStatus.EXHAUSTED
        mock.certificate = None
        mock.cover_classes_total = 1
        mock.cover_classes_checked = 1
        mock.cover_candidates_checked = 1
        mock.morphism_states = 2
        mock.morphism_assignments = 2
        mock.morphism_searches_exhausted = 1
        mock.cover_classes_complete = True
        mock.morphisms_complete = True
        mock.configured_source_parameters = ((2,0),)
        mock.limits = tuple(sorted(worker.COVER_LIMITS.items()))
        mock.reasons = ()
        with patch.object(worker,"search_covering_divergence",return_value=mock):
            result = worker.analyze_cover(nx.cycle_graph(9))
        self.assertEqual(result["status"],"EXHAUSTED")
        self.assertEqual(result["proof_status"],"none")
        self.assertIsNone(result["witness"])
        self.assertEqual(result["search"]["cover_classes_checked"],1)


if __name__ == "__main__":
    unittest.main()
