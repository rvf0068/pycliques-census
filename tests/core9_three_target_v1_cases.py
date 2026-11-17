"""Regression tests for the strictly bounded three-core versioned experiment."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import networkx as nx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import core9_three_target_v1 as stage


def test_independent_special_witness_and_negative():
    octahedron = nx.octahedral_graph()
    witness = stage.independent_special(octahedron)
    assert witness is not None and len(witness[0]) == 3
    assert stage.special_result(octahedron)["status"] == "FOUND"
    assert stage.special_result(nx.complete_graph(7))["status"] == "ABSENT_EXHAUSTIVE"


def test_target_retractions_on_a_known_divergent_graph():
    graph = nx.octahedral_graph()
    rows = stage.targeted_result(graph, b1=0)
    assert [row["family"] for row in rows] == list(stage.FAMILIES)
    assert rows[0]["status"] == "FOUND"
    for row in rows:
        stage.replay_target(graph, row)


def test_tampered_positive_retraction_is_rejected():
    graph = nx.octahedral_graph()
    row = stage.targeted_result(graph, b1=0)[0]
    assert row["status"] == "FOUND"
    forged = dict(row)
    forged["projection"] = [[u, 0] for u in graph]
    with pytest.raises(ValueError, match="does not replay"):
        stage.replay_target(graph, forged)


def test_no_witness_on_negative_search():
    graph = nx.complete_graph(6)
    bad = {
        "family": "octahedra", "status": "LIMIT_REACHED",
        "vertices": [0], "projection": None, "target_kind": None,
    }
    with pytest.raises(ValueError, match="Nonpositive"):
        stage.replay_target(graph, bad)


def test_exact_historic_three_core_membership():
    assert sum(size for _, size in stage.CORE.values()) == 696
    assert stage.MAX_LEVEL == 3
    assert stage.CLIQUE_BOUND == 120
    assert stage.TARGET_LIMITS["max_target_order"] <= 16
    for core_id, (g6, size) in stage.CORE.items():
        row = stage.historic(core_id)
        assert row["input_graph6"] == g6
        assert row["member_count"] == size
        assert row["failure_iterate"] == 4
        assert len(row["iterates"]) == 4
        assert all(x["betti1_mod2"] == 0 for x in row["iterates"])


def test_timeout_cannot_claim_divergence():
    index = 6914104
    g6, size = stage.CORE[index]
    good = {
        "schema": stage.SCHEMA, "core_id": index, "core_graph6": g6,
        "original_members": size, "status": "TIMEOUT",
        "limit_seconds": stage.WORKER_SECONDS, "phase": "probe",
    }
    stage.validate_record(good, index)
    bad = dict(good, positive_certificates=[{"rule": "special_octahedron"}])
    with pytest.raises(ValueError, match="Timed-out"):
        stage.validate_record(bad, index)



def test_negative_row_cannot_hide_discovered_positive():
    graph = nx.octahedral_graph()
    actual = stage.targeted_result(graph, 0)
    stage.validate_targeted_rows(graph, 0, actual)
    changed = [dict(x) for x in actual]
    assert changed[0]["status"] == "FOUND"
    changed[0]["status"] = "EXHAUSTED"
    changed[0]["target_kind"] = None
    changed[0]["vertices"] = None
    changed[0]["projection"] = None
    with pytest.raises(ValueError, match="differ from a fresh bounded replay"):
        stage.validate_targeted_rows(graph, 0, changed)


def test_timeout_requires_exact_resource_limit_and_no_extra_fields():
    core_id = 6914104
    g6, size = stage.CORE[core_id]
    record = {
        "schema": stage.SCHEMA,
        "core_id": core_id, "core_graph6": g6,
        "original_members": size, "status": "TIMEOUT",
        "limit_seconds": stage.WORKER_SECONDS, "phase": "probe",
    }
    stage.validate_record(record, core_id)
    for forged in (
        dict(record, limit_seconds=1234),
        dict(record, raw_levels=[{"status": "FOUND"}]),
        dict(record, phase="unbounded_validation"),
    ):
        with pytest.raises(ValueError, match="invalid limit, phase or extra data"):
            stage.validate_record(forged, core_id)



def test_full_record_replay_invokes_resource_limited_subprocess(monkeypatch, tmp_path):
    import subprocess

    observed = {}

    def fake_run(arguments, **kwargs):
        observed["arguments"] = arguments
        observed["kwargs"] = kwargs
        return subprocess.CompletedProcess(arguments, 0, stdout="replayed", stderr="")

    monkeypatch.setattr(stage.subprocess, "run", fake_run)
    stage.bounded_validate_record(tmp_path / "record.json", 6914104)
    assert observed["arguments"][2] == "check"
    assert observed["kwargs"]["timeout"] == stage.WORKER_SECONDS
    assert observed["kwargs"]["preexec_fn"] is stage.limit_worker
    assert observed["kwargs"]["capture_output"] is True
