"""Independently replay every saved positive order-10 S^1 divergence witness.

Usage: .venv/bin/python scripts/verify_s1_divergence.py
This is read-only and never recomputes unsuccessful searches.
"""
from __future__ import annotations

import sys

from staged import census, checked_records
from s1_divergence import verify_json_record


def main() -> None:
    _, source, _ = census(10)
    records = checked_records(10, "s1divergence", source)
    checked = 0
    for index, record in sorted(records.items()):
        if record["status"] != "DIVERGENT":
            continue
        print(f"Replaying divergent certificate at original index {index}", flush=True)
        if not verify_json_record(record):
            raise SystemExit(f"INVALID divergence certificate for graph index {index}")
        checked += 1
    print(
        f"VERIFIED {checked} divergence certificates from "
        f"{len(records)} completed S^1 search records"
    )


if __name__ == "__main__":
    main()
