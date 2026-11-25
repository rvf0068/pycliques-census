"""Independently certify exactly six ten-v25 -> ten-v26 divergent promotions.

The five positive P3 -> O_d retractions and the sixth original's complete
P3 isomorphism are replayed from immutable PR #100 certificates. Resource
limits and failed searches are never grounds for a census promotion.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("Do not optimize away census certification assertions")

from research.order10_p4_crossdepth_o15_v25.verify import (
    git_blob, source_rows,
)
from research.order10_overcap_p3_coaffine_v1.verify_positives import (
    EXPECTED, PROMOTABLE_ORIGINALS, replay_positive_witnesses,
)

ROOT = Path(__file__).resolve().parents[2]
BEFORE = ROOT / "indeterminate_order_10_v25.txt"
LATEST = ROOT / "indeterminate_order_10_v26.txt"
WORKING = ROOT / "indeterminate_order_10.txt"
NINE = ROOT / "indeterminate_order_9.txt"
NINE_FROZEN = ROOT / "indeterminate_order_9_v9.txt"
ORIGINAL_V25_BLOB = "d31d52d28427adcef6055cc1d277565fe88f32d5"
EXPECTED_REMOVALS = (
    11367777, 11611429, 11623375,
    11651749, 11708546, 11713770,
)
ORIGINAL_GRAPH6 = {
    11367777: r"ICrVL^y^W",
    11611429: r"IEhvtznno",
    11623375: r"IEjbtnN~_",
    11651749: r"IEnb}~{|W",
    11708546: r"IQyuvj}^o",
    11713770: r"IQzTvzu]w",
}
EXPECTED_BEFORE_COUNTS = {9: 430, 10: 622}
EXPECTED_AFTER_COUNTS = {9: 430, 10: 616}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise AssertionError(reason)


def audit_rows(
    before: dict[int, str],
    after: dict[int, str],
    certified_indices: set[int],
) -> None:
    """Reject extra removals, changed retained rows and unproved promotions."""
    require(len(before) == 1052 and len(after) == 1046,
            "Wrong original graph counts at ten-v25 -> ten-v26")
    require(certified_indices == set(EXPECTED_REMOVALS)
            and set(EXPECTED_REMOVALS) == set(PROMOTABLE_ORIGINALS),
            "Divergent certificates did not cover exactly six originals")
    require(set(before) - set(after) == certified_indices
            and not (set(after) - set(before)),
            "An uncertified original was deleted or a new original inserted")
    require(all(before[i] == after[i] for i in after),
            "A retained indeterminate graph6 or census row was altered")
    require(list(after) == sorted(after), "New snapshot lost canonical McKay order")
    for i in EXPECTED_REMOVALS:
        require(before[i] == f"{i} 10 {ORIGINAL_GRAPH6[i]} - - -",
                f"Promoted original McKay {i} does not match frozen graph6")
    def count_orders(rows: dict[int, str]) -> dict[int, int]:
        return dict(Counter(int(row.split()[1]) for row in rows.values()))
    require(count_orders(before) == EXPECTED_BEFORE_COUNTS,
            "Original ten-v25 population composition changed")
    require(count_orders(after) == EXPECTED_AFTER_COUNTS,
            "New ten-v26 population composition changed")


def verify() -> dict:
    require(git_blob(BEFORE.read_bytes()) == ORIGINAL_V25_BLOB,
            "Historical ten-v25 source Git blob changed")
    require(WORKING.read_bytes() == LATEST.read_bytes(),
            "Active ten-vertex census root differs from certified v26")
    require(NINE.read_bytes() == NINE_FROZEN.read_bytes(),
            "Nine-v9 canonical census root was modified")
    before = source_rows(BEFORE)
    after = source_rows(LATEST)

    # Independent complete graph certificates, not the native solver's
    # claimed FOUND status, establish the precise source indices.
    proof = replay_positive_witnesses()
    proved = set(proof["divergent_original_indices"])
    require(proof["positive_p3_retraction_count"] == 5
            and proof["exact_p3_isomorphic_originals"] == 1
            and len(proof["records"]) == 6,
            "Unexpected PR100 positive proof schema or number of proofs")
    audit_rows(before, after, proved)
    require(set(EXPECTED) | {11651749} == proved,
            "Promoted six are not exactly five O_d + one P3-class member")
    summary = {
        "schema": 1,
        "kind": "ten_v25_to_v26_six_independent_octahedral_p3_divergence_proofs",
        "previous_snapshot": BEFORE.name,
        "previous_git_blob": ORIGINAL_V25_BLOB,
        "new_snapshot": LATEST.name,
        "population": {
            "before": 1052,
            "after": 1046,
            "removed": 6,
            "nine_vertex_pared_cores_unchanged": 430,
            "stiff_ten_vertex_before": 622,
            "stiff_ten_vertex_after": 616,
        },
        "proved_divergent_original_indices": list(EXPECTED_REMOVALS),
        "direct_third_iterate_octahedral_retractions": sorted(EXPECTED),
        "other_original_by_exact_p3_isomorphism": 11651749,
        "further_oversized_P3_classes_still_unresolved": [
            11505012, 11595632, 11656793, 11709142, 11713984,
        ],
        "indeterminate_nine_originals_unchanged": 3,
        "no_negative_inference_from_limited_search": True,
    }
    return summary


def main() -> None:
    import json
    result = verify()
    print(json.dumps(result, sort_keys=True, indent=2))
    print("PASS: six and only six original ten-v25 graphs promoted by full "
          "ordinary octahedral retractions at P3 and exact P3 isomorphism")


if __name__ == "__main__":
    main()
