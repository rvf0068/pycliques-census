"""Certify exact v9->v10 removal of 351 nine-core + 350 ten-core positives.

Only unconditional octahedral retraction proofs may disappear from the
working indeterminate index. Every other historical census row must remain
byte-for-byte identical, and all conjecture-dependent labels stay unchanged.

CI separately reruns the entire underlying positive-proof archives.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V9 = ROOT / "indeterminate_order_10_v9.txt"
V10 = ROOT / "indeterminate_order_10_v10.txt"
CURRENT = ROOT / "indeterminate_order_10.txt"
CORES = ROOT / "reports/order10_core_index_v1/classes.tsv"
TEN_PROOFS = ROOT / "research/order10_third_iterate_high_octahedra_proofs_v1/certificates.json"
V9_BLOB = "704219076c6d61b595374cd129c5fa520253a089"
CORE_BLOB = "9c1559191231a7c61d95955d14f41a22e4565f79"
NINE_CLASSES = {5418647: 116, 6974529: 235}
EXPECTED_TEN_PROOFS = 350

HEADER = [
    "# Connected order-ten unresolved population after 351 nine-core and 350 ten-core octahedral retraction proofs",
    "# Remaining=7219 previous_v9=7920 newly_proved_divergent=701",
    "# Two raw third-iterate nine-core O5/O6 proofs cover 351 originals; 350 raw third-iterate stiff-ten O4/O5/O6 proofs cover 350 originals.",
    "# All earlier versioned snapshots and historical stage/proof records remain immutable.",
    "# Format: original_index pared_order pared_graph6 certificate_rule certificate_target_status certificate_target_label",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def blob_hash(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def parse(raw: bytes) -> tuple[list[str], dict[int, str]]:
    headers = []
    result: dict[int, str] = {}
    previous = -1
    for line in raw.decode("utf-8").splitlines():
        if not line:
            continue
        if line.startswith("#"):
            headers.append(line)
            continue
        row = line.split()
        require(len(row) == 6, "Malformed six-column census entry")
        index = int(row[0])
        require(index > previous, "Census indices must be strictly increasing")
        previous = index
        result[index] = line
    return headers, result


def verify() -> dict:
    source = V9.read_bytes()
    target = V10.read_bytes()
    require(blob_hash(source) == V9_BLOB, "Frozen v9 source was modified")
    require(blob_hash(CORES.read_bytes()) == CORE_BLOB,
            "Frozen core-class index was modified")
    # v10 is now a frozen historical proof transition. The independent v11
    # verifier certifies the newer authoritative current root and its removals.
    require(CURRENT.read_bytes() in (
        target, (ROOT / "indeterminate_order_10_v11.txt").read_bytes()
    ), "Current authoritative index is neither v10 nor v11")
    _, old = parse(source)
    headers, new = parse(target)
    require(headers == HEADER and len(old) == 7920 and len(new) == 7219,
            "Incorrect v10 header or source/target population")
    require(all(index in old and old[index] == line
                for index, line in new.items()),
            "One or more retained original rows were changed")

    class_rows = {}
    for line in CORES.read_text(encoding="utf-8").splitlines()[1:]:
        if line:
            cells = line.split("\t")
            require(len(cells) == 6, "Malformed archived core class")
            class_rows[int(cells[0])] = cells
    proved_nine = set()
    for core, size in NINE_CLASSES.items():
        cls = class_rows[core]
        require(cls[1] == "9" and int(cls[3]) == size
                and int(cls[0]) == core,
                "Nine-core class identity or source-size mismatch")
        members = [int(index) for index in cls[5].split(",")]
        require(len(members) == len(set(members)) == size,
                "Wrong nine-core isomorphism class membership")
        for index in members:
            require(index not in proved_nine, "Overlapping nine-core classes")
            row = old.get(index)
            require(row is not None, "Absent nine-core member in v9")
            parts = row.split()
            require(parts[1] == "9" and parts[3:] == ["-", "-", "-"],
                    "Nine-core proof covers a conjectured or non-stiff source")
            proved_nine.add(index)
    require(len(proved_nine) == 351, "Wrong number of proved nine-core originals")

    record = json.loads(TEN_PROOFS.read_text(encoding="utf-8"))
    require(
        record["schema"] == 1 and record["iterate"] == 3
        and record["source"] == V9.name
        and type(record["proofs"]) is list
        and len(record["proofs"]) == EXPECTED_TEN_PROOFS,
        "Missing complete frozen-source ten-stiff proof archive"
    )
    proved_ten = set()
    for proof in record["proofs"]:
        index = proof["index"]
        require(type(index) is int and index not in proved_ten,
                "Duplicate stiff ten-core proof")
        old_line = old.get(index)
        require(old_line is not None, "Ten-core proof index absent in v9")
        cells = old_line.split()
        require(cells[1] == "10" and cells[2] == proof["graph6"]
                and cells[3:] == ["-", "-", "-"],
                "Ten-core proof source differs from v9 unclassified graph")
        proved_ten.add(index)

    proved = proved_nine | proved_ten
    require(len(proved) == 701 and proved_nine.isdisjoint(proved_ten),
            "Nine-core and ten-core proof sets overlap")
    require(set(old) - set(new) == proved,
            "Removed indices differ from the 701 positive proofs")

    source_conditional = sum(
        line.split()[4] == "conjectured_divergent" for line in old.values()
    )
    target_conditional = sum(
        line.split()[4] == "conjectured_divergent" for line in new.values()
    )
    require(source_conditional == target_conditional == 4509,
            "Conjecture-dependent references were removed or altered")
    after_orders = {
        order: sum(line.split()[1] == str(order) for line in new.values())
        for order in (8, 9, 10)
    }
    require(after_orders == {8: 2092, 9: 3132, 10: 1995},
            "Unexpected distribution of remaining pared orders")
    return {
        "previous": 7920, "current": 7219,
        "nine_core_positive_originals": len(proved_nine),
        "stiff_ten_positive_originals": len(proved_ten),
        "unchanged_conditional_references": target_conditional,
        "remaining_by_pared_order": after_orders,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
    print("VERIFIED v10: exactly 701 proved K-divergent indices removed;"
          " no conditional or other historical entries modified.")
