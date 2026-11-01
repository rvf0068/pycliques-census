"""Refuse to resume a run with different data, source, or parameters."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path

import networkx as nx


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--min-order", type=int, required=True)
    ap.add_argument("--max-order", type=int, required=True)
    ap.add_argument("--batch-size", type=int, required=True)
    ap.add_argument("--bound", type=int, required=True)
    args = ap.parse_args()
    source = args.root / ".deps" / "pycliques-project"
    head = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    pin = (args.root / "config" / "pycliques_commit.txt").read_text().strip()
    if head != pin:
        raise SystemExit("Pinned upstream SHA does not match the installed checkout")
    uv_path = shutil.which("uv")
    uv_version = subprocess.check_output([uv_path, "--version"], text=True).strip() if uv_path else "unavailable"
    h = hashlib.sha256()
    source_paths = sorted((args.root / "scripts").glob("*.py"))
    source_paths += sorted((args.root / "scripts").glob("*.sh"))
    source_paths += [args.root / "config" / "pycliques_commit.txt", args.root / ".devcontainer" / "devcontainer.json"]
    for path in source_paths:
        h.update(str(path.relative_to(args.root)).encode("utf-8") + b"\0")
        h.update(path.read_bytes() + b"\0")

    from pyg6data.lists import _dict_connected, _get_data_file_path

    dataset_digests = {}
    for n in range(max(6, args.min_order), args.max_order + 1):
        # Hash the complete original source, not a rerendered graph6 inventory.
        dataset_digests[str(n)] = hashlib.sha256(
            _get_data_file_path(_dict_connected[n]).read_bytes()
        ).hexdigest()

    info = {
        "schema": 2,
        "scope": "connected unlabeled simple graphs only",
        "upstream_url": "https://github.com/rvf0068/pycliques-project.git",
        "upstream_commit": head,
        "upstream_uv_lock_sha256": digest(source / "uv.lock"),
        "runner_source_sha256": h.hexdigest(),
        "bundled_connected_graph6_sha256": dataset_digests,
        "min_order": args.min_order,
        "max_order": args.max_order,
        "batch_size": args.batch_size,
        "bound": args.bound,
        "clockwork_depth": 2,
        "skip_dominated": False,
        "lookup_prior_indeterminate": False,
        "python": sys.version.split()[0],
        "networkx": nx.__version__,
        "pycliques": metadata.version("pycliques"),
        "pyg6data": metadata.version("pyg6data"),
        "uv": uv_version,
    }
    args.run_dir.mkdir(parents=True, exist_ok=True)
    destination = args.run_dir / "manifest.json"
    if destination.exists():
        stored = json.loads(destination.read_text(encoding="utf-8"))
        if stored != info:
            raise SystemExit(
                "Cannot resume: manifest differs from installed packages, script or parameters. "
                "Use a NEW RUN_DIR (and commit previous results first).\n"
                "Old: " + repr(stored) + "\nNew: " + repr(info)
            )
    else:
        tmp = destination.with_suffix(".partial")
        tmp.write_text(json.dumps(info, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, destination)
    print("Pinned census configuration:", json.dumps(info, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
