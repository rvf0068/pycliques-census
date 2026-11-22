# Certified fourth-pared-iterate O6 retraction: McKay 10185592

**Positive result.** The connected ten-vertex McKay graph **10185592**
(graph6 `ICXmdbj\o`) is a flag triangulation of S^2 and an
unresolved entry in the immutable order-ten **v16** census. Its
**fourth completely pared clique iterate admits an explicit graph
retraction onto an induced O6**.

Let P0(G) be obtained by successively deleting vertices dominated in
the closed-neighborhood sense, and put P(j+1)(G)=P(K(Pj(G))).
The iterates have orders 10, 16, 26, 56, 262 and edge counts
24, 70, 184, 930, 21,822.

The twelve O6 vertices in the independent NetworkX labeling are
paired antipodally as follows:

    (64,144) (99,185) (36,73)
    (239,94) (176,85) (61,93)

The complete 262-image projection is stored in certificate.json as a
lossless base64 array of little-endian unsigned 16-bit vertex labels,
indexed by sorted host vertices. The independent verifier reconstructs
all pared iterates from the original graph6, checks the exact edge
signature, checks the induced O6 nonedges, checks pointwise fixation of
the twelve target vertices and checks the weak graph morphism condition
for each of the 21,822 host edges. No discovery algorithm is trusted.

Use NetworkX 3.6.1:

    python research/order10_surface_10185592_o6_v1/verify.py

With the public pycliques package installed, also run:

    python research/order10_surface_10185592_o6_v1/verify.py --public

The public replay reconstructs each iterate through the exported
pycliques.clique_graph and pycliques.completely_pared_graph functions,
then calls verify_induced_octahedron and verify_retraction_witness.

Since K(O_d) is isomorphic to O_(2^(d-1)) for d>=3, O6 is K-divergent.
The retraction theorem of Neumann-Lara and the behavior-preservation
theorem for dominated-vertex dismantling (Frías-Armenta, Neumann-Lara
and Pizaña, "Dismantlings and iterated clique graphs",
Discrete Mathematics 282 (2004), 263–265) imply that **McKay
10185592 is K-divergent**.

This is deliberately **proof-only**: it leaves all historical results,
the authoritative order-ten root and the immutable v16 index unchanged.
A separate audited promotion can reduce v16's count from 2,341 to 2,340
after CI and review.
