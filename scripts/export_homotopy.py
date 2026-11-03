"""Export the order-10 homotopy post-stage as a readable root-level TSV.

The per-graph JSON records remain authoritative. Exporting neither reruns
the homotopy computations nor changes an existing stage manifest. A partial
stage exports only completed records, and later exports rebuild the file.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

import staged


COLUMNS = (
    "original_index",
    "original_graph6",
    "pared_order",
    "pared_graph6",
    "is_exact",
    "is_limited",
    "homotopy_type",
    "spheres",
    "verdict",
    "reason",
)


def describe_homotopy(row: dict) -> str:
    """Report a type only when the record certifies an exact result."""
    spheres = row.get("spheres")
    if row.get("is_exact") is not True or row.get("is_limited") is True:
        return "not certified"
    if not isinstance(spheres, dict):
        return "not certified"
    if not spheres:
        return "contractible"
    parts = []
    for dimension, multiplicity in sorted(spheres.items(), key=lambda item: int(item[0])):
        if not (
            isinstance(multiplicity, int)
            and not isinstance(multiplicity, bool)
            and multiplicity > 0
        ):
            return "not certified"
        noun = "copy" if multiplicity == 1 else "copies"
        parts.append(f"{multiplicity} {noun} of S^{dimension}")
    return "wedge of " + ", ".join(parts)


def export_homotopy() -> int | None:
    """Create/update homotopy_order_10.tsv, or skip if no stage exists yet.

    This is safe to call after an interrupted stage. It does not modify
    the stage JSON records, summaries, or code-revision provenance.
    """
    folder = staged.stage_dir(10, "homotopy")
    if not folder.exists():
        return None

    selection, source = staged.stage_selection(10, "homotopy")
    records = staged.checked_records(10, "homotopy", source)
    unexpected = set(records) - set(selection)
    if unexpected:
        raise ValueError(f"Homotopy records outside the selected cohort: {sorted(unexpected)[:5]}")

    _, _, origins = staged.census(10)
    target = staged.ROOT / "homotopy_order_10.tsv"
    temp = target.with_name(target.name + ".partial")
    try:
        with temp.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
            writer.writerow(COLUMNS)
            for index in sorted(records):
                record = records[index]
                original_fields = origins[index].split()
                spheres = record.get("spheres")
                writer.writerow((
                    index,
                    source[index]["graph6"],
                    original_fields[1],
                    original_fields[2],
                    str(record["is_exact"]).lower(),
                    str(record.get("is_limited", False)).lower(),
                    describe_homotopy(record),
                    json.dumps(spheres, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
                    if spheres is not None else "",
                    record.get("verdict", ""),
                    record.get("reason", ""),
                ))
        os.replace(temp, target)
    finally:
        temp.unlink(missing_ok=True)
    return len(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    count = export_homotopy()
    if count is not None:
        print(f"Exported {count} completed order-10 homotopy records to homotopy_order_10.tsv")


if __name__ == "__main__":
    main()
