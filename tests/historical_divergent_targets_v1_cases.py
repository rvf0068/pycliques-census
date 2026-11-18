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
    # A later induced-O6 exclusion rules out all larger octahedra.
    # The "previously searched" tag must cover *every* O_d whose
    # target order does not exceed the bound, not only O3..O6.
    octahedral_models=[g for label,g in models if label=="O_d"]
    assert {len(g) for g in octahedral_models}==set(range(
        6,stage.MAX_TARGET_ORDER+1,2
    ))


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



def test_historical_six_divergent_nine_cores_and_first_iterates():
    """Independent, small finite screen before mining the 10,104 records."""
    from pycombtop.bounded_betti import bounded_reduced_betti_mod2
    sources = {
        6938923: "HEht}pl",
        6939350: "HEht~bl",
        7454135: "HEnb~jl",
        9678187: "HQyuzpt",
        10768817: "HUZ~v~}",
        11363569: "HUzrv~}",
    }
    for index, source in sources.items():
        graph = nx.from_graph6_bytes(source.encode("ascii"))
        for level in range(3):
            if graph is None:
                assert level == 2
                break
            stiff, steps = stage.stiff_fold(graph)
            assert not steps
            betti = bounded_reduced_betti_mod2(
                stiff, max_faces=stage.MAX_FACES, max_degree=5
            )
            assert betti is not None
            if index in (6938923, 6939350, 7454135, 9678187):
                assert betti == {i:int(i==2) for i in range(6)}
            elif index == 10768817:
                assert betti == {
                    i:int(i==(3 if level==0 else 5)) for i in range(6)
                }
            else:
                assert betti == {
                    i:int(i==(2 if level==0 else 4)) for i in range(6)
                }
            if level < 2:
                graph = stage.raw_clique_graph_bounded(graph)
        if index in (10768817, 11363569):
            assert graph is None  # The next raw clique graph exceeds 40.
    graph=nx.from_graph6_bytes(b"HUzrv~}")
    target=stage.raw_clique_graph_bounded(graph)
    assert target is not None
    assert nx.is_isomorphic(target,nx.complement(nx.cycle_graph(14)))



def test_historical_graph6_source_archives_are_exactly_frozen():
    checksums = stage.validate_source_archives()
    assert set(checksums) == {"6","7","8","9"}
    assert all(len(digest)==64 for digest in checksums.values())


def test_betti_retract_inequality_and_unknown_status_are_not_zero_filled():
    zero = {i:0 for i in range(6)}
    host3 = {i:int(i==3) for i in range(6)}
    host4 = {i:int(i==4) for i in range(6)}
    sphere3 = {i:int(i==3) for i in range(6)}
    sphere4 = {i:int(i==4) for i in range(6)}
    excess3 = dict(sphere3, **{})
    excess3[3] = 2
    assert stage.homology_necessary(sphere3,host3)==(
        "PASSES_BETTI_0_TO_5",[]
    )
    assert stage.homology_necessary(sphere4,host3)==(
        "HOMOLOGY_OBSTRUCTED",[4]
    )
    assert stage.homology_necessary(sphere3,host4)==(
        "HOMOLOGY_OBSTRUCTED",[3]
    )
    assert stage.homology_necessary(excess3,host3)==(
        "HOMOLOGY_OBSTRUCTED",[3]
    )
    assert stage.homology_necessary(zero,host3)==(
        "PASSES_BETTI_0_TO_5",[]
    )
    assert stage.homology_necessary(None,host3)==(
        "UNKNOWN_BETTI_RESOURCE_LIMIT",[]
    )
    partial={3:1}
    assert stage.homology_necessary(partial,host3)==(
        "UNKNOWN_INCOMPLETE_BETTI",[]
    )


def test_positive_stages_match_complete_frozen_cohorts():
    evidence=stage.staged_proven_positive_indices()
    from collections import Counter
    assert Counter(row["stage"] for row in evidence.values()) == Counter(
        {"c10":4,"bound60":1,"bound70":3}
    )
    assert len(evidence)==8
    assert all(row["record_sha256"] and len(nx.from_graph6_bytes(row["graph6"].encode("ascii")))==9
               for row in evidence.values())
