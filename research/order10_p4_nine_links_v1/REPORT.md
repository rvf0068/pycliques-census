# Four further exact P4 dependencies on unresolved nine-vertex graphs (proof only)

## Positive theorem

Let P0 be complete closed-neighborhood dominated-vertex paring and set
P(j+1)(G) = P(K(Pj(G))). The complete, explicitly checked
fourth-iterate vertex bijections in the accompanying certificates.json
prove the following graph isomorphisms:

| Stiff ten-vertex McKay original | Nine-vertex McKay reference | P3 of ten-original | P4 of both graphs (vertices, edges) | Full map |
|---:|---:|---:|---:|---|
| **11287666** | **251628** | 58 vertices, 1,274 edges | **1,034, 467,517** | 1,034 coordinates |
| **11287670** | **249576** | 57 vertices, 1,184 edges | **685, 199,283** | 685 coordinates |
| **11567994** | **249576** | 57 vertices, 1,184 edges | **685, 199,283** | exact identity in canonical labeling |
| **11568314** | **249576** | 57 vertices, 1,182 edges | **685, 199,283** | exact identity in canonical labeling |

These are **positive full graph isomorphisms**, not merely dimension
matches, equal degree multisets, or bounded solver results.
All four ten-vertex graphs are singletons in the immutable, certified
global P3 class archive, disjoint from the 66 stiff ten-vertex graphs
previously linked to a pending nine-core in [PR #94](../order10_nine_core_dependency_v1/REPORT.md).

Two maps are little-endian unsigned 16-bit Base64; for the others
the deterministically reconstructed fourth iterates are **identical
as labeled graphs**, so the complete 685-vertex maps are the identity.
The SHA-256 digests of all four exact image arrays are independently
hard-coded in the verifier.

## Conditional consequences

The dismantling theorem for clique graphs preserves eventual clique
behavior under dominated-vertex paring. Consequently, isomorphic
completely pared iterates imply equal eventual clique behavior.

| Currently indeterminate nine-original | Previous ten-dependents | New stiff P4 dependents | New total |
|---:|---:|---:|---:|
| McKay 249576 | 159 | **3** | **162** |
| McKay 251628 | 170 | **1** | **171** |
| McKay 260040 | 167 | **0** | **167** |
| **Total** | **496** | **4** | **500** |

Thus **500 of the current 1,052 indeterminate connected ten-vertex
originals** have the same eventual clique behavior as one of the
three unresolved nine-vertex originals. **552 stiff ten-vertex
originals have not yet been linked** by these certificates. These
are conditional dependencies, **not convergence or divergence proofs**.
The authoritative nine-v9 / ten-v25 census remains exactly unchanged,
at 3 and 1,052 unresolved original graphs.

## Certificate reconstruction and verification

The independent verifier reuses the merged census implementation
of the P3/P4 construction, especially the P4 cross-checked facet
enumerators and complete multi-round dominated-vertex paring.
For each of the four positives it:

1. Authenticates immutable nine-v9, ten-v25, PR #94's preceding
   dependency certificate, and the global P3 equivalence certificate
   by their **code-pinned Git blob digests**, not by expected hashes
   obtained from the mutable certificate being verified.
2. Checks all original McKay indices, graph6 identities, immutable
   and mutable root equality, and exclusion of the 66 previously
   established stiff dependencies.
3. Reconstructs both nine-reference P4 graphs and each ten-source
   P4 graph starting from its original graph6. At both P3 and P4
   stages the existing verifier checks NetworkX and independent bitset
   Bron--Kerbosch clique enumeration, followed by complete paring.
4. Checks original P3 dimensions, every raw fourth-iterate order,
   every folding round, and the exact pared P4 dimensions.
5. Constructs all coordinates of each complete P4 permutation,
   validates its independently code-pinned SHA-256, checks **every
   ordered vertex pair** for edge and nonedge preservation, and runs
   a separately label-constrained GraphMatcher on the complement.
6. Independently checks the disjoint 496 + 4 = 500 and
   622 - 66 - 4 = 552 dependency counts without any census promotion.

Mutation tests reject a tampered saved permutation, a forged mapping
digest, unknown historical evidence paths, and attempted overrides of
the two exact identity maps. Optimized Python is explicitly rejected.

Reproduce from the census root with Python 3.12 and NetworkX 3.6.1:

    python -m research.order10_p4_nine_links_v1.verify
    python -m unittest research.order10_p4_nine_links_v1.test_verify -v

## Exploration limits and future work

This was a candidate search based on fourth-iterate signatures,
followed by **full positive graph-isomorphism certification**.
It is not an exhaustive negative test of all remaining ten-vertex
cores. Ten particularly large P3 classes exceeded the exploratory
6,500-facet cap at the next stage. This cap is a resource limitation,
not a non-isomorphism or K-behavior result.

The third unresolved nine-reference, McKay 260040, has a reconstructed
P4 of 1,227 vertices and 658,528 edges. No new direct positive
fourth-iterate equivalence with it was found in the completed screen.

Future work should use the existing exact equivalence classes and
general-purpose pycliques/pycombtop retraction or homology methods
before adding graph-specific searches.
