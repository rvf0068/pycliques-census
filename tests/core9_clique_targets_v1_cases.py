"""Unit and mathematical regression tests for clique-graph target retractions."""
from __future__ import annotations

from pathlib import Path
import json
import sys

import networkx as nx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import core9_clique_targets_v1 as stage


def test_suspension_clique_graph_homology_and_o4():
    o4 = stage.previous.prototype("octahedra", 4)
    assert nx.is_isomorphic(stage.raw_clique_graph(stage.suspension_cycle(4)), o4)
    for n in (5, 6, 8, 12, 20):
        target = stage.raw_clique_graph(stage.suspension_cycle(n))
        assert len(target) == 2*n
        b = stage.previous.exact_low_betti(target, max_degree=2)
        assert b[0] == b[1] == 0 and b[2] == 1


def test_complement_cycle_clique_graph_betti_and_perrin_formula():
    expect = {8: 10, 9: 12, 10: 17, 11: 22, 12: 29, 13: 39, 14: 51}
    for n, count in expect.items():
        assert stage.perrin(n) == count
        target = stage.raw_clique_graph(stage.complement_cycle(n))
        assert len(target) == count
    hom = {
        8: (2, 1),
        9: (3, 4),
        10: (3, 1),
        11: (5, 1),
    }
    for n, (degree, rank) in hom.items():
        target = stage.raw_clique_graph(stage.complement_cycle(n))
        computed = stage.previous.exact_low_betti(target, max_degree=5)
        assert computed[degree] == rank
        assert sum(computed.values()) == rank
    assert stage.perrin(21) > 40


def test_n12_and_n13_excluded_by_invariant_edge_bounds():
    first, _ = stage.host(6914104)
    second, _ = stage.host(6962151)
    t12 = stage.raw_clique_graph(stage.complement_cycle(12))
    t13 = stage.raw_clique_graph(stage.complement_cycle(13))
    comp_edges = nx.complement(t12).number_of_edges()
    assert comp_edges == 46
    assert stage.complement_edge_lower_bound(first, len(t12)) == 73
    assert stage.complement_edge_lower_bound(second, len(t12)) == 57
    assert 73 > comp_edges and 57 > comp_edges
    assert len(t13) == 39 and len(first) < 39
    assert t13.number_of_edges() == 663 > second.number_of_edges()


def test_target_homology_restricts_to_one_case():
    first, b_first = stage.host(6914104)
    second, b_second = stage.host(6962151)
    a = stage.classify_targets(first, b_first)
    b = stage.classify_targets(second, b_second)
    assert a["parameters_remaining_for_retraction"] == ["K(C_10^c)"]
    assert b["parameters_remaining_for_retraction"] == []
    assert len(a["suspension_targets"]) == 15
    assert len(b["suspension_targets"]) == 17


def test_independent_csp_positive_and_negative():
    target = stage.raw_clique_graph(stage.complement_cycle(10))
    result = stage.exhaustive_retraction(target, list(target))
    assert result["status"] == "FOUND"
    assert result["retraction"] == [[v, v] for v in target]
    # A triangle cannot retract onto its two nonadjacent vertices.
    g = nx.path_graph(3)
    assert stage.exhaustive_retraction(g, [0, 2])["status"] == "EXHAUSTED"
    # Ordinary morphisms may collapse edges to equal images.
    assert stage.exhaustive_retraction(g, [0, 1])["status"] == "FOUND"


def test_corrupted_timeout_schema_cannot_hide_a_result(tmp_path):
    record = {
        "schema": stage.SCHEMA, "core_id": 6914104,
        "status": "TIMEOUT", "phase": "worker",
        "limit_seconds": stage.TIMEOUT_SECONDS,
    }
    path = tmp_path / "record.json"
    path.write_text(json.dumps(record))
    stage.authenticate_record(path, 6914104)
    path.write_text(json.dumps({**record, "positive_retraction_found": True}))
    with pytest.raises(ValueError, match="Forged timeout"):
        stage.authenticate_record(path, 6914104)


def test_expensive_replay_stays_in_bounded_subprocess(monkeypatch, tmp_path):
    import subprocess
    observed = {}

    def fake_run(args, **kwargs):
        observed["args"] = args
        observed["kwargs"] = kwargs
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(stage.subprocess, "run", fake_run)
    stage.bounded("check", 6914104, tmp_path / "record.json")
    assert observed["args"][2] == "check"
    assert observed["kwargs"]["timeout"] == stage.TIMEOUT_SECONDS
    assert observed["kwargs"]["preexec_fn"] is stage.resource_limits
    assert observed["kwargs"]["capture_output"] is True
