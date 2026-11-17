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
    proof_totals = stage.certified_method_totals(result["core_proofs"])
    assert result["special_raw_K3_originals"] == proof_totals["special_raw_K3_originals"] == 98
    assert result["suspension_coaffine_originals"] == proof_totals["suspension_coaffine_originals"] == 69
    assert Counter(row["core_id"] for row in result["members"]) == {
        7454135: 61, 9678187: 37, 10768817: 33, 11363569: 36
    }
    assert len({row["original_graph6"] for row in result["members"]}) == 167
    assert all(row["dominated_folds"] for row in result["members"])


def test_method_totals_are_derived_from_verified_groups():
    proofs = [
        {"method": "special_O_d_in_raw_K3", "original_members": 7},
        {"method": "suspension_of_connected_coaffine_graph", "original_members": 5},
    ]
    assert stage.certified_method_totals(proofs) == {
        "special_raw_K3_originals": 7, "suspension_coaffine_originals": 5
    }
    proofs[0]["original_members"] = 11
    assert stage.certified_method_totals(proofs)["special_raw_K3_originals"] == 11
    proofs[0]["method"] = "unverified_method"
    with pytest.raises(ValueError, match="Invalid verified core proof"):
        stage.certified_method_totals(proofs)


def test_same_count_forged_previous_certificates_are_rejected(tmp_path, monkeypatch):
    """A corrupted set of 133 indices cannot authenticate itself."""
    header = (
        "index\toriginal_graph6\thistorical_pared_graph6\tcore_id\t"
        "core_graph6\tdominated_folds\tresidual_graph6\t"
        "residual_to_core\tcertified_direct_v5\n"
    )
    original = header + "".join(
        f"{1000 + i}\tI?qbT^[\\g\tHEht}pl\t6938923\tHEht}pl\t"
        f"[[3,8]]\tHEht}pl\t[]\tfalse\n"
        for i in range(133)
    )
    expected = {"members.tsv": original.encode(), "manifest.json": b"{}"}
    for name, blob in expected.items():
        (tmp_path / name).write_bytes(blob)

    monkeypatch.setattr(stage, "OLD_REPORT", tmp_path / "members.tsv")
    monkeypatch.setattr(stage.previous, "prepare", lambda: expected)
    assert stage.authenticated_previous_members() == set(range(1000, 1133))

    # Change a single original index, preserving all 133 unique rows.
    tampered = original.replace("1000\t", "999999\t", 1)
    (tmp_path / "members.tsv").write_text(tampered, encoding="utf-8")
    with pytest.raises(ValueError, match="modified or stale"):
        stage.authenticated_previous_members()
