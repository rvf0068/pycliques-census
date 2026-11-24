"""Adversarial tests for complete ten-v24 P4 isomorphism certificates."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import networkx as nx

from . import verify as proof

from .verify import (
    ARCHIVE, BASE_G6, BASE_HASH, EXPECTED_V24_HEADER, INDICES,
    NEW, SOURCE, V23_BLOB,
    canonical_bijection, git_blob, reconstruct, require,
    source_rows, verify_full_bijection, verify_index_change,
)


class ExactFourthLiftsV24Tests(unittest.TestCase):
    def test_frozen_provenance_and_exact_three_removals(self):
        data = json.loads(ARCHIVE.read_text(encoding="utf-8"))
        self.assertEqual(git_blob(SOURCE.read_bytes()), V23_BLOB)
        self.assertEqual([item["index"] for item in data["witnesses"]],
                         list(INDICES))
        verify_index_change(data)

    def test_snapshot_header_matches_v24_proof(self):
        actual_headers = [
            line for line in NEW.read_text(encoding="ascii").splitlines()
            if line.startswith("#")
        ]
        self.assertEqual(actual_headers, EXPECTED_V24_HEADER)

    def test_reject_stale_snapshot_metadata_even_with_valid_records(self):
        data = json.loads(ARCHIVE.read_text(encoding="utf-8"))
        current = NEW.read_text(encoding="ascii")
        stale = current.replace(
            "# Remaining=1056 previous_v23=1059 newly_proved_divergent=3",
            "# Remaining=1059 previous_v22=1208 newly_proved_divergent=149",
            1,
        )
        self.assertNotEqual(current, stale)
        with tempfile.TemporaryDirectory() as directory:
            fake_root = Path(directory) / "stale_v24.txt"
            fake_root.write_text(stale, encoding="ascii")
            with (
                patch.object(proof, "NEW", fake_root),
                patch.object(proof, "CURRENT", fake_root),
            ):
                with self.assertRaisesRegex(
                    AssertionError, "header does not describe"
                ):
                    verify_index_change(data)

    def test_distinct_fourth_sources_all_have_unique_colors(self):
        data = json.loads(ARCHIVE.read_text(encoding="utf-8"))
        reference_sizes, reference = reconstruct(BASE_G6)
        self.assertEqual(reference_sizes[-1], (182, 14298))
        from .verify import host_sha
        self.assertEqual(host_sha(reference), BASE_HASH)
        for item in data["witnesses"]:
            with self.subTest(mckay=item["index"]):
                _, graph = reconstruct(item["graph6"])
                mapping = canonical_bijection(graph, reference)
                self.assertEqual(len(set(mapping)), 182)
                self.assertEqual(sorted(mapping), list(range(182)))

    def test_reject_bad_complete_permutation(self):
        first = nx.path_graph(6)
        with self.assertRaisesRegex(AssertionError, "Invalid full"):
            verify_full_bijection(first, first, [0, 1, 1, 3, 4, 5])

    def test_reject_wrong_edge_and_nonedge(self):
        g = nx.path_graph(6)
        with self.assertRaisesRegex(AssertionError, "edge or nonedge"):
            verify_full_bijection(g, g, [1, 0, 2, 3, 4, 5])

    def test_reject_source_mutation(self):
        data = json.loads(ARCHIVE.read_text(encoding="utf-8"))
        data["from_git_blob"] = "0" * 40
        with self.assertRaisesRegex(AssertionError, "metadata"):
            verify_index_change(data)


if __name__ == "__main__":
    unittest.main()
