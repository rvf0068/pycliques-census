"""Reproduce the exhaustive finite nine-reference direct-retraction screen.

Discovery is independent of the saved bijections: use NetworkX GraphMatcher
and check vertex deletion/projection directly from frozen ten-v22 graph6.
Negative results are *not* K-convergence certificates.
"""
from __future__ import annotations

from collections import Counter
import json

import networkx as nx

from .verify import (
    CERT, ROOT, V22, REFERENCES, BY_REFERENCE, check, rows,
)


def has_direct_projection(source: nx.Graph, target: nx.Graph) -> bool:
    """Whether some nine-point induced section is a retract of a 10-graph."""
    target_degrees = sorted(d for _, d in target.degree())
    vertices = sorted(source)
    for deleted in vertices:
        keep = [v for v in vertices if v != deleted]
        # A one-vertex retraction to the induced section must send u to
        # a retained vertex v with N(u) subset N(v) union {v}.
        valid_images = [
            v for v in keep
            if all(v == w or source.has_edge(v, w)
                   for w in source[deleted])
        ]
        if not valid_images:
            continue
        section = source.subgraph(keep)
        if sorted(d for _, d in section.degree()) != target_degrees:
            continue
        if nx.algorithms.isomorphism.GraphMatcher(
            section, target
        ).is_isomorphic():
            # No extra edge test is needed: a valid image together with
            # pointwise fixation is already a total ordinary retraction.
            return True
    return False


def screen() -> None:
    prior = rows(V22)
    v4 = rows(ROOT / "indeterminate_order_9_v4.txt")
    unresolved = rows(ROOT / "indeterminate_order_9_v9.txt")
    nine_proved = sorted(set(v4) - set(unresolved))
    check(len(nine_proved) == 9 and set(REFERENCES) <= set(nine_proved),
          "Wrong independent nine-source target pool")
    nine_targets = {
        i: nx.from_graph6_bytes(v4[i].split()[2].encode("ascii"))
        for i in nine_proved
    }
    check(all(nx.is_connected(t) and len(t) == 9 for t in nine_targets.values()),
          "Invalid proved nine-target graph6")
    for i, g6 in REFERENCES.items():
        check(v4[i] == f"{i} 9 {g6} - - -",
              f"Changed nine-source identity {i}")

    found: dict[int, int] = {}
    checked = 0
    for original_index, record in prior.items():
        index, order, graph6, *_ = record.split()
        if int(order) != 10:
            continue
        checked += 1
        graph = nx.from_graph6_bytes(graph6.encode("ascii"))
        check(len(graph) == 10, f"Wrong stiff ten-vertex graph6: {index}")
        for ref, target in nine_targets.items():
            if has_direct_projection(graph, target):
                found[original_index] = ref
                break

    archive = json.loads(CERT.read_text(encoding="utf-8"))
    certified = {case["original_index"]: case["reference_index"]
                 for case in archive["witnesses"]}
    check(checked == 778, f"Wrong original stiff ten-core search size: {checked}")
    check(found == certified,
          f"Independent full screen disagrees: missed={sorted(set(certified)-set(found))}, "
          f"unexpected={sorted(set(found)-set(certified))}, "
          f"reference_disagreements={[i for i in found if i in certified and found[i] != certified[i]]}")
    distribution = Counter(found.values())
    check(distribution == BY_REFERENCE, f"Wrong exhaustive target counts: {distribution}")
    print(f"PASS: exhaustive independent direct-retraction screen of {checked}"
          f" stiff ten-vertex originals against {len(nine_targets)} certified"
          " nine-vertex divergent references; exactly 149 positive originals"
          " matching the archived certificates; no negative verdicts.")


if __name__ == "__main__":
    screen()
