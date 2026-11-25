"""Independently certify exactly two ten-v26 -> ten-v27 divergent promotions.

Replay the permanent 216-vertex P3 -> O11 retraction and the independent
complete P3 isomorphism of the second original. Neither bounded search
status nor any candidate-specific obstruction is used for promotions.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("Do not optimize away census certification assertions")

from research.order10_p4_crossdepth_o15_v25.verify import git_blob, source_rows
from research.order10_five_p3_native_v1.verify_positive import (
    ORIGINAL, OTHER_ORIGINAL, verify_positive,
)

ROOT = Path(__file__).resolve().parents[2]
BEFORE = ROOT / "indeterminate_order_10_v26.txt"
LATEST = ROOT / "indeterminate_order_10_v27.txt"
WORKING = ROOT / "indeterminate_order_10.txt"
NINE = ROOT / "indeterminate_order_9.txt"
NINE_FROZEN = ROOT / "indeterminate_order_9_v9.txt"

ORIGINAL_V26_BLOB = "6a61df2e6b68ca2229cb94667cfa932fb5b5d73f"
ORIGINAL_NINE_V9_BLOB = "d18a7a843be935f3a7fe911691dd1c86dac2addd"
EXPECTED_REMOVALS = (11656793, 11658674)
ORIGINAL_GRAPH6 = {
    11656793: r"IErtv\}~O",
    11658674: r"IEzTmvm^o",
}
EXPECTED_BEFORE_COUNTS = {9: 430, 10: 616}
EXPECTED_AFTER_COUNTS = {9: 430, 10: 614}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise AssertionError(reason)


def audit_nine_v9(active: bytes, frozen: bytes) -> None:
    """Authenticate both the immutable nine-v9 catalog and working root."""
    require(git_blob(frozen) == ORIGINAL_NINE_V9_BLOB,
            "Historical nine-v9 source Git blob changed")
    require(active == frozen,
            "Nine-v9 canonical census root differs from certified snapshot")


def audit_rows(
    before: dict[int, str], after: dict[int, str], certified: set[int]
) -> None:
    """No modified records, spurious additions, or unproved removals."""
    require(len(before) == 1046 and len(after) == 1044,
            "Wrong original graph counts at ten-v26 -> ten-v27")
    require(certified == set(EXPECTED_REMOVALS),
            "Divergent certificates did not cover exactly two originals")
    require(set(before) - set(after) == certified
            and not (set(after) - set(before)),
            "An uncertified original was deleted or a new original inserted")
    require(all(before[i] == after[i] for i in after),
            "A retained indeterminate graph6 or census row was altered")
    require(list(after) == sorted(after), "New snapshot lost canonical McKay order")
    for index in EXPECTED_REMOVALS:
        require(before[index] ==
                f"{index} 10 {ORIGINAL_GRAPH6[index]} - - -",
                f"Promoted original McKay {index} has incorrect frozen graph6")
    counts = lambda rows: dict(Counter(
        int(row.split()[1]) for row in rows.values()
    ))
    require(counts(before) == EXPECTED_BEFORE_COUNTS,
            "Original ten-v26 population composition changed")
    require(counts(after) == EXPECTED_AFTER_COUNTS,
            "New ten-v27 population composition changed")


def verify() -> dict:
    require(git_blob(BEFORE.read_bytes()) == ORIGINAL_V26_BLOB,
            "Historical ten-v26 source Git blob changed")
    require(WORKING.read_bytes() == LATEST.read_bytes(),
            "Active ten-vertex census root differs from certified v27")
    audit_nine_v9(NINE.read_bytes(), NINE_FROZEN.read_bytes())
    before = source_rows(BEFORE)
    after = source_rows(LATEST)

    # Full permanent proof replay, independent of native C++ solver or
    # archived search FOUND claims, checks all 19663 P3 source edges,
    # every O11 target edge/nonedge, and the complete second P3 bijection.
    proof = verify_positive()
    proved = set(proof["divergent_original_indices"])
    require(proof["ordinary_retraction_proved"] is True
            and proof["original_K_divergent"] is True
            and proof["p3_isomorphism_checked_on_all_pairs"] is True
            and proof["target"] == "O11"
            and proof["original_mckay"] == ORIGINAL
            and proof["second_original_by_exact_p3_isomorphism"] == OTHER_ORIGINAL,
            "Permanent O11 positive proof schema or certificate changed")
    audit_rows(before, after, proved)

    return {
        "schema": 1,
        "kind": "ten_v26_to_v27_two_independent_P3_O11_divergences",
        "previous_snapshot": BEFORE.name,
        "previous_git_blob": ORIGINAL_V26_BLOB,
        "new_snapshot": LATEST.name,
        "population": {
            "before": 1046,
            "after": 1044,
            "removed": 2,
            "nine_vertex_pared_cores_unchanged": 430,
            "stiff_ten_vertex_before": 616,
            "stiff_ten_vertex_after": 614,
        },
        "proved_divergent_original_indices": list(EXPECTED_REMOVALS),
        "direct_third_iterate_octahedral_retraction": ORIGINAL,
        "other_original_by_exact_p3_isomorphism": OTHER_ORIGINAL,
        "other_oversized_P3_classes_still_unresolved": [
            11505012, 11595632, 11709142, 11713984,
        ],
        "indeterminate_nine_originals_unchanged": 3,
        "no_negative_inference_from_limited_search": True,
    }


def main() -> None:
    import json
    result = verify()
    print(json.dumps(result, sort_keys=True, indent=2))
    print("PASS: exactly two ten-v26 originals promoted by independently "
          "replayed P3-to-O11 retraction and complete P3 isomorphism")


if __name__ == "__main__":
    main()
