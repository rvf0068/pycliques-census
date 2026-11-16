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
import targeted_retractions_v2 as stage


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


def test_positive_target_retraction_record_and_independent_replay(tmp_path,monkeypatch):
    monkeypatch.setattr(stage, "ITERATES", 1)
    graph=octahedron(3)
    family=stage.search_targeted_retractions(graph)
    assert family["octahedra"].status is TargetSearchStatus.FOUND
    saved=stage.serialize_family(graph,family["octahedra"])
    assert saved["status"]=="FOUND"
    record={
        "schema":2,"index":3,"input_graph6":stage.graph6(graph),
        "status":"COMPLETED","analysis_complete":True,
        "scope":"pared_input_and_pared_iterates_only",
        "no_automatic_behavior_verdict":True,
        "levels":[{
            "level":0,"graph6":stage.graph6(graph),
            "order":len(graph),"edges":graph.number_of_edges(),
            "status":"COMPLETED",
            "homology_cache_key":stage.cache_homology(graph,tmp_path)[1],
            "betti_known":{"0":0,"1":0,"2":1},
            "families":{name:stage.serialize_family(graph,result)
                        for name,result in family.items()},
        }],
    }
    stage.verify_record(record,record["input_graph6"],tmp_path)
    record["levels"][0]["families"]["octahedra"]["projection_indices"][0]=99
    with pytest.raises(ValueError,match="Malformed graph-retraction witness arrays|replay"):
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


def test_manifest_rejects_preexisting_unversioned_artifacts(tmp_path,monkeypatch):
    # Critical: no adoption of a cache without frozen source/pin/algorithm.
    root = tmp_path/"runs"/"order9"/"targeted-retractions-v2"
    (root/"homology_cache").mkdir(parents=True)
    (root/"homology_cache"/"orphan.json").write_text("{}")
    monkeypatch.setattr(stage,"root_dir",lambda _order:root)
    with pytest.raises(ValueError,match="without manifest"):
        stage.require_manifest(9)
    assert not (root/"manifest.json").exists()


def test_manifest_rejects_changed_computation_settings(tmp_path,monkeypatch):
    root=tmp_path/"runs"/"order9"/"targeted-retractions-v2"
    monkeypatch.setattr(stage,"root_dir",lambda _order:root)
    stage.require_manifest(9)
    monkeypatch.setattr(stage,"MAX_TARGET_ORDER",stage.MAX_TARGET_ORDER+1)
    with pytest.raises(ValueError,match="Frozen targeted"):
        stage.require_manifest(9)


def test_complete_record_detects_missing_or_modified_iterate(tmp_path,monkeypatch):
    graph=stage.graph6(snub_disphenoid())
    monkeypatch.setattr(stage,"ITERATES",2)
    record=stage.analyze(180476,graph,tmp_path)
    stage.verify_record(record,graph,tmp_path,index=180476)
    import copy
    corrupted=copy.deepcopy(record)
    corrupted["levels"][1]["graph6"]=corrupted["levels"][0]["graph6"]
    with pytest.raises(ValueError,match="actual pared clique iterate"):
        stage.verify_record(corrupted,graph,tmp_path,index=180476)
    corrupted=copy.deepcopy(record)
    corrupted["levels"]=corrupted["levels"][:1]
    with pytest.raises(ValueError,match="ends before"):
        stage.verify_record(corrupted,graph,tmp_path,index=180476)
    corrupted=copy.deepcopy(record)
    corrupted["levels"]=[]
    with pytest.raises(ValueError,match="Missing/truncated"):
        stage.verify_record(corrupted,graph,tmp_path,index=180476)
    corrupted=copy.deepcopy(record)
    corrupted["analysis_complete"]=False
    with pytest.raises(ValueError,match="Incomplete"):
        stage.verify_record(corrupted,graph,tmp_path,index=180476)
    with pytest.raises(ValueError,match="Incomplete"):
        stage.verify_record(record,graph,tmp_path,index=99999)


def test_complete_record_rejects_cache_provenance_and_missing_family(
    tmp_path,monkeypatch
):
    import copy
    graph=stage.graph6(snub_disphenoid())
    monkeypatch.setattr(stage,"ITERATES",1)
    original=stage.analyze(180476,graph,tmp_path)
    stage.verify_record(original,graph,tmp_path)
    corrupted=copy.deepcopy(original)
    corrupted["levels"][0]["homology_cache_key"]="not_the_graph_sha"
    with pytest.raises(ValueError,match="cached graph key"):
        stage.verify_record(corrupted,graph,tmp_path)
    corrupted=copy.deepcopy(original)
    del corrupted["levels"][0]["families"]["suspensions"]
    with pytest.raises(ValueError,match="family results"):
        stage.verify_record(corrupted,graph,tmp_path)
    key=original["levels"][0]["homology_cache_key"]
    path=tmp_path/"homology_cache"/(key+".json")
    metadata=json.loads(path.read_text(encoding="utf-8"))
    metadata["max_faces"]=100
    path.write_text(json.dumps(metadata),encoding="utf-8")
    with pytest.raises(ValueError,match="provenance"):
        stage.verify_record(original,graph,tmp_path)


