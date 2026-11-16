"""Exact GF(2) homology filters and non-special retractions for snub K^0..K^3.

The search distinguishes:
- homologically impossible targets (no graph retraction possible),
- targets not present as induced subgraphs,
- full exhaustion of graph-retraction CSP over EVERY induced copy,
- verified positive retractions, if any.

For K^3, the complement's induced matchings encode *all* O_d and
its chordless cycles encode *all* complements of cycles. No clique
divergence or convergence is inferred from a negative result.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from itertools import combinations
import json
from pathlib import Path

import networkx as nx

SNUB = "GQyuzw"
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports/snub_retraction_homology_v1"
ORDERS_EDGES = ((8, 18), (12, 46), (20, 136), (56, 1196))
MAX_CSP_STATES = 10000


def raw_clique_graph(graph: nx.Graph) -> nx.Graph:
    """Build the next unpared K-iterate without importing pycliques."""
    cliques = [frozenset(c) for c in nx.find_cliques(graph)]
    result = nx.Graph()
    result.add_nodes_from(range(len(cliques)))
    result.add_edges_from(
        (i, j) for i, j in combinations(range(len(cliques)), 2)
        if cliques[i] & cliques[j]
    )
    return result


def snub_iterates() -> list[nx.Graph]:
    graph = nx.from_graph6_bytes(SNUB.encode("ascii"))
    result = []
    for n, edges in ORDERS_EDGES:
        if (len(graph), graph.number_of_edges()) != (n, edges):
            raise AssertionError("Unexpected snub clique-iterate graph")
        result.append(graph)
        if len(result) < 4:
            graph = raw_clique_graph(graph)
    return result


def bit_rank(columns) -> int:
    """Exact GF(2) column rank via highest-set-bit Gaussian elimination."""
    pivots = {}
    for word in columns:
        while word:
            j = word.bit_length() - 1
            old = pivots.get(j)
            if old is None:
                pivots[j] = word
                break
            word ^= old
    return len(pivots)


def full_betti(graph: nx.Graph) -> dict:
    """Compute every simplicial face and all boundary ranks (levels 0,1,2)."""
    faces = defaultdict(set)
    for facet in nx.find_cliques(graph):
        facet = sorted(facet)
        for size in range(1, len(facet)+1):
            faces[size-1].update(combinations(facet, size))
    simplices = {d:sorted(items) for d,items in faces.items()}
    ranks = {0: 0}
    for d in range(1, max(simplices)+1):
        positions = {s:i for i,s in enumerate(simplices[d-1])}
        def columns():
            for simplex in simplices[d]:
                col = 0
                for j in range(len(simplex)):
                    col ^= 1 << positions[simplex[:j]+simplex[j+1:]]
                yield col
        ranks[d] = bit_rank(columns())
    betti = {
        str(d): len(items)-ranks.get(d,0)-ranks.get(d+1,0)
        for d,items in simplices.items()
    }
    return {
        "complete": True,
        "faces_by_dimension": {str(k):len(v) for k,v in simplices.items()},
        "boundary_rank": {str(k):v for k,v in ranks.items() if k>0},
        "betti_mod2": betti,
    }


def k3_low_betti(graph: nx.Graph) -> dict:
    """Compute exact beta_0..beta_3 without expanding high-dimensional faces.

    Enumerate triangles/tetrahedra/five-vertex cliques in increasing label
    order, reducing boundary columns over GF(2). This is not an assertion
    about Betti numbers in dimensions >=4.
    """
    n = len(graph)
    neighbors = {v:set(graph[v]) for v in graph}
    edges = sorted(tuple(sorted(edge)) for edge in graph.edges())
    edge_index = {e:i for i,e in enumerate(edges)}
    triangles = []
    tetrahedra = []
    for a in range(n):
        for b in sorted(v for v in neighbors[a] if v>a):
            for c in sorted(v for v in neighbors[a]&neighbors[b] if v>b):
                triangles.append((a,b,c))
                for d in sorted(v for v in neighbors[a]&neighbors[b]&neighbors[c] if v>c):
                    tetrahedra.append((a,b,c,d))
    triangle_index = {face:i for i,face in enumerate(triangles)}
    tetra_index = {face:i for i,face in enumerate(tetrahedra)}

    rank2 = bit_rank(
        (1 << edge_index[(a,b)])
        ^ (1 << edge_index[(a,c)])
        ^ (1 << edge_index[(b,c)])
        for a,b,c in triangles
    )
    rank3 = bit_rank(
        (1 << triangle_index[(a,b,c)])
        ^ (1 << triangle_index[(a,b,d)])
        ^ (1 << triangle_index[(a,c,d)])
        ^ (1 << triangle_index[(b,c,d)])
        for a,b,c,d in tetrahedra
    )
    five_count = 0
    def boundary_four():
        nonlocal five_count
        for a,b,c,d in tetrahedra:
            for e in sorted(
                v for v in neighbors[a]&neighbors[b]&neighbors[c]&neighbors[d] if v>d
            ):
                five_count += 1
                yield (
                    (1 << tetra_index[(a,b,c,d)])
                    ^ (1 << tetra_index[(a,b,c,e)])
                    ^ (1 << tetra_index[(a,b,d,e)])
                    ^ (1 << tetra_index[(a,c,d,e)])
                    ^ (1 << tetra_index[(b,c,d,e)])
                )
    rank4 = bit_rank(boundary_four())
    # Connected graph => rank of edge-vertex boundary is n-1.
    rank1 = n-1
    betti = {
        "0":1,
        "1":len(edges)-rank1-rank2,
        "2":len(triangles)-rank2-rank3,
        "3":len(tetrahedra)-rank3-rank4,
    }
    if betti != {"0":1,"1":0,"2":0,"3":0}:
        raise AssertionError(f"Unexpected K3 low-dimensional homology {betti}")
    return {
        "complete": False,
        "faces_by_dimension": {
            "0":n, "1":len(edges), "2":len(triangles),
            "3":len(tetrahedra), "4":five_count,
        },
        "boundary_rank":{"1":rank1,"2":rank2,"3":rank3,"4":rank4},
        "betti_mod2":betti,
        "higher_dimensions": "not computed",
    }


def suspended_cycle(n: int) -> nx.Graph:
    graph = nx.cycle_graph(n)
    graph.add_nodes_from((n,n+1))
    graph.add_edges_from((v,u) for v in range(n) for u in (n,n+1))
    return graph


def octahedron(d: int) -> nx.Graph:
    return nx.complement(nx.disjoint_union_all([nx.path_graph(2) for _ in range(d)]))


def validate_retraction(graph: nx.Graph, target_vertices: set, mapping: dict) -> bool:
    """Replay a positive retract without calling the backtracking algorithm."""
    if (
        set(mapping) != set(graph)
        or set(mapping.values()) - target_vertices
        or any(mapping[v] != v for v in target_vertices)
    ):
        return False
    target = graph.subgraph(target_vertices)
    return all(
        mapping[u] == mapping[v] or target.has_edge(mapping[u],mapping[v])
        for u,v in graph.edges()
    )


def constrained_retraction(graph: nx.Graph, target_vertices: set, *, max_states=MAX_CSP_STATES):
    """Search a fixed induced target, preserving equality of edge images."""
    target = graph.subgraph(target_vertices)
    target_neighbors = {v:set(target[v])|{v} for v in target}
    variables = [v for v in graph if v not in target_vertices]
    domains = {}
    for v in variables:
        d = set(target_vertices)
        for neighbor in graph[v]:
            if neighbor in target_vertices:
                d.intersection_update(target_neighbors[neighbor])
        if not d:
            return "EXHAUSTED",None,0
        domains[v] = d
    assignment = {v:v for v in target_vertices}
    states = 0

    def recurse():
        nonlocal states
        states += 1
        if states > max_states:
            return "LIMIT"
        if len(assignment) == len(graph):
            return assignment.copy()
        choices = []
        for vertex in variables:
            if vertex in assignment:
                continue
            possibilities = domains[vertex].copy()
            for neighbor in graph[vertex]:
                if neighbor in assignment:
                    possibilities.intersection_update(
                        target_neighbors[assignment[neighbor]]
                    )
                    if not possibilities:
                        return False
            choices.append((len(possibilities),vertex,possibilities))
        _,v,choices_v = min(choices,key=lambda item:(item[0],item[1]))
        for image in sorted(choices_v):
            assignment[v] = image
            found = recurse()
            if found == "LIMIT" or found:
                return found
            del assignment[v]
        return False

    result = recurse()
    if result == "LIMIT":
        return "LIMIT_REACHED",None,states
    if result is False:
        return "EXHAUSTED",None,states
    if not validate_retraction(graph,target_vertices,result):
        raise AssertionError("Incorrect positive graph retraction")
    return "FOUND",result,states


def scan_subgraph_isomorphisms(graph: nx.Graph, target: nx.Graph):
    """Exhaust all induced *vertex sets*; target automorphisms are redundant."""
    matcher = nx.algorithms.isomorphism.GraphMatcher(graph,target)
    unique = set()
    embedding_count = 0
    total_states = 0
    for embedding in matcher.subgraph_isomorphisms_iter():
        embedding_count += 1
        vertices = frozenset(embedding)
        if vertices in unique:
            continue
        unique.add(vertices)
        status, mapping, states = constrained_retraction(graph,set(vertices))
        total_states += states
        if status == "LIMIT_REACHED":
            raise RuntimeError("CSP budget reached; cannot claim exhaustive absence")
        if status == "FOUND":
            return {
                "status":"FOUND",
                "embeddings_enumerated":embedding_count,
                "distinct_targets":len(unique),
                "csp_states":total_states,
                "target_vertices":sorted(vertices),
                "retraction_map":[mapping[v] for v in range(len(graph))],
            }
    return {
        "status":"EXHAUSTED",
        "embeddings_enumerated":embedding_count,
        "distinct_targets":len(unique),
        "csp_states":total_states,
    }


def early_retractions(graph: nx.Graph) -> dict:
    n = len(graph)
    targets = [("O_3",octahedron(3),"proven_divergent")]
    targets.extend(
        (f"Susp(C_{k})",suspended_cycle(k),
         "proven_divergent" if k in (5,6,7) else "structural_only")
        for k in range(5,min(18,n-2)+1)
    )
    targets.extend(
        (f"C_{k}^c",nx.complement(nx.cycle_graph(k)),"proven_divergent")
        for k in (8,10) if k<=n
    )
    rows = {}
    for label,target,known in targets:
        result = scan_subgraph_isomorphisms(graph,target)
        rows[label] = {"target_order":len(target),"target_status":known,**result}
    if any(row["status"]!="EXHAUSTED" for row in rows.values()):
        raise AssertionError("Unexpected positive/limited retraction: check proofs")
    return rows


def induced_matchings_cover(graph: nx.Graph, target_pairs: int):
    """Enumerate each induced matching in the complement exactly once."""
    complement = nx.complement(graph)
    edges = sorted(tuple(sorted(pair)) for pair in complement.edges())
    blocked = {v:set(complement[v])|{v} for v in complement}
    compatibility = []
    for i,(u,v) in enumerate(edges):
        unavailable = blocked[u]|blocked[v]
        mask = sum(
            1 << j for j in range(i+1,len(edges))
            if edges[j][0] not in unavailable and edges[j][1] not in unavailable
        )
        compatibility.append(mask)

    def search(level: int, candidates: int, chosen: tuple[int,...]):
        if level == target_pairs:
            yield frozenset(v for index in chosen for v in edges[index])
            return
        while candidates:
            bit = candidates & -candidates
            j = bit.bit_length()-1
            candidates ^= bit
            next_mask = candidates & compatibility[j]
            if next_mask.bit_count() >= target_pairs-level-1:
                yield from search(level+1,next_mask,chosen+(j,))
    for i in range(len(edges)):
        if compatibility[i].bit_count() >= target_pairs-1:
            yield from search(1,compatibility[i],(i,))


def k3_retractions(graph: nx.Graph) -> dict:
    stats = {}
    pair_targets = 0
    pair_states = 0
    for vertices in induced_matchings_cover(graph,5):
        pair_targets += 1
        status,mapping,states = constrained_retraction(graph,set(vertices))
        pair_states += states
        if status == "FOUND":
            raise AssertionError("Found O5 retraction; requires independent proof review")
        if status != "EXHAUSTED":
            raise RuntimeError("Incomplete O5 retraction search")
    # If there is no induced O6, larger O_d are impossible too.
    o6_count = sum(1 for _ in induced_matchings_cover(graph,6))
    stats["octahedra"] = {
        "O3_O4":"excluded_by_mod2_homology",
        "O5_induced_targets":pair_targets,
        "O5_retractions_found":0,
        "O5_CSP_states":pair_states,
        "O6_induced_targets":o6_count,
        "O_d_d_ge_6": "excluded_by_induced_O6_absence" if o6_count==0 else "unknown",
    }
    if o6_count:
        raise AssertionError("Unsearched O6 targets require further investigation")

    C = nx.complement(graph)
    cycle_counts = Counter()
    target_counts = Counter()
    target_states = Counter()
    for cycle in nx.chordless_cycles(C):
        length = len(cycle)
        cycle_counts[length] += 1
        if length in (14,15):
            target_counts[length] += 1
            status,mapping,states = constrained_retraction(graph,set(cycle))
            target_states[length] += states
            if status == "FOUND":
                raise AssertionError("Found cycle-complement retraction; verify independently")
            if status != "EXHAUSTED":
                raise RuntimeError("Incomplete cycle-complement retraction search")
        if length>=16:
            raise AssertionError("Unsearched long chordless cycles require followup")
    stats["cycle_complements"] = {
        "chordless_cycles_by_length": {str(k):v for k,v in sorted(cycle_counts.items())},
        "C14c_induced_targets":target_counts[14],
        "C14c_retractions_found":0,
        "C14c_CSP_states":target_states[14],
        "C15c_induced_targets":target_counts[15],
        "C15c_retractions_found":0,
        "C15c_CSP_states":target_states[15],
        "C_n_c_n_5_to_13":"excluded_by_mod2_homology",
        "C_n_c_n_ge_16":"excluded_by_no_chordless_cycles",
    }
    return stats


def compute() -> dict:
    graphs = snub_iterates()
    summary = []
    for level,graph in enumerate(graphs):
        homology = full_betti(graph) if level<3 else k3_low_betti(graph)
        if level<3:
            nonzero = {k:v for k,v in homology["betti_mod2"].items() if v}
            if nonzero != {"0":1,"2":1}:
                raise AssertionError("Unexpected early sphere homology")
            retractions = {"exhaustive":early_retractions(graph)}
        else:
            retractions = k3_retractions(graph)
        summary.append({
            "level":level,
            "order":len(graph),
            "edges":graph.number_of_edges(),
            "homology":homology,
            "retraction_tests":retractions,
        })
    return {
        "schema":1,
        "source_graph6":SNUB,
        "source":"raw clique iterates K^0 through K^3",
        "status":"finite tested target families ruled out; no clique-behavior verdict",
        "results":summary,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("print","verify","write"),nargs="?",default="print")
    args=p.parse_args()
    result=compute()
    path=OUTPUT/"results.json"
    encoded=json.dumps(result,sort_keys=True,indent=2)+"\n"
    if args.action=="write":
        OUTPUT.mkdir(parents=True,exist_ok=True)
        path.write_text(encoded,encoding="utf-8")
        print(path)
    elif args.action=="verify":
        if path.read_text(encoding="utf-8") != encoded:
            raise AssertionError("Saved result differs from reproducible calculation")
        print("Verified exact mod-2 ranks and exhaustive structural retraction searches")
    else:
        print(encoded)


if __name__ == "__main__":
    main()
