# McKay 260910 has a third-pared-iterate O15 retraction

The nine-vertex original connected graph **McKay 260910**, graph6
`HUZvvzu`, is **K-divergent**. The complete certificate is archived in
[certificate.json](certificate.json), with an independent full verifier
[verify.py](verify.py).

For the completely pared clique iteration
\(P_0(G)=P(G)\), \(P_{j+1}(G)=P(K(P_j(G)))\), the third pared iterate
\(P_3(G)\) has **132 vertices and 7,880 edges**. Its induced
\(O_{15}=\overline{15K_2}\) target has 30 vertices with nonedge pairs
in the verifier's independent numbered labeling:

```text
(0,58)   (1,83)   (5,112)  (7,130)  (9,70)
(21,53)  (24,113) (28,95)  (29,50) (35,56)
(36,88)  (37,49)  (60,126) (78,114) (82,129)
```

The certificate stores the image under a graph retraction of
**every one of the 132 host vertices**, encoded as 132 raw unsigned
bytes and then base64. The independent verifier:

1. Checks the original McKay graph6 and its occurrence in frozen order-nine v4.
2. Independently builds the entire third pared clique iterate by NetworkX
   maximal complete sets and successive closed-neighborhood domination.
3. Checks a SHA-256 fingerprint of the complete labeled graph6 source.
4. Checks all 15 pairs are nonedges with all cross-pair edges present,
   that the projection is total and fixes the 30 target vertices, and
   that **every one of the 7,880 host edges** maps to an edge or equality.
5. Rebuilds the graph separately using the public `pycliques` APIs,
   transports the saved projection by exact graph isomorphism, and
   invokes `verify_induced_octahedron` and
   `verify_retraction_witness` on the public reconstruction.

Consequently, Neumann-Lara's retraction theorem and
Frías-Armenta–Neumann-Lara–Pizaña's
*Dismantlings and iterated clique graphs* (Discrete Mathematics 282,
2004, 263–265) prove divergence of the original nine-vertex graph,
because \(K(O_d)\cong O_{2^{d-1}}\) for every \(d\ge3\).

This retraction was discovered by the general target-free coaffine
endomorphism search (separate public-`pycliques` PR #34) after
**52 search states**, without supplying antipodal target coordinates.
No historical census index was edited by this proof-only PR.

Reproduce in the census repository with pinned `pycliques`:

```bash
PYTHONHASHSEED=0 python research/order9_260910_o15_v1/verify.py
```
