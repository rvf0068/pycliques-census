"""Proof-only certification of 98 previously exploratory small ten-P4 cores.

Every input is an original frozen ten-v25 graph6 graph, not a cropped
third-iterate host from a mutable notebook.  The 98-item source list is
required to equal *all* surviving global-P3 class representatives with
P3 order <=40.  The fourth iterates are reconstructed using the
previously certified BK + NetworkX facet crosscheck and complete
multi-round dominated-vertex folds.

No K-behavior claim or census promotion is made by this verifier.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

from research.order10_full_nine_reference_v1 import index as refs
from research.order10_p4_cap_rescue_v24.verify import (
    p4_from_graph6,
)

if sys.flags.optimize:
    raise RuntimeError("Proof-critical assertions must not be bypassed")

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ARCHIVE = HERE / "exploratory_results.json"

# Independent immutable repository Git blob IDs, read from the actual
# merged files and the newly imported exploratory source; not recomputed
# from the mutable expected assertions.
EXPECTED_BLOBS = {
    "indeterminate_order_10_v25.txt":
        "d31d52d28427adcef6055cc1d277565fe88f32d5",
    "research/order10_p3_global_v23_index/certificates.json":
        "ab5a9f1c075dfad63b111929368147884519f2a3",
    "research/order10_small_p4_98_v1/exploratory_results.json":
        "68c3d3d196e4e19f1612a09a1e196df8aa4e1852",
}
EXPECTED_COUNT = 98
MAX_P3 = 40


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise AssertionError(reason)


def read_pinned(name: str) -> bytes:
    require(name in EXPECTED_BLOBS, "Unexpected historical input path")
    data = (ROOT / name).read_bytes()
    require(refs.blob(data) == EXPECTED_BLOBS[name],
            "Historical source or exploratory evidence changed: " + name)
    return data


def dims(rows: list[int]) -> list[int]:
    n = len(rows)
    require(all(type(x) is int and not(x >> n)
                and not (x & (1 << u))
                for u, x in enumerate(rows)),
            "Invalid P4 adjacency row")
    require(all(bool(rows[u] & (1 << v))
                == bool(rows[v] & (1 << u))
                for u in range(n) for v in range(u + 1, n)),
            "Asymmetric P4 adjacency matrix")
    return [n, sum(row.bit_count() for row in rows) // 2]


def row_hash(rows: list[int]) -> str:
    """SHA256 of canonical P4 adjacency rows in minimal-width little endian."""
    width = (len(rows) + 7) // 8
    return hashlib.sha256(b"".join(
        row.to_bytes(width, "little") for row in rows
    )).hexdigest()


def assert_stiff(rows: list[int]) -> None:
    n = len(rows)
    for u in range(n):
        closed_u = rows[u] | (1 << u)
        for v in range(n):
            if u != v:
                require(bool(closed_u & ~(rows[v] | (1 << v))),
                        "P4 still has a dominated vertex")


def source_catalog() -> tuple[list[dict], dict[int, str]]:
    # Confirm source archive identity and every original McKay graph6.
    saved = json.loads(read_pinned(ARCHIVE.relative_to(ROOT).as_posix()))
    require(saved.get("schema") == 1
            and saved.get("source") == "PR96 hosts artifact (verified input)"
            and isinstance(saved.get("records"), list)
            and len(saved["records"]) == EXPECTED_COUNT,
            "Unexpected 98-case P4 source archive schema/count")
    raw_ten = read_pinned("indeterminate_order_10_v25.txt").decode("ascii")
    ten = {}
    rows_seen = 0
    for line in raw_ten.splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        require(len(fields) == 6, "Malformed frozen ten-v25 source")
        rows_seen += 1
        if fields[1] == "10":
            idx = int(fields[0])
            require(idx not in ten
                    and fields[3:] == ["-", "-", "-"],
                    "Unexpected stiff ten source/certificate state")
            ten[idx] = fields[2]
    require(rows_seen == 1052 and len(ten) == 622,
            "Current stiff ten-v25 cohort changed")

    old_global = json.loads(read_pinned(
        "research/order10_p3_global_v23_index/certificates.json"
    ))
    require(old_global["counts"]["exact_isomorphism_classes"] == 525
            and len(old_global["singleton_indices"]) == 492
            and len(old_global["nontrivial_classes"]) == 33,
            "Unexpected historical global P3 class certification")
    saved_reps = sorted(set(old_global["singleton_indices"]) | {
        x["representative"] for x in old_global["nontrivial_classes"]
    })
    surviving = sorted(i for i in saved_reps if i in ten)
    require(len(surviving) == 521,
            "Current ten-v25 class representative cohort changed")

    # PR #96 host-index function authenticates and independently
    # reconstructs P3 for all 521 currently surviving representatives.
    hosts = refs.hosts()
    require(len(hosts["records"]) == len(surviving) == 521,
            "Previously certified current P3 hosts changed")
    hosts_by_id = {x["index"]: x for x in hosts["records"]}
    require(sorted(hosts_by_id) == surviving,
            "Missing or unexpected current P3 representative")
    small = sorted(i for i in surviving
                   if hosts_by_id[i]["p3"][0] <= MAX_P3)
    require(len(small) == EXPECTED_COUNT,
            "Current small P3-order cohort is not the promised 98")
    records = saved["records"]
    require([x["index"] for x in records] == small,
            "Exploratory results do not enumerate all and only 98 targets")
    for record in records:
        idx = record["index"]
        host = hosts_by_id[idx]
        require(record["graph6"] == ten[idx] == host["graph6"]
                and record["p3"] == host["p3"]
                and record.get("crosschecked_enumerators") == "exact_bk_vs_nx"
                and record.get("facets") == record["raw_p4"][0],
                "Wrong original McKay graph6, P3 shape or exploratory provenance")
    return records, ten


def verify_record(record: dict) -> tuple[list[int], list[int]]:
    """Replay all four stages, 2 facet enumerators, folds and full P4 hash."""
    raw, pared, rounds, p3 = p4_from_graph6(record["graph6"])
    require(
        list(p3) == record["p3"]
        and dims(raw) == record["raw_p4"]
        and len(raw) == record["facets"]
        and dims(pared) == record["p4"]
        and rounds == record["fold_rounds"]
        and row_hash(pared) == record["p4_adj_sha256"],
        "Crosschecked P4 reconstruction or canonical adjacency SHA mismatch"
        f" at original McKay {record['index']}",
    )
    assert_stiff(pared)
    return raw, pared


def verify() -> None:
    records, _ = source_catalog()
    groups: dict[tuple[int, int], list[tuple[int, tuple[int, ...]]]] = (
        defaultdict(list)
    )
    bucket_counts: Counter[str] = Counter()
    for row in records:
        _, pared = verify_record(row)
        degrees = tuple(sorted(int(x).bit_count() for x in pared))
        groups[tuple(row["p4"])].append((row["index"], degrees))
        order = len(pared)
        category = ("up_to_100" if order <= 100 else
                    "101_to_200" if order <= 200 else
                    "201_to_500" if order <= 500 else "over_500")
        bucket_counts[category] += 1
        print(f"PASS small-P4 McKay={row['index']} "
              f"P3={row['p3'][0]} P4={order} edges={row['p4'][1]}",
              flush=True)
    # Distinct dimensions imply nonisomorphism. In the four repeated
    # dimensions, distinct degree multisets are an exact obstruction;
    # do not trust different labeled SHA256 digests as a proof.
    collided = [group for group in groups.values() if len(group) > 1]
    require(
        len(collided) == 4
        and sorted(len(x) for x in collided) == [2, 2, 3, 3]
        and all(len({degrees for _i, degrees in group}) == len(group)
                for group in collided),
        "A fourth-iterate dimension collision remains unclassified",
    )
    from research.order10_full_nine_p4_crossdepth_v1.search import (
        host_catalog,
    )
    earlier = host_catalog()
    historical_shapes = {tuple(x["p4"]) for x in earlier["records"]}
    require(not set(groups).intersection(historical_shapes),
            "A new P4 shape collides with a previously certified P4 host")
    require(bucket_counts == {
        "up_to_100": 5,
        "101_to_200": 40,
        "201_to_500": 52,
        "over_500": 1,
    }, "Size distribution changed")
    print("CERTIFIED: 98 current stiff original ten-P3 class "
          "representatives of P3 order <=40: all P4 reconstructed, "
          "two independent fourth-stage clique enumerators agree, "
          "round-by-round complete paring verified, 98 distinct P4 "
          "isomorphism types by dimensions and exact degree obstructions; "
          "no dimensions overlap the 210 formerly archived P4 hosts; "
          "no census classification changed", flush=True)


if __name__ == "__main__":
    verify()
