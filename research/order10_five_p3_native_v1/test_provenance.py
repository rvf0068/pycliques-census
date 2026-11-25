"""Adversarial source pin regression for public Jupyter and CLI paths."""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from research.order10_five_p3_native_v1 import search


class SolverProvenanceTests(unittest.TestCase):
    def test_direct_jupyter_entry_rejects_false_revision_before_any_search(self):
        with patch.dict(os.environ, {"PYCLIQUES_PINNED_SHA": "wrong"}):
            with self.assertRaisesRegex(AssertionError, "monorepo checkout SHA"):
                search.investigate(search.REMAINING[0], "label")

    def test_runtime_guard_rejects_missing_pin(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(AssertionError, "monorepo checkout SHA"):
                search.validate_runtime()

    def test_pin_and_all_dependency_versions_are_explicit(self):
        self.assertEqual(len(search.PYCLIQUES_SOURCE_GIT_BLOBS), 7)
        self.assertEqual(search.RUNTIME_VERSIONS["networkx"], "3.6")
        self.assertEqual(search.RUNTIME_VERSIONS["grandiso"], "2.2.0")
        self.assertEqual(search.RUNTIME_VERSIONS["rich"], "14.3.3")
        self.assertEqual((search.MAX_STATES, search.SECONDS), (2_000_000, 90))


if __name__ == "__main__":
    unittest.main()
