"""Regression tests for immutable, read-only order-10 pared-core indexing."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import core_isomorphism_index as core


def g6(graph: nx.Graph) -> str:
    return nx.to_graph6_bytes(
        nx.convert_node_labels_to_integers(graph, ordering="sorted"), header=False
    ).decode("ascii").strip()


class CoreIndexTests(unittest.TestCase):
    def test_true_isomorphism_not_graph6_string_equality(self):
        # Actual historical order-9 core encodings of the same graph.
        first = "HEiv^p{"
        permuted = "HEivrzk"
        self.assertNotEqual(first, permuted)
        self.assertTrue(nx.is_isomorphic(core.decode(first), core.decode(permuted)))
        rows = {
            15: core.Row(15, 9, permuted, "-"),
            3: core.Row(3, 9, first, "-"),
            8: core.Row(8, 9, g6(nx.path_graph(9)), "-"),
        }
        classes = core.group_rows(rows)
        self.assertEqual(len(classes), 2)
        self.assertEqual([g.rep.index for g in classes], [3, 8])
        self.assertEqual([r.index for r in classes[0].members], [3, 15])
        self.assertEqual([r.index for r in classes[1].members], [8])

    def test_fingerprint_is_only_necessary_invariant(self):
        cycle = nx.cycle_graph(6)
        relabeled = nx.relabel_nodes(cycle, {0: 4, 1: 2, 2: 1, 3: 0, 4: 5, 5: 3})
        self.assertEqual(core.fingerprint(cycle), core.fingerprint(relabeled))
        self.assertFalse(nx.is_isomorphic(cycle, nx.disjoint_union(nx.cycle_graph(3), nx.cycle_graph(3))))

    def test_v3_membership_delta_checks_source_and_statuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            v3 = root / "v3"
            (v3 / "records").mkdir(parents=True)
            cycle6 = g6(nx.cycle_graph(5))
            path6 = g6(nx.path_graph(5))
            old = {
                1: core.Row(1, 5, cycle6, "-"),
                2: core.Row(2, 5, path6, "-"),
            }
            active = {2: old[2]}
            meta = {"order": 10, "stage": "bound120-timeboxed-v3", "indices": [1, 2]}
            (v3 / "manifest.json").write_text(json.dumps(meta))
            (v3 / "summary.json").write_text(json.dumps({
                "manifest": meta, "processed": 2,
                "counts": {"CONVERGENT": 1, "BOUND_EXCEEDED": 1},
            }))
            first = {
                "index": 1, "graph6": cycle6, "status": "CONVERGENT",
                "proof_status": "verified_chain", "proof": {"origin_graph6": cycle6},
            }
            second = {"index": 2, "graph6": path6, "status": "BOUND_EXCEEDED"}
            a = v3 / "records" / "00000001.json"
            a.write_text(json.dumps(first))
            (v3 / "records" / "00000002.json").write_text(json.dumps(second))
            counts, checksum = core.check_v3(old, active, v3)
            self.assertEqual(counts["CONVERGENT"], 1)
            self.assertEqual(len(checksum), 64)
            self.assertRaisesRegex(
                ValueError, "Active list",
                core.check_v3, old, {1: old[1], 2: old[2]}, v3,
            )
            first["proof"]["origin_graph6"] = path6
            a.write_text(json.dumps(first))
            self.assertRaisesRegex(ValueError, "Unlinked positive", core.check_v3, old, active, v3)

    def test_build_is_atomic_and_refuses_changed_outputs(self):
        outputs = {
            "manifest.json": b"{}\n",
            "assignments.tsv": b"index\tcore_id\n",
            "classes.tsv": b"core_id\tmembers\n",
            "summary.md": b"# Test\n",
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "index"
            core.build(folder, outputs)
            core.check_saved(folder, outputs)
            core.build(folder, outputs)
            self.assertEqual((folder / "classes.tsv").read_bytes(), outputs["classes.tsv"])
            (folder / "classes.tsv").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "stale or modified"):
                core.check_saved(folder, outputs)
            with self.assertRaisesRegex(ValueError, "stale or modified"):
                core.build(folder, outputs)
            self.assertEqual((folder / "classes.tsv").read_bytes(), b"tampered")

    def test_real_committed_post_v3_partition(self):
        # Real-data regression guards against splitting one core class because
        # its graph6 vertex ordering differs, and against losing graph indices.
        old = core.load_rows(core.HISTORICAL)
        current = core.load_rows(core.ACTIVE)
        self.assertEqual(len(old), 8648)
        self.assertEqual(len(current), 8533)
        counts, _ = core.check_v3(old, current, core.V3)
        self.assertEqual(counts["CONVERGENT"], 115)
        self.assertEqual(counts["BOUND_EXCEEDED"], 38)
        classes = core.group_rows(current)
        self.assertEqual(len(classes), 2439)
        distribution = {
            n: (
                len([g for g in classes if g.rep.order == n]),
                sum(len(g.members) for g in classes if g.rep.order == n)
            )
            for n in (8, 9, 10)
        }
        self.assertEqual(distribution, {
            8: (1, 2092),
            9: (35, 4038),
            10: (2403, 2403),
        })
        self.assertEqual(
            len({r.index for g in classes for r in g.members}),
            8533
        )
        self.assertEqual(classes[0].rep.index, 2317572)
        self.assertEqual(len(classes[0].members), 2092)


if __name__ == "__main__":
    unittest.main()
