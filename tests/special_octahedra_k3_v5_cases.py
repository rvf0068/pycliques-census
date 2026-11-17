"""Regression tests for the fast, graph6-deduplicated K³ special sweep."""
from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path

import networkx as nx
import pytest
from pycliques.named import octahedron
from pycliques.small import CliqueSequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import targeted_retractions_v2 as v2
import targeted_retractions_v3 as v3
import special_octahedra_k3_v5 as v5


def fake_verified_source(graph: nx.Graph) -> dict:
    """Three valid pared levels without running any general retraction search."""
    seq = CliqueSequence(graph, bound=v5.CLIQUE_BOUND)
    return {
        "levels": [{
            "level": i, "status": "COMPLETED",
            "graph6": v2.graph6(seq[i]), "order": len(seq[i]),
        } for i in range(3)]
    }


def test_special_octahedron_is_a_sufficient_retraction_certificate(monkeypatch):
    host = octahedron(3)
    encoded = v2.graph6(host)
    monkeypatch.setattr(v3, "index_to_graph6", lambda: {42: encoded})

    def no_k3(_level):
        raise AssertionError("A positive special certificate must stop first")

    monkeypatch.setattr(v5, "reconstruct_k3", no_k3)
    source = {"levels": []}
    # The v3 source always has three completed levels, even when v5 stops
    # immediately on the original graph.
    source = {"levels": [{"level": i, "status": "COMPLETED",
                          "graph6": encoded} for i in range(3)]}
    record = v5.analyze(42, encoded, source)
    assert len(record["levels"]) == 1
    assert record["divergence_certificate"] == {
        "rule": "special_octahedron",
        "iterate_index": 0,
        "dimension": 3,
        "target_kind": "octahedra:3",
        "conclusion": "proven_divergent",
    }
    v5.verify_record(record, encoded, source)
    bad = deepcopy(record)
    bad["levels"][0]["special"]["antipode_indices"][0] = (
        bad["levels"][0]["special"]["clique_indices"][0]
    )
    with pytest.raises(ValueError, match="positive witness"):
        v5.verify_record(bad, encoded, source)


def test_all_four_levels_are_checked_without_betti_or_general_retractions(
    monkeypatch
):
    host = nx.path_graph(5)
    encoded = v2.graph6(host)
    monkeypatch.setattr(v3, "index_to_graph6", lambda: {5: encoded})
    source = fake_verified_source(host)
    seen = []
    original = v5.reconstruct_k3

    def wrapped(level):
        seen.append(level["graph6"])
        return original(level)

    monkeypatch.setattr(v5, "reconstruct_k3", wrapped)
    monkeypatch.setattr(
        v2, "cache_homology",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("V5 must not calculate homology")
        ),
    )
    record = v5.analyze(5, encoded, source)
    assert [l["level"] for l in record["levels"]] == [0, 1, 2, 3]
    assert len(seen) == 1
    assert record["divergence_certificate"] is None
    assert all(l["special"] == {"status": "EXHAUSTED"}
               for l in record["levels"])
    v5.verify_record(record, encoded, source)
    assert len(seen) == 2
    tampered = deepcopy(record)
    tampered["levels"][3]["graph6"] = "wrong"
    with pytest.raises(ValueError, match="actual pared iterate"):
        v5.verify_record(tampered, encoded, source)


def test_bounded_k3_is_not_a_negative_special_search(monkeypatch):
    host = nx.path_graph(5)
    encoded = v2.graph6(host)
    monkeypatch.setattr(v3, "index_to_graph6", lambda: {5: encoded})
    monkeypatch.setattr(v5, "reconstruct_k3", lambda _level: None)
    source = fake_verified_source(host)
    record = v5.analyze(5, encoded, source)
    assert record["levels"][-1] == {
        "level": 3, "status": "CLIQUE_BOUND_EXCEEDED",
    }
    v5.verify_record(record, encoded, source)
    assert record["divergence_certificate"] is None


def test_progress_journal_preserves_timeout_phase(tmp_path, monkeypatch):
    monkeypatch.setattr(v5, "STAGE", tmp_path)
    monkeypatch.setattr(v3, "index_to_graph6", lambda: {5: "GQyuzw"})
    v5.phase(5, "GQyuzw", "CHECK_LEVEL3")
    assert v5.read_phase("GQyuzw", 5) == "CHECK_LEVEL3"
    terminal = {
        "schema": v5.SCHEMA, "index": 5, "graph6": "GQyuzw",
        "status": "TIMEOUT", "last_phase": "CHECK_LEVEL3",
    }
    v5.verify_terminal(terminal, "GQyuzw")
    with pytest.raises(ValueError, match="terminal worker"):
        v5.verify_terminal(dict(terminal, index=True), "GQyuzw")
    with pytest.raises(ValueError, match="terminal worker"):
        v5.verify_terminal(dict(terminal, last_phase="UNKNOWN"), "GQyuzw")


