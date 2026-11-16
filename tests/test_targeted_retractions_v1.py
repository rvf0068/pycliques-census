"""Isolated cache and positive-witness tests for the targeted postpass."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import networkx as nx
import pytest
from pycliques.named import octahedron, snub_disphenoid
from pycliques.targeted_retractions import TargetSearchStatus

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import targeted_retractions_v1 as stage


def test_cached_exact_profile_is_reused(tmp_path,monkeypatch):
    graph=octahedron(3)
    first,key=stage.cache_homology(graph,tmp_path)
    assert first is not None and first[2]==1
    cache=tmp_path/"homology_cache"/(key+".json")
    assert cache.exists()
    data=json.loads(cache.read_text(encoding="utf-8"))
    assert data["graph6"]==stage.graph6(graph)
    assert data["betti_numbers"]["2"]==1
    def forbidden(*_args,**_kwargs):
        raise AssertionError("Betti computation repeated instead of reusing cache")
    monkeypatch.setattr(stage,"bounded_reduced_betti_mod2",forbidden)
    second,key2=stage.cache_homology(graph,tmp_path)
    assert first==second and key==key2


def test_unknown_when_homology_budget_exceeded(tmp_path,monkeypatch):
    monkeypatch.setattr(stage,"MAX_BETTI_FACES",2)
    profile,key=stage.cache_homology(octahedron(3),tmp_path)
    assert profile is None
    data=json.loads((tmp_path/"homology_cache"/(key+".json")).read_text())
    assert data["mode"]=="face_limit"
    assert data["betti_numbers"] is None


def test_positive_target_retraction_record_and_independent_replay(tmp_path):
    graph=octahedron(3)
    family=stage.search_targeted_retractions(graph)
    assert family["octahedra"].status is TargetSearchStatus.FOUND
    saved=stage.serialize_family(graph,family["octahedra"])
    assert saved["status"]=="FOUND"
    record={
        "schema":1,"index":3,"input_graph6":stage.graph6(graph),
        "levels":[{
            "level":0,"graph6":stage.graph6(graph),
            "order":len(graph),"edges":graph.number_of_edges(),
            "status":"COMPLETED",
            "homology_cache_key":stage.cache_homology(graph,tmp_path)[1],
            "betti_known":{"0":0,"1":0,"2":1},
            "families":{"octahedra":saved},
        }],
    }
    stage.verify_record(record,record["input_graph6"],tmp_path)
    record["levels"][0]["families"]["octahedra"]["projection_indices"][0]=99
    with pytest.raises(ValueError,match="replay"):
        stage.verify_record(record,record["input_graph6"],tmp_path)


def test_snub_profiles_and_scoped_search(tmp_path,monkeypatch):
    monkeypatch.setattr(stage,"ITERATES",1)
    g6=stage.graph6(snub_disphenoid())
    record=stage.analyze(180476,g6,tmp_path)
    assert record["no_automatic_behavior_verdict"] is True
    assert record["scope"]=="pared_input_and_pared_iterates_only"
    assert record["levels"][0]["betti_known"]["2"]==1
    assert all(
        x["status"] in ("EXHAUSTED","HOMOLOGY_EXCLUDED")
        for x in record["levels"][0]["families"].values()
    )


def test_cache_is_not_misapplied_to_another_graph(tmp_path):
    a=octahedron(3)
    profile,key=stage.cache_homology(a,tmp_path)
    b=nx.cycle_graph(5)
    other,key2=stage.cache_homology(b,tmp_path)
    assert key!=key2
    assert profile[2]==1 and other[1]==1
