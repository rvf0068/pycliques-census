"""Exact finite clique-iterate comparison for six snub-retracting nine-cores.

Independently enumerate maximal cliques at each level. Extend an explicit
induced embedding by mapping every source maximal clique to its UNIQUE
maximal extension in the target. At K^4 use integer face masks, without
materializing a million-edge NetworkX graph. Verify every adjacency and
nonadjacency, and cone/complete-link witnesses proving the S^1 summand.

No result claims a proof of clique divergence or an all-iterate pattern.
Earlier censuses and proofs are read only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "research/order9_snub_retractions_v2/certificates.json"
SOURCE_MANIFEST = "research/order9_snub_retractions_v2/manifest.json"
CLASS_INDEX = "reports/order10_core_index_v1/classes.tsv"
DEST = "research/order9_snub_handle_iterates_v1"
SOURCE_SHA256 = "e24b6fd591ae04d209237a7a7ba13d3dbf712b8bc5a66f4009007836f7f6d225"
CLASS_SHA256 = "5a9b08c548aa5671f9c1403cf1badd0044211f7ef75129c83980462efa6f16eb"
EXPECTED_IDS = (2317843, 3148541, 3505942, 4952669, 4953338, 5601875)
EXPECTED_MEMBERS = (70, 114, 133, 86, 196, 111)
EXPECTED_SIZE_PAIRS = ((8, 9), (12, 14), (20, 21), (56, 58), (1076, 1077))
EXPECTED_EXTRA_LINKS_K4 = ((1, 1), (1, 1), (1, 82), (1, 1), (1, 62), (1, 34))


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def graph(g6: str) -> nx.Graph:
    g = nx.from_graph6_bytes(g6.encode("ascii"))
    return nx.convert_node_labels_to_integers(g)


def facets(g: nx.Graph) -> list[frozenset[int]]:
    return sorted(
        (frozenset(q) for q in nx.find_cliques(g)),
        key=lambda q: tuple(sorted(q)),
    )


def clique_graph_from_facets(f: list[frozenset[int]]) -> nx.Graph:
    g = nx.Graph()
    g.add_nodes_from(range(len(f)))
    g.add_edges_from(
        (i, j)
        for i in range(len(f))
        for j in range(i + 1, len(f))
        if f[i].intersection(f[j])
    )
    return g


def frozen_rows(root: Path) -> list[dict]:
    for path, expected in ((SOURCE, SOURCE_SHA256), (CLASS_INDEX, CLASS_SHA256)):
        if digest((root / path).read_bytes()) != expected:
            raise ValueError(f"Frozen original proof/index changed: {path}")
    manifest = json.loads((root / SOURCE_MANIFEST).read_text(encoding="utf-8"))
    if manifest["outputs_sha256"]["certificates.json"] != SOURCE_SHA256:
        raise ValueError("Existing independent snub certificate provenance changed")
    source = json.loads((root / SOURCE).read_text(encoding="utf-8"))
    if source["snub_graph6"] != "GQyuzw" or source["new_retract_core_ids"] != list(EXPECTED_IDS):
        raise ValueError("Expected six newly certified snub retractions have changed")
    rows = [
        r for r in source["records"]
        if r["core_id"] in EXPECTED_IDS
    ]
    if [r["core_id"] for r in rows] != list(EXPECTED_IDS):
        raise ValueError("Unexpected source certificate order")
    if tuple(r["original_order10_members"] for r in rows) != EXPECTED_MEMBERS:
        raise ValueError("Unexpected original ten-vertex class memberships")
    if any(
        r["status"] != "SNUB_RETRACT"
        or r["pared_K2_to_snub_pared_K2"] is not None
        or not r["retractions"]
        for r in rows
    ):
        raise ValueError("One of the six cores no longer satisfies the input theorem")
    return rows


def initial_embedding(h: nx.Graph, g: nx.Graph) -> list[int]:
    if len(h) != 8 or len(g) != 9:
        raise ValueError("Unexpected snub/order-nine source size")
    subgraph = g.subgraph([v for v in g if v != 2])
    matcher = nx.algorithms.isomorphism.GraphMatcher(h, subgraph)
    candidates = (
        tuple(bijection[i] for i in range(len(h)))
        for bijection in matcher.isomorphisms_iter()
    )
    try:
        return list(min(candidates))
    except ValueError as exc:
        raise ValueError("The core does not contain the recorded induced snub") from exc


def verify_small_embedding(h: nx.Graph, g: nx.Graph, phi: list[int]) -> None:
    if len(phi) != len(h) or len(set(phi)) != len(h):
        raise ValueError("Induced graph embedding is not injective")
    if any(
        h.has_edge(i, j) != g.has_edge(phi[i], phi[j])
        for i, j in combinations(range(len(h)), 2)
    ):
        raise ValueError("Induced source and target adjacency matrices disagree")


def even_attachment(
    h: nx.Graph, g: nx.Graph, phi: list[int], extra: int,
) -> dict:
    # Every neighbor of the extra vertex must belong to the old
    # induced source, and the link must be TWO disjoint complete graphs.
    inverse = {v: i for i, v in enumerate(phi)}
    neighbors = set(g.neighbors(extra))
    if not neighbors <= set(inverse):
        raise ValueError("The single new vertex has unrecorded new neighbors")
    link = h.subgraph([inverse[i] for i in neighbors])
    pieces = sorted(
        (sorted(component) for component in nx.connected_components(link)),
        key=lambda x: (len(x), x),
    )
    if len(pieces) != 2 or any(
        link.subgraph(piece).number_of_edges() != len(piece) * (len(piece) - 1) // 2
        for piece in pieces
    ):
        raise ValueError("Even iterate lacks a pair of disjoint complete link components")
    return {"kind": "two_clique_cone_bridge", "components": pieces}


def odd_attachment(
    h: nx.Graph, g: nx.Graph, phi: list[int], extras: list[int],
) -> dict:
    if len(extras) != 2 or not g.has_edge(*extras):
        raise ValueError("Odd iterate lacks the edge between its two extra vertices")
    supports = [
        sorted(i for i in range(len(h)) if g.has_edge(extra, phi[i]))
        for extra in extras
    ]
    if set(supports[0]).intersection(supports[1]) or any(not side for side in supports):
        raise ValueError("Odd iterate old-vertex supports overlap or are empty")
    apices = []
    for side in supports:
        # The induced clique complex is a cone at any vertex adjacent
        # (or equal) to every vertex of the support.
        centers = [
            i for i in side
            if all(i == j or h.has_edge(i, j) for j in side)
        ]
        if not centers:
            raise ValueError("An odd-iterate attachment link is not a verified cone")
        apices.append(min(centers))
    return {
        "kind": "adjacent_pair_disjoint_cone_links",
        "supports": supports, "cone_apices": apices,
    }


def mask(f: frozenset[int]) -> int:
    return sum(1 << v for v in f)


def fourth_attachment(
    f_h: list[frozenset[int]],
    f_g: list[frozenset[int]],
    phi: list[int],
    extra: int,
) -> tuple[dict, int, int]:
    # K^4 vertices are facets of the third iterate; intersections of
    # facet bitsets give every edge exactly, without building huge graphs.
    a = [mask(f) for f in f_h]
    b = [mask(f) for f in f_g]
    nh = len(f_h)
    if len(f_g) != nh + 1 or len(set(phi)) != nh:
        raise ValueError("Fourth-iterate embedding is not 1076 into 1077")
    edges = 0
    for i in range(nh):
        for j in range(i + 1, nh):
            old_edge = bool(a[i] & a[j])
            new_edge = bool(b[phi[i]] & b[phi[j]])
            if old_edge != new_edge:
                raise ValueError("K4 old vertices do not form an induced snub K4")
            edges += old_edge
    neighbor_labels = [
        i for i in range(nh) if b[phi[i]] & b[extra]
    ]
    # Build ONLY the link of the one added K4 vertex, not the full
    # 1077-vertex graph. This is an exact induced-subgraph test.
    link = nx.Graph()
    link.add_nodes_from(neighbor_labels)
    link.add_edges_from(
        (i, j) for i, j in combinations(neighbor_labels, 2)
        if a[i] & a[j]
    )
    pieces = sorted(
        (sorted(component) for component in nx.connected_components(link)),
        key=lambda x: (len(x), x),
    )
    if len(pieces) != 2 or any(
        link.subgraph(piece).number_of_edges() != len(piece) * (len(piece) - 1) // 2
        for piece in pieces
    ):
        raise ValueError("Fourth iterate fails exact two-clique ear test")
    return (
        {"kind": "two_clique_cone_bridge", "components": pieces},
        edges, edges + len(neighbor_labels)
    )


def one_core(source: dict, snub: nx.Graph) -> dict:
    h, g = snub.copy(), graph(source["core_graph6"])
    phi = initial_embedding(h, g)
    levels = []
    for degree in range(5):
        if degree == 4:
            # The level-four facet lists have just been constructed.
            extra = sorted(set(range(len(fg))) - set(phi))
            if len(extra) != 1:
                raise ValueError("Expected one extra fourth-iterate maximal clique")
            attachment, edges_h, edges_g = fourth_attachment(fh, fg, phi, extra[0])
            size_h, size_g = len(fh), len(fg)
        else:
            verify_small_embedding(h, g, phi)
            size_h, size_g = len(h), len(g)
            edges_h, edges_g = h.number_of_edges(), g.number_of_edges()
            extra = sorted(set(g) - set(phi))
            attachment = (
                even_attachment(h, g, phi, extra[0])
                if degree % 2 == 0 and len(extra) == 1
                else odd_attachment(h, g, phi, extra)
            )
        if (size_h, size_g) != EXPECTED_SIZE_PAIRS[degree]:
            raise ValueError(f"Unexpected vertex pair at iterate {degree}")
        levels.append({
            "iterate": degree,
            "snub_order": size_h, "core_order": size_g,
            "snub_edges": edges_h, "core_edges": edges_g,
            "snub_to_core_vertex_map": phi,
            "extra_core_vertices": extra,
            "link_certificate": attachment,
        })
        if degree == 4:
            break
        fh, fg = facets(h), facets(g)
        index = {f: j for j, f in enumerate(fg)}
        next_phi = []
        for q in fh:
            required = {phi[v] for v in q}
            extensions = [
                j for j, f in enumerate(fg)
                if required.issubset(f)
            ]
            if len(extensions) != 1:
                raise ValueError("A source maximal clique has nonunique target maximal extension")
            next_phi.append(extensions[0])
        if len(set(next_phi)) != len(next_phi):
            raise ValueError("Maximal-clique map is not injective")
        phi = next_phi
        if degree < 3:
            h, g = clique_graph_from_facets(fh), clique_graph_from_facets(fg)
    if tuple(
        tuple(len(component) for component in level["link_certificate"]["components"])
        for level in (levels[4],)
    )[0] not in EXPECTED_EXTRA_LINKS_K4:
        raise ValueError("Unexpected noncanonical K4 bridge link")
    return {
        "core_id": source["core_id"],
        "core_graph6": source["core_graph6"],
        "order9_index": source["order9_index"],
        "original_order10_members": source["original_order10_members"],
        "levels": levels,
    }


def prepare(root: Path = ROOT) -> dict[str, bytes]:
    sources = frozen_rows(root)
    snub = graph("GQyuzw")
    records = [one_core(row, snub) for row in sources]
    expected_links = [
        tuple(map(len, row["levels"][4]["link_certificate"]["components"]))
        for row in records
    ]
    if tuple(expected_links) != EXPECTED_EXTRA_LINKS_K4:
        raise ValueError("Six expected K4 link signatures have changed")
    cert = {
        "schema": 1, "snub_graph6": "GQyuzw",
        "scope": "Exact induced-clique-iterate embeddings and contractible attachment links, levels zero through four ONLY",
        "no_all_iterate_theorem": True,
        "no_new_K_divergence_verdicts": True,
        "original_ten_graphs_represented": 710,
        "records": records,
    }
    report = [
        "# A persistent circle attachment in six snub-retracting cores",
        "",
        "## Theorem (finite, exact, independently reproducible)",
        "",
        "Let S be the eight-vertex snub disphenoid `GQyuzw`. Let G be",
        "any of the six nine-vertex stiff cores below. For EVERY j=0,...,4,",
        "K^j(S) is isomorphic to a recorded **induced** subgraph of K^j(G),",
        "and as clique complexes:",
        "",
        "**Delta(K^j(G)) is homotopy equivalent to Delta(K^j(S)) wedge S^1.**",
        "",
        "This is a theorem **only for these five finite iterates**. It does",
        "**not** imply K-divergence, K-convergence, or the same clique behavior",
        "at all future iterates. The snub's divergence remains conjectural.",
        "",
        "| j | Order K^j(S) | Order K^j(G) | Exact attachment type |",
        "|---:|---:|---:|---|",
        "| 0 | 8 | 9 | 1 vertex, link is two disjoint cliques |",
        "| 1 | 12 | 14 | 2 adjacent vertices, disjoint nonempty cone links |",
        "| 2 | 20 | 21 | 1 vertex, link is two disjoint cliques |",
        "| 3 | 56 | 58 | 2 adjacent vertices, disjoint nonempty cone links |",
        "| 4 | 1076 | 1077 | 1 vertex, link is two disjoint cliques |",
        "",
        "## Complete six-core witness table",
        "",
        "| Nine-core ID | Graph6 | Ten-vertex originals | K4 extra-link clique sizes |",
        "|---:|---|---:|---|",
    ]
    for rec, link in zip(records, expected_links):
        report.append(
            f"| {rec['core_id']} | \`{rec['core_graph6']}\` | "
            f"{rec['original_order10_members']} | {link[0]} + {link[1]} |"
        )
    report += [
        "",
        "These six distinct classes represent **710** original ten-vertex",
        "graphs. Their K-behavior remains unresolved, as does that of S.",
        "",
        "## Proof of the homotopy equivalence",
        "",
        "We use two elementary simplicial gluing lemmas, valid whenever the",
        "old graph X is connected. First, add one vertex x with link the",
        "disjoint union of two nonempty complete subgraphs A,B of X.",
        "Then Delta(X+x) is Delta(X) union the cone on",
        "Delta(A) disjoint union Delta(B). Both pieces of that link",
        "are contractible. Contracting each component within its mapping",
        "cylinder shows Delta(X+x) is homotopy equivalent to",
        "Delta(X) wedge S^1.",
        "",
        "Second, add adjacent vertices x,y to X so their sets of old",
        "neighbors P,Q are disjoint and the clique complexes of X[P]",
        "and X[Q] are each cones. The closed simplicial stars of x and y",
        "are contractible and intersect in the closed star of edge xy,",
        "also contractible. Their union B is therefore contractible.",
        "Its intersection with Delta(X) is precisely the disjoint union",
        "Delta(X[P]) disjoint union Delta(X[Q]). The same homotopy-pushout",
        "argument proves Delta(X+x+y) equivalent to Delta(X) wedge S^1.",
        "",
        "Each recorded even-level link is checked to consist of exactly",
        "two induced complete components. Each odd-level attachment is",
        "checked to have an edge xy, disjoint nonempty supports in X,",
        "and explicit universal vertices in both supports (cone apices).",
        "These are *stronger* witnesses than homology calculations.",
        "",
        "## Proof of each induced embedding",
        "",
        "At level zero, independently verify an eight-vertex induced snub",
        "by testing all pairwise adjacencies, not only edges. To pass",
        "from j to j+1, enumerate all maximal cliques of both graphs.",
        "For every source maximal clique Q, its image has **exactly one**",
        "maximal target extension. Distinct source cliques have distinct",
        "extensions, and their intersection graphs agree on *every pair*",
        "of old vertices (including nonedges). The resulting map is thus",
        "an induced copy of K^(j+1)(S). Repeat through j=4.",
        "",
        "At j=4 the checker avoids creating the 1077-vertex clique graph:",
        "the integer bitsets of the 1076 and 1077 third-iterate facets",
        "give the exact pairwise intersections, and therefore all edges,",
        "nonedges, and both parts of the new vertex's link.",
        "All explicit vertex maps and cone/component witnesses are stored",
        "in certificates.json, together with source graph6 and class IDs.",
        "",
        "## Why the divergence question remains open",
        "",
        "The five verified cases suggest a recurrence: one extra vertex",
        "in even iterates, two adjacent extras in odd iterates. Such a",
        "uniform bound at *every* iterate would imply equality of",
        "K-convergence/divergence behavior with the snub, but no induction",
        "hypothesis preserved under K has yet been proved. In particular,",
        "these finite equalities cannot be used as a divergence certificate.",
        "",
        "## Reproduction",
        "",
        "From pycliques-census, with its pinned historical environment:",
        "",
        "```bash",
        "bash scripts/bootstrap_special_k3_v5.sh",
        ".venv-special-k3-v5/bin/python scripts/core9_snub_handle_iterates_v1.py verify",
        ".venv-special-k3-v5/bin/python -m unittest discover -s tests -p 'test_core9_snub_handle_iterates_v1.py' -v",
        "```",
        "",
        "The verifier checks the frozen source SHA-256, all original classes,",
        "all five embeddings and links, and byte-for-byte identity of",
        "every versioned output. No historical results are modified.",
        "",
    ]
    markdown = "\n".join(report).replace("\\`", "`")
    out = {
        "certificates.json": (json.dumps(cert, sort_keys=True, indent=2) + "\n").encode(),
        "summary.md": markdown.encode("utf-8"),
    }
    manifest = {
        "schema": 1, "stage": "core9_snub_handle_iterates_v1",
        "source_sha256": SOURCE_SHA256,
        "source_class_index_sha256": CLASS_SHA256,
        "cores": list(EXPECTED_IDS),
        "checked_iterates": [0, 1, 2, 3, 4],
        "outputs_sha256": {k: digest(v) for k, v in sorted(out.items())},
    }
    out["manifest.json"] = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    return {str(Path(DEST) / k): v for k, v in out.items()}


def verify(root: Path = ROOT) -> None:
    for filename, expected in prepare(root).items():
        path = root / filename
        if not path.is_file() or path.read_bytes() != expected:
            raise ValueError(f"Missing or altered exact circle-attachment witness: {filename}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "verify", "report"))
    args = parser.parse_args()
    data = prepare()
    if args.action == "build":
        for filename, content in data.items():
            path = ROOT / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and path.read_bytes() != content:
                raise ValueError(f"Refusing to overwrite a differing proof: {filename}")
            path.write_bytes(content)
    if args.action != "report":
        verify()
    if args.action == "report":
        print(data[f"{DEST}/summary.md"].decode())
    else:
        print("Verified six snub-related nine-cores across K^0..K^4; "
              "exact circle summand at every checked level; no clique-divergence verdict.")


if __name__ == "__main__":
    main()
