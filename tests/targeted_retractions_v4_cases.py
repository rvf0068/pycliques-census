"""Certified special-octahedron first search through the pared third iterate."""
from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path

import networkx as nx
import pytest
from pycliques.named import octahedron
from pycliques.retractions import find_special_octahedron_witness

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import targeted_retractions_v2 as v2
import targeted_retractions_v3 as v3
import targeted_retractions_v4 as v4


def test_special_octahedron_is_verified_and_preempts_target_search(monkeypatch):
    graph = octahedron(3)
    witness = find_special_octahedron_witness(graph)
    assert witness is not None and witness.dimension == 3

    def forbidden(*args, **kwargs):
        raise AssertionError("A special octahedron must be checked first")

    monkeypatch.setattr(v4, "search_targeted_retractions", forbidden)
    monkeypatch.setattr(v2, "cache_homology", forbidden)
    row = v4.serialize_level(1, graph, 3, {})
    assert row["special"]["status"] == "FOUND"
    assert row["special"]["dimension"] == 3
    assert row["retractions"]["mode"] == "SKIPPED_SPECIAL_CERTIFICATE"
    assert v4.verify_special(graph, row["special"])

    corrupt = deepcopy(row["special"])
    corrupt["clique_indices"][0] = corrupt["antipode_indices"][0]
    assert not v4.verify_special(graph, corrupt)


def test_special_positive_independently_certifies_divergence_at_iterate_zero(
    monkeypatch
):
    graph = octahedron(3)
    encoded = v2.graph6(graph)
    monkeypatch.setattr(v3, "index_to_graph6", lambda: {42: encoded})
    result = v4.analyze(42, encoded, {"levels": []})
    assert len(result["levels"]) == 1
    assert result["divergence_certificate"] == {
        "rule": "special_octahedron",
        "iterate_index": 0,
        "dimension": 3,
        "conclusion": "proven_divergent",
    }
    v4.verify_record(result, encoded, {"levels": []})

    tampered = deepcopy(result)
    tampered["divergence_certificate"]["iterate_index"] = 1
    with pytest.raises(ValueError, match="divergence certificate"):
        v4.verify_record(tampered, encoded, {"levels": []})


def test_negative_special_then_reuses_existing_v3_target_families():
    graph = nx.path_graph(5)
    encoded = v2.graph6(graph)
    old_families = {
        family: {
            "status": "EXHAUSTED", "patterns": 0, "induced_targets": 0,
            "states": 0, "assignments": 0, "reason": "test",
        }
        for family in v4.FAMILIES
    }
    inherited = {1: {
        "level": 1,
        "status": "COMPLETED",
        "graph6": encoded,
        "families": old_families,
    }}
    result = v4.serialize_level(0, graph, 1, inherited)
    assert result["special"] == {"status": "EXHAUSTED"}
    assert result["retractions"] == {
        "mode": "REUSED_VERIFIED_V3",
        "families": old_families,
    }


