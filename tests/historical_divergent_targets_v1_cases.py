"""Mathematical and historical-source regression tests for target discovery."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import networkx as nx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
import historical_divergent_targets_v1 as stage


def test_archive_summary_counts_are_frozen():
    baseline=json.loads((stage.BASE/"summary.json").read_text())
    nine=json.loads((stage.NINE/"initial/summary.json").read_text())
    assert {int(r["order"]):int(r["divergent"]) for r in baseline["orders"]
            if 6<=r["order"]<=8}=={6:1,7:9,8:222}
    assert nine["orders"][0]["divergent"]==9864
    assert nine["orders"][0]["indeterminate"]==63
    assert sum(stage.HIST_COUNTS.values())+sum(stage.ADDITIONAL_NINE.values())==10104
    extras=stage.staged_proven_positive_indices()
    assert len(extras)==8
    assert {v["stage"] for v in extras.values()}=={"c10","bound60","bound70"}


def test_dominated_vertex_certificate_and_stiff_core_are_exact():
    g=nx.complete_graph(4)
    g.add_node(4)
    g.add_edge(4,0)
    stiff,steps=stage.stiff_fold(g)
    assert len(stiff)==1
    assert len(steps)==4
    copy=g.copy()
    for deleted,dominator in steps:
        assert deleted in copy and dominator in copy and deleted!=dominator
        assert set(copy[deleted])|{deleted} <= (set(copy[dominator])|{dominator})
        copy.remove_node(deleted)
    assert nx.is_isomorphic(copy,stiff)


def test_stiff_octahedron_and_its_clique_iterate():
    octahedron=nx.octahedral_graph()
    stiff,folds=stage.stiff_fold(octahedron)
    assert folds==[]
    assert nx.is_isomorphic(stiff,octahedron)
    second=stage.raw_clique_graph_bounded(octahedron)
    assert second is not None
    assert nx.is_isomorphic(second,stage.prior.previous.prototype("octahedra",4))
    assert stage.raw_clique_graph_bounded(nx.complete_graph(4)) is not None


def test_structural_filters_are_only_necessary():
    host=nx.complete_graph(6)
    assert stage.structural_necessary(nx.complete_graph(4),host) is None
    assert stage.structural_necessary(nx.empty_graph(7),host)=="ORDER"
    assert stage.structural_necessary(nx.empty_graph(4),host) in (
        "COMPLEMENT_DEGREES","COMPLEMENT_EDGE_BOUND"
    )
    assert stage.structural_necessary(host,host) is None


def test_expected_mod2_homology_for_divergent_octahedron_targets():
    from pycombtop.bounded_betti import bounded_reduced_betti_mod2
    for dimension in (2,3,4):
        g=stage.prior.previous.prototype("octahedra",dimension+1)
        betti=bounded_reduced_betti_mod2(g,max_faces=stage.MAX_FACES,max_degree=5)
        assert betti is not None
        assert betti=={i:int(i==dimension) for i in range(6)}


def test_historical_target_models_are_nonempty_and_previous_families_tagged():
    models=stage.known_target_models()
    assert models
    g=nx.octahedral_graph()
    assert any(name=="O_d" and nx.is_isomorphic(g,m)
               for name,m in models)


def test_bounded_worker_replay_and_strict_timeout_schema(tmp_path,monkeypatch):
    import subprocess
    observed={}
    def fake_run(cmd,**kwargs):
        observed.update(cmd=cmd,kwargs=kwargs)
        return subprocess.CompletedProcess(cmd,0,"","")
    monkeypatch.setattr(stage.subprocess,"run",fake_run)
    stage.subprocess_bounded("check",tmp_path/"output.json")
    assert observed["cmd"][2]=="check"
    assert observed["kwargs"]["preexec_fn"] is stage.limit
    assert observed["kwargs"]["timeout"]==stage.TIMEOUT_SECONDS
    correct={"schema":stage.SCHEMA,"status":"TIMEOUT",
             "phase":"worker","limit_seconds":stage.TIMEOUT_SECONDS}
    path=tmp_path/"result.json"
    path.write_text(json.dumps(correct))
    stage.authenticate(path)
    path.write_text(json.dumps({**correct,"candidate_targets":[]}))
    with pytest.raises(ValueError,match="Forged timeout"):
        stage.authenticate(path)
