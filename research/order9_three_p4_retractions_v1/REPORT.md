# Three new P4 octahedral retractions: nine-vertex McKay 249436, 249574, and 250814

## Certified positive theorem

For a graph G, let P0(G) be its completely dominated-vertex-pared graph
and define P(j+1)(G) to be the completely pared clique graph of Pj(G).
Write O_d for the complement of d disjoint edges.

| Connected-nine McKay | Original graph6 | P4 vertices | P4 edges | Exact retraction | Successful native order | States |
|---:|---|---:|---:|---:|---|---:|
| 249436 | HEhff^{ | 353 | 49,491 | P4 -> O10 | Ascending degree | 215 |
| 249574 | HEhfvx} | 306 | 40,622 | P4 -> O12 | Ascending degree | 176 |
| 250814 | HEhuvzm | 222 | 21,487 | P4 -> O14 | Descending degree | 266 |

All three are K-divergent, by the standard octahedral-retraction
criterion and preservation of clique behavior under dominated-vertex
dismantlings. This is the same proof method as the earlier
McKay 253650 P4 -> O12 certificate (merged PR #69), based on
Neumann-Lara's retraction theorem and
Frías-Armenta--Neumann-Lara--Pizaña, "Dismantlings and iterated clique
graphs", Discrete Mathematics 282 (2004), 263--265.

## Complete independent certificates

Each record of certificate.json contains the original graph6, McKay
index, five successive pared orders and sizes, SHA-256 of the exact
*labeled* P4 edge list, every antipodal pair, and the image of
**every vertex of P4**.

The full projection is stored compactly as a base64-encoded byte array.
For each vertex in ascending host-label order (labels may be sparse after
paring), the byte gives the ordinal of its projection image among the
sorted 2d target vertices. Decoded arrays have exactly 353, 306, and
222 bytes, respectively.

The NetworkX-only verifier independently builds maximal cliques,
constructs their intersection graph, and exhaustively pares dominated
vertices. It checks each iterate's order/size and the exact fourth
labeled graph hash; it independently verifies the induced O_d, every
antipodal nonedge, pointwise fixation, totality, image surjectivity,
and edge preservation of the entire saved projection. The proof never
trusts the native search to certify the stored witness.
Optional public validation uses the separate
pycliques.verify_induced_octahedron and
pycliques.verify_retraction_witness routines.

## 344 ten-vertex divergence consequences

| Original nine-core McKay | Distinct ten-vertex originals in frozen v17 |
|---:|---:|
| 249436 | 141 |
| 249574 | 82 |
| 250814 | 121 |
| **Total** | **344** |

The verifier reads frozen indeterminate_order_9_v6.txt and
indeterminate_order_10_v17.txt. It independently examines all 1,144
v17 cases with pared order 9, checks isomorphisms to each proved
nine-vertex core, and verifies each isomorphism mapping edge by edge.
The three sets of original ten-vertex indices are pairwise disjoint.
This gives unconditional behavior-preservation consequences.

When proof review and a **separate** census promotion are complete, the
expected indeterminate counts become **6** connected-nine originals
(from 9), and **1,681** connected-ten originals (from 2,025).
This proof-only PR intentionally modifies no frozen or authoritative
census list, prior proof, or historical result.

## Discovery from scratch and significance of vertex ordering

Merged pycliques-project PR #36 provides a native C++17 unseeded search
for coaffine weak endomorphisms, and independently validates each
FOUND witness. Under the previous input ordering, short bounded trials
gave LIMIT_REACHED. Merely sorting P4 vertices by degree, breaking ties
by the original integer label, caused that *same* solver to find the
three positive retractions in 215, 176, and 266 search states.

The included discover.py reconstructs all iterates from original
graph6 with NetworkX and calls the public
pycliques.find_octahedral_retraction_coaffine function without
specifying a target, antipodal pair, or projection. It verifies the
result using pycliques' independent witness routines.

CI pins the merged PR #36 revision
d140bd3a666ca6abf77e5823740ecef85e75a842 and NetworkX 3.6.1.
A separate job requires the explicit C++17 native build and from-scratch
rediscovery. Proof verification itself does **not** require a compiler.

## Reproduce

From the census repository root (Python 3.12, NetworkX 3.6.1):

    python research/order9_three_p4_retractions_v1/verify.py

With pinned public pycliques also installed:

    python research/order9_three_p4_retractions_v1/verify.py --public
    python research/order9_three_p4_retractions_v1/discover.py

Both scripts reject optimized Python, which would otherwise discard
proof-critical assertions.

## Open cases

After promotion, the remaining connected-nine McKay indices will be
249576, 251628, 251759, 251902, 254369, and 260040.
Their clique behavior remains indeterminate. Initial degree-ordered
native searches on the fourth pared iterates of McKay 251759
(403 vertices), 251902 (461 vertices), and 254369 (394 vertices)
reached only LIMIT_REACHED. The remaining three have fourth pared
iterates above the native backend's 512-vertex limit.
None of these incomplete runs establishes a negative result.
