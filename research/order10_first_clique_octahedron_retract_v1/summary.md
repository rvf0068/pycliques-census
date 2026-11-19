# First-clique-graph octahedron retraction: one new divergent ten-graph

The stiff connected original ten-vertex graph of McKay index
11634099 (graph6 IEjer^{lo) has precisely 17 maximal cliques,
so its first clique graph K(G) has 17 vertices and 87 edges.
The induced vertices 1,5,9,10,14,15 of K(G) form O3,
the complement of 3 disjoint edges.
The missing pairs are (1,15), (5,10), (9,14).
The exact total retraction of K(G) onto these vertices,
in independently sorted integer-bitmask facet labeling, is:

14,1,5,15,14,5,1,10,1,9,10,10,9,10,14,15,14

It fixes its induced O3 target pointwise and every source
edge maps to a target edge OR a single vertex. The
certificate includes all 17 maximal cliques of the original
ten-vertex graph and checks each edge. Since K(O3) is O4
and iterated octahedral dimensions increase, O3 is
K-divergent. Neumann-Lara's Retraction Theorem implies
K(G) is K-divergent, hence G itself is K-divergent.

The independent complete screen of 2,394 previously
indeterminate stiff ten-vertex originals examines all
induced O3 subgraphs in their first clique graphs and
retraction constraints with no configured CSP limit reached.
Other negative cases remain K-behavior indeterminate.

Sources examined: 2394
Induced O3 candidates: 3941
Source graphs containing O3: 39
New positive divergence certificates: 1

The new versioned indeterminate_order_10_v6.txt contains
8,223 original graphs: 2,092 with a snub eight-core;
3,738 with an unresolved nine-core; and 2,393 with
a stiff ten-core. Earlier v3/v4/v5 lists, certificates
and reports are completely unchanged.

Reproduction with Python and NetworkX 3.6.1:
  python scripts/first_clique_octahedron_retract_v1.py verify
  python -m unittest discover -s tests -p test_first_clique_octahedron_retract_v1.py -v
