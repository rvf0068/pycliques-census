"""Audit every archived discovery batch against the independently checked proofs.

This is intentionally separate from the raw graph-retraction verifier. CI
must run both programs. Every saved PROOF_JSON is an exact copy of one map
that the raw-iterate verifier reconstructs and validates edge by edge.
The interrupted batch 3 cannot be advertised as an exhaustive negative run.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
V9 = ROOT / "indeterminate_order_10_v9.txt"
CERTS = HERE / "certificates.json"
BATCHES = HERE / "batches"
V9_BLOB = "704219076c6d61b595374cd129c5fa520253a089"
RUN_ID = 44847590866
JOBS = {
    0: 136671003299, 1: 136671003372,
    2: 136671003087, 3: 136671003287,
    4: 136671003434, 5: 136671003429,
    6: 136671003257, 7: 136671003263,
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def source_cohort() -> list[int]:
    raw = V9.read_bytes()
    blob = hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()
    require(blob == V9_BLOB, "Frozen source v9 changed")
    cohort = [
        int(fields[0])
        for line in raw.decode("utf-8").splitlines()
        if line and not line.startswith("#")
        for fields in [line.split()]
        if fields[1] == "10" and fields[3:] == ["-", "-", "-"]
    ]
    require(len(cohort) == 1393 and cohort == sorted(cohort),
            "Unexpected frozen fully-unclassified ten-core cohort")
    return cohort


def audit(source: list[int], proofs: list[dict],
          archives: dict[int, dict], corrected: dict) -> dict:
    require(len(archives) == 8 and set(archives) == set(range(8)),
            "All eight batch records must be present")
    proof_by_id = {p["index"]: p for p in proofs}
    require(len(proof_by_id) == len(proofs),
            "Duplicate consolidated proof")
    claimed = set()
    for batch in range(8):
        item = archives[batch]
        partial = batch == 3
        require(
            item.get("schema") == 1 and item.get("run_id") == RUN_ID
            and item.get("job_id") == JOBS[batch]
            and item.get("batch") == batch
            and type(item.get("proofs")) is list,
            "Invalid archived batch identity or proof list"
        )
        if partial:
            require(item.get("partial") is True
                    and "summary" not in item
                    and len(item["proofs"]) == 36
                    and isinstance(item.get("note"), str),
                    "Runner-shutdown batch 3 must remain marked partial")
        else:
            require(item.get("partial") is None
                    and type(item.get("summary")) is dict,
                    "Complete batch has invalid or missing summary")
            summary = item["summary"]
            require(
                summary.get("batch") == batch
                and summary.get("batches") == 8
                and summary.get("input") == len(source[batch::8])
                and summary.get("positive") == len(item["proofs"])
                and type(summary.get("examined")) is int
                and 0 <= summary["examined"] <= summary["input"]
                and summary.get("skipped_error") == 0,
                "Historic batch summary or positive count is inconsistent")
        allowed = set(source[batch::8])
        seen = set()
        for row in item["proofs"]:
            idx = row["index"]
            require(idx in allowed and idx not in seen and idx not in claimed,
                    "Batch proof duplicate or not in frozen source slice")
            require(proof_by_id.get(idx) == row,
                    "Archived positive map differs from the map"
                    " independently checked by raw retraction replay")
            seen.add(idx)
        claimed |= seen
    # The independent fixed-code rerun successfully finished batch 3.
    # Its two additional maps supplement the original interrupted 36.
    require(
        corrected.get("schema") == 1
        and corrected.get("run_id") == 44848083302
        and corrected.get("job_id") == 136672634498
        and corrected.get("batch") == 3
        and type(corrected.get("proofs")) is list,
        "Invalid provenance for corrected batch 3"
    )
    summary = corrected["summary"]
    require(
        summary.get("batch") == 3
        and summary.get("batches") == 8
        and summary.get("input") == len(source[3::8])
        and summary.get("examined") == summary["input"]
        and summary.get("positive") == len(corrected["proofs"]) == 38
        and summary.get("skipped_error") == 0,
        "Corrected batch 3 did not finish with the recorded count"
    )
    old_partial = {
        p["index"]: p for p in archives[3]["proofs"]
    }
    corrected_by_id: dict[int, dict] = {}
    allowed_corrected = set(source[3::8])
    for row in corrected["proofs"]:
        idx = row["index"]
        require(idx in allowed_corrected and idx not in corrected_by_id,
                "Duplicate or out-of-cohort corrected proof")
        require(proof_by_id.get(idx) == row,
                "Corrected run map differs from the independently"
                " verified complete retraction")
        corrected_by_id[idx] = row
    require(all(corrected_by_id.get(idx) == p
                for idx, p in old_partial.items()),
            "A previously certified partial-batch map disappeared")
    additional = set(corrected_by_id) - set(old_partial)
    require(additional == {11638656, 11652579},
            "Unexpected corrected-run additions")
    require(claimed | set(corrected_by_id) == set(proof_by_id),
            "Consolidated proofs lack a matching archived batch record")
    return {
        "original_batch_files": len(archives),
        "corrected_batch3_files": 1,
        "partially_completed_original_batches": 1,
        "original_positive_maps": len(claimed),
        "additional_corrected_positive_maps": len(additional),
        "total_independently_verified_positive_maps": len(proof_by_id),
    }


def main() -> None:
    cohort = source_cohort()
    document = json.loads(CERTS.read_text(encoding="utf-8"))
    require(document["schema"] == 1 and document["iterate"] == 3
            and document["source"] == V9.name
            and type(document["proofs"]) is list,
            "Consolidated certificate format changed")
    archives = {}
    for i in range(8):
        filename = f"batch{i}_partial.json" if i == 3 else f"batch{i}.json"
        archives[i] = json.loads(
            (BATCHES / filename).read_text(encoding="utf-8")
        )
    corrected = json.loads(
        (BATCHES / "batch3_corrected.json").read_text(encoding="utf-8")
    )
    result = audit(cohort, document["proofs"], archives, corrected)

    # Regression mutations: corrupting any archived map or batch summary
    # must be detected even if the verified canonical proofs are untouched.
    damaged = copy.deepcopy(archives)
    damaged[5]["proofs"][0]["projection"][0] = -1234
    try:
        audit(cohort, document["proofs"], damaged, corrected)
    except ValueError:
        pass
    else:
        raise AssertionError("Mutation of archived batch-5 map went undetected")
    damaged = copy.deepcopy(archives)
    damaged[5]["summary"]["positive"] += 1
    try:
        audit(cohort, document["proofs"], damaged, corrected)
    except ValueError:
        pass
    else:
        raise AssertionError("Mutation of batch-5 positive count went undetected")
    damaged = copy.deepcopy(corrected)
    damaged["proofs"][-1]["projection"][0] = -1234
    try:
        audit(cohort, document["proofs"], archives, damaged)
    except ValueError:
        pass
    else:
        raise AssertionError("Mutation of corrected batch-3 map undetected")
    print(json.dumps(result, sort_keys=True))
    print("VERIFIED: every batch positive equals one complete, independently"
          " replayed raw K³-to-O_d certificate; no negative claim inferred.")


if __name__ == "__main__":
    main()
