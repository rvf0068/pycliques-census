"""Build and verify a CURRENT order-10 unresolved list from independently certified cores.

The historical initial and v3 lists are immutable. Six nine-vertex stiff
core classes have already been proven K-divergent by replayable certificates:
two special-O4 core lifts (133 originals) and four separate historical core
lifts (167 originals). The complete proof mechanisms and each original
dominated-fold/isomorphism map are replayed by the accompanying CI workflow.

This script only reconciles EXACT saved original indices and class memberships;
it does not infer convergence/divergence from failed searches, homology,
conjectured snub dependencies, or graph6 string equality.
"""
from __future__ import annotations

import argparse
import csv
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "indeterminate_order_10_v3.txt"
CLASS_INDEX = "reports/order10_core_index_v1/classes.tsv"
OLD_CERTIFICATES = "reports/order10_special_octahedron_core_lift_v1/members.tsv"
OUTPUT = "indeterminate_order_10_v4.txt"
PROVEN_INDEX = "research/order10_current_indeterminates_v4/certified_divergent.tsv"
SUMMARY = "research/order10_current_indeterminates_v4/summary.md"

# Frozen theorem-backed core proofs, independently reconstructed by CI.
# (core graph6, original members, provenance)
PROOFS: dict[int, tuple[str, int, str]] = {
    6938923: ("HEht}pl", 23, "special_O4_core_lift_v1"),
    6939350: ("HEht~bl", 110, "special_O4_core_lift_v1"),
    7454135: ("HEnb~jl", 61, "historical_raw_K3_special_O7"),
    9678187: ("HQyuzpt", 37, "historical_raw_K3_special_O4"),
    10768817: ("HUZ~v~}", 33, "historical_coaffine_suspension"),
    11363569: ("HUzrv~}", 36, "historical_coaffine_suspension"),
}
OLD_CORES = frozenset((6938923, 6939350))


def tsv(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(StringIO(text), delimiter="\t"))


