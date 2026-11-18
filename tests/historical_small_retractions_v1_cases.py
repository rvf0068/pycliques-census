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



def test_exact_complement_triangle_obstruction_on_historical_targets():
    """Triangle counts rule out large stiff targets without CSP search."""
    host37,_=stage.prior.host(6914104)
    host40,_=stage.prior.host(6962151)
    assert stage.complement_triangle_count(host37)==7
    assert stage.complement_triangle_count(host40)==3

    # Independent graph6 inputs reproduced from completed pilot.
    sources = [
        ("W~~~~zz|~ZX|rzj^tnw^~VnsN~xnzw^~tuv~Vnnxnv~`~|~",
         24,220,8,host37),
        (r"Y~~~~~~~v}~n~n{~|rf]xrdNm]lSx~^}~^n\rzn|n}nsz~~\zo^BfN~?",
         26,256,12,host37),
        ("X~~~~~~~~}^f~N}~}~~n~z~~^~m~}|~^}~^~^n^zzz~nv^}^]~z",
         25,268,6,host40),
        (r"X~~~~~~~~}^v~^}z~Z~N~x~~^~}~~|~~y~~z\~|z^~nm~|}Z~zz",
         25,268,6,host40),
        ("X~~~~~~~~}^v}^}^}~~n~z~~^n}}~|~~]~~^^^nzv|~nnn}]~^z",
         25,268,6,host40),
        ("X~~~~~~~~~^r~V~N~^~~]~fN|Y~xr~vn~v~~r~~|^~~r~~~^~~~",
         25,268,6,host40),
    ]
    for name,n,m,triangles,host in sources:
        target=nx.from_graph6_bytes(name.encode("ascii"))
        assert (len(target),target.number_of_edges())==(n,m)
        assert stage.complement_triangle_count(target)==triangles
        result=stage.probe(host,target,"VF2")
        assert result["status"]=="EXHAUSTED"
        assert result["method"]=="COMPLEMENT_TRIANGLE_OBSTRUCTION"
        assert result["labeled_embedding_maps"]==0
        assert result["induced_vertex_sets"]==0
        assert result["obstruction"]=={
            "type":"COMPLEMENT_TRIANGLE_COUNT",
            "host_triangles":stage.complement_triangle_count(host),
            "target_triangles":triangles,
        }


def test_triangle_obstruction_never_rejects_an_induced_copy():
    host=nx.cycle_graph(5)
    target=host.subgraph([0,1,2]).copy()
    assert stage.complement_triangle_count(target)<=stage.complement_triangle_count(host)
    res=stage.probe(host,target,"ISMAGS")
    assert res["induced_vertex_sets"]>=1
    assert res["method"]=="ISMAGS"


def test_symmetry_aware_matcher_completely_excludes_remnant_large_patterns():
    target20=nx.from_graph6_bytes(
        b"S~~~~~~~~}^v~^}z~Z~N~v~}~~zn~z^~{"
    )
    target24=nx.from_graph6_bytes(
        b"W~~~~~~~~~~{~d~b~n~un}j~f~}n~m^~]vv~jz~zmlnltl}"
    )
    for host_id in (6914104,6962151):
        host,_=stage.prior.host(host_id)
        for target in (target20,target24):
            assert (len(target),target.number_of_edges()) in stage.EXPECTED_ENGINES
            found=stage.probe(host,target,"ISMAGS")
            assert found["status"]=="EXHAUSTED"
            assert found["induced_vertex_sets"]==0
            assert found["obstruction"] is None



