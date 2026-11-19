"""Independent exact retraction and audit tests for nine new stiff divergences."""
from __future__ import annotations

from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import direct_divergent_ninecore_retracts_v1 as study  # noqa: E402


class IndependentNineRetractions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.found, cls.counts = study.audit()
        cls.payload = study.generated()

    def test_all_six_proved_targets_and_nine_new_stiff_originals(self):
        self.assertEqual(
            tuple(x["original_index"] for x in self.found), study.EXPECTED_IDS
        )
        self.assertEqual(len(study.TARGETS), 6)
        self.assertEqual(self.counts["stiff_ten_sources_tested"], 2403)
        self.assertEqual(self.counts["induced_target_copies"], 31)
        self.assertEqual(self.counts["new_certified_stiff_ten_divergences"], 9)
        self.assertEqual(self.counts["target_positive_counts"]["10768817"], 4)
        self.assertEqual(self.counts["target_positive_counts"]["11363569"], 5)

    def test_every_section_and_edge_equal_morphism_independently(self):
        for row in self.found:
            G = nx.from_graph6_bytes(row["original_graph6"].encode())
            H = nx.from_graph6_bytes(row["target_graph6"].encode())
            projection = row["projection"]
            section = row["section"]
            self.assertEqual(set(projection), set(range(9)))
            self.assertEqual(len(set(section)), 9)
            self.assertEqual([projection[section[q]] for q in range(9)],
                             list(range(9)))
            for i in range(9):
                for j in range(i + 1, 9):
                    self.assertEqual(
                        H.has_edge(i, j),
                        G.has_edge(section[i], section[j]),
                    )
            for u, v in G.edges():
                self.assertTrue(
                    projection[u] == projection[v]
                    or H.has_edge(projection[u], projection[v]),
                    (row["original_index"], u, v),
                )
            self.assertEqual(len(G), 10)
            self.assertEqual(len(H), 9)
            self.assertNotIn(row["deleted_vertex"], section)
            self.assertFalse(any(
                u != v and
                (set(G[u]) | {u}) <= (set(G[v]) | {v})
                for u in G for v in G
            ))

    def test_neumann_lara_retracts_are_not_accidental_edge_only_maps(self):
        # Every positive map genuinely collapses a pair of distinct
        # vertices, with a nine-vertex induced target section.
        for record in self.found:
            projection = record["projection"]
            self.assertEqual(len(set(projection)), 9)
            collapsed = [
                {i for i, value in enumerate(projection) if value == q}
                for q in range(9)
            ]
            self.assertEqual(sorted(len(s) for s in collapsed),
                             [1] * 8 + [2])

    def test_modified_projection_and_section_fail_closed(self):
        for row in self.found:
            G = study.decode(row["original_graph6"])
            H = study.decode(row["target_graph6"])
            deleted = row["deleted_vertex"]
            valid = list(row["projection"])
            # Construct a genuinely forbidden value by inspecting all
            # source edges rather than guessing a perturbation.
            forbidden = next(
                q for q in H if any(
                    q != valid[v] and not H.has_edge(q, valid[v])
                    for v in G[deleted]
                )
            )
            invalid = valid.copy()
            invalid[deleted] = forbidden
            with self.assertRaises(ValueError):
                study.certify_retraction(G, H, invalid, row["section"])
            section = row["section"].copy()
            section[0], section[1] = section[1], section[0]
            with self.assertRaises(ValueError):
                study.certify_retraction(G, H, valid, section)

    def test_two_coaffine_suspension_certificates(self):
        for i in study.COAFFINE:
            study.certify_divergent_suspension(i)
        a, b, images = study.COAFFINE[10768817]
        original = study.COAFFINE[10768817]
        try:
            study.COAFFINE[10768817] = (a, b, b)
            with self.assertRaisesRegex(ValueError, "2-coaffination"):
                study.certify_divergent_suspension(10768817)
        finally:
            study.COAFFINE[10768817] = original

    def test_new_v5_removes_exactly_nine_and_keeps_other_rows_identical(self):
        old = {
            line for line in (ROOT / study.OLD_LIST).read_text().splitlines()
            if line and not line.startswith("#")
        }
        new = {
            line for line in self.payload[study.NEW_LIST].decode().splitlines()
            if line and not line.startswith("#")
        }
        removed = {line.split()[0] for line in old - new}
        self.assertEqual(removed, {str(i) for i in study.EXPECTED_IDS})
        self.assertEqual(len(old), 8233)
        self.assertEqual(len(new), 8224)
        self.assertTrue(new <= old)

    def test_reject_modified_source_even_if_population_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for source in (study.CORE_TABLE, study.OLD_LIST):
                path = root / source
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / source, path)
            # A one-byte graph6 modification must not be accepted.
            source = root / study.CORE_TABLE
            source.write_bytes(source.read_bytes().replace(b"HUZ~v~}", b"HUZ~v~{", 1))
            with self.assertRaisesRegex(ValueError, "index has changed"):
                study.frozen_inputs(root)

    def test_committed_certificates_and_new_current_list_replay_exactly(self):
        study.verify()


if __name__ == "__main__":
    unittest.main()
