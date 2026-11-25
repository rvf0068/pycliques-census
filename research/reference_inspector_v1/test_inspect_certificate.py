"""Compare the public inspector with independent historical v3 replay."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from inspect_certificate import archived, inspect_graph, small


class InspectorTest(unittest.TestCase):
    def test_helly_certificate_and_proved_only_selection(self):
        graph6 = "ICvbvy}|g"
        original = archived.classify_example(graph6)
        if hasattr(small, "select_reference_graphs"):
            references = small.select_reference_graphs()
            with (
                tempfile.TemporaryDirectory() as directory,
                patch.object(
                    small,
                    "classify_clique_behavior",
                    wraps=small.classify_clique_behavior,
                ) as classify,
            ):
                result = inspect_graph(
                    graph6,
                    proved_only=True,
                    diagnostics=Path(directory) / "trace.jsonl",
                )
            self.assertEqual(
                classify.call_args.kwargs["references"],
                small.select_reference_graphs(proved_only=True),
            )
            self.assertEqual(small.select_reference_graphs(), references)
            self.assertTrue(result["diagnostics"]["methods_tried"])
        else:
            with self.assertRaisesRegex(ValueError, "per-call reference"):
                inspect_graph(graph6, proved_only=True)
            result = inspect_graph(graph6)
        self.assertEqual(result["proof"], original["proof"])
        self.assertEqual(result["proof"]["iterate_index"], 3)
        self.assertTrue(archived.verify_record(result, verify_iterate=True))
