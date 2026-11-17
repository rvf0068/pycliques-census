"""Independent finite fold and class-isomorphism checks for certificate lift."""
from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import networkx as nx
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import special_octahedron_class_lift_v1 as lift


def path_witness() -> tuple[dict, nx.Graph]:
    original = nx.path_graph(10)
    core, folds = lift.witness_folds(original)
    rep = nx.convert_node_labels_to_integers(core, ordering="sorted")
    original_g6 = lift.numbered_g6(original)
    core_g6 = lift.numbered_g6(core)
    return {
        "index": 12,
        "original_graph6": original_g6,
        "historical_pared_graph6": core_g6,
        "core_id": 12,
        "core_graph6": core_g6,
        "dominated_folds": folds,
        "residual_graph6": core_g6,
        "residual_to_core": lift.isomorphism_map(core, rep),
        "certified_direct_v5": False,
    }, rep


def test_complete_dominated_fold_chain_and_explicit_core_isomorphism():
    row, rep = path_witness()
    assert len(row["dominated_folds"]) == 9
    assert not lift.dominated_pair(rep)
    lift.validate_member(
        row, original_graph6=row["original_graph6"],
        historical_graph6=row["historical_pared_graph6"],
        representative=rep,
    )


def test_reject_non_dominated_deletion_even_with_valid_final_core():
    row, rep = path_witness()
    bad = deepcopy(row)
    bad["dominated_folds"][0] = [4, 7]
    with pytest.raises(ValueError, match="closed-neighborhood"):
        lift.validate_member(
            bad, original_graph6=row["original_graph6"],
            historical_graph6=row["historical_pared_graph6"],
            representative=rep,
        )


def test_reject_wrong_initial_source_and_wrong_final_isomorphism():
    row, rep = path_witness()
    with pytest.raises(ValueError, match="initial census"):
        lift.validate_member(
            row, original_graph6="not-the-source",
            historical_graph6=row["historical_pared_graph6"],
            representative=rep,
        )
    bad = deepcopy(row)
    bad["residual_to_core"][0][1] = 77
    with pytest.raises(ValueError, match="Core bijection"):
        lift.validate_member(
            bad, original_graph6=row["original_graph6"],
            historical_graph6=row["historical_pared_graph6"],
            representative=rep,
        )


def test_nonisomorphic_core_is_never_accepted():
    path = nx.path_graph(4)
    triangle = nx.complete_graph(4)
    with pytest.raises(ValueError, match="does not match"):
        lift.isomorphism_map(path, triangle)


def test_tsv_parser_rejects_header_changes_and_missing_columns(tmp_path):
    columns = ("index", "core_id")
    rows = [{"index": "1", "core_id": "3"}]
    blob = lift.write_tsv(columns, rows)
    path = tmp_path / "members.tsv"
    path.write_bytes(blob)
    assert lift.read_tsv(path, columns) == rows
    with pytest.raises(ValueError, match="columns"):
        lift.read_tsv(path, ("index", "wrong"))
    path.write_text("index\tcore_id\n1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Malformed"):
        lift.read_tsv(path, columns)


def test_immutable_report_requires_exact_source_and_output_bytes(tmp_path):
    destination = tmp_path / "report"
    files = {
        "classes.tsv": b"core_id\n1\n",
        "members.tsv": b"index\n7\n",
        "summary.md": b"Verified summary\n",
        "manifest.json": b"{}\n",
    }
    lift.build(destination, files)
    lift.check_saved(destination, files)
    lift.build(destination, files)  # idempotent
    (destination / "members.tsv").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="modified or stale"):
        lift.check_saved(destination, files)
    with pytest.raises(ValueError, match="modified or stale"):
        lift.build(destination, files)


def test_complete_committed_cohort_independent_replay():
    """Integration: eleven K3 specials, two core isomorphism classes, 133 originals.

    Validate original ten-vertex source graph6, every dominated fold and the
    representative isomorphism, and independently replay each special witness.
    """
    files = lift.prepare()
    summary = json.loads(files["manifest.json"])
    assert summary["classes"] == 2
    assert summary["positive_graph6_records"] == 11
    assert summary["original_members_certified"] == 133
    assert summary["direct_v5_original_indices"] == 25
    assert summary["additional_lifted_original_indices"] == 108

    with __import__("io").StringIO(files["classes.tsv"].decode("utf-8")) as buffer:
        import csv
        classes = list(csv.DictReader(buffer, delimiter="\t"))
    assert {
        (int(row["core_id"]), int(row["original_members"]),
         int(row["direct_v5_members"]))
        for row in classes
    } == {(6938923, 23, 4), (6939350, 110, 21)}
