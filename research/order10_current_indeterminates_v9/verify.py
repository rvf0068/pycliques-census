"""Independently audit the v8 -> v9 ten-vertex census progression.

The new v9 root may omit ONLY the twelve complete positive K^2 -> O_3
proofs. All other v8 rows must be byte-identical, with no status changes.
All older versioned snapshots are immutable.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V8 = ROOT / "indeterminate_order_10_v8.txt"
V9 = ROOT / "indeterminate_order_10_v9.txt"
CURRENT = ROOT / "indeterminate_order_10.txt"
CERTIFICATES = ROOT / "research/order10_second_clique_o3_retracts_v1/certificates.json"
V8_GIT_BLOB = "b8d36442ae3c4cda702900b7cbc74d8be45f7072"

HEADER = (
    "# Order-10 unresolved after twelve independently certified raw K^2(G) to O3 retractions",
    "# Remaining=7920 previous_v8=7932 newly_proved_divergent=12",
    "# Existing v8 and earlier snapshots, historical stage reports and proof records remain unchanged.",
    "# Format: original_index pared_order pared_graph6 certificate_rule certificate_target_status certificate_target_label",
)

IDS = (
    10298587, 10582171, 10592280, 11031164, 11031734, 11106678,
    11551444, 11566611, 11585214, 11599630, 11602159, 11624876,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def rows(data: bytes) -> tuple[list[str], list[str]]:
    lines = data.decode("utf-8").splitlines()
    header = [line for line in lines if line.startswith("#")]
    body = [line for line in lines if line and not line.startswith("#")]
    require(all(len(line.split()) == 6 for line in body),
            "Every data row must have exactly six columns")
    ids = [int(line.split()[0]) for line in body]
    require(len(ids) == len(set(ids)), "Repeated McKay index")
    require(ids == sorted(ids), "McKay indices out of order")
    return header, body


def verify() -> None:
    before = V8.read_bytes()
    after = V9.read_bytes()
    require(git_blob(before) == V8_GIT_BLOB,
            "Frozen v8 Git blob unexpectedly changed")
    require(CURRENT.read_bytes() == after,
            "Authoritative root is not byte-for-byte equal to v9")
    old_headers, old = rows(before)
    new_headers, new = rows(after)
    require(tuple(new_headers) == HEADER and len(old) == 7932
            and len(new) == 7920, "Malformed v9 header or row count")
    source = {int(s.split()[0]): s for s in old}
    target = {int(s.split()[0]): s for s in new}
    require(set(target) <= set(source),
            "A v9 row was not present in the frozen v8 cohort")
    require(all(target[i] == source[i] for i in target),
            "A v9 row was changed instead of preserved exactly")

    removed = sorted(set(source) - set(target))
    require(tuple(removed) == IDS,
            "Removed records differ from the twelve certified cases")
    certificates = json.loads(CERTIFICATES.read_text(encoding="utf-8"))
    proof = certificates["certificates"]
    require(tuple(x["index"] for x in proof) == IDS,
            "Proof archive does not match removed indices")
    for certificate in proof:
        index = certificate["index"]
        cells = source[index].split()
        require(cells[1] == "10" and cells[2] == certificate["graph6"]
                and cells[3:] == ["-", "-", "-"],
                "Removed a non-stiff, conditionally classified or mismatched case")

    count_conditional = lambda entries: sum(
        line.split()[4] == "conjectured_divergent" for line in entries
    )
    require(count_conditional(old) == count_conditional(new) == 4509,
            "Conditional references changed")
    require(sum(s.split()[1] == "10" for s in old) == 2357,
            "Frozen stiff ten-core count changed")
    require(sum(s.split()[1] == "10" for s in new) == 2345,
            "New stiff ten-core count changed")
    print("VERIFIED v9: 7,932 -> 7,920; exactly twelve positive proofs removed")
    print("VERIFIED stiff ten-cores: 2,357 -> 2,345")
    print("VERIFIED conjectured cases: 4,509 unchanged")
    print("VERIFIED frozen v8 and byte-identical preserved rows; root equals v9")


if __name__ == "__main__":
    verify()
