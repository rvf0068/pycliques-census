"""Finite P5 growth and induced-O20 witness, NOT a K-divergence proof.

P4 is reconstructed with the immutable independent ten-v24 proof.
Two maximal-clique enumerators independently establish all 1977
facets of P4. Complete closed-neighborhood containment certificates
fold the 1977-vertex K(P4) to a stiff 1896-vertex P5.

An induced dominating O20 is checked, together with an explicit
contradiction to a retraction onto THAT particular octahedron.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import networkx as nx

if sys.flags.optimize:
    raise RuntimeError("Optimized execution bypasses finite proof assertions")

from research.order10_p4_no_octahedral_10820813_v1.verify import (
    reconstruct_all,
    git_blob,
)

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ARCHIVE = HERE / "certificates.json"
OLD = ROOT / "research/order10_p4_no_octahedral_10820813_v1/certificates.json"


def need(value: bool, reason: str) -> None:
    if not value:
        raise AssertionError(reason)


def bits(mask: int):
    while mask:
        low = mask & -mask
        yield low.bit_length() - 1
        mask -= low


def digest(rows: list[int]) -> str:
    width = (len(rows) + 7) // 8
    return hashlib.sha256(
        b"".join(row.to_bytes(width, "little") for row in rows)
    ).hexdigest()


def fourth(cert: dict) -> nx.Graph:
    source = "ICp" + chr(96) + "fpv~_"
    need(
        cert["schema"] == 1 and cert["source_index"] == 10820813
        and cert["source_graph6"] == source
        and cert["previous_proof_archive"] == OLD.relative_to(ROOT).as_posix()
        and cert["previous_proof_git_blob"] == git_blob(OLD.read_bytes()),
        "Uncertified fourth-iterate source substitution",
    )
    previous = json.loads(OLD.read_text(encoding="utf-8"))
    need(
        previous["source"]["index"] == 10820813
        and previous["source"]["graph6"] == source
        and previous["P4_graph6_sha256"] ==
            cert["frozen_P4_graph6_sha256"],
        "Saved ten-v24 earlier-stage source changed",
    )
    graph = reconstruct_all(previous)[-1]
    need(len(graph) == 70 and graph.number_of_edges() == 1830,
         "Unexpected P4 order/edge count")
    return graph


def clique_facets_nx(g: nx.Graph) -> list[int]:
    facets = []
    for clique in nx.find_cliques(g):
        facets.append(sum(1 << v for v in clique))
        need(len(facets) <= 10_000, "Explicit P4 facet enumeration cap")
    return sorted(facets)


def clique_facets_bk(g: nx.Graph) -> list[int]:
    """Independent pivoted integer-bitset Bron--Kerbosch enumeration."""
    n = len(g)
    need(set(g) == set(range(n)), "Noncanonical P4 labels")
    adj = [sum(1 << v for v in g[u]) for u in range(n)]
    facets = []

    def bk(r: int, p: int, x: int) -> None:
        if p == 0 and x == 0:
            facets.append(r)
            need(len(facets) <= 10_000, "Independent BK facet cap")
            return
        choices = p | x
        pivot = (
            max(bits(choices), key=lambda u: (p & adj[u]).bit_count())
            if choices else None
        )
        selected = p & ~adj[pivot] if pivot is not None else p
        for u in list(bits(selected)):
            bit = 1 << u
            bk(r | bit, p & adj[u], x & adj[u])
            p &= ~bit
            x |= bit

    bk(0, (1 << n) - 1, 0)
    return sorted(facets)


def build_raw(g: nx.Graph) -> tuple[list[int], list[int]]:
    facets = clique_facets_nx(g)
    need(facets == clique_facets_bk(g) and len(facets) == 1977,
         "Fifth-stage facets differ between the two enumerators")
    incident = [0] * len(g)
    for i, mask in enumerate(facets):
        for v in bits(mask):
            incident[v] |= 1 << i
    raw = []
    for i, mask in enumerate(facets):
        neighbors = 0
        for v in bits(mask):
            neighbors |= incident[v]
        raw.append(neighbors & ~(1 << i))
    need(sum(row.bit_count() for row in raw) == 2 * 1742560,
         "Raw fifth-iterate size changed")
    # Check all possible facet pairs, including every nonedge.
    for i, mask in enumerate(facets):
        for j in range(i + 1, len(facets)):
            need(bool(mask & facets[j]) == bool(raw[i] & (1 << j)),
                 "Clique-intersection adjacency mismatch")
    return facets, raw


def pare_raw(raw: list[int]) -> tuple[list[int], list[int], dict[int, int]]:
    """One simultaneous fold; each deleted vertex has a surviving dominator."""
    n = len(raw)
    full = (1 << n) - 1
    complement = [full & ~(raw[u] | (1 << u)) for u in range(n)]
    sizes = [row.bit_count() for row in complement]
    ordering = sorted(range(n), key=lambda u: (sizes[u], u))
    deleted: dict[int, int] = {}
    for u in range(n):
        for v in ordering:
            if sizes[v] > sizes[u] or (sizes[v] == sizes[u] and v >= u):
                break
            if not (complement[v] & ~complement[u]):
                deleted[u] = v
                break
    kept = [i for i in range(n) if i not in deleted]
    need(len(deleted) == 81 and len(kept) == 1896,
         "Wrong number of dominated vertices")
    alive = sum(1 << i for i in kept)
    for u in deleted:
        v = u
        while v in deleted:
            v = deleted[v]
        need(v in kept and not (complement[v] & ~complement[u]),
             f"Deleted vertex {u} has no surviving dominator")
    for u in kept:
        cu = complement[u] & alive
        for v in kept:
            if u != v:
                need(bool((complement[v] & alive) & ~cu),
                     f"Remaining fifth-iterate vertex {u} dominated by {v}")
    labels = {u: i for i, u in enumerate(kept)}
    pared = [
        sum(1 << labels[v] for v in bits(raw[u] & alive))
        for u in kept
    ]
    need(sum(row.bit_count() for row in pared) == 2 * 1601683,
         "Wrong fifth-pared-iterate size")
    return kept, pared, deleted


def check_octahedron(
    rows: list[int], pairs: list[list[int]],
) -> tuple[int, dict[int, int]]:
    """Check induced antipodes, complement domination and forced images."""
    n = len(rows)
    full = (1 << n) - 1
    H = [full & ~(row | (1 << i)) for i, row in enumerate(rows)]
    target = [v for pair in pairs for v in pair]
    need(
        len(target) == len(set(target)) == 2 * len(pairs)
        and len(pairs) >= 3
        and all(len(pair) == 2 and all(type(v) is int and 0 <= v < n
                                      for v in pair) for pair in pairs),
        "Invalid O_d target label sequence",
    )
    for i, (a, b) in enumerate(pairs):
        need(bool(H[a] & (1 << b)), "Antipodal pair is a host edge")
        for c, d in pairs[:i]:
            need(not ((H[a] | H[b]) & ((1 << c) | (1 << d))),
                 "Cross pair is missing an edge in proposed octahedron")
    cover = 0
    for a, b in pairs:
        cover |= H[a] | H[b] | (1 << a) | (1 << b)
    need(cover == full, "Octahedral target does not dominate complement")
    forced: dict[int, int] = {}
    fixed = set(target)
    for u in range(n):
        if u in fixed:
            continue
        options = 0
        for a, b in pairs:
            if H[u] & (1 << a):
                options |= 1 << b
            if H[u] & (1 << b):
                options |= 1 << a
        need(bool(options), "Dominating target has an outside vertex with no image")
        if options.bit_count() == 1:
            forced[u] = options.bit_length() - 1
    return sum(row.bit_count() for row in H) // 2, forced


def verify() -> None:
    cert = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    need(
        cert["schema"] == 1 and cert["claim"] ==
        "exact_fifth_pared_clique_iterate_and_dominating_induced_O20_without_retraction_to_that_target",
        "Wrong scope of P5 finite certificate",
    )
    g = fourth(cert)
    facets, raw = build_raw(g)
    saved = cert["raw_K5"]
    need(
        len(facets) == len(raw) == saved["order"] ==
        saved["maximal_cliques_of_P4"] and
        saved["edges"] == 1742560 and
        saved["little_endian_adjacency_sha256"] == digest(raw),
        "Exact K(P4) source adjacency digest changed",
    )
    kept, pared, deleted = pare_raw(raw)
    saved = cert["one_round_pared"]
    need(
        len(deleted) == saved["deleted_vertices"] and
        len(kept) == saved["stiff_survivor_order"] and
        saved["stiff_survivor_edges"] == 1601683 and
        saved["little_endian_adjacency_sha256"] == digest(pared),
        "P5 fold certificate or complete adjacency digest changed",
    )
    witness = cert["witness"]
    need(
        witness["target"] == "induced_O20_in_P5"
        and len(witness["antipodal_pairs"]) == 20
        and witness["complement_dominates_all_1896"] is True,
        "Missing target or false O20 dimension",
    )
    complement_edges, forced = check_octahedron(
        pared, witness["antipodal_pairs"]
    )
    need(
        complement_edges == saved["complement_edges"] == 194777
        and len(forced) == witness["forced_outside_vertices"] == 210,
        "Incorrect complementary domination or forced-domain count",
    )
    conflict = witness["forced_conflict"]
    x, y = conflict["host_edge"]
    a, b = conflict["forced_target_images"]
    need(
        0 <= x < len(pared) and 0 <= y < len(pared) and x != y
        and bool(pared[x] & (1 << y))
        and forced.get(x) == a and forced.get(y) == b
        and any({a, b} == set(pair)
                for pair in witness["antipodal_pairs"]),
        "Forced-image antipodal host-edge obstruction is invalid",
    )
    print(
        "CERTIFIED: raw K5 1977 vertices/1742560 edges; 81 valid"
        " closed-neighborhood folds leave stiff P5 1896 vertices/"
        "1601683 edges. An induced complement-dominating O20"
        " exists, but this particular target has the forced antipodal"
        " host-edge conflict 87-458 -> 857-1397, so it does NOT retract."
        " No claim about K-divergence.",
        flush=True,
    )


if __name__ == "__main__":
    verify()
