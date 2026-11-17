"""Regressions for complete coaffine-join target enumeration and retractions."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import networkx as nx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import core9_coaffine_join_targets_v1 as stage


def test_cycle_independence_homology_and_complete_parameter_sets():
    assert stage.cycle_independence_homology(5) == (1, 1)
    assert stage.cycle_independence_homology(6) == (1, 2)
    assert stage.cycle_independence_homology(7) == (1, 1)
    assert stage.cycle_independence_homology(8) == (2, 1)
    assert stage.cycle_independence_homology(10) == (2, 1)
    assert stage.cycle_independence_homology(11) == (3, 1)
    assert stage.cycle_independence_homology(12) == (3, 2)
    assert stage.cycle_independence_homology(13) == (3, 1)
    assert stage.candidate_parameters(6914104) == stage.EXPECTED[6914104]
    assert stage.candidate_parameters(6962151) == stage.EXPECTED[6962151]


def test_every_family_homology_via_independent_boundary_reduction():
    for core_id in stage.CORES:
        graph, betti = stage.earlier.host(core_id)
        targets = stage.validate_candidate_homology(
            graph, core_id, stage.candidate_parameters(core_id)
        )
        assert len(targets) == len(stage.EXPECTED[core_id])
        for row in targets:
            assert row["reduced_mod2_betti_0_to_5"][str(stage.HOMOLOGY_DIM[core_id])] == 1
            assert sum(row["reduced_mod2_betti_0_to_5"].values()) == 1


def test_induced_coaffine_join_seed_and_named_clique_target_relationship():
    root = nx.from_graph6_bytes(b"HUZ~v~}")
    candidate = stage.join_target(5, 2)
    assert nx.is_isomorphic(root, candidate)
    other = nx.from_graph6_bytes(b"HUzrv~}")
    first_clique = stage.earlier.raw_clique_graph(other)
    assert nx.is_isomorphic(
        first_clique, nx.complement(nx.cycle_graph(14))
    )


def test_induced_counts_and_complete_negative_certificates_on_first_core():
    host, _ = stage.earlier.host(6914104)
    expected = {
        (5,2):(1422,821,820,1),
        (7,2):(9721,629,0,629),
        (8,1):(6381,704,704,0),
        (10,1):(10862,71,71,0),
    }
    for (n,r),(cycles,targets,impossible,exhausted) in expected.items():
        record = stage.probe_family(host,n,r)
        assert record["cycle_count"] == cycles
        assert record["induced_target_count"] == targets
        assert record["local_impossible"] == impossible
        assert record["csp_exhausted"] == exhausted
        assert record["found_count"] == 0
        assert record["status"] == "EXHAUSTED"
        assert len(record["targets"]) == targets


def test_no_induced_target_on_second_core():
    host, _ = stage.earlier.host(6962151)
    expected = {
        (5,3):1323, (7,3):18684, (8,2):12467,
        (10,2):30841, (11,1):1483, (13,1):17,
    }
    for (n,r),cycles in expected.items():
        row = stage.probe_family(host,n,r)
        assert row["cycle_count"] == cycles
        assert row["induced_target_count"] == 0
        assert row["status"] == "EXHAUSTED"


def test_solver_positive_and_forged_positive_are_rejected():
    graph = stage.join_target(7,2)
    positive = stage.check_retraction(graph, list(graph))
    assert positive["status"] == "FOUND"
    assert positive["witness"] == [[i,i] for i in graph]
    # The pinned and standalone solvers both recognize an induced target
    # and its pointwise-fixed retraction.
    extra = graph.copy()
    extra.add_node(len(graph))
    extra.add_edges_from(
        (len(graph),v) for v in graph
        if v == 0 or graph.has_edge(0,v)
    )
    assert stage.check_retraction(extra,list(graph))["status"] == "FOUND"


def test_strict_timeout_schema(tmp_path):
    sample = {"schema":stage.SCHEMA,"core_id":6914104,
              "status":"TIMEOUT","phase":"worker",
              "limit_seconds":stage.TIMEOUT_SECONDS}
    path = tmp_path / "example.json"
    path.write_text(json.dumps(sample))
    stage.authenticate(path,6914104)
    path.write_text(json.dumps({**sample,"positive_witnesses":[]}))
    with pytest.raises(ValueError,match="Forged timeout"):
        stage.authenticate(path,6914104)


def test_exhaustive_replay_is_separately_bounded(monkeypatch,tmp_path):
    import subprocess
    observed={}
    def fake_run(args,**kwargs):
        observed["args"]=args
        observed["kwargs"]=kwargs
        return subprocess.CompletedProcess(args,0,"","")
    monkeypatch.setattr(stage.subprocess,"run",fake_run)
    stage.bounded("check",6914104,tmp_path/"record.json")
    assert observed["args"][2]=="check"
    assert observed["kwargs"]["timeout"]==stage.TIMEOUT_SECONDS
    assert observed["kwargs"]["preexec_fn"] is stage.restrict_resources
