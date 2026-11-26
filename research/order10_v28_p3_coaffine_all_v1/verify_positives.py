"""Permanent solver-independent proof of four new ten-vertex divergences.

Reconstruct all four third pared clique iterates from immutable ten-v28,
verify every coordinate of the compressed native map, and independently
check the exact coaffine-power retraction and both published connected-
summand/three-summand hypotheses. No native solver is executed.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import sys
import zlib

if sys.flags.optimize:
    raise RuntimeError("Do not optimize away four positive proof checks")

import networkx as nx

from research.order10_p4_crossdepth_o15_v25.verify import git_blob, source_rows
from research.order10_p3_global_v23_index.independent_verify import independent_p3

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "indeterminate_order_10_v28.txt"
SOURCE_BLOB = "35bb83b56bb8b4fd453b0ba272d354dc6b42e68c"
HISTORICAL_INDEX = ROOT / "research/order10_p3_global_v23_index/certificates.json"
HISTORICAL_INDEX_BLOB = "ab5a9f1c075dfad63b111929368147884519f2a3"
CERTIFICATE = Path(__file__).with_name("positive_retractions.json")
EXPECTED_INDICES = (10481909, 10586728, 11438191, 11578321)


def need(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def audit_endomorphism(G: nx.Graph, f: list[int]) -> None:
    """Every vertex and every original source edge, not a sample."""
    n = len(G)
    need(set(G) == set(range(n))
         and len(f) == n
         and all(type(v) is int and 0 <= v < n for v in f),
         "Malformed total original coaffine map")
    need(all(v != f[v] and not G.has_edge(v, f[v]) for v in G),
         "Coaffine vertex-neighborhood condition fails")
    need(all(f[u] == f[v] or G.has_edge(f[u], f[v])
             for u, v in G.edges()),
         "Coaffine weak morphism fails original source edge")


def audit_stable_retraction(
    G: nx.Graph, f: list[int], exponent: int,
) -> tuple[nx.Graph, list[int]]:
    audit_endomorphism(G, f)
    S = set(range(len(G)))
    while True:
        new = {f[v] for v in S}
        need(new <= S, "Stable image is not a nested image")
        if new == S:
            break
        S = new
    need(S and set(f[v] for v in S) == S,
         "Nonempty invariant eventual image not found")
    need(all(G.has_edge(u, v) == G.has_edge(f[u], f[v])
             for u in S for v in S),
         "Eventual coaffination is not a graph automorphism")
    need(type(exponent) is int and 1 <= exponent <= 100,
         "Wrong finite-power retraction exponent")
    r = list(range(len(G)))
    for _ in range(exponent):
        r = [f[v] for v in r]
    need(set(r) == S and all(r[v] == v for v in S),
         "Claimed endomorphism power does not fix its exact stable image")
    need(all(r[u] == r[v] or G.has_edge(r[u], r[v])
             for u, v in G.edges()),
         "Powered map is not an ordinary graph retraction")
    return G.subgraph(sorted(S)).copy(), r


def verify_factor_theorem(Y: nx.Graph, f: list[int], kind: str) -> dict:
    """Check every factor and cross-edge of the claimed expansive join."""
    H = nx.complement(Y)
    components = sorted(
        (sorted(c) for c in nx.connected_components(H)),
        key=lambda x: (len(x), min(x)),
    )
    orders = [len(c) for c in components]
    required = [2, 2, 7] if kind == "O2_join_complement_C7" else [2, 15]
    need(orders == required,
         "Stable image does not have the claimed complement components")
    for i, c in enumerate(components):
        need(set(f[v] for v in c) == set(c),
             "One alleged coaffine join factor is not invariant")
        need(all(v != f[v] and not Y.has_edge(v, f[v]) for v in c),
             "Factor automorphism is not coaffine")
        need(all(Y.has_edge(u, v) == Y.has_edge(f[u], f[v])
                 for u in c for v in c),
             "Factor automorphism fails an ordered pair")
        for other in components[i+1:]:
            need(all(Y.has_edge(u, v) for u in c for v in other),
                 "Alleged graph join is missing a cross-edge")
    for c in components:
        if len(c) == 2:
            need(H.has_edge(*c),
                 "Alleged octahedral antipodes are adjacent in Y")
    if kind == "O2_join_complement_C7":
        need(nx.is_isomorphic(H.subgraph(components[-1]), nx.cycle_graph(7))
             and nx.is_connected(Y.subgraph(components[-1])),
             "Seven-vertex factor is not connected complement(C7)")
        theorem = "Larrión--Neumann-Lara--Pizaña 2009, Theorem 3.6"
    else:
        need(nx.is_connected(Y.subgraph(components[-1])),
             "The fifteen-vertex coaffine summand is not connected")
        theorem = "Larrión--Neumann-Lara--Pizaña 2009, Theorem 4.6"
    return {
        "stable_image_vertices": len(Y),
        "stable_image_edges": Y.number_of_edges(),
        "complement_component_orders": orders,
        "coaffine_factors_invariant_and_automorphic": True,
        "at_least_one_connected_coaffine_factor": True,
        "complete_join_cross_edges": True,
        "published_expansivity_theorem": theorem,
        "image_expansive_and_K_divergent": True,
    }


def check_positive(row: dict, originals: dict[int, str]) -> tuple[dict, nx.Graph]:
    i = row["original_index"]
    source = row["original_graph6"]
    need(i in originals and originals[i] == source
         and source_rows(SOURCE)[i] == f"{i} 10 {source} - - -",
         "Wrong original McKay graph6 or currently unresolved source")
    G = independent_p3(source)
    g6 = nx.to_graph6_bytes(G, header=False).decode("ascii").strip()
    need([len(G), G.number_of_edges()] == row["P3"]
         and hashlib.sha256(g6.encode("ascii")).hexdigest()
             == row["P3_graph6_sha256"],
         "Independent complete third-iterate graph6 differs")
    need(row["map_codec"] == "zlib+base64/uint8"
         and row["native_value_order"] == "label"
         and type(row["native_states"]) is int
         and row["native_states"] >= 1,
         "Positive provenance schema changed")
    raw = zlib.decompress(base64.b64decode(
        row["map_zlib_base64"], validate=True
    ))
    need(len(raw) == len(G) and hashlib.sha256(raw).hexdigest()
         == row["map_raw_sha256"],
         "The permanent positive full coaffine map is corrupted")
    f = list(raw)
    Y, r = audit_stable_retraction(G, f, row["power_exponent"])
    need(len(Y) == row["stable_image_order"]
         and Y.number_of_edges() == row["stable_image_edges"],
         "Positive retract graph dimensions differ")
    kind = ("O2_join_complement_C7" if i == 11438191
            else "O1_join_connected_coaffine_15")
    proof = verify_factor_theorem(Y, f, kind)
    need(proof["complement_component_orders"] ==
         row["stable_image_complement_component_orders"],
         "Permanent complement decomposition differs")
    return ({
        "original_index": i,
        "P3": [len(G), G.number_of_edges()],
        "power_exponent": row["power_exponent"],
        "full_endomorphism_verified_on_every_edge": True,
        "ordinary_graph_retraction_verified_on_every_edge": True,
        "retract_description": kind,
        "retract": proof,
        "original_K_divergent": True,
    }, Y)


def verify() -> dict:
    need(git_blob(SOURCE.read_bytes()) == SOURCE_BLOB
         and git_blob(HISTORICAL_INDEX.read_bytes()) ==
             HISTORICAL_INDEX_BLOB,
         "Frozen ten-v28 or exact historical P3 source has changed")
    need((ROOT / "indeterminate_order_10.txt").read_bytes() ==
         SOURCE.read_bytes(),
         "Authoritative census root must remain ten-v28 until promotion")
    cert = json.loads(CERTIFICATE.read_text(encoding="utf-8"))
    need(cert.get("schema") == 1
         and cert.get("kind") ==
             "four_exact_P3_coaffine_power_retractions_onto_connected_coaffine_joins"
         and cert.get("source_git_blob") == SOURCE_BLOB
         and cert.get("frozen_exact_p3_class_blob") ==
             HISTORICAL_INDEX_BLOB
         and cert.get("historical_positive_workflow_run") == 45745202885
         and cert.get("limits_are_not_negative_proofs") is True,
         "Wrong permanent positive certificate provenance")
    originals = {i: row.split()[2] for i, row in source_rows(SOURCE).items()
                 if row.split()[1] == "10"}
    need(len(originals) == 613, "Wrong stiff ten-v28 cohort")
    positives = []
    targets = []
    need([row["original_index"] for row in cert["positives"]] ==
         list(EXPECTED_INDICES),
         "Exactly four McKay identities must be positively certified")
    for row in cert["positives"]:
        case, Y = check_positive(row, originals)
        positives.append(case)
        targets.append(Y)
    common = [targets[j] for j in (0, 1, 3)]
    need(all(nx.is_isomorphic(common[0], t) for t in common[1:]),
         "Three 17-vertex coaffine join retracts are not actually isomorphic")
    return {
        "schema": 1,
        "kind": "four_permanent_exact_coaffine_power_retractions_and_K_divergences",
        "source": SOURCE.name,
        "source_git_blob": SOURCE_BLOB,
        "originals_proven_K_divergent": list(EXPECTED_INDICES),
        "count_newly_proved_divergent": len(positives),
        "common_17_vertex_expansive_target_isomorphism_verified": True,
        "complete_retractions_replayed": positives,
        "census_snapshots_unchanged": True,
    }


def main() -> None:
    print(json.dumps(verify(), sort_keys=True, indent=2))
    print("PASS: four complete P3 coaffine-power retractions and "
          "connected-summand divergent originals independently certified",
          flush=True)


if __name__ == "__main__":
    main()
