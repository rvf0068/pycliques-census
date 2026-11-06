"""Regression tests for future-only version-3 proof and diagnostic records."""

from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

import networkx as nx
from pycliques import retractions, small

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

HAS_WITNESS_API = hasattr(retractions, "verify_special_octahedron_witness")


@unittest.skipUnless(HAS_WITNESS_API, "Historical census pin predates witness APIs")
class CertificateRecordV3Tests(unittest.TestCase):
    def setUp(self):
        from certificate_records_v3 import serialize_result, verify_record

        self.serialize_result = serialize_result
        self.verify_record = verify_record

    def test_special_octahedron_roundtrip_and_tampering(self):
        graph = nx.octahedral_graph()
        found = small._test_iterate_certificates(
            small.CliqueSequence(graph), tries=1, retraction_depth=0, targets=()
        )
        self.assertIsNotNone(found)
        verdict, reason, cert = found
        self.assertEqual(verdict, small.Verdict.DIVERGENT)
        behavior = small.CliqueBehavior(verdict, reason, 1, False, graph, cert)
        record = self.serialize_result(graph, behavior)
        self.assertEqual(record["proof_status"], "verified_local")
        self.assertEqual(record["proof"]["rule"], "special_octahedron")
        self.assertTrue(self.verify_record(record))
        altered = copy.deepcopy(record)
        altered["proof"]["antipode_indices"][0] = altered["proof"]["clique_indices"][0]
        self.assertFalse(self.verify_record(altered, verify_iterate=False))
        altered = copy.deepcopy(record)
        altered["proof"]["origin_graph6"] = "Dhc"
        self.assertFalse(self.verify_record(altered, verify_iterate=True))

    def test_fixed_target_retraction_roundtrip(self):
        graph = nx.octahedral_graph()
        target = graph.copy()
        witness = retractions.retracts(graph, target)
        self.assertIsInstance(witness, tuple)
        cert = small.Certificate(
            rule="retracts",
            source=graph,
            target=target,
            target_status="proven_divergent",
            iterate_index=0,
            map=witness,
        )
        behavior = small.CliqueBehavior(
            small.Verdict.DIVERGENT, "known divergent retract", 1, False, graph, cert
        )
        record = self.serialize_result(graph, behavior)
        self.assertEqual(record["proof"]["rule"], "retracts")
        self.assertTrue(self.verify_record(record, verify_iterate=True))
        altered = copy.deepcopy(record)
        altered["proof"]["inclusion"][-1] = altered["proof"]["inclusion"][0]
        self.assertFalse(self.verify_record(altered, verify_iterate=False))

    def test_helly_proof_reconstructs_iterate(self):
        graph = nx.from_graph6_bytes(b"ICvbvy}|g")
        result = small.classify_clique_behavior(graph, bound=120)
        self.assertEqual(result.verdict, small.Verdict.CONVERGENT)
        record = self.serialize_result(graph, result)
        self.assertEqual(record["proof_status"], "verified_local")
        self.assertEqual(record["proof"]["rule"], "eventually_clique_helly")
        self.assertTrue(self.verify_record(record, verify_iterate=True))

    def test_unproved_or_unsupported_certificates_never_claim_proof(self):
        graph = nx.cycle_graph(5)
        conditional = small.Certificate(
            rule="reference",
            target_status="conjectured_divergent",
        )
        result = small.CliqueBehavior(
            small.Verdict.INDETERMINATE,
            "conjectural",
            1,
            False,
            graph,
            conditional,
        )
        record = self.serialize_result(graph, result)
        self.assertEqual(record["proof_status"], "not_serialized")
        self.assertIsNone(record["proof"])
        self.assertFalse(self.verify_record(record))

    def test_v3_diagnostics_labels_stable_methods_and_iterates(self):
        from timeboxed_trace_v2 import ProgressTrace
        from timeboxed_trace_v3 import summarize_events_v3, trace_classifier_v3

        with tempfile.TemporaryDirectory() as folder:
            journal = Path(folder) / "events.jsonl"
            with ProgressTrace(journal) as trace:
                with trace_classifier_v3(trace):
                    outcome = small.classify_clique_behavior(
                        nx.cycle_graph(5), tries=1, clockwork_depth=0
                    )
            self.assertEqual(outcome.verdict, small.Verdict.CONVERGENT)
            data = summarize_events_v3(str(journal))
            self.assertEqual(data["diagnostic_schema"], 3)
            helly = [
                row for row in data["methods_tried"]
                if row["method"] == "clique_helly"
            ]
            self.assertEqual(len(helly), 1)
            self.assertEqual(helly[0]["outcome"], "positive")
            self.assertEqual(helly[0]["iterate"], 0)
            self.assertEqual(data["iterates"][0]["index"], 0)


if __name__ == "__main__":
    unittest.main()