def test_preverified_pilot_catalog_rejects_forged_bytes_and_bad_candidate(
    monkeypatch,tmp_path
):
    """An attested manifest cannot authenticate altered or malformed data."""
    manifest={"stage":"pilot-test","sha256":"a"*64}
    monkeypatch.setattr(stage.pilot,"manifest",lambda:manifest)
    records={
        "schema":stage.pilot.SCHEMA,
        "status":"COMPLETED",
        "source_graphs":240,
        "historical_positive_stages":{
            "initial":232,"c10":4,"bound60":1,"bound70":3,
        },
        "candidate_targets":[{"graph6":"test"}],
        "eligible_target_classes":1,
        "eligible_by_host":{"6914104":1,"6962151":0},
    }
    path=tmp_path/"catalog.json"
    manifest_file=tmp_path/"manifest.json"
    manifest_file.write_text(json.dumps(manifest))
    path.write_text(json.dumps(records))
    digests=(stage.sha(path),stage.sha(manifest_file))
    # Even with matching SHA-256, bad graph6 is rejected independently.
    with pytest.raises(ValueError,match="Invalid candidate graph6"):
        stage.authenticated_pilot(path,*digests)

    # Tampering with catalog bytes or its sidecar cannot be covered up by
    # the other file; expected hashes came from a separate upstream job.
    path.write_text(json.dumps({**records,"candidate_targets":[]}))
    with pytest.raises(ValueError,match="catalog digest differs"):
        stage.authenticated_pilot(path,*digests)
    path.write_text(json.dumps(records))
    manifest_file.write_text(json.dumps({"stage":"wrong"}))
    with pytest.raises(ValueError,match="manifest digest differs"):
        stage.authenticated_pilot(path,*digests)
    manifest_file.write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match="Missing or malformed"):
        stage.authenticated_pilot(path,None,None)

    records["status"]="INCOMPLETE"
    path.write_text(json.dumps(records))
    # Even a hypothetical valid digest must fail on an incomplete catalog.
    with pytest.raises(ValueError,match="Incomplete"):
        stage.authenticated_pilot(path,stage.sha(path),stage.sha(manifest_file))


def test_semantic_catalog_checker_rejects_duplicate_host_pairs_and_bad_betti():
    """The structural layer is independent from the byte-level seal."""
    fake={
        "schema":stage.pilot.SCHEMA,
        "status":"COMPLETED",
        "source_graphs":240,
        "historical_positive_stages":{
            "initial":232,"c10":4,"bound60":1,"bound70":3,
        },
        "eligible_target_classes":1,
        "eligible_by_host":{"6914104":2,"6962151":0},
        "candidate_targets":[{
            "graph6":nx.to_graph6_bytes(nx.path_graph(4),header=False)
                        .decode("ascii").strip(),
            "order":4,"edges":3,
            "eligible_hosts":[6914104,6914104],
        }],
    }
    with pytest.raises(ValueError,match="repeated eligible host"):
        stage.validate_pilot_candidates(fake)
    fake["candidate_targets"][0]["eligible_hosts"]=[6914104]
    fake["candidate_targets"][0]["homology_status"]="EXACT_THROUGH_5"
    fake["candidate_targets"][0]["mod2_betti_degrees_0_to_5"]={
        str(i):("not-a-number" if i==3 else 0) for i in range(6)
    }
    with pytest.raises(ValueError,match="Invalid exact Betti"):
        stage.validate_pilot_candidates(fake)


def test_bounded_replayer_passes_same_pilot_catalog_to_subprocess(monkeypatch,tmp_path):
    import subprocess
    observed={}
    def mock_run(args,**kwargs):
        observed["args"]=args
        observed["kwargs"]=kwargs
        return subprocess.CompletedProcess(args,0,"","")
    monkeypatch.setattr(stage.subprocess,"run",mock_run)
    catalog=tmp_path/"catalog.json"
    digest1="a"*64
    digest2="b"*64
    stage.bounded("check",tmp_path/"retractions.json",catalog,digest1,digest2)
    assert observed["args"][2]=="check"
    assert observed["args"][-6:]==[
        "--catalog",str(catalog),
        "--catalog-sha256",digest1,
        "--catalog-manifest-sha256",digest2,
    ]
    assert observed["kwargs"]["timeout"]==stage.TIMEOUT_SECONDS
    assert observed["kwargs"]["preexec_fn"] is stage.limit
    with pytest.raises(ValueError,match="Missing or malformed"):
        stage.bounded("check",tmp_path/"retractions.json",catalog)
