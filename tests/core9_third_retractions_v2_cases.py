"""Exact homology and independently certified non-special retraction tests."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import networkx as nx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import core9_third_retractions_v2 as stage


def test_exact_mod2_homology_of_octahedra_and_complements_of_cycles():
    o3 = stage.prototype("octahedra", 3)
    o4 = stage.prototype("octahedra", 4)
    o5 = stage.prototype("octahedra", 5)
    assert stage.exact_low_betti(o3) == {
        0: 0, 1: 0, 2: 1, 3: 0, 4: 0, 5: 0,
    }
    assert stage.exact_low_betti(o4)[3] == 1
    assert stage.exact_low_betti(o5)[4] == 1
    assert stage.exact_low_betti(stage.prototype("cycle_complements", 11))[3] == 1
    assert stage.exact_low_betti(stage.prototype("cycle_complements", 12))[3] == 2


def test_eligible_parameters_exclude_all_known_homology_obstructions():
    first = stage.target_candidates({0: 0, 1: 0, 2: 0, 3: 1, 4: 0, 5: 0})
    second = stage.target_candidates({0: 0, 1: 0, 2: 0, 3: 0, 4: 1, 5: 0})
    assert [x["parameter"] for x in first["octahedra"]] == [4]
    assert [x["parameter"] for x in first["cycle_complements"]] == [11, 13]
    assert first["suspensions"] == []
    assert [x["parameter"] for x in second["octahedra"]] == [5]
    assert [x["parameter"] for x in second["cycle_complements"]] == [14]
    assert second["suspensions"] == []


def test_necessary_fixed_target_neighborhood_filter():
    graph = nx.octahedral_graph()
    target = frozenset(graph)
    assert stage.fixed_target_feasible(graph, target)
    graph.add_node(6)
    graph.add_edges_from((6, v) for v in target)
    assert not stage.fixed_target_feasible(graph, target)
    graph.remove_edges_from((6, v) for v in target if v != 0)
    assert stage.fixed_target_feasible(graph, target)


def test_target_search_positive_graph_has_independent_retraction():
    graph = nx.octahedral_graph()
    chosen = [{"parameter": 3, "target_betti": {}}]
    record = stage.run_family(graph, "octahedra", chosen)
    assert record["status"] == "FOUND"
    assert record["witness"]["target_vertices"] == list(range(6))
    stage.ensure_positive_retraction(
        graph, "octahedra", 3, tuple(range(6)),
        record["witness"]["projection"],
    )
    forged = [[v, 0] for v in graph]
    with pytest.raises(ValueError, match="failed independent replay|does not fix"):
        stage.ensure_positive_retraction(graph, "octahedra", 3, tuple(range(6)), forged)


def test_homology_excludes_inadmissible_target_search():
    record = stage.run_family(nx.octahedral_graph(), "octahedra", [])
    assert record["status"] == "HOMOLOGY_EXCLUDED"
    assert record["patterns"] == 0
    assert record["witness"] is None


def test_timeout_schema_rejects_an_extra_witness(tmp_path):
    core_id = 6914104
    base = {
        "schema": stage.SCHEMA, "core_id": core_id,
        "core_graph6": stage.prior.CORE[core_id][0],
        "represented_originals": stage.prior.CORE[core_id][1],
        "status": "TIMEOUT", "phase": "compute",
        "limit_seconds": stage.TIMEOUT_SECONDS,
    }
    target = tmp_path / "timeout.json"
    target.write_text(json.dumps(base))
    stage.authenticate_record(target, core_id)
    target.write_text(json.dumps({**base, "positive_certificates": []}))
    with pytest.raises(ValueError, match="Forged timeout"):
        stage.authenticate_record(target, core_id)


def test_replay_is_bounded_by_memory_and_wall_time(tmp_path, monkeypatch):
    import subprocess

    observed = {}

    def fake_run(command, **options):
        observed.update(command=command, options=options)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(stage.subprocess, "run", fake_run)
    stage.bounded_subprocess("check", 6914104, tmp_path / "case.json")
    assert observed["command"][2] == "check"
    assert observed["options"]["timeout"] == stage.TIMEOUT_SECONDS
    assert observed["options"]["preexec_fn"] is stage.limit_resources


def test_two_frozen_cores_exactly_match_prior_research_scope():
    assert stage.CORES == (6914104, 6962151)
    assert sum(stage.prior.CORE[i][1] for i in stage.CORES) == 461
    assert stage.MAX_PATTERNS > stage.prior.TARGET_LIMITS["max_patterns"]
    assert stage.MAX_DEGREE == 5



def test_global_named_target_ceiling_from_exhaustive_complement_graphs():
    first = stage.prior.pared_iterates(6914104)[3]
    second = stage.prior.pared_iterates(6962151)[3]
    a = stage.structural_target_ceiling(first)
    b = stage.structural_target_ceiling(second)
    assert a["induced_o5"] == 0
    assert a["induced_o6"] == b["induced_o6"] == 0
    assert b["induced_o5"] == 6
    assert a["maximum_complement_chordless_cycle"] == 12
    assert b["maximum_complement_chordless_cycle"] == 14
    assert b["cycle_complement_candidates_by_length"]["14"] == 1


def test_unique_c14_complement_candidate_is_not_a_retract():
    graph = stage.prior.pared_iterates(6962151)[3]
    eligible = [{
        "parameter": 14, "target_betti": {"4": 1},
    }]
    result = stage.run_family(graph, "cycle_complements", eligible)
    assert result["status"] == "EXHAUSTED"
    assert result["patterns"] == 1
    assert result["locally_feasible"] == 1
    assert result["retractions_attempted"] == 1
    assert result["witness"] is None
