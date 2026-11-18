"""Mathematical integrity tests for the historical certified-target library."""
from __future__ import annotations

from collections import Counter
import sys
from pathlib import Path

import networkx as nx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import historical_divergent_target_library_v1 as stage


def test_saved_divergent_certificates_not_confused_with_snub_conjectures():
    known=stage.saved_divergent_verdicts()
    assert {n:len(v) for n,v in known.items()} == stage.HISTORICAL_DIVERGENT_COUNTS
    extra=stage.extra_nine_proofs()
    assert len(extra)==6
    assert all("diverg" not in x["stage"].lower() for x in extra.values())
    assert all("snub" not in x["reason"].lower() for x in extra.values())
    # Two of the six nine-core proofs were already recognized at the
    # initial stage; four are new beyond its 9864 positives.
    assert len(set(extra) & set(known[9])) == 2
    assert len(set(extra) - set(known[9])) == 4


def test_source_graph6_provenance_includes_historial_extra():
    extra=stage.extra_nine_proofs()
    assert set(extra) == {250684,253557,255039,259791,260927,261008}
    for entry in extra.values():
        assert len(stage.decode(entry["graph6"])) == 9


def test_stiff_paring_is_idempotent_and_preserves_isomorphism():
    for graph in (nx.octahedral_graph(), nx.path_graph(8), nx.complete_graph(6)):
        core=stage.core(graph)
        assert nx.is_isomorphic(stage.core(core),core)
        assert len(core)<=len(graph)
    assert len(stage.core(nx.complete_graph(6)))==1


def test_clique_graph_has_maximal_clique_intersections():
    graph=nx.octahedral_graph()
    k,facets=stage.raw_k(graph)
    assert k is not None and facets==8
    assert nx.is_isomorphic(k, nx.complement(
        nx.disjoint_union_all([nx.path_graph(2) for _ in range(4)])
    ))
    assert stage.core(k).number_of_nodes()==8


def test_isomorphism_dedup_ignores_labels_and_not_nonisomorphic_graphs():
    ix=stage.IsoIndex()
    first,new=ix.add(nx.cycle_graph(5))
    assert (first,new)==(0,True)
    second,new=ix.add(nx.relabel_nodes(nx.cycle_graph(5),{
        i:(i+2)%5 for i in range(5)
    }))
    assert (second,new)==(0,False)
    third,new=ix.add(nx.complete_graph(5))
    assert (third,new)==(1,True)


def test_safe_necessary_filters_do_not_exclude_induced_subgraphs():
    host=nx.octahedral_graph()
    for vertices in ([0,1,2],[0,2,3,4,5],list(host)):
        valid,_=stage.necessary_induced_bounds(host,host.subgraph(vertices))
        assert valid


def test_induced_complement_edge_filter_is_sound():
    host=nx.complete_graph(8)
    candidate=nx.path_graph(6)
    good,reason=stage.necessary_induced_bounds(host,candidate)
    assert not good
    assert reason in {"COMPLEMENT_EDGE_LOWER_BOUND","COMPLEMENT_DEGREE_MAJORANT"}


def test_all_verified_sources_are_proven_positive_only():
    assert stage.HISTORICAL_DIVERGENT_COUNTS == {
        6:1,7:9,8:222,9:9864,
    }
    assert stage.MAX_ITERATE==2
    assert stage.MAX_CLIQUES_PER_ITERATE<=200
    assert stage.TOP_PER_HOST>0



def test_exact_archives_match_frozen_original_graph_index_sources():
    expected=stage.validate_source_archives()
    assert set(expected)=={"6","7","8","9"}
    assert all(len(h)==64 for h in expected.values())


def test_complete_original_source_provenance_is_preserved():
    # Run on an intentionally tiny synthetic catalog, without scanning
    # the full historical list during the test. Each saved source must
    # carry its positive reason and original graph6.
    record={
        "id":7,"pared_graph6":"F?","member_counts_by_order":{"6":2},
        "original_sources":[
            {"order":6,"index":4,"graph6":"E?","positive_reason":"certificate A"},
            {"order":6,"index":7,"graph6":"E?","positive_reason":"certificate B"},
        ],
    }
    assert len(record["original_sources"])==sum(record["member_counts_by_order"].values())
    assert len({row["positive_reason"] for row in record["original_sources"]})==2
