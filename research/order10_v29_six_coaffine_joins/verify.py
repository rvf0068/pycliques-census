"""Independent exact six-original K-divergence promotion from ten-v28 to ten-v29.

No historical archives or evidence are changed. Four source complete P3
coaffine power maps and two P1 coaffine joins are independently rebuilt
from the ORIGINAL connected ten-vertex graph6 using existing proof code.
Only their exact six six-column records may be removed from the v28 list.
The 430 nine-core dependents and all other stiff originals stay unchanged.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("Do not optimize away exact ten-v29 proof assertions")

import networkx as nx

from research.order10_p4_crossdepth_o15_v25.verify import git_blob, source_rows
from research.order10_v28_p1_coaffine_join_v1 import verify_permanent as p1
from research.order10_v28_p3_coaffine_all_v1 import verify_positives as p3

ROOT = Path(__file__).resolve().parents[2]
BEFORE = ROOT / "indeterminate_order_10_v28.txt"
LATEST = ROOT / "indeterminate_order_10_v29.txt"
WORKING = ROOT / "indeterminate_order_10.txt"
NINE = ROOT / "indeterminate_order_9.txt"
NINE_FROZEN = ROOT / "indeterminate_order_9_v9.txt"

ORIGINAL_V28_BLOB = "35bb83b56bb8b4fd453b0ba272d354dc6b42e68c"
ORIGINAL_NINE_V9_BLOB = "d18a7a843be935f3a7fe911691dd1c86dac2addd"
P1_REMOVALS = (11715667, 11716441)
P3_REMOVALS = (10481909, 10586728, 11438191, 11578321)
EXPECTED_REMOVALS = tuple(sorted(P1_REMOVALS + P3_REMOVALS))
EXPECTED_GRAPH6 = {
    10481909: "ICZTfX}}o",
    10586728: "ICZelxz~_",
    11438191: "ICrdvp}|o",
    11578321: "IEhtrnksw",
    11715667: "IUZu~r|zo",
    11716441: "IUzvrz}zo",
}
BEFORE_COUNTS = {9: 430, 10: 613}
AFTER_COUNTS = {9: 430, 10: 607}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def audit_nine(active: bytes, frozen: bytes) -> None:
    require(git_blob(frozen) == ORIGINAL_NINE_V9_BLOB,
            "Historical nine-v9 source Git blob changed")
    require(active == frozen, "Nine-v9 working root differs from frozen index")


def audit_rows(
    before: dict[int, str], after: dict[int, str], certified: set[int],
) -> None:
    require(len(before) == 1043 and len(after) == 1037,
            "Wrong ten-v28/ten-v29 original counts")
    require(certified == set(EXPECTED_REMOVALS),
            "Exactly six independently certified originals must be removed")
    require(set(before) - set(after) == certified
            and not (set(after) - set(before)),
            "An uncertified original was deleted or a new original inserted")
    require(all(after[i] == before[i] for i in after),
            "A retained six-column record was changed")
    require(list(before) == sorted(before) and list(after) == sorted(after),
            "Canonical McKay original ordering changed")
    for index, g6 in EXPECTED_GRAPH6.items():
        require(before.get(index) == f"{index} 10 {g6} - - -",
                f"Wrong original McKay {index} graph6 or pared order")
    def counts(rows: dict[int, str]) -> dict[int, int]:
        return dict(Counter(int(line.split()[1]) for line in rows.values()))
    require(counts(before) == BEFORE_COUNTS,
            "Wrong frozen ten-v28 pared-order composition")
    require(counts(after) == AFTER_COUNTS,
            "Wrong certified ten-v29 pared-order composition")


def verify_p3_from_immutable_originals(
    frozen: dict[int, str],
) -> dict:
    """Replay the four historical permanent full maps, without its old root alias.

    Reuse the exact independent source constructor, complete edge audit,
    finite-power retraction, factor coaffinations, and full graph-level
    isomorphism checks from the previously merged historical proof.
    """
    require(git_blob(p3.SOURCE.read_bytes()) == p3.SOURCE_BLOB
            and p3.SOURCE == BEFORE
            and git_blob(p3.HISTORICAL_INDEX.read_bytes())
                == p3.HISTORICAL_INDEX_BLOB,
            "Four-P3 historical source identity or exact class archive changed")
    certificate = json.loads(p3.CERTIFICATE.read_text(encoding="utf-8"))
    require(certificate.get("schema") == 1
            and certificate.get("kind") ==
                "four_exact_P3_coaffine_power_retractions_onto_connected_coaffine_joins"
            and certificate.get("source_git_blob") == ORIGINAL_V28_BLOB
            and certificate.get("frozen_exact_p3_class_blob") ==
                p3.HISTORICAL_INDEX_BLOB
            and certificate.get("historical_positive_workflow_run") ==
                45745202885
            and certificate.get("limits_are_not_negative_proofs") is True,
            "An original P3 positive source certificate changed")
    entries = certificate["positives"]
    require(tuple(row["original_index"] for row in entries) ==
            P3_REMOVALS,
            "Exactly four P3 positive McKay original identities required")
    proof_rows = []
    targets = []
    originals = {i: row.split()[2] for i, row in frozen.items()
                 if row.split()[1] == "10"}
    for entry in entries:
        index = entry["original_index"]
        require(index in originals
                and entry["original_graph6"] == EXPECTED_GRAPH6[index]
                and frozen[index] == (
                    f"{index} 10 {entry['original_graph6']} - - -"
                ), "A P3 original identity is not the frozen ten-v28 record")
        proof, Y = p3.check_positive(entry, originals)
        require(proof["original_index"] == index
                and proof["original_K_divergent"] is True
                and proof["full_endomorphism_verified_on_every_edge"] is True
                and proof["ordinary_graph_retraction_verified_on_every_edge"]
                    is True
                and proof["retract"]["image_expansive_and_K_divergent"] is True
                and proof["retract"]["coaffine_factors_invariant_and_automorphic"]
                    is True
                and proof["retract"]["complete_join_cross_edges"] is True,
                "Third-iterate full retraction or published expansivity proof failed")
        proof_rows.append(proof)
        targets.append(Y)
    require(all(nx.is_isomorphic(targets[0], targets[j]) for j in (1, 3)),
            "Three certified 17-vertex expansive stable images are not isomorphic")
    return {
        "proof_indices": [x["original_index"] for x in proof_rows],
        "independently_replayed_full_coaffine_power_retractions": 4,
        "three_17_vertex_retracts_isomorphic": True,
        "verified_complete_proofs": proof_rows,
    }


def verify() -> dict:
    require(git_blob(BEFORE.read_bytes()) == ORIGINAL_V28_BLOB,
            "Immutable ten-v28 input Git blob differs")
    require(WORKING.read_bytes() == LATEST.read_bytes(),
            "Current ten-original working root must equal certified ten-v29")
    audit_nine(NINE.read_bytes(), NINE_FROZEN.read_bytes())

    frozen = source_rows(BEFORE)
    current = source_rows(LATEST)

    # Both separate proof archives were merged before this transition.
    # This deliberately runs full proofs; no historical solver-search
    # status or indefinite CLI artifact is trusted as a divergence proof.
    p1_proof = p1.verify()
    require(tuple(p1_proof["originals_proven_K_divergent"]) ==
            P1_REMOVALS
            and p1_proof["all_original_P1s_independently_reconstructed"]
                is True
            and p1_proof["two_P1_targets_exactly_isomorphic"] is True
            and all(q["original_K_divergent"] is True
                    and q["published_theorem"].endswith("Theorem 3.6")
                    for q in p1_proof["complete_positive_proofs"]),
            "The two complete P1 coaffine-join proofs were not replayed")
    p3_proof = verify_p3_from_immutable_originals(frozen)
    proved = set(p1_proof["originals_proven_K_divergent"]) | set(
        p3_proof["proof_indices"]
    )
    audit_rows(frozen, current, proved)
    return {
        "schema": 1,
        "kind": "ten_v28_to_v29_six_independent_coaffine_join_divergences",
        "frozen_before": BEFORE.name,
        "frozen_before_git_blob": ORIGINAL_V28_BLOB,
        "new_snapshot": LATEST.name,
        "population": {
            "before": 1043, "after": 1037, "removed": 6,
            "nine_pared_originals_unchanged": 430,
            "stiff_ten_before": 613, "stiff_ten_after": 607,
        },
        "proved_K_divergent_originals": list(EXPECTED_REMOVALS),
        "P1_expansive_O2_join_originals": list(P1_REMOVALS),
        "P3_expansive_coaffine_power_retraction_originals": list(P3_REMOVALS),
        "positive_11_vertex_retracts_replayed": 2,
        "positive_P3_full_maps_replayed": 4,
        "retained_rows_verbatim": True,
        "nine_v9_working_and_frozen_index_unchanged": True,
        "no_indeterminate_original_promoted_by_negative_search": True,
    }


def main() -> None:
    print(json.dumps(verify(), sort_keys=True, indent=2))
    print("PASS: exactly six independently certified ten-v29 original "
          "K-divergences with immutable ten-v28 and nine-v9 indexes",
          flush=True)


if __name__ == "__main__":
    main()
