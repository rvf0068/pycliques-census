# McKay 251902 is K-divergent: complete fourth-iterate retraction onto O17

## Certified theorem

Let G be connected-nine original McKay 251902, graph6 HEhvvzm.
Write P0(G) for its completely dominated-vertex-pared graph, and
P(j+1)(G) for the completely pared clique graph of Pj(G).

**Theorem.** The graph P4(G) admits an **ordinary graph retraction**
onto an induced O17, where O_d = complement(d disjoint edges).
Hence G is K-divergent by the standard octahedral-retraction
divergence criterion and preservation of clique behavior under
dominated-vertex dismantlings.

The independently reconstructed pared sequence has the following exact
vertex and edge counts:

| Pared level | Vertices | Edges |
|---|---:|---:|
| P0 | 9 | 24 |
| P1 | 12 | 45 |
| P2 | 18 | 114 |
| P3 | 41 | 641 |
| **P4** | **461** | **94,642** |

The normalized labeled P4 edge list has SHA-256

    e09bfabf7e7a2ab4af810f09c16942b6e64a9dfba9e5027f9cd62a5bee66efb1

and the complete 17 antipodal pairs, with indices in this exact
normalized P4 labeling, are

    (231,48), (18,181), (63,214), (14,386), (242,71),
    (407,296), (15,180), (300,409), (156,406), (280,155),
    (130,253), (150,305), (241,26), (356,101), (293,140),
    (369,84), (25,400).

These 34 vertices induce O17 with precisely the 17 listed nonedges.
The **complete graph retraction image of all 461 source vertices**
is preserved in certificate.json as a 461-byte base64-encoded array:
each byte is the ordinal of its image in the sorted list of the
34 target labels, indexed by normalized host label 0,...,460.

The independent verification does not trust the search solver.
It reconstructs P4 from original graph6 using NetworkX, checks the
exact labeled-edge hash, all 17 antipodal pairs, totality, image
surjectivity, pointwise fixation of all 34 target vertices, and the
graph-morphism condition **on all 94,642 source edges** (adjacent
vertices may have equal images). Its optional --public mode
independently checks the result with public
pycliques.verify_induced_octahedron and
pycliques.verify_retraction_witness. All claims are finite and
independently checkable.

## Exactly 150 ten-vertex divergence consequences

The immutable ten-v18 census contains **150 distinct original
connected-ten McKay indices** with completely pared nine-vertex
core isomorphic to G. The verifier independently enumerates all
**800** residual pared-nine ten-v18 original graphs, tests
isomorphism to G and verifies every returned nine-vertex mapping
edge by edge. All 150 original ten-vertex graphs are therefore
also K-divergent.

This is a **proof-only PR**: current authoritative nine-v7 and
ten-v18 snapshots (six and 1,681 unresolved original graphs) are
not modified. After review and a separate exact promotion audit,
their expected populations become **five and 1,531**, respectively,
with all retained rows unchanged and old versions frozen.

## Unseeded rediscovery and a reusable search-ordering insight

Previous short coaffine searches with default, degree-ascending,
degree-descending, neighbor-degree, and random vertex orderings
returned only LIMIT_REACHED, not negative certificates.

The search that found the positive witness uses the integer weights
of an **edge-neighborhood covering dual**: assign each host vertex
the weight from the exact McKay 251902 P4 dual certificate in
[PR #77](https://github.com/rvf0068/pycliques-census/pull/77),
then sort all 461 vertices by

    (dual_weight[v], -degree_P4(v), normalized_vertex_label)

i.e. **ascending dual weight**, descending degree on ties, and
ascending integer label on further ties.

This ordering supplies **no target, antipodal pair, or projection**.
The native coaffine algorithm from merged
[pycliques-project PR #36](https://github.com/rvf0068/pycliques-project/pull/36)
found P4 -> O17 in **300 search states** (23,311 arc revisions
would be incorrect; the observed count is **22,311** revisions
and 315 assignments). This discovery is therefore not hardcoding
the result of a previous octahedral search.

Both the **complete positive certificate** and a copy of the
integer dual weights used *only* for search ordering are stored
in this PR's certificate.json. Thus this PR does not depend on
PR #77 being merged first. The discovered retraction is
independently proved even without the dual weights.

discover.py reconstructs the complete P4 directly from original
graph6, applies this reproducible ordering, explicitly compiles
the optional C++17 solver and calls the public
pycliques.find_octahedral_retraction_coaffine with
min_dimension=6, max_states=10000, time_limit=60,
backend=native. If it reports FOUND, the returned witness is
rechecked against the independently implemented public
octahedral and retraction verifiers. CI pins PR #36's
merged revision d140bd3a666ca6abf77e5823740ecef85e75a842.
A LIMIT_REACHED status can never be interpreted as a positive
or negative proof.

The edge-neighborhood dual originally established that ordinary
P4 retractions to O5 are impossible; the positive O17 retraction
now demonstrates that the exact low-dimension exclusion and
K-divergence are entirely compatible.

The ordering strategy is an attractive generally useful
**search heuristic** for the native coaffine solver. It is
not claimed to be complete under resource limits.

## Reproduction

From the census repository root, with NetworkX 3.6.1:

    python -m research.order9_251902_p4_o17_v1.verify

With pinned public pycliques:

    python -m research.order9_251902_p4_o17_v1.verify --public
    python -m research.order9_251902_p4_o17_v1.discover

The default verifier requires neither C++ nor SciPy; the
unseeded rediscovery uses a C++17 compiler.
Both scripts reject optimized Python to protect proof-critical
assertions. The CI workflow independently checks the saved
full projection and the native rediscovery.

## Next priorities

The five remaining connected-nine McKay originals after
promotion would be 249576, 251628, 251759, 254369, 260040.
The integer-weight ordering mechanism should be generalized
and tried on their fourth pared iterates. No convergence
or divergence is inferred for them from bounded searches.

Mathematical sources include the preceding O_d retraction
proofs in research/order9_three_p4_retractions_v1/ and
the standard clique graph retraction and dominated-vertex
dismantling theorems; see also
Frías-Armenta, Neumann-Lara and Pizaña,
"Dismantlings and iterated clique graphs",
Discrete Mathematics 282 (2004), 263-265.
