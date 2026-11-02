"""The root working order-9 unresolved list is a derived, atomic view."""

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "postpasses"))
import refresh_indeterminate_order9 as mod  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RefreshIndeterminateTests(unittest.TestCase):
    def fixture(self, base: Path) -> tuple[Path, Path, Path, Path]:
        run = base / "runs" / "order9"
        order = run / "order9"
        order.mkdir(parents=True)
        manifest = {"min_order": 9, "max_order": 9, "upstream_commit": "abc"}
        (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        # Three ordinary cases; one conditional on conjectured divergence.
        rows = [
            (100, "HA", "reference conjectured_divergent snub_disphenoid",
             "reference conjectured divergent"),
            (101, "HB", "- - -", "clique count exceeded bound"),
            (102, "HC", "- - -", "clique count exceeded bound"),
            (103, "HD", "- - -", "clique count exceeded bound"),
        ]
        summary = {
            "manifest": manifest,
            "orders": [{"order": 9, "connected_total": 261080, "indeterminate": 4}],
            "unresolved": [
                {"order": 9, "index": i, "graph6": g6, "reason": reason}
                for i, g6, _, reason in rows
            ],
        }
        (run / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
        original = order / "indeterminate_order_9.txt"
        original.write_text(
            "".join(f"{i} 9 {g6} {cert}\n" for i, g6, cert, _ in rows),
            encoding="utf-8",
        )
        postpass = run / "postpasses" / "clique_retract_comp_c10"
        postpass.mkdir(parents=True)
        postmeta = {
            "order": 9,
            "target": "complement_of_cycle(10)",
            "graph_under_test": "K(G)",
            "source_run_manifest_sha256": digest(run / "manifest.json"),
            "source_run_summary_sha256": digest(run / "summary.json"),
            "unresolved_cohort_sha256": digest(original),
            "eligible_indices": [101, 102, 103],
        }
        (postpass / "manifest.json").write_text(
            json.dumps(postmeta), encoding="utf-8"
        )
        (postpass / "records").mkdir()
        dest = base / "indeterminate_order_9.txt"
        return run, postpass, dest, original

    @staticmethod
    def record(directory: Path, index: int, status: str, graph6: str) -> None:
        data = {
            "index": index,
            "graph6": graph6,
            "status": status,
            "witness": {"target_vertex_to_K_vertex": []}
            if status == "RETRACTION_FOUND" else None,
        }
        (directory / "records" / f"{index:06d}.json").write_text(
            json.dumps(data), encoding="utf-8"
        )

    def test_refresh_removes_only_proven_retractions(self):
        with tempfile.TemporaryDirectory() as temp:
            run, postpass, dest, original = self.fixture(Path(temp))
            original_text = original.read_text(encoding="utf-8")
            first = mod.refresh(run, postpass, dest)
            self.assertEqual(first["remaining"], 4)
            self.assertEqual(first["checked"], 0)

            self.record(postpass, 101, "RETRACTION_FOUND", "HB")
            self.record(postpass, 102, "NO_RETRACTION", "HC")
            second = mod.refresh(run, postpass, dest)
            self.assertEqual(second, {
                "original": 4, "conditional": 1, "eligible": 3,
                "checked": 2, "resolved": 1, "remaining": 3,
            })
            result = dest.read_text(encoding="utf-8")
            data = [line for line in result.splitlines() if not line.startswith("#")]
            self.assertEqual([int(line.split()[0]) for line in data], [100, 102, 103])
            self.assertIn("# Checked=2 resolved_by_retraction=1 remaining=3", result)
            self.assertEqual(original.read_text(encoding="utf-8"), original_text)

            # More post-pass records must not change the original result file.
            self.record(postpass, 103, "INCONCLUSIVE", "HD")
            last = mod.refresh(run, postpass, dest)
            self.assertEqual(last["checked"], 3)
            self.assertEqual(last["remaining"], 3)
            self.assertEqual(mod.refresh(run, postpass, dest), last)

    def test_malformed_postpass_record_does_not_replace_root_file(self):
        with tempfile.TemporaryDirectory() as temp:
            run, postpass, dest, original = self.fixture(Path(temp))
            dest.write_text("unchanged\n", encoding="utf-8")
            self.record(postpass, 101, "RETRACTION_FOUND", "WRONG")
            with self.assertRaisesRegex(ValueError, "Invalid post-pass record"):
                mod.refresh(run, postpass, dest)
            self.assertEqual(dest.read_text(encoding="utf-8"), "unchanged\n")

    def test_wrong_source_hash_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            run, postpass, dest, _ = self.fixture(Path(temp))
            (run / "manifest.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "manifest"):
                mod.refresh(run, postpass, dest)


if __name__ == "__main__":
    unittest.main()
