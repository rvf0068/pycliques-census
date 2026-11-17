"""Independent regression tests for the four additional divergent nine-cores."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import networkx as nx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import historical_ninecore_lift_v1 as stage


@pytest.mark.parametrize("core_id", [7454135, 9678187])
def test_explicit_raw_special_octahedron(core_id):
    spec = stage.SPECS[core_id]
    data = stage.core_certificate(core_id, spec)
    assert data["dimension"] == len(spec["facet"])
    assert data["iterate"] == 3
    assert data["raw_levels"][-1] == [spec["third_order"], spec["third_edges"]]


@pytest.mark.parametrize("core_id", [10768817, 11363569])
def test_explicit_coaffination(core_id):
    spec = stage.SPECS[core_id]
    data = stage.core_certificate(core_id, spec)
    assert data["method"] == "suspension_of_connected_coaffine_graph"


def test_special_rejects_bad_antipode():
    spec = stage.SPECS[7454135]
    graph = nx.from_graph6_bytes(spec["graph6"].encode())
    for _ in range(3):
        graph = stage.raw_clique_graph(graph)
    wrong = list(spec["antipodes"])
    wrong[0] = spec["facet"][0]
    with pytest.raises(ValueError, match="Invalid octahedron"):
        stage.check_special(graph, spec["facet"], wrong)


def test_coaffination_rejects_fixed_point():
    spec = stage.SPECS[10768817]
    graph = nx.from_graph6_bytes(spec["graph6"].encode())
    bad = list(spec["coaffination_images"])
    bad[0] = spec["base_vertices"][0]
    with pytest.raises(ValueError, match="suspension or permutation|2-coaffination"):
        stage.check_suspension(
            graph, spec["poles"], spec["base_vertices"], bad
        )


def test_certify_all_167_and_disjoint_from_previous_133(tmp_path):
    result = stage.certify()
    assert result["certified_originals_new"] == 167
    assert result["certified_originals_previous"] == 133
    assert result["certified_originals_total"] == 300
    assert result["special_raw_K3_originals"] == 98
    assert result["suspension_coaffine_originals"] == 69
    assert Counter(row["core_id"] for row in result["members"]) == {
        7454135: 61, 9678187: 37, 10768817: 33, 11363569: 36
    }
    assert len({row["original_graph6"] for row in result["members"]}) == 167
    assert all(row["dominated_folds"] for row in result["members"])
