"""Exercise chunk recording/resuming without running a large graph census."""

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import stream_connected  # noqa: E402
import validate  # noqa: E402
from pycliques.small import Verdict  # noqa: E402


class StreamingTests(unittest.TestCase):
    def test_resume_and_atomic_replay(self):
        graphs = [nx.path_graph(9), nx.cycle_graph(9), nx.complete_graph(9)]
        calls = []

        def fake_classifier(graph, *, bound):
            self.assertEqual(bound, 30)
            calls.append(graph.number_of_edges())
            result = Verdict.INDETERMINATE if graph.number_of_edges() == 9 else Verdict.CONVERGENT
            return SimpleNamespace(
                verdict=result, reason="test-only classifier", pared_graph=graph, certificate=None
            )

        with tempfile.TemporaryDirectory() as temp, patch.dict(
            stream_connected.EXPECTED_COUNTS, {9: 3}
        ), patch.object(stream_connected, "connected_graphs", lambda n: iter(graphs)), patch.object(
            stream_connected, "classify_clique_behavior", fake_classifier
        ), patch.object(validate, "connected_graphs", lambda n: iter(graphs)):
            folder = Path(temp) / "order9"
            stream_connected.classify_order(9, folder, 2, 30)
            summary, unresolved = validate.verify_order(folder, 9, 2)
            self.assertEqual(summary["connected_total"], 3)
            self.assertEqual(len(unresolved), 1)
            self.assertEqual(len(calls), 3)
            stream_connected.classify_order(9, folder, 2, 30)
            self.assertEqual(len(calls), 3)  # completed chunks are not reclassified
            (folder / "completed" / "00000002-00000002.done").unlink()
            stream_connected.classify_order(9, folder, 2, 30)
            self.assertEqual(len(calls), 4)
            self.assertEqual(validate.verify_order(folder, 9, 2)[0], summary)

    def test_small_order_validation_needs_no_graph_inventory(self):
        """Order-1 verdicts validate with no graph_index.tsv present."""
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "order1"
            folder.mkdir()
            (folder / "verdicts.tsv").write_text(
                "# index\\tverdict\\treason\\n"
                "0\\tCONVERGENT\\tunit-test\\n",
                encoding="utf-8",
            )
            summary, unresolved = validate.verify_order(folder, 1, 100)
            self.assertEqual(summary["connected_total"], 1)
            self.assertEqual(summary["convergent"], 1)
            self.assertEqual(unresolved, [])
            self.assertFalse((folder / "graph_index.tsv").exists())

    def test_duplicate_index_is_invalid(self):
        import gzip

        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "order9"
            (folder / "chunks").mkdir(parents=True)
            (folder / "completed").mkdir()
            (folder / "unresolved_chunks").mkdir()
            (folder / "completed" / "00000000-00000001.done").write_text("0\t1\n")
            (folder / "unresolved_chunks" / "00000000-00000001.tsv.gz").write_bytes(b"x")
            with gzip.open(folder / "chunks" / "00000000-00000001.tsv.gz", "wt") as z:
                z.write("0\tCONVERGENT\ta\n0\tDIVERGENT\tb\n")
            with self.assertRaisesRegex(ValueError, "duplicate or out-of-order"):
                list(validate.iter_chunks(folder, 9, 2))[:2]  # limited mock: validate first chunk


if __name__ == "__main__":
    unittest.main()
