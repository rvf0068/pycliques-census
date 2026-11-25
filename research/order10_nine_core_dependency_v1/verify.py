"""Independent positive clique-behavior dependency audit (proof only).

All three saved 9-to-10 third-iterate bijections, all 65 historical ten
class-member bijections, and the historical 685-coordinate fourth-iterate
bridge are checked on every edge and nonedge. No census verdict changes.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import struct
import sys

import networkx as nx

if sys.flags.optimize:
    raise RuntimeError("Optimized Python bypasses proof-critical checks")

from research.order10_p3_global_v23_index.independent_verify import (
    independent_p3,
    verify_pair,
)
from research.order10_p4_cap_rescue_v24.verify import (
    check_bijection,
    p4_from_graph6,
)

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CERTIFICATE = HERE / "certificates.json"


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError(reason)


def git_blob(data: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()


def verified_archive(path: str, sha: str) -> bytes:
    raw = (ROOT / path).read_bytes()
    require(git_blob(raw) == sha, f"Historical Git blob changed: {path}")
    return raw


def parse_rows(raw: bytes) -> dict[int, tuple[str, str]]:
    rows: dict[int, tuple[str, str]] = {}
    for line in raw.decode("ascii").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        require(
            len(fields) == 6 and fields[1] in ("9", "10")
            and fields[3:] == ["-", "-", "-"],
            "Unexpected census row format",
        )
        idx = int(fields[0])
        require(idx not in rows, "Duplicate McKay index")
        rows[idx] = (fields[1], fields[2])
    require(list(rows) == sorted(rows), "Noncanonical census order")
    return rows


def verify_p4_bridge(rows: dict[int, tuple[str, str]],
                     data: dict, archived: dict) -> int:
    """Replay the already certified fourth-iterate identification."""
    pair = data["prior_p4_link"]
    require(pair == {
        "from_ten_index": 7044680,
        "to_ten_index": 11614797,
        "order": 685,
        "edges": 199283,
        "archived_map_sha256":
            "bd2a5bb6713fa5dc02d55b906f58b4567fe425b57add9efd2dfb0f95a0a3e363",
    }, "Unexpected historical fourth-iterate link")
    old = archived["positive_isomorphism"]
    require(
        old["from_index"] == pair["from_ten_index"]
        and old["to_index"] == pair["to_ten_index"]
        and old["vertices"] == pair["order"]
        and old["edges"] == pair["edges"]
        and old["map_format"] == "uint16_little_endian_base64"
        and old["map_sha256"] == pair["archived_map_sha256"]
        and old["merged_originals"] == 18
        and old["former_p3_source_class_members"] == 17,
        "Historical full P4 certificate provenance changed",
    )
    first = p4_from_graph6(rows[pair["from_ten_index"]][1])[1]
    second = p4_from_graph6(rows[pair["to_ten_index"]][1])[1]
    require(
        len(first) == len(second) == pair["order"]
        and sum(x.bit_count() for x in first) // 2 == pair["edges"]
        and sum(x.bit_count() for x in second) // 2 == pair["edges"],
        "Reconstructed fourth-iterate dimensions differ",
    )
    encoded = base64.b64decode(old["map_b64"], validate=True)
    require(
        len(encoded) == 2 * pair["order"]
        and hashlib.sha256(encoded).hexdigest() ==
            pair["archived_map_sha256"],
        "Historical fourth-iterate map bytes changed",
    )
    mapping = list(struct.unpack("<" + str(pair["order"]) + "H", encoded))
    check_bijection(first, second, mapping)
    return pair["to_ten_index"]


def verify() -> None:
    data = json.loads(CERTIFICATE.read_text(encoding="utf-8"))
    require(data["schema"] == 1 and data["kind"] ==
            "exact_pending_nine_core_clique_behavior_equivalences_without_census_promotion",
            "Unexpected dependency certificate schema")
    nine = parse_rows(verified_archive(
        data["nine_snapshot"], data["nine_git_blob"]))
    ten = parse_rows(verified_archive(
        data["ten_snapshot"], data["ten_git_blob"]))
    require(
        data["nine_snapshot"] == "indeterminate_order_9_v9.txt"
        and data["ten_snapshot"] == "indeterminate_order_10_v25.txt"
        and (ROOT / "indeterminate_order_9.txt").read_bytes() ==
            (ROOT / data["nine_snapshot"]).read_bytes()
        and (ROOT / "indeterminate_order_10.txt").read_bytes() ==
            (ROOT / data["ten_snapshot"]).read_bytes()
        and len(nine) == 3 and len(ten) == 1052,
        "Current authoritative indices do not match immutable evidence",
    )
    global_data = json.loads(verified_archive(
        data["global_p3_archive"], data["global_p3_git_blob"]))
    p4_data = json.loads(verified_archive(
        data["p4_archive"], data["p4_git_blob"]))
    require(
        data["global_p3_archive"] ==
            "research/order10_p3_global_v23_index/certificates.json"
        and data["p4_archive"] ==
            "research/order10_p4_cap_rescue_v24/certificates.json",
        "Unexpected upstream archives",
    )

    sources = data["three_p3_equivalences"]
    require(
        [(x["nine_index"], x["ten_rep_index"]) for x in sources] ==
        [(249576, 7044680), (251628, 7070392), (260040, 7479384)],
        "Unexpected three unresolved core references",
    )
    nine_graphs: dict[int, nx.Graph] = {}
    stiff_members: set[int] = set()
    stiff_by_nine: list[int] = []

    for item in sources:
        ni, ri = item["nine_index"], item["ten_rep_index"]
        require(
            nine[ni] == ("9", item["nine_graph6"])
            and ten[ri] == ("10", item["ten_rep_graph6"]),
            "Incorrect original graph6 identity",
        )
        nine_original = nx.from_graph6_bytes(item["nine_graph6"].encode("ascii"))
        nine_graphs[ni] = nine_original
        source_p3 = independent_p3(item["nine_graph6"])
        rep_p3 = independent_p3(item["ten_rep_graph6"])
        require(
            len(source_p3) == len(rep_p3) == item["p3_order"]
            and source_p3.number_of_edges() ==
                rep_p3.number_of_edges() == item["p3_edges"],
            "Unexpected third-iterate dimensions",
        )
        verify_pair(source_p3, rep_p3, item["nine_to_ten_p3"])

        groups = [
            group for group in global_data["nontrivial_classes"]
            if group["representative"] == ri
        ]
        require(len(groups) == 1, "Historical P3 class absent or ambiguous")
        group = groups[0]
        require(
            group["order"] == item["p3_order"]
            and group["edges"] == item["p3_edges"]
            and len(group["members"]) == item["class_members"],
            "Historical class size or third-iterate invariant changed",
        )
        ids = [m["index"] for m in group["members"]]
        require(ids == sorted(set(ids)) and ids[0] == ri,
                "Noncanonical historical member list")
        for member in group["members"]:
            i = member["index"]
            require(i not in stiff_members and ten[i][0] == "10",
                    "Duplicate or nonstiff ten-vertex family member")
            member_p3 = independent_p3(ten[i][1])
            verify_pair(member_p3, rep_p3, member["bijection"])
            stiff_members.add(i)
        stiff_by_nine.append(len(ids))
        print(
            f"EXACT nine {ni} -> ten representative {ri}: "
            f"P3 ({item['p3_order']}, {item['p3_edges']}), "
            f"{len(ids)} ten-vertex originals",
            flush=True,
        )

    # All 430 ten-vertex originals having pared nine-vertex cores are
    # independently assigned by actual graph isomorphism, not by a
    # graph6 string match or merely matching order/edge counts.
    direct_counts = {i: 0 for i in nine_graphs}
    direct_ids: set[int] = set()
    for i, (order, g6) in ten.items():
        if order != "9":
            continue
        graph = nx.from_graph6_bytes(g6.encode("ascii"))
        choices = [
            ni for ni, reference in nine_graphs.items()
            if nx.is_isomorphic(graph, reference)
        ]
        require(len(choices) == 1, "Pared-nine class has no unique source")
        direct_counts[choices[0]] += 1
        direct_ids.add(i)

    require(11614797 in global_data["singleton_indices"],
            "The fourth-iterate extra source was not a P3 singleton")
    extra = verify_p4_bridge(ten, data, p4_data)
    require(extra not in stiff_members and extra not in direct_ids,
            "Extra P4 equivalence duplicates a known dependency")
    require(
        stiff_by_nine == data["counts"]["additional_stiff_p3"] ==
            [17, 23, 25]
        and list(direct_counts.values()) ==
            data["counts"]["nine_pared_dependents"] == [141, 147, 142]
        and data["counts"] == {
            "nine_unresolved": 3,
            "ten_unresolved": 1052,
            "nine_pared_dependents": [141, 147, 142],
            "additional_stiff_p3": [17, 23, 25],
            "additional_stiff_p4": 1,
            "all_pending_nine_dependent": 496,
            "stiff_not_yet_linked": 556,
        }
        and len(direct_ids) == 430
        and len(stiff_members) == 65
        and len(direct_ids | stiff_members | {extra}) == 496
        and sum(order == "10" for order, _ in ten.values()) == 622
        and 622 - len(stiff_members) - 1 == 556,
        "The conditional 496/556 partition does not follow from proofs",
    )
    print(
        "CERTIFIED conditional dependency: 430 pared-nine originals "
        "+ 65 exact P3 stiff class members + 1 historical P4 bridge "
        "= 496 unresolved ten-vertex originals depending on three "
        "unresolved nine-vertex graphs; 556 stiff originals not yet "
        "linked; 1052 remain indeterminate; no classification promoted",
        flush=True,
    )


if __name__ == "__main__":
    verify()