def test_unknown_homology_never_excludes_target(tmp_path,monkeypatch):
    monkeypatch.setattr(stage,"MAX_BETTI_FACES",2)
    monkeypatch.setattr(stage,"ITERATES",1)
    graph=stage.graph6(octahedron(3))
    record=stage.analyze(123,graph,tmp_path)
    row=record["levels"][0]
    assert row["betti_known"] is None
    assert row["families"]["octahedra"]["status"]=="FOUND"
    stage.verify_record(record,graph,tmp_path)


def test_plan_and_resume_reject_incomplete_saved_records(tmp_path):
    graph = stage.graph6(snub_disphenoid())
    index = 180476
    path = tmp_path/"records"/f"{index:08d}.json"
    assert stage.finished_record(path,index,graph) is False
    stage.atomic(path,{
        "schema":stage.SCHEMA,"index":index,
        "no_automatic_behavior_verdict":True,
        "status":"COMPLETED","analysis_complete":True,
        "input_graph6":graph,"scope":"pared_input_and_pared_iterates_only",
        "levels":[],
    })
    with pytest.raises(ValueError,match="Incomplete targeted stage"):
        stage.finished_record(path,index,graph)
    stage.atomic(path,{
        "schema":stage.SCHEMA,"index":index,
        "no_automatic_behavior_verdict":True,"status":"TIMEOUT",
    })
    assert stage.finished_record(path,index,graph)
    with pytest.raises(ValueError,match="Malformed targeted stage"):
        stage.finished_record(path,index+1,graph)


def test_v2_uses_new_output_and_frozen_version():
    assert stage.SCHEMA == 2
    assert stage.OUT_PATTERN.endswith("targeted-retractions-v2")
    assert stage.PIN_FILE.name == "pycliques_commit_targeted_v2.txt"


def test_nondivergent_cycle_complement_does_not_mask_different_target():
    graph = nx.from_graph6_bytes(b"O~~~xepAWJqNO~W~yCuCN")
    results = stage.search_targeted_retractions(
        graph, families=("cycle_complements",),
        max_target_order=16,
        max_patterns=stage.MAX_PATTERNS,
        max_states=stage.MAX_STATES,
        max_assignments=stage.MAX_ASSIGNMENTS,
    )
    assert results["cycle_complements"].status is TargetSearchStatus.EXHAUSTED
    assert results["cycle_complements"].induced_targets_checked == 0


@pytest.mark.parametrize(
    "changes",
    [
        {"algorithm": "other.homology.method"},
        {"max_faces": 42},
        {"max_partial_degree": 1},
        {"mode": "unknown"},
        {"mode": "partial"},
        {"mode": "face_limit"},
        {"betti_numbers": None},
        {"betti_numbers": {"0": 0, "1": "0", "2": 1}},
        {"betti_numbers": {"0": 0, "1": False, "2": 1}},
        {"betti_numbers": {"0": 0, "1": -1, "2": 1}},
        {"betti_numbers": {"0": 0, "2": 1}},
        {"betti_numbers": {"00": 0, "1": 0, "2": 1}},
        {"betti_numbers": {"0": 0, "1": 0, "2": 1, "999": 1}},
    ],
)
def test_cache_load_rejects_invalid_provenance_or_exact_profile(
    tmp_path, monkeypatch, changes
):
    graph = octahedron(3)
    _, key = stage.cache_homology(graph, tmp_path)
    cache = tmp_path/"homology_cache"/(key+".json")
    original = json.loads(cache.read_text(encoding="utf-8"))
    original.update(changes)
    cache.write_text(json.dumps(original), encoding="utf-8")

    def must_not_recompute(*args, **kwargs):
        raise AssertionError("Invalid caches must fail closed, not recompute")

    monkeypatch.setattr(stage, "bounded_reduced_betti_mod2", must_not_recompute)
    with pytest.raises(ValueError, match="cache|Betti|homology"):
        stage.cache_homology(graph, tmp_path)


def test_cache_load_accepts_valid_face_limit_and_partial_mode(tmp_path, monkeypatch):
    graph = octahedron(3)
    _, key = stage.cache_homology(graph, tmp_path)
    cache = tmp_path/"homology_cache"/(key+".json")
    original = json.loads(cache.read_text(encoding="utf-8"))

    face_limit = dict(original, mode="face_limit", betti_numbers=None)
    cache.write_text(json.dumps(face_limit), encoding="utf-8")
    assert stage.cache_homology(graph, tmp_path) == (None, key)

    partial = dict(original, mode="partial", betti_numbers={
        str(degree): 0 for degree in range(stage.MAX_BETTI_PARTIAL_DEGREE + 1)
    })
    cache.write_text(json.dumps(partial), encoding="utf-8")
    known, key2 = stage.cache_homology(graph, tmp_path)
    assert known == {
        degree: 0 for degree in range(stage.MAX_BETTI_PARTIAL_DEGREE + 1)
    }
    assert key2 == key

    partial["betti_numbers"].pop(str(stage.MAX_BETTI_PARTIAL_DEGREE))
    cache.write_text(json.dumps(partial), encoding="utf-8")
    with pytest.raises(ValueError, match="partial homology cache"):
        stage.cache_homology(graph, tmp_path)