def test_k3_search_uses_independent_new_cache_and_witness_checks(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(v4, "STAGE", tmp_path)
    graph = nx.path_graph(5)
    row = v4.serialize_level(0, graph, 3, {})
    assert row["special"] == {"status": "EXHAUSTED"}
    assert row["retractions"]["mode"] == "NEW_V4"
    assert set(row["retractions"]["families"]) == v4.FAMILIES
    v4.verify_families(graph, row["retractions"]["families"])
    ranks = row["retractions"]["betti_known"]
    assert ranks is None or ranks.get("0") == 0
    cache = v4.read(
        tmp_path / "homology_cache"
        / (row["retractions"]["homology_cache_key"] + ".json")
    )
    assert cache["graph6"] == v2.graph6(graph)


def test_special_search_even_when_target_hosts_exceed_80(monkeypatch):
    graph = nx.empty_graph(v4.MAX_TARGET_HOST_VERTICES + 1)

    def no_special(_graph):
        return None

    monkeypatch.setattr(v4, "find_special_octahedron_witness", no_special)
    row = v4.serialize_level(0, graph, 3, {})
    assert row["special"] == {"status": "EXHAUSTED"}
    assert row["retractions"]["mode"] == "SKIPPED_HOST_ORDER_LIMIT"

    # Special detection happens BEFORE the 80-vertex target-search cap.
    witness = find_special_octahedron_witness(octahedron(3))
    assert witness is not None


def test_manifest_is_frozen_and_v3_is_unmodified(tmp_path, monkeypatch):
    monkeypatch.setattr(v4, "STAGE", tmp_path / "v4")
    v4.require_stage()
    expected = v4.manifest()
    assert v4.read(v4.STAGE / "manifest.json") == expected
    modified = deepcopy(expected)
    modified["max_level"] = 2
    v2.atomic(v4.STAGE / "manifest.json", modified)
    with pytest.raises(ValueError, match="Frozen v4"):
        v4.require_stage()


@pytest.mark.parametrize("bad_index", [None, True, "2317572", 2318241])
def test_terminal_worker_provenance_requires_correct_index(monkeypatch, bad_index):
    graph6 = "GQyuzw"
    monkeypatch.setattr(v3, "index_to_graph6", lambda: {2317572: graph6})
    good = {
        "schema": v4.SCHEMA, "graph6": graph6,
        "index": 2317572, "status": "TIMEOUT",
    }
    v4.verify_terminal(good, graph6)
    with pytest.raises(ValueError, match="terminal worker provenance"):
        v4.verify_terminal(dict(good, index=bad_index), graph6)


def test_v4_reports_legacy_and_k3_results_separately(tmp_path, monkeypatch):
    monkeypatch.setattr(v4, "STAGE", tmp_path)
    groups = [
        {"graph6": "GQyuzw", "indices": [1, 2], "unclassified": False},
        {"graph6": "HCrlvhz", "indices": [3], "unclassified": True},
    ]
    monkeypatch.setattr(v4, "source_groups", lambda: groups)
    for g in groups:
        v2.atomic(
            v4.key_path(g["graph6"], "imports"),
            {"schema": v4.SCHEMA, "graph6": g["graph6"]},
        )
    v2.atomic(
        v4.record_path(groups[0]["graph6"]),
        {
            "schema": v4.SCHEMA,
            "graph6": groups[0]["graph6"],
            "status": "COMPLETED",
            "divergence_certificate": {
                "rule": "special_octahedron",
                "iterate_index": 3,
            },
            "levels": [
                {
                    "status": "COMPLETED",
                    "retractions": {"mode": "SKIPPED_SPECIAL_CERTIFICATE"},
                }
            ],
        },
    )
    summary = v4.summary()
    assert summary["distinct_v3_imports"] == 2
    assert summary["completed_unique"] == 1
    assert summary["covered_input_indices"] == 2
    assert summary["certified_special"] == 1
    assert summary["certified_special_at_k3"] == 1
    assert summary["pending_unique"] == 1


def test_atomic_progress_journal_is_diagnostic_only(tmp_path, monkeypatch):
    monkeypatch.setattr(v4, "STAGE", tmp_path)
    monkeypatch.setattr(
        v3, "index_to_graph6", lambda: {2317572: "GQyuzw"}
    )
    v4.write_progress(
        2317572, "GQyuzw", 3, "SPECIAL_OCTAHEDRON_SEARCH"
    )
    assert v4.read_progress(2317572, "GQyuzw") == {
        "schema": v4.SCHEMA,
        "index": 2317572,
        "graph6": "GQyuzw",
        "level": 3,
        "phase": "SPECIAL_OCTAHEDRON_SEARCH",
    }
    timeout = {
        "schema": v4.SCHEMA,
        "graph6": "GQyuzw",
        "status": "TIMEOUT",
        "index": 2317572,
        "last_progress": v4.read_progress(2317572, "GQyuzw"),
    }
    v4.verify_terminal(timeout, "GQyuzw")
    wrong = deepcopy(timeout)
    wrong["last_progress"]["level"] = 4
    with pytest.raises(ValueError, match="terminal progress"):
        v4.verify_terminal(wrong, "GQyuzw")


def test_invalid_progress_source_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(v4, "STAGE", tmp_path)
    monkeypatch.setattr(
        v3, "index_to_graph6", lambda: {2317572: "GQyuzw"}
    )
    with pytest.raises(ValueError, match="Invalid progress"):
        v4.write_progress(
            2317572, "HCrlvhz", 2, "SPECIAL_OCTAHEDRON_SEARCH"
        )
    with pytest.raises(ValueError, match="Invalid progress"):
        v4.write_progress(2317572, "GQyuzw", 4, "LEVEL_COMPLETED")
