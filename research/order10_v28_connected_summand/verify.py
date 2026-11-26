"""Independently certify exactly one ten-v27 -> ten-v28 positive promotion.

The source is a full ordinary retraction from P3 of McKay 11713984 onto
O14 joined with complement(C7). Both factor coaffinations are independently
verified and the Connected Summand Theorem 4.6 proves K-divergence.
No bounded search result or large finite iterate alone certifies divergence.
Historical v27 and all other census snapshots remain immutable.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("Do not optimize away census certification assertions")

from research.order10_p4_crossdepth_o15_v25.verify import git_blob, source_rows
from research.order10_11713984_coaffine_retract_v1.verify import (
    ORIGINAL, SOURCE_G6, verify as verify_connected_summand,
)

ROOT = Path(__file__).resolve().parents[2]
BEFORE = ROOT / "indeterminate_order_10_v27.txt"
LATEST = ROOT / "indeterminate_order_10_v28.txt"
WORKING = ROOT / "indeterminate_order_10.txt"
NINE = ROOT / "indeterminate_order_9.txt"
NINE_FROZEN = ROOT / "indeterminate_order_9_v9.txt"

ORIGINAL_V27_BLOB = "a2a1fdbb7a83a4e2d6a7b7e695c5edd601d0cc78"
ORIGINAL_NINE_V9_BLOB = "d18a7a843be935f3a7fe911691dd1c86dac2addd"
EXPECTED_REMOVALS = (11713984,)
EXPECTED_BEFORE_COUNTS = {9: 430, 10: 614}
EXPECTED_AFTER_COUNTS = {9: 430, 10: 613}


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError(reason)


def audit_nine(active: bytes, frozen: bytes) -> None:
    """Two independent provenance conditions, not only mutable equality."""
    require(git_blob(frozen) == ORIGINAL_NINE_V9_BLOB,
            "Historical nine-v9 source Git blob changed")
    require(active == frozen,
            "Nine-v9 working root differs from the frozen certified catalog")


def audit_rows(
    before: dict[int, str], after: dict[int, str], certified: set[int]
) -> None:
    """Require an exact one-record deletion, no changed or reordered rows."""
    require(len(before) == 1044 and len(after) == 1043,
            "Wrong original graph counts at ten-v27 -> ten-v28")
    require(certified == set(EXPECTED_REMOVALS),
            "Positive certificate did not cover exactly one original")
    require(set(before) - set(after) == certified
            and not (set(after) - set(before)),
            "An uncertified original was deleted or an original inserted")
    require(all(before[i] == after[i] for i in after),
            "A retained indeterminate census row was altered")
    require(list(before) == sorted(before) and list(after) == sorted(after),
            "McKay index order changed")
    require(before[ORIGINAL] == f"{ORIGINAL} 10 {SOURCE_G6} - - -",
            "Promoted original McKay index or graph6 is incorrect")

    count = lambda rows: dict(Counter(
        int(row.split()[1]) for row in rows.values()
    ))
    require(count(before) == EXPECTED_BEFORE_COUNTS,
            "Historical ten-v27 population composition changed")
    require(count(after) == EXPECTED_AFTER_COUNTS,
            "New ten-v28 population composition changed")


def verify() -> dict:
    require(git_blob(BEFORE.read_bytes()) == ORIGINAL_V27_BLOB,
            "Historical ten-v27 source Git blob changed")
    require(WORKING.read_bytes() == LATEST.read_bytes(),
            "Active ten-vertex census root differs from certified v28")
    audit_nine(NINE.read_bytes(), NINE_FROZEN.read_bytes())

    before = source_rows(BEFORE)
    after = source_rows(LATEST)

    # Permanently replay the source P3 graph6 and 169-coordinate map,
    # the coaffine morphism and its ordinary 14th-power retraction,
    # both coaffine join factors, and the exact Theorem 4.6 hypotheses.
    proof = verify_connected_summand()
    connected = proof["connected_summand_certificate"]
    require(proof["original_index"] == ORIGINAL
            and proof["original_K_divergent"] is True
            and proof["coaffine_weak_endomorphism_verified_on_all_edges"] is True
            and proof["ordinary_retraction_from_fourteenth_power_verified_on_all_edges"] is True
            and proof["retraction_image"] == {
                "vertices": 35, "edges": 574,
                "isomorphic_to": "O14_join_complement_C7",
            }
            and connected["theorem_name"] ==
                "Neumann-Lara Connected Summand Theorem"
            and connected["coaffine_octahedral_factor_dimension"] == 14
            and connected["connected_coaffine_factor"] == "complement_C7"
            and connected["both_coaffinations_verified_on_all_pairs"] is True
            and connected["expansive_retract"] is True
            and connected["original_K_divergent_by_ordinary_retraction_and_paring"] is True,
            "Positive complete retraction or connected-summand theorem changed")

    audit_rows(before, after, {proof["original_index"]})
    return {
        "schema": 1,
        "kind": "ten_v27_to_v28_connected_summand_one_original_divergence",
        "previous_snapshot": BEFORE.name,
        "previous_git_blob": ORIGINAL_V27_BLOB,
        "new_snapshot": LATEST.name,
        "population": {
            "before": 1044, "after": 1043, "removed": 1,
            "nine_vertex_pared_cores_unchanged": 430,
            "stiff_ten_vertex_before": 614,
            "stiff_ten_vertex_after": 613,
        },
        "proved_divergent_original_indices": list(EXPECTED_REMOVALS),
        "retraction_target": "O14_join_complement_C7",
        "divergence_theorem": "Larrión--Neumann-Lara--Pizaña 2009 Theorem 4.6",
        "other_oversized_P3_classes_still_unresolved": [
            11505012, 11595632, 11709142,
        ],
        "indeterminate_nine_originals_unchanged": 3,
        "no_negative_inference_from_limited_search": True,
    }


def main() -> None:
    import json
    print(json.dumps(verify(), sort_keys=True, indent=2))
    print("PASS: exact one-original ten-v28 promotion by independently "
          "replayed 35-vertex retraction and Connected Summand Theorem 4.6")


if __name__ == "__main__":
    main()
