"""The v2 launcher loops by default, without touching pinned Python code."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class StageV2AutoloopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        (self.root / "scripts").mkdir()
        (self.root / ".venv" / "bin").mkdir(parents=True)
        shutil.copyfile(ROOT / "scripts" / "stage.sh", self.root / "scripts" / "stage.sh")

        # An isolated worker stub: finish after three five-graph batches.
        stub = self.root / ".venv" / "bin" / "python"
        stub.write_text(
            "#!/usr/bin/env bash\n"
            "set -e\n"
            'case "$1" in\n'
            '  scripts/timeboxed_v2.py)\n'
            '    echo "$2" >> v2_calls.txt\n'
            '    count=$(wc -l < v2_calls.txt)\n'
            '    if (( count >= 3 )); then\n'
            '      mkdir -p runs/order10/bound120-timeboxed-v2\n'
            '      touch runs/order10/bound120-timeboxed-v2/summary.json\n'
            '    fi\n'
            '    ;;\n'
            '  scripts/staged.py|scripts/export_homotopy.py) ;;\n'
            '  *) exit 15 ;;\n'
            'esac\n',
            encoding="utf-8",
        )
        stub.chmod(0o755)

    def invoke(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(self.root / "scripts" / "stage.sh"), "10",
             "bound120-timeboxed-v2", *args],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def calls(self) -> list[str]:
        path = self.root / "v2_calls.txt"
        return path.read_text(encoding="utf-8").splitlines() if path.exists() else []

    def test_default_continues_and_does_not_rerun_finished_stage(self):
        first = self.invoke()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(self.calls(), ["next"] * 3)
        second = self.invoke()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.calls(), ["next"] * 3)

    def test_explicit_next_runs_one_then_default_resumes(self):
        first = self.invoke("next")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(self.calls(), ["next"])
        resumed = self.invoke()
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(self.calls(), ["next"] * 3)

    def test_explicit_numeric_batch_runs_once(self):
        result = self.invoke("17")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls(), ["17"])

    def test_explicit_all_loops(self):
        result = self.invoke("all")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls(), ["next"] * 3)


if __name__ == "__main__":
    unittest.main()
