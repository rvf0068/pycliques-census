"""Verify saved divergence proofs from triangular double covers.

All intermediate clique graphs are recomputed. Supported witness types:
cover_pared_clockwork (including deleting non-triangle edges) and
cover_coaffine_embedding (LNP 2006, Theorems 2.6 and 3.1).
Covering and edge-deletion implications follow LNPV 2013 and FANP 2013.
This module replays finite witnesses; it does not search for new ones.
"""
from itertools import combinations
import networkx as nx

if not __debug__:
    raise RuntimeError("Never run certificate validation under Python -O")


def clique_step(graph, max_cliques=250, max_edges=15000):
    cliques = []
    for complete in nx.find_cliques(graph):
        cliques.append(tuple(sorted(complete)))
        if len(cliques) > max_cliques:
            raise ValueError("clique count exceeded verification budget")
    cliques.sort()
    h = nx.Graph()
    h.add_nodes_from(range(len(cliques)))
    for i, q in enumerate(cliques):
        for j in range(i):
            if not set(q).isdisjoint(cliques[j]):
                h.add_edge(i, j)
                if h.number_of_edges() > max_edges:
                    raise ValueError("edge count exceeded verification budget")
    return h, cliques


def completely_pared(graph):
    h = graph.copy()
    while True:
        victim = None
        for v in h:
            closed = set(h[v]) | {v}
            for w in h[v]:
                if closed <= set(h[w]) | {w}:
                    victim = v
                    break
            if victim is not None:
                break
        if victim is None:
            return h
        h.remove_node(victim)


def triangular_double_cover(base, voltage_one):
    """Cover vertex 2*v+s represents vertex v in sheet s."""
    n = len(base)
    assert set(base) == set(range(n))
    shifts = {frozenset(edge) for edge in voltage_one}
    assert len(shifts) == len(voltage_one)
    assert shifts <= {frozenset(edge) for edge in base.edges()}
    for triple in combinations(base, 3):
        if all(base.has_edge(*edge) for edge in combinations(triple, 2)):
            assert sum(frozenset(edge) in shifts
                       for edge in combinations(triple, 2)) % 2 == 0
    cover = nx.Graph()
    cover.add_nodes_from(range(2*n))
    for u, v in base.edges():
        change = int(frozenset((u, v)) in shifts)
        for s in (0, 1):
            cover.add_edge(2*u+s, 2*v+(s ^ change))
    assert nx.is_connected(cover)
    for v in cover:
        local = {v} | set(cover[v])
        neighbors = {v//2} | set(base[v//2])
        assert {x//2 for x in local} == neighbors
        assert len(local) == len(neighbors)
        assert all(
            cover.has_edge(x, y) == base.has_edge(x//2, y//2)
            for x, y in combinations(local, 2)
        )
    deck = {v:v^1 for v in cover}
    assert all(cover.has_edge(deck[u], deck[v]) for u, v in cover.edges())
    return cover, deck


def check_coaffine(graph, symmetry, radius):
    assert set(symmetry) == set(graph)
    assert set(symmetry.values()) == set(graph)
    assert all(symmetry[symmetry[v]] == v for v in graph)
    assert all(graph.has_edge(symmetry[u], symmetry[v]) for u, v in graph.edges())
    assert all(nx.shortest_path_length(graph, v, symmetry[v]) >= radius
               for v in graph)


def lift_symmetry(cliques, symmetry):
    index = {q:i for i,q in enumerate(cliques)}
    assert len(index) == len(cliques)
    return {i:index[tuple(sorted(symmetry[v] for v in q))]
            for i,q in enumerate(cliques)}


def verify_witness(graph, witness):
    """Replay every assertion from graph G and supplied finite witness."""
    assert isinstance(witness, dict)
    base = graph.copy()
    for u,v in witness.get("deleted_edges", []):
        assert base.has_edge(u, v) and not (set(base[u]) & set(base[v]))
        base.remove_edge(u, v)
    cover, symmetry = triangular_double_cover(base, witness["voltage_ones"])
    kind, depth = witness["kind"], int(witness["depth"])
    assert kind in ("cover_pared_clockwork", "cover_coaffine_embedding")
    assert 1 <= depth <= 5
    h, history = cover, []
    for _ in range(depth):
        k, cliques = clique_step(h)
        if kind == "cover_pared_clockwork":
            k = completely_pared(k)
        else:
            symmetry = lift_symmetry(cliques, symmetry)
        h = k
        history.append([len(cliques), len(h)])
    if kind == "cover_pared_clockwork":
        from pycliques.clockwork import (
            clockwork_graph, clockwork_divergence_result, ClockworkDivergenceStatus,
        )
        spec = witness["clockwork"]
        template = clockwork_graph(
            spec["core_sizes"], spec["core_neighbors"],
            spec["crown_size"], spec["crown_permutation"],
        )
        verdict = clockwork_divergence_result(template)
        assert verdict.status is ClockworkDivergenceStatus.DIVERGENT, verdict
        assert verdict.structure and verdict.structure.good_segments
        assert nx.is_isomorphic(h, template)
        assert len(completely_pared(template)) == len(template)
        return {"kind":kind, "cover_order":len(cover), "history":history,
                "target_order":len(h),
                "good_segments":list(verdict.structure.good_segments)}
    from pycliques.clockwork_pairs import r_clock, canonical_clockwork_coaffination
    m,n = int(witness["m"]),int(witness["n"])
    assert m >= 2 and n >= 0
    source = r_clock(m,n)
    source_symmetry = canonical_clockwork_coaffination(m,n)
    check_coaffine(source, source_symmetry, m+1)
    check_coaffine(h, symmetry, m+1)
    phi = witness["embedding"]
    assert set(source) == set(range(len(phi)))
    assert len(set(phi)) == len(phi) and all(x in h for x in phi)
    assert all(h.has_edge(phi[u],phi[v]) for u,v in source.edges())
    assert all(phi[source_symmetry[u]] == symmetry[phi[u]] for u in source)
    return {"kind":kind, "cover_order":len(cover), "history":history,
            "target_order":len(h), "source_order":len(source), "radius":m+1}


def scan(graph, witnesses):
    """A missing witness remains INDETERMINATE; no negative proofs."""
    graph6 = nx.to_graph6_bytes(graph, header=False).decode("ascii").strip()
    witness = witnesses.get(graph6)
    if witness is None:
        return {"status":"INDETERMINATE", "rule":"-",
                "reason":"No saved cover certificate", "witness":None}
    result = verify_witness(graph, witness)
    return {"status":"DIVERGENT", "rule":result["kind"],
            "reason":"Independently replayed finite covering divergence certificate",
            "witness":witness, "verification":result}


def verify_record(record):
    """Replay independently using only the original graph6 and saved witness."""
    if record.get("status") != "DIVERGENT":
        return False
    if not isinstance(record.get("witness"), dict):
        return False
    try:
        graph = nx.from_graph6_bytes(record["graph6"].encode("ascii"))
        verify_witness(graph, record["witness"])
        return True
    except (AssertionError, KeyError, ValueError, IndexError, TypeError, nx.NetworkXException):
        return False
