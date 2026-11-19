# Two unresolved nine-vertex spherical cores: exact homotopy through K²

This is a **positive topological theorem**, not a K-divergence or K-convergence
classification. The two original graphs are stiff, flag 2-sphere
triangulations, and neither currently has an unconditional K-behavior proof.

## Theorem

For each of the graphs \(G\) below,

\[
\Delta(G)\simeq\Delta(K(G))\simeq\Delta(K^2(G))\simeq S^2.
\]

The equivalences are induced by **explicit finite simplicial elementary
collapse sequences** onto connected triangulations of the sphere.

| Original order-9 index | Original graph6 | Order-10 core ID | Original order-10 class |
|---:|---|---:|---:|
| 208409 | \`HCZTf\\}\` | 3663513 | 72 |
| 248687 | \`HEher^{\` | 6912818 | 63 |

The historical conditional-reference mechanism additionally attaches 120
order-10 graphs to the first graph and 99 to the second; these populations
may overlap the completely-pared-core counts and are not added to those
counts here.

## Complete reproducible computation

For each iterate, enumerate **all** maximal cliques with NetworkX; define
\(K(X)\) by intersecting these cliques, using a deterministic integer-bitmask
sort to label the vertices. Enumerate the nonempty face poset of the clique
complex \(\Delta(K^j(G))\) exactly.

An elementary collapse deletes a pair \((\sigma,\tau)\) where \(\sigma\) is
a maximal face and \(\tau\) is one of its codimension-one faces contained
in no other facet. The program supplies every such pair explicitly.
Its **independent checker** replays the entire sequence against the current
full face poset, testing both maximality and uniqueness at *every* step.
The greedy generator uses a separate incremental immediate-coface counter.

| G | j | vertices of K^j(G) | total starting nonempty faces | elementary collapses | remaining sphere \((f_0,f_1,f_2)\) |
|---|---:|---:|---:|---:|---|
| \`HCZTf\\}\` | 0 | 9 | 44 | 0 | (9,21,14) |
| \`HCZTf\\}\` | 1 | 14 | 242 | 84 | (14,36,24) |
| \`HCZTf\\}\` | 2 | 23 | 2170 | 1054 | (12,30,20) |
| \`HEher^{\` | 0 | 9 | 44 | 0 | (9,21,14) |
| \`HEher^{\` | 1 | 14 | 226 | 76 | (14,36,24) |
| \`HEher^{\` | 2 | 23 | 2164 | 1048 | (13,33,22) |

For each terminal complex, the checker independently verifies:

1. All faces have dimension at most two.
2. The 1-skeleton is connected.
3. Every edge belongs to exactly two triangles.
4. The link of every vertex is a single cycle.
5. \(f_0-f_1+f_2=2\).

Consequently, each terminal complex is a connected closed combinatorial
surface with Euler characteristic two, and hence a triangulation of
\(S^2\). Elementary simplicial collapses preserve homotopy type. This
proves the theorem, provided the finite certificate replays successfully.

## Reproduce

With NetworkX 3.6.1 installed, from the repository root:

\`\`\`bash
python scripts/core9_sphere_collapse_v1.py build
python scripts/core9_sphere_collapse_v1.py verify
python -m unittest discover -s tests -p 'test_core9_sphere_collapse_v1.py' -v
\`\`\`

The \`build\` command writes the **complete deterministic pairs and
terminal triangles** to
\`research/order9_two_sphere_collapses_v1/certificates.json\` (a generated
artifact, not a historical source). \`verify\` independently replays the
pairs. The script refuses to overwrite a different existing certificate.

The conclusions are restricted to \(j=0,1,2\); they say nothing yet about
the exact homotopy type of \(K^3(G)\), and do not imply K-divergence or
convergence. No census behavior status is modified.
