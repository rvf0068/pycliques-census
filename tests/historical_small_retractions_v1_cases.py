"""Mathematical regression tests for exhaustive historical target retractions."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import networkx as nx
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import historical_small_retractions_v1 as stage


def target_from_historical_graph(graph6:str)->nx.Graph:
    g=nx.from_graph6_bytes(graph6.encode("ascii"))
    for _ in range(2):
        g=stage.pilot.full.raw_clique_graph_bounded(g)
        assert g is not None
    raw=g.copy()
    stiff,steps=stage.pilot.full.stiff_fold(g)
    # K^2(H) need not be stiff: validate each explicit domination fold
    # rather than incorrectly requiring zero folds. For this example
    # the two legitimate deletions are [11,13] and [17,15].
    for deleted,dominator in steps:
        assert deleted in raw and dominator in raw and deleted!=dominator
        assert (set(raw[deleted]) | {deleted}) <= (
            set(raw[dominator]) | {dominator}
        )
        raw.remove_node(deleted)
    assert nx.is_isomorphic(raw,stiff)
    if graph6=="GUZvvW":
        assert steps==[[11,13],[17,15]]
    return stiff


def test_one_historic_divergent_k2_target_has_69_locally_impossible_embeddings():
    target=target_from_historical_graph("GUZvvW")
    assert (len(target),target.number_of_edges())==(16,94)
    host,_=stage.prior.host(6914104)
    found=stage.probe(host,target,"ISMAGS")
    assert found["status"]=="EXHAUSTED"
    assert found["induced_vertex_sets"]==69
    assert found["locally_impossible"]==69
    assert found["positive_retractions"]==0
    for rec in found["negative_certificates"]:
        x=rec["empty_domain_vertex"]
        assert x not in rec["vertices"]
        assert stage.domain_obstruction(host,set(rec["vertices"])) is not None


def test_complement_vf2_eliminates_larger_historical_candidate():
    target=target_from_historical_graph("GEjf~w")
    assert (len(target),target.number_of_edges())==(26,256)
    for cid in (6914104,6962151):
        host,_=stage.prior.host(cid)
        outcome=stage.probe(host,target,"VF2")
        assert outcome["status"]=="EXHAUSTED"
        assert outcome["induced_vertex_sets"]==0


def test_independent_solvers_recognize_positive_identity():
    target=target_from_historical_graph("GUZvvW")
    answer=stage.two_solvers(target,list(target))
    assert answer["status"]=="FOUND"
    assert answer["projection"]==[[v,v] for v in target]


def test_timeout_and_replay_resource_budget(monkeypatch,tmp_path):
    import subprocess
    observed={}
    def fake_run(cmd,**kwargs):
        observed.update(command=cmd,kwargs=kwargs)
        return subprocess.CompletedProcess(cmd,0,"","")
    monkeypatch.setattr(stage.subprocess,"run",fake_run)
    stage.bounded("check",tmp_path/"records.json")
    assert observed["command"][2]=="check"
    assert observed["kwargs"]["timeout"]==stage.TIMEOUT_SECONDS
    assert observed["kwargs"]["preexec_fn"] is stage.limit


def test_expected_novel_candidate_families():
    assert len(stage.EXPECTED_ENGINES)==6
    assert stage.EXPECTED_ENGINES[(16,94)]=="ISMAGS"
    assert stage.EXPECTED_ENGINES[(26,256)]=="VF2"
