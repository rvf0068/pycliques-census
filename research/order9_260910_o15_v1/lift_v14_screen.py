"""Positive-only direct/retraction/P2 lifts from new McKay 260910 O15 proof.

Unmerged researcher pilot: never edits indices, never claims convergence.
Uses public pycliques as the graph/retraction engine. An exact independent
O15 source proof is required at launch.

Reads immutable v14 (2568 rows, 120 F45 conditional) so the results can
be compared with pending PR #63 v15, not silently assumed disjoint.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import networkx as nx
import pycliques

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SOURCE = ROOT / "indeterminate_order_10_v14.txt"
REFERENCE = "HUZvvzu"
SOURCE_BLOB = "3ee92e02891b3046059241d4a2304794b0e34380"


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def canon_p2(g: nx.Graph, bound: int = 1500) -> nx.Graph | None:
    current = pycliques.completely_pared_graph(g)
    for _ in range(2):
        k = pycliques.clique_graph(current, bound=bound)
        if k is None:
            return None
        current = pycliques.completely_pared_graph(k)
    return nx.convert_node_labels_to_integers(current)


def signature(g: nx.Graph) -> tuple:
    return (
        len(g), g.number_of_edges(),
        tuple(sorted(d for _, d in g.degree())),
        nx.weisfeiler_lehman_graph_hash(nx.complement(g)),
    )


def exact_mapping(g: nx.Graph, target: nx.Graph) -> dict | None:
    if signature(g) != signature(target):
        return None
    gm = nx.isomorphism.GraphMatcher(nx.complement(g), nx.complement(target))
    if not gm.is_isomorphic():
        return None
    mapping = gm.mapping
    if not all(
        g.has_edge(u, v) == target.has_edge(mapping[u], mapping[v])
        for u in g for v in g
    ):
        raise AssertionError("VF2 returned nonisomorphism")
    return mapping


def find_direct_retraction(
    g: nx.Graph, target: nx.Graph,
) -> dict | None:
    if not len(g) == len(target) + 1:
        return None
    # pycliques.retracts is an exact positive finder using induced VF2
    # embeddings, weak graph maps and the target fixed-point condition.
    certificate = pycliques.retracts(g, target)
    if not isinstance(certificate, tuple):
        return None
    projection, inclusion = certificate
    if not pycliques.verify_retraction_witness(g, target, certificate):
        raise AssertionError("Invalid public-pycliques direct retraction")
    return {
        "projection": [[int(v), int(w)] for v, w in sorted(projection.items())],
        "inclusion": [[int(v), int(w)] for v, w in sorted(inclusion.items())],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--shards", type=int, default=1)
    args = parser.parse_args()
    if not 0 <= args.shard < args.shards:
        raise ValueError("Invalid shard")
    from research.order9_260910_o15_v1.verify import verify

    verify()
    raw = SOURCE.read_bytes()
    if git_blob(raw) != SOURCE_BLOB:
        raise AssertionError("Frozen v14 input changed")
    rows = [x.split() for x in raw.decode("utf-8").splitlines()
            if x and not x.startswith("#")]
    if len(rows) != 2568 or len({int(x[0]) for x in rows}) != 2568:
        raise AssertionError("Wrong v14 census population")

    target = nx.from_graph6_bytes(REFERENCE.encode("ascii"))
    p2_target = canon_p2(target)
    if p2_target is None:
        raise AssertionError("Positive reference P2 bound unexpectedly exceeded")
    reference_p2_signature = [len(p2_target), p2_target.number_of_edges()]
    print("REFERENCE_P2", reference_p2_signature, flush=True)

    matches = []
    skipped = []
    candidates = 0
    core_cache = {}
    direct_cache = {}
    for row in rows:
        original = int(row[0])
        if original % args.shards != args.shard:
            continue
        candidates += 1
        g6, order = row[2], int(row[1])
        if g6 not in core_cache:
            source = nx.from_graph6_bytes(g6.encode("ascii"))
            if len(source) != order:
                raise AssertionError(f"Wrong order for McKay {original}")

            claim = None
            if order == len(target):
                witness = exact_mapping(source, target)
                if witness is not None:
                    claim = {
                        "kind": "reference",
                        "map": [[int(k), int(v)] for k, v in sorted(witness.items())],
                    }
            elif order == len(target) + 1:
                if g6 not in direct_cache:
                    direct_cache[g6] = find_direct_retraction(source, target)
                if direct_cache[g6] is not None:
                    claim = {
                        "kind": "retraction",
                        **direct_cache[g6],
                    }

            if claim is None:
                p2_source = canon_p2(source)
                if p2_source is None:
                    skipped.append(g6)
                else:
                    witness = exact_mapping(p2_source, p2_target)
                    if witness is not None:
                        claim = {
                            "kind": "P2_iso",
                            "map": [[int(k), int(v)] for k, v in sorted(witness.items())],
                            "p2_order": len(p2_source),
                            "p2_edges": p2_source.number_of_edges(),
                        }
            core_cache[g6] = claim

        claim = core_cache[g6]
        if claim is not None:
            found = {"index": original, "source_g6": g6, "source_order": order, **claim}
            matches.append(found)
            print("POSITIVE", original, claim["kind"], flush=True)
        if candidates % 500 == 0:
            print("PROGRESS", args.shard, candidates, "positives", len(matches),
                  "distinct", len(core_cache), flush=True)
    data = {
        "schema": 1, "reference_original_index": 260910,
        "reference_g6": REFERENCE,
        "reference_p2": reference_p2_signature,
        "source_v14_git_blob": SOURCE_BLOB,
        "shard": args.shard, "shards": args.shards,
        "processed": candidates, "distinct_core_graph6": len(core_cache),
        "skipped_P2_bound": sorted(set(skipped)),
        "positive": matches,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")
    print("SUMMARY", candidates, "POSITIVE", len(matches),
          "skipped", len(set(skipped)),
          "by_kind", dict(Counter(x["kind"] for x in matches)), flush=True)


if __name__ == "__main__":
    main()
