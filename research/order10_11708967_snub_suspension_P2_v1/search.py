"""Exact McKay 11708967 suspended-snub structure and pinned P2 native pilot.

Uses the existing independently verified canonical maximal-clique
enumerators and ordinary dominated-vertex paring. Invokes only the
existing public native pycliques coaffine and octahedral solvers,
without duplicating a native solver or modifying the monorepo.
Full positive maps are independently replayed on all source edges;
no timeout or exhaustion is a K-behavior classification.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("Cannot optimize away suspension P2 source proof")

import networkx as nx

from research.order10_p4_crossdepth_o15_v25.verify import git_blob, source_rows
from research.order10_p3_global_v23_index.independent_verify import (
    independent_clique_graph, independent_pare,
)
from research.order10_five_p3_native_v1.search import (
    MONOREPO_SHA, validate_runtime,
)
from research.order10_overcap_p3_coaffine_v1.pilot import (
    independent_octahedral_retraction_check,
)
from research.order10_three_p3_coaffine_native_v1.verify import (
    audit_positive_map,
)
from research.order10_v28_p3_coaffine_all_v1.orbit_certificates import (
    orbit_certificate,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "indeterminate_order_10_v28.txt"
SOURCE_BLOB = "35bb83b56bb8b4fd453b0ba272d354dc6b42e68c"
INDEX = 11708967
SOURCE_G6 = "IQyuzz~~o"
SNUB_G6 = "GQyuzw"
POLICIES = ("label", "fiber")
KINDS = ("coaffine", "octahedral")
MAX_STATES = 500_000
TIME_LIMIT = 45.0


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise AssertionError(reason)


def graph6_digest(graph: nx.Graph) -> str:
    require_ints = set(graph) == set(range(len(graph)))
    need(require_ints, "Canonical P2 graph labels required")
    raw = nx.to_graph6_bytes(graph, header=False).strip()
    return hashlib.sha256(raw).hexdigest()


def source() -> tuple[nx.Graph, nx.Graph, nx.Graph]:
    need(git_blob(SOURCE.read_bytes()) == SOURCE_BLOB,
         "Immutable ten-v28 source Git blob changed")
    rows = source_rows(SOURCE)
    need(len(rows) == 1043
         and rows[INDEX] == f"{INDEX} 10 {SOURCE_G6} - - -",
         "Original connected-ten McKay graph6 or status differs")

    G = nx.from_graph6_bytes(SOURCE_G6.encode("ascii"))
    need(len(G) == 10 and G.number_of_edges() == 34
         and nx.is_connected(G), "Unexpected original connected ten-graph")

    # Derive the two suspension poles from the original graph, not
    # hard-coded node indices. Each pole is adjacent to precisely
    # the other eight vertices, and not to the other pole.
    poles = sorted(v for v in G if G.degree[v] == 8)
    need(len(poles) == 2 and not G.has_edge(*poles),
         "Original does not have two nonadjacent universal base poles")
    base = G.copy()
    base.remove_nodes_from(poles)
    need(len(base) == 8
         and all(set(G[p]) == set(base) for p in poles)
         and nx.is_isomorphic(base, nx.from_graph6_bytes(SNUB_G6.encode("ascii"))),
         "Original is not the suspension of the verified snub disphenoid")

    G0 = independent_pare(G)
    need(len(G0) == 10, "Original is not stiff")
    P1 = independent_pare(independent_clique_graph(
        G0, stage=1, orders=[10]
    ))
    need((len(P1), P1.number_of_edges()) == (24,236),
         "First completely pared clique graph differs")
    P2 = independent_pare(independent_clique_graph(
        P1, stage=2, orders=[10,24]
    ))
    need((len(P2), P2.number_of_edges()) == (288,37772),
         "Second completely pared clique graph differs")

    # General exact suspension identity:
    # complement K(O1*H) == K2 tensor_product complement K(H).
    S = nx.convert_node_labels_to_integers(base, ordering="sorted")
    KS = independent_clique_graph(S, stage=1, orders=[8])
    doublecover = nx.tensor_product(nx.complete_graph(2), nx.complement(KS))
    need((len(KS), KS.number_of_edges()) == (12,46)
         and (len(doublecover), doublecover.number_of_edges()) == (24,40)
         and nx.is_isomorphic(nx.complement(P1), doublecover),
         "Suspension clique-graph categorical-double-cover identity fails")
    complement_P2 = nx.complement(P2)
    components = sorted(
        [complement_P2.subgraph(v).copy()
         for v in nx.connected_components(complement_P2)],
        key=len,
    )
    need([len(c) for c in components] == [2,286]
         and components[0].number_of_edges() == 1,
         "Unexpected second-iterate complement decomposition")
    return G,P1,P2


def probe(policy: str, kind: str) -> dict:
    need(policy in POLICIES and kind in KINDS,
         "Unexpected native policy or graph-retraction family")
    runtime = validate_runtime()
    _,P1,X = source()
    if kind == "coaffine":
        from pycliques import find_coaffine_endomorphism
        native = find_coaffine_endomorphism(
            X, backend="native", value_order=policy,
            max_states=MAX_STATES, time_limit=TIME_LIMIT,
        )
    else:
        from pycliques import find_octahedral_retraction_coaffine
        native = find_octahedral_retraction_coaffine(
            X, backend="native", value_order=policy,
            min_dimension=3, max_states=MAX_STATES,
            time_limit=TIME_LIMIT,
        )
    status = native.status.name
    need(status in ("FOUND","EXHAUSTED","LIMIT_REACHED")
         and type(native.states_explored) is int
         and 0 <= native.states_explored <= MAX_STATES
         and type(native.assignments_tried) is int
         and native.assignments_tried >= 0
         and type(native.arc_revisions) is int
         and native.arc_revisions >= 0,
         "Malformed exact pinned native result")
    item = {
        "schema": 1,
        "kind": "bound_native_P2_of_suspension_of_snub",
        "original_index": INDEX,
        "original_graph6": SOURCE_G6,
        "immutable_source_blob": SOURCE_BLOB,
        "monorepo_solver_commit": MONOREPO_SHA,
        "installed_native_code_blobs_verified": True,
        "dependency_versions": runtime,
        "P1": [len(P1), P1.number_of_edges()],
        "P2": [len(X), X.number_of_edges()],
        "P2_graph6_sha256": graph6_digest(X),
        "policy": policy,
        "target_family": kind,
        "max_states": MAX_STATES,
        "time_limit_seconds": TIME_LIMIT,
        "status": status,
        "states_explored": native.states_explored,
        "assignments_tried": native.assignments_tried,
        "arc_revisions": native.arc_revisions,
        "no_negative_behavior_from_exhaustion_or_limit": True,
    }
    if status == "FOUND":
        if kind == "coaffine":
            need(native.endomorphism is not None,
                 "FOUND coaffine map is missing")
            f = [native.endomorphism[v] for v in range(len(X))]
            full = audit_positive_map(X,f)
            orbit = orbit_certificate(X,f)
            item["complete_coaffine_weak_endomorphism"] = f
            item["stable_retraction_analysis"] = full
            item["invariant_coaffine_orbit_analysis"] = orbit
            item["original_K_divergent_proved"] = bool(
                full["expansive_witness"]["proved"]
                or orbit["expansive_coaffine_subgraph_proved"]
            )
        else:
            need(native.dimension is not None
                 and native.antipodal_pairs is not None
                 and native.retraction is not None,
                 "FOUND octahedral retraction is incomplete")
            pairs = tuple(tuple(q) for q in native.antipodal_pairs)
            independent_octahedral_retraction_check(
                X,pairs,native.retraction
            )
            item["target_dimension"] = native.dimension
            item["antipodal_pairs"] = [list(q) for q in pairs]
            item["complete_ordinary_retraction"] = [
                native.retraction[v] for v in range(len(X))
            ]
            item["original_K_divergent_proved"] = True
    else:
        need(getattr(native,"endomorphism",None) is None
             and getattr(native,"retraction",None) is None,
             "Inconclusive native return contained an unverified map")
    return item


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--policy", choices=POLICIES, required=True)
    p.add_argument("--kind", choices=KINDS, required=True)
    p.add_argument("--output", type=Path, required=True)
    options = p.parse_args()
    record = probe(options.policy, options.kind)
    options.output.parent.mkdir(parents=True,exist_ok=True)
    options.output.write_text(
        json.dumps(record,sort_keys=True,indent=2)+"\n",encoding="utf-8"
    )
    print(f"PASS: suspension-snub P2 exact {options.kind} "
          f"policy={options.policy} status={record['status']} "
          f"states={record['states_explored']} "
          f"K_divergent_proved={record.get('original_K_divergent_proved',False)}",
          flush=True)


if __name__ == "__main__":
    main()