def test_manifest_is_frozen_and_refuses_unversioned_adoption(
    tmp_path, monkeypatch
):
    target = tmp_path / "stage"
    monkeypatch.setattr(v5, "STAGE", target)
    v5.require_stage()
    first = v5.read(target / "manifest.json")
    assert first == v5.manifest()
    corrupt = deepcopy(first)
    corrupt["clique_bound"] = 999
    v2.atomic(target / "manifest.json", corrupt)
    with pytest.raises(ValueError, match="Frozen v5"):
        v5.require_stage()
    (target / "manifest.json").unlink()
    # An empty stage can legitimately be initialized again. Adoption is
    # forbidden only if other result artifacts survive without a manifest.
    (target / "records").mkdir()
    (target / "records" / "orphan.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="without a frozen manifest"):
        v5.require_stage()


def test_summary_counts_exact_graph6_aliases_once(tmp_path, monkeypatch):
    monkeypatch.setattr(v5, "STAGE", tmp_path)
    row = {"graph6": "GQyuzw", "indices": [1, 2, 3], "unclassified": False}
    monkeypatch.setattr(v5, "imported_groups", lambda: [row])
    v2.atomic(
        v5.path_for("GQyuzw", "records"),
        {
            "schema": v5.SCHEMA, "index": 1, "graph6": "GQyuzw",
            "status": "COMPLETED",
            "divergence_certificate": {
                "rule": "special_octahedron",
                "iterate_index": 3,
                "dimension": 3,
                "conclusion": "proven_divergent",
            },
            "levels": [{"status": "COMPLETED"}],
        },
    )
    totals = v5.summary()
    assert totals["completed_unique"] == 1
    assert totals["covered_input_indices"] == 3
    assert totals["certified_divergent_unique"] == 1
    assert totals["certified_divergent_indices"] == 3
    assert totals["certified_by_level"] == {"3": 1}


def test_reject_incorrect_level0_encoding(monkeypatch):
    host = nx.path_graph(5)
    encoded = v2.graph6(host)
    monkeypatch.setattr(v3, "index_to_graph6", lambda: {5: encoded})
    source = fake_verified_source(host)
    record = v5.analyze(5, encoded, source)
    record["levels"][0]["graph6"] = "bad"
    with pytest.raises(ValueError, match="actual pared iterate"):
        v5.verify_record(record, encoded, source)


@pytest.mark.parametrize("status", ["CLIQUE_BOUND_EXCEEDED", "HOST_ORDER_LIMIT"])
def test_v3_completed_capsule_with_early_terminal_is_ineligible(status):
    # A v3 outer COMPLETED means its analysis finished, not that
    # all three requested pared iterates were successfully constructed.
    inner = {
        "levels": [
            {"level": 0, "status": "COMPLETED"},
            {"level": 1, "status": status},
        ]
    }
    assert not v5.complete_v3_source(inner)
    assert not v5.complete_v3_source({"levels": inner["levels"] + [
        {"level": 2, "status": "COMPLETED"},
    ]})
    assert v5.complete_v3_source({"levels": [
        {"level": i, "status": "COMPLETED"} for i in range(3)
    ]})


def test_v3_early_terminal_is_skipped_on_import_and_rejected_on_replay(
    tmp_path, monkeypatch
):
    encoded = "GQyuzw"
    index = 2317572
    original_v3 = tmp_path / "source-v3"
    current_v5 = tmp_path / "stage-v5"
    monkeypatch.setattr(v5, "STAGE", current_v5)
    monkeypatch.setattr(v3, "STAGE", original_v3)
    monkeypatch.setattr(v3, "index_to_graph6", lambda: {index: encoded})
    monkeypatch.setattr(v5, "groups", lambda: [{
        "graph6": encoded, "indices": [index, 2317841],
        "unclassified": True,
    }])
    monkeypatch.setattr(v3, "require_stage", lambda: original_v3)
    # Source provenance is checked separately by v3 in production; use a
    # synthetic valid-v3 capsule here to isolate v5 cohort selection.
    checked = []
    monkeypatch.setattr(
        v3, "verify_capsule",
        lambda capsule, graph6: checked.append((capsule, graph6)),
    )
    v2.atomic(original_v3 / "manifest.json", {"synthetic": True})
    original_path = v3.record_path(encoded)
    incomplete = {
        "schema": v3.SCHEMA,
        "graph6": encoded,
        "status": "COMPLETED",
        "origin": "v3_worker",
        "record": {
            "index": index,
            "input_graph6": encoded,
            "levels": [
                {"level": 0, "status": "COMPLETED"},
                {"level": 1, "status": "CLIQUE_BOUND_EXCEEDED"},
            ],
        },
    }
    v2.atomic(original_path, incomplete)
    result = v5.import_v3()
    assert result["imported_unique"] == 0
    assert result["skipped_incomplete_v3_unique"] == 1
    assert result["skipped_incomplete_v3_indices"] == 2
    assert checked and checked[0][1] == encoded
    assert not v5.path_for(encoded, "imports").exists()
    assert v5.imported_groups() == []

    # Even a forged receipt does not allow an early-terminated v3 capsule
    # to enter the worker or its independent verifier.
    v2.atomic(v5.path_for(encoded, "imports"), {
        "schema": v5.SCHEMA, "graph6": encoded, "index": index,
        "source_sha256": v5.digest(original_path.read_bytes()),
        "source_manifest_sha256": v5.digest(
            (original_v3 / "manifest.json").read_bytes()
        ),
    })
    with pytest.raises(ValueError, match="lacks three completed"):
        v5.verify_import(encoded)
    # Reject silently adopting an old, ineligible imported record.
    with pytest.raises(ValueError, match="Previously imported"):
        v5.import_v3()

    # Once a verified source has three completed levels, it is eligible.
    # Remove the old synthetic receipt and refresh its hash.
    v5.path_for(encoded, "imports").unlink()
    complete = deepcopy(incomplete)
    complete["record"]["levels"] = [
        {"level": i, "status": "COMPLETED"} for i in range(3)
    ]
    v2.atomic(original_path, complete)
    outcome = v5.import_v3()
    assert outcome["imported_unique"] == 1
    assert outcome["skipped_incomplete_v3_unique"] == 0
    assert v5.verify_import(encoded) == complete["record"]