def generate(root: Path = ROOT) -> dict[str, bytes]:
    """Construct all v4 artifacts, rejecting any source/provenance change."""
    source_text = (root / SOURCE).read_text(encoding="utf-8")
    head, *rest = source_text.splitlines()
    if head != "# Order-10 unresolved cases, after independently verified v3 positives":
        raise ValueError("Unexpected frozen v3 unresolved source")
    if not rest or rest[0] != "# Remaining=8533 v3_proven=115":
        raise ValueError("Expected the frozen v3 8,533-case population")
    lines = [line for line in source_text.splitlines() if line and not line.startswith("#")]
    source_rows = {}
    for line in lines:
        fields = line.split()
        if len(fields) != 6 or not fields[0].isdecimal() or not fields[1].isdecimal():
            raise ValueError("Malformed original index or record")
        idx = int(fields[0])
        if idx in source_rows:
            raise ValueError("Repeated original index in v3 unresolved source")
        source_rows[idx] = line
    if len(source_rows) != 8533:
        raise ValueError("Incorrect frozen v3 row count")

    classes = tsv((root / CLASS_INDEX).read_text(encoding="utf-8"))
    if len(classes) != 2439:
        raise ValueError("Changed frozen core-class population")
    members_by_core: dict[int, list[int]] = {}
    all_member_ids: set[int] = set()
    for row in classes:
        core_id = int(row["core_id"])
        if core_id in members_by_core:
            raise ValueError("Repeated core identifier")
        indices = [int(v) for v in row["member_indices"].split(",")]
        if (
            len(indices) != int(row["members"])
            or len(indices) != len(set(indices))
            or any(i in all_member_ids for i in indices)
        ):
            raise ValueError("Incorrect or overlapping core membership")
        all_member_ids.update(indices)
        members_by_core[core_id] = indices
        if core_id in PROOFS:
            encoded, expected, _reason = PROOFS[core_id]
            if (
                row["core_order"] != "9"
                or row["core_graph6"] != encoded
                or len(indices) != expected
                or min(indices) != core_id
                or int(row["conjectured_members"]) != 0
            ):
                raise ValueError(f"Saved proven core does not match certificate {core_id}")
    if all_member_ids != set(source_rows):
        raise ValueError("Core index does not cover precisely the v3 unresolved indices")

    old_rows = tsv((root / OLD_CERTIFICATES).read_text(encoding="utf-8"))
    expected_old = {
        index: core_id for core_id in OLD_CORES
        for index in members_by_core[core_id]
    }
    actual_old = {}
    for row in old_rows:
        index = int(row["index"])
        core_id = int(row["core_id"])
        if index in actual_old or core_id not in OLD_CORES:
            raise ValueError("Invalid duplicate or non-O4 positive certificate")
        if row["core_graph6"] != PROOFS[core_id][0]:
            raise ValueError("Positive source graph6 does not match core proof")
        actual_old[index] = core_id
    if actual_old != expected_old or len(actual_old) != 133:
        raise ValueError("The 133 certified special-O4 originals do not match")

    proven = {
        index: (core_id, PROOFS[core_id][2])
        for core_id in sorted(PROOFS)
        for index in members_by_core[core_id]
    }
    if len(proven) != 300 or len(proven) - len(actual_old) != 167:
        raise ValueError("Proven 300 = 133 + 167 original cohorts are not disjoint")
    remaining = [line for i, line in source_rows.items() if i not in proven]
    if len(remaining) != 8233:
        raise ValueError("Incorrect post-certification unresolved count")
    if sum("conjectured_divergent" in line for line in remaining) != 4608:
        raise ValueError("A conditional snub-dependent case was inadvertently removed")

    working = "\n".join([
        "# Current order-10 unresolved cases after v3 and six independently certified nine-core classes",
        "# Remaining=8233 previous_v3=8533 additional_certified_divergent=300",
        "# Certified lifts: special_O4=133 historical_four_cores=167; v3 and historical verdicts unchanged.",
        "# Format: original_index pared_order pared_graph6 certificate_rule certificate_target_status certificate_target_label",
        *remaining,
        "",
    ])
    certified = "\n".join([
        "original_index\tcore_id\tcore_graph6\tproof_family",
        *(
            f"{index}\t{core_id}\t{PROOFS[core_id][0]}\t{family}"
            for index, (core_id, family) in sorted(proven.items())
        ),
        "",
    ])
    summary_lines = [
        "# Current order-10 indeterminate population, certificate lift v4",
        "",
        "This is a **certified accounting update**, not a new divergence theorem.",
        "The original and v3 census results and all historical proof files remain",
        "unchanged. The previous v3 list contained 8,533 graphs; six distinct",
        "nine-vertex stiff-core classes with independently replayable divergence",
        "certificates cover 300 of those original connected ten-vertex graphs.",
        "",
        "| Core representative | Graph6 | Original members | Certified mechanism |",
        "|---:|---|---:|---|",
    ]
    for core_id, (encoded, expected, family) in sorted(PROOFS.items()):
        summary_lines.append(f"| {core_id} | `{encoded}` | {expected} | {family} |")
    summary_lines.extend([
        "",
        "**Total newly excluded from the stale v3 working list: 300**",
        "(133 special-O4-core-lift originals plus 167 disjoint historical",
        "nine-core-lift originals). Every index was still in v3.",
        "",
        "**Remaining indeterminate: 8,233 original connected order-ten graphs.**",
        "These comprise 2,092 representatives with an eight-vertex pared core",
        "(the conjectural snub-disphenoid class), 3,738 original members",
        "distributed among 29 still unresolved nine-vertex cores, and",
        "2,403 original graphs with a ten-vertex stiff core.",
        "The 4,608 entries annotated conjectured_divergent retain their",
        "unproved status; **no conjectural cases are promoted to proofs**.",
        "",
        "This stage uses the original zero-based McKay census indices.",
        "Its certified_divergent.tsv records every excluded index, its",
        "exact nine-core class and the source of its existing proof.",
        "",
        "## Mathematical provenance",
        "",
        "- For cores 6938923 and 6939350, replay the saved independent",
        "  special-O4 K^3 witnesses and 133 original dominated-fold/isomorphism",
        "  certificates via scripts/special_octahedron_class_lift_v1.py verify.",
        "- For the other four core classes, scripts/historical_ninecore_lift_v1.py",
        "  independently verifies 167 complete original fold and isomorphism",
        "  certificates, special O7/O4 witnesses in raw K^3, or an explicit",
        "  suspension coaffination. These cores are proved K-divergent.",
        "- The theorem of Frías-Armenta--Neumann-Lara--Pizaña (2004) preserves",
        "  clique convergence/divergence under dominated-vertex deletions.",
        "  The suspension certificates use Larrión--Neumann-Lara--Pizaña",
        "  (2009), Theorem 4.6.",
        "",
        "Neither failure of a bounded retraction search nor conditional",
        "snub-disphenoid evidence is used to discard any further graph.",
        "",
        "## Reproduction",
        "",
        "From the census repository with the pinned historical environment:",
        "",
        "```bash",
        "bash scripts/bootstrap_special_k3_v5.sh",
        ".venv-special-k3-v5/bin/python scripts/special_octahedron_class_lift_v1.py verify",
        ".venv-special-k3-v5/bin/python scripts/historical_ninecore_lift_v1.py --output /tmp/historical-ninecore-lift-167.json",
        ".venv-special-k3-v5/bin/python scripts/historical_ninecore_lift_v1.py --verify /tmp/historical-ninecore-lift-167.json",
        ".venv-special-k3-v5/bin/python scripts/current_indeterminate_v4.py verify",
        "```",
        "",
        "The v4 verification command independently rebuilds all three",
        "committed v4 artifacts in memory and compares their bytes. Its",
        "build command refuses to overwrite different existing results.",
        "",
    ])
    summary = "\n".join(summary_lines)
    return {
        OUTPUT: working.encode("utf-8"),
        PROVEN_INDEX: certified.encode("utf-8"),
        SUMMARY: summary.encode("utf-8"),
    }


def check(root: Path = ROOT) -> None:
    for name, blob in generate(root).items():
        if not (root / name).is_file() or (root / name).read_bytes() != blob:
            raise ValueError(f"Missing, modified or stale certified v4 artifact: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "build", "verify"))
    args = parser.parse_args()
    prepared = generate()
    if args.action == "build":
        for name, blob in prepared.items():
            path = ROOT / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and path.read_bytes() != blob:
                raise ValueError(f"Refusing to replace a conflicting v4 artifact: {name}")
            path.write_bytes(blob)
    if args.action in ("build", "verify"):
        check()
    print("Order 10: 8533 v3 unresolved, 300 proved divergent, 8233 current unresolved.")
    if args.action == "verify":
        print("All three versioned v4 artifacts independently reconstructed and verified.")


if __name__ == "__main__":
    main()
