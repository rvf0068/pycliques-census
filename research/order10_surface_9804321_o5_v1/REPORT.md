# Exact fourth-pared-iterate O5 retraction: ten-vertex McKay 9804321

## Result

McKay **9804321**, original graph6 ````ICR`tlmv_````, is a ten-vertex flag
triangulation of S^2 in the frozen **v16** unresolved census.
Its **fourth completely pared clique iterate P4(G)** retracts onto an
induced octahedral graph **O5** (complement of five pairwise disjoint edges).

The independent reconstructed sequence is:

| Pared iterate | Vertices | Edges |
|---|---:|---:|
| P0 | 10 | 24 |
| P1 | 16 | 71 |
| P2 | 26 | 182 |
| P3 | 46 | 662 |
| P4 | 202 | 13,606 |

The complement of the induced target is the perfect matching

    (96,37)  (5,76)  (171,84)  (142,52)  (87,127)

The complete retraction of 202 vertices is archived in
\`certificate.json\` as 202 little-endian uint16 images compressed to
base64, ordered by **sorted P4 vertex labels**. These labels have gaps
after closed-neighborhood dismantling (maximum label 215), so the
base64-array index must **not** be interpreted as the original vertex
label. For instance, target vertices 96, 171 and 142 lie at sorted
ranks 89, 160 and 131, respectively, and are fixed by the projection.

The independent \`verify.py\` reconstructs every pared iterate using
NetworkX maximal-clique enumeration and pairwise clique intersection,
verifies graph and iterate metadata against the frozen v16 census,
checks the exact SHA-256 digest of P4's sorted edge list,
decodes all 202 projection values, verifies all target vertices are
fixed, identifies the induced O5, and checks adjacency-or-equality on
each of P4's 13,606 edges. It explicitly refuses optimized Python
execution (which could otherwise disable its assertions).

For a fully independent cross-check, its \`--public\` mode reconstructs
all five iterates using the released \`pycliques\` functions and invokes
the public octahedral and retraction witness verifiers.

### Reproduction

From the census repository root, with NetworkX 3.6.1:

    python research/order10_surface_9804321_o5_v1/verify.py

With public \`pycliques\` also installed:

    python research/order10_surface_9804321_o5_v1/verify.py --public

The dedicated workflow verifies both modes and requires
\`python -O verify.py\` to fail.

Because O5 is K-divergent and divergence passes along graph
retractions, P4(G) is K-divergent. Since completely paring commutes with
K-behavior by the dominated-vertex theorem, **G is K-divergent**.

References: Frías-Armenta, Neumann-Lara, and Pizaña (2004),
"Dismantlings and iterated clique graphs", Discrete Mathematics 282,
263--265; and the standard Neumann-Lara clique-retraction theorem.

## Scope

This is a proof-only archive. It does **not** edit
\`indeterminate_order_10.txt\`, immutable \`indeterminate_order_10_v16.txt\`,
or any earlier certificates. A later audited promotion may delete
the newly proved McKay 9804321 entry, along with the already proved
McKay 10185592 from merged PR #67.
