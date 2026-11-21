"""Positive-only exact audit of the order-ten v11 -> v12 transition.

The archived O6 and O12 maps, plus the already independently certified
33-member K3 isomorphism family and five P4 isomorphism maps,
are the only allowed justifications.
This checker does not modify indexes and never promotes a bounded failure.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from research.order10_pared_k3_33class_v1.verify import MCKAY
from research.order10_fourth_oct_v1.verify_o6 import main as verify_o6
from research.order10_fourth_oct_v1.verify_o12 import main as verify_o12
from research.order10_fourth_oct_v1.verify_extra5 import main as verify_extra5

ROOT = Path(__file__).resolve().parents[2]
BEFORE = ROOT / "indeterminate_order_10_v11.txt"
AFTER = ROOT / "indeterminate_order_10_v12.txt"
CURRENT = ROOT / "indeterminate_order_10.txt"
PINNED_V11 = "34023e9323945c4a6e5e1249c37ba955ba62473f"
DIRECT = {10223467, 10775850, 11104269, 11563706}
EXTRA_FOURTH_ISOS = {11251181, 11425747, 11509851, 11556261, 11599112}
REMOVED = set(MCKAY) | DIRECT | EXTRA_FOURTH_ISOS


def require(condition, message):
    if not condition:
        raise ValueError(message)


def rows(raw):
    result = {}
    for line in raw.decode("utf-8").splitlines():
        if line and not line.startswith("#"):
            cols = line.split()
            require(len(cols) == 6, "Wrong row columns")
            index = int(cols[0])
            require(index not in result, "Duplicate index")
            result[index] = cols
    require(list(result) == sorted(result), "Unsorted census rows")
    return result


def verify_indexes():
    prior = BEFORE.read_bytes()
    digest = hashlib.sha1(b"blob " + str(len(prior)).encode() + b"\0" + prior).hexdigest()
    require(digest == PINNED_V11, "Immutable prior v11 changed")
    current, after = CURRENT.read_bytes(), AFTER.read_bytes()
    require(current == after, "Current root is not exactly v12")
    old, new = rows(prior), rows(after)
    require(len(old) == 2830 and len(new) == 2788, "Unexpected record counts")
    require(len(REMOVED) == 42, "Unexpected proof cohort cardinality")
    require(set(old) - set(new) == REMOVED, "Wrong McKay deletion set")
    require(all(old[i] == row for i, row in new.items()), "Retained row was changed")
    require(all(old[i][1] == "10" and old[i][3:] == ["-", "-", "-"]
                for i in REMOVED), "An unproved or conditional row was deleted")
    require(sum(row[4] == "conjectured_divergent" for row in new.values()) == 120,
            "The independent HCZTf\\} conditional population changed")
    return old, new


def main():
    old, new = verify_indexes()
    verify_o6()
    verify_o12()
    verify_extra5()
    print("CERTIFIED_ORDER10_V12 old=2830 removed=42 remaining=2788")
    print("CERTIFIED_MCKAY_INDICES", sorted(REMOVED))


if __name__ == "__main__":
    main()
