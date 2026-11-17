"""Regression tests for deduplicated v3 provenance and queue ordering."""
from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest
from pycliques.named import octahedron

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import targeted_retractions_v2 as v2
import targeted_retractions_v3 as v3


def test_priority_and_exact_graph6_aliasing(tmp_path, monkeypatch):
    source = tmp_path / "source.txt"
    source.write_text(
        "# index pared_order graph6 status annotation witness\n"
        "1 8 GQyuzw reference conjectured_divergent snub_disphenoid\n"
        "2 8 GQyuzw retracts conjectured_divergent snub_disphenoid\n"
        "3 9 HCrlvhz - - -\n"
        "4 9 HCrlvhz - - -\n"
        "5 8 GQzZtk reference conjectured_divergent snub_disphenoid\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(v3, "SOURCE", source)
    monkeypatch.setattr(
        v3, "index_to_graph6",
        lambda: {1: "GQyuzw", 2: "GQyuzw", 3: "HCrlvhz",
                 4: "HCrlvhz", 5: "GQzZtk"},
    )
    groups = v3.source_groups()
    assert len(groups) == 3
    assert groups[0]["graph6"] == "HCrlvhz"
    assert groups[0]["indices"] == [3, 4]
    assert groups[1]["indices"] == [1, 2]
    assert groups[2]["indices"] == [5]
    assert len({v3.sha(g["graph6"].encode("ascii")) for g in groups}) == 3


def test_source_rejects_conflicting_or_duplicate_index(tmp_path, monkeypatch):
    source = tmp_path / "input.txt"
    source.write_text(
        "1 8 GQyuzw reference conjectured_divergent snub_disphenoid\n"
        "1 8 GQzZtk reference conjectured_divergent snub_disphenoid\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(v3, "SOURCE", source)
    monkeypatch.setattr(v3, "index_to_graph6", lambda: {1: "GQyuzw"})
    with pytest.raises(ValueError, match="Source row disagreement"):
        v3.source_groups()


def test_v3_manifest_isolated_and_immutable(tmp_path, monkeypatch):
    stage = tmp_path / "v3"
    monkeypatch.setattr(v3, "STAGE", stage)
    v3.require_stage()
    assert v3.read(stage / "manifest.json") == v3.manifest()
    frozen = v3.read(stage / "manifest.json")
    frozen["priority"] = "wrong_priority"
    v2.atomic(stage / "manifest.json", frozen)
    with pytest.raises(ValueError, match="Frozen v3"):
        v3.require_stage()


def test_v3_refuses_preexisting_unversioned_outputs(tmp_path, monkeypatch):
    stage = tmp_path / "v3"
    monkeypatch.setattr(v3, "STAGE", stage)
    (stage / "records").mkdir(parents=True)
    (stage / "records" / "junk.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="without a manifest"):
        v3.require_stage()


def test_copy_verified_cache_rejects_conflicting_payload(tmp_path, monkeypatch):
    old = tmp_path / "v2"
    new = tmp_path / "v3"
    monkeypatch.setattr(v3, "V2_STAGE", old)
    monkeypatch.setattr(v3, "STAGE", new)
    graph = octahedron(3)
    _, key = v2.cache_homology(graph, old)
    record = {
        "levels": [{
            "status": "COMPLETED",
            "graph6": v2.graph6(graph),
            "homology_cache_key": key,
        }]
    }
    v3.copy_verified_caches(record)
    assert (
        (new / "homology_cache" / (key + ".json")).read_bytes()
        == (old / "homology_cache" / (key + ".json")).read_bytes()
    )
    v3.copy_verified_caches(record)
    dest = new / "homology_cache" / (key + ".json")
    bad = json.loads(dest.read_text(encoding="utf-8"))
    bad["max_faces"] = 2
    v2.atomic(dest, bad)
    with pytest.raises(ValueError, match="Conflicting cache"):
        v3.copy_verified_caches(record)


def test_v3_worker_record_independently_verified(tmp_path, monkeypatch):
    monkeypatch.setattr(v3, "STAGE", tmp_path)
    # A real row from the frozen order-10 source, representing an 8-vertex
    # pared graph with a fully reproducible three-level clique sequence.
    index = 2317572
    encoded = v3.index_to_graph6()[index]
    record = v2.analyze(index, encoded, tmp_path)
    capsule = {
        "schema": v3.SCHEMA,
        "graph6": encoded,
        "status": "COMPLETED",
        "origin": "v3_worker",
        "record": record,
    }
    v3.verify_capsule(capsule, encoded)
    wrong = deepcopy(capsule)
    wrong["record"]["levels"][0]["graph6"] = "incorrect"
    with pytest.raises(ValueError, match="actual pared clique iterate"):
        v3.verify_capsule(wrong, encoded)
    wrong = deepcopy(capsule)
    wrong["graph6"] = "incorrect"
    with pytest.raises(ValueError, match="identity"):
        v3.verify_capsule(wrong, encoded)


def test_summary_counts_alias_coverage_once_per_distinct_graph6(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(v3, "STAGE", tmp_path)
    group = {
        "graph6": "GQyuzw",
        "indices": [2317572, 2317841],
        "unclassified": False,
    }
    v2.atomic(
        v3.record_path(group["graph6"]),
        {
            "schema": v3.SCHEMA,
            "graph6": group["graph6"],
            "status": "COMPLETED",
            "origin": "verified_v2_import",
            "record": {"levels": [], "index": 2317572},
        },
    )
    result = v3.summary([group])
    assert result["completed_unique"] == 1
    assert result["covered_input_indices"] == 2
    assert result["imported_unique"] == 1
    assert result["pending_unique"] == 0


def test_report_aggregates_exact_search_results(tmp_path, monkeypatch):
    monkeypatch.setattr(v3, "STAGE", tmp_path)
    group = {"graph6": "GQyuzw", "indices": [1, 2], "unclassified": True}
    v2.atomic(
        v3.record_path(group["graph6"]),
        {
            "schema": v3.SCHEMA,
            "graph6": group["graph6"],
            "status": "COMPLETED",
            "origin": "v3_worker",
            "record": {
                "index": 1,
                "levels": [
                    {
                        "level": 0,
                        "status": "COMPLETED",
                        "families": {
                            "cycle_complements": {
                                "status": "EXHAUSTED",
                                "induced_targets": 7,
                                "states": 20,
                            }
                        },
                    }
                ],
            },
        },
    )
    result = v3.report([group])
    assert result["completed_by_category"] == {"unclassified": 1}
    assert result["family_statuses"] == {"cycle_complements:EXHAUSTED": 1}
    assert result["total_induced_targets_checked"] == {"cycle_complements": 7}
    assert result["total_search_states"] == {"cycle_complements": 20}


@pytest.mark.parametrize("terminal_status", ["TIMEOUT", "ERROR"])
def test_import_v2_replaces_verified_terminal_and_is_idempotent(
    tmp_path, monkeypatch, terminal_status
):
    source_stage = tmp_path / "frozen-v2"
    target_stage = tmp_path / "new-v3"
    monkeypatch.setattr(v3, "V2_STAGE", source_stage)
    monkeypatch.setattr(v3, "STAGE", target_stage)
    monkeypatch.setattr(v2, "root_dir", lambda _order: source_stage)

    index = 2317572
    encoded = v3.index_to_graph6()[index]
    monkeypatch.setattr(v3, "index_to_graph6", lambda: {index: encoded})
    v2.require_manifest(10)
    v3.require_stage()  # Existing worker files require the frozen v3 manifest.
    original = v2.analyze(index, encoded, source_stage)
    v2.verify_record(original, encoded, source_stage, index=index)
    v2.atomic(v3.v2_source_path(index), original)

    # The previously terminal v3 worker has a valid graph6 and source index,
    # but must not block a later completed, independently verified v2 import.
    v2.atomic(
        v3.record_path(encoded),
        {
            "schema": v3.SCHEMA,
            "graph6": encoded,
            "status": terminal_status,
            "origin": "v3_worker",
            "index": index,
        },
    )
    receipt = v3.import_v2()
    assert receipt["verified_v2_records"] == 1
    assert receipt["distinct_verified_v2_graph6"] == 1
    capsule = v3.read(v3.record_path(encoded))
    assert capsule["status"] == "COMPLETED"
    assert capsule["origin"] == "verified_v2_import"
    assert capsule["v2_source_index"] == index
    v3.verify_capsule(capsule, encoded)

    # Reimport must retain this already verified capsule unchanged.
    before = v3.record_path(encoded).read_bytes()
    assert v3.import_v2() == receipt
    assert v3.record_path(encoded).read_bytes() == before

    # A corrupt existing completed capsule must never be silently skipped.
    corrupted = deepcopy(capsule)
    corrupted["record"]["levels"][0]["graph6"] = "tampered"
    v2.atomic(v3.record_path(encoded), corrupted)
    with pytest.raises(ValueError, match="actual pared clique iterate"):
        v3.import_v2()


@pytest.mark.parametrize(
    "bad_index",
    [None, True, "2317572", 99999999, 2318241],
)
@pytest.mark.parametrize("status", ["TIMEOUT", "ERROR"])
def test_terminal_capsule_requires_source_index_matching_graph6(
    monkeypatch, status, bad_index
):
    index = 2317572
    encoded = v3.index_to_graph6()[index]
    good = {
        "schema": v3.SCHEMA,
        "graph6": encoded,
        "status": status,
        "origin": "v3_worker",
        "index": index,
    }
    v3.verify_capsule(good, encoded)
    bad = dict(good, index=bad_index)
    with pytest.raises(ValueError, match="terminal worker index/provenance"):
        v3.verify_capsule(bad, encoded)
    del bad["index"]
    with pytest.raises(ValueError, match="terminal worker index/provenance"):
        v3.verify_capsule(bad, encoded)


def test_import_v2_rejects_bad_terminal_instead_of_overwriting(
    tmp_path, monkeypatch
):
    source_stage = tmp_path / "frozen-v2"
    target_stage = tmp_path / "new-v3"
    monkeypatch.setattr(v3, "V2_STAGE", source_stage)
    monkeypatch.setattr(v3, "STAGE", target_stage)
    monkeypatch.setattr(v2, "root_dir", lambda _order: source_stage)
    index = 2317572
    encoded = v3.index_to_graph6()[index]
    monkeypatch.setattr(v3, "index_to_graph6", lambda: {index: encoded})
    v2.require_manifest(10)
    v3.require_stage()  # Existing worker files require the frozen v3 manifest.
    original = v2.analyze(index, encoded, source_stage)
    v2.atomic(v3.v2_source_path(index), original)
    terminal = {
        "schema": v3.SCHEMA,
        "graph6": encoded,
        "origin": "v3_worker",
        "status": "TIMEOUT",
        "index": 2318241,
    }
    v2.atomic(v3.record_path(encoded), terminal)
    with pytest.raises(ValueError, match="terminal worker index/provenance"):
        v3.import_v2()
    assert v3.read(v3.record_path(encoded)) == terminal
