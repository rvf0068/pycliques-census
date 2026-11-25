# The remaining 203 bounded fourth iterates and 14 persistent complete ears

## Objective and exact numerical coverage

Let \(P_0(G)\) be complete closed-neighborhood paring, and set \(P_{j+1}(G)=P(K(P_j(G)))\), where \(K\) is the maximal-clique intersection graph. The frozen ten-v25 unresolved census has 521 reconstructed third-iterate isomorphism classes. Their fourth iterates now split into:

| Distinct surviving P3 class representatives | Certified fourth-stage coverage |
|---|---:|
| Previously verified ten-P4 reference pilot, capped-case rescue, and nine-core links | 210 |
| All representatives with at most 40 vertices in P3 (merged PR #98) | 98 |
| Newly reconstructed representatives with 56–60 vertices in P3 | 144 |
| Newly reconstructed representatives with 61–80 vertices in P3 | 58 |
| One further representative with P3 order 87, McKay 11543836 | 1 |
| **Total fully reconstructed within current bounds** | **511 / 521** |
| Further P3 classes whose fourth-stage facet count exceeds 6,000 | 10 |

All 203 new P4 source identities are checked against the frozen ten-v25 original graph6, the 521-class exact global P3 host index, and all previously merged 210 and 98 P4 archives. The 203 records have at most 2,223 maximal cliques of P3. Each complete raw fourth clique graph and every dominated fold round is independently reproduced.

The ten other class representatives are McKay 11367777, 11505012, 11595632, 11611429, 11623375, 11656793, 11708546, 11709142, 11713770, and 11713984. For each, an exact original P3 graph6 is reconstructed and two distinct-stage witnesses confirm that the P3 graph has *at least 6,001 maximal cliques*. These cases are **resource-limited**, not disproved or classified.

## Independent certification, exact adjacency and pairwise nonisomorphism

The primary verifier reuses merged PR #98's complete fourth-stage reconstruction from each original graph6: independent NetworkX and bitset Bron--Kerbosch maximal-clique enumeration, clique-graph incidence construction, complete multiround domination, stiffness, full dimensions, and SHA-256 of each canonical final P4 adjacency matrix.

The second verifier reconstructs the same P3 by the existing independent P3 proof, checks the entire P4 facet family against a separate imported bitset Bron--Kerbosch enumerator (cap 2,500, above all 203 exact facet counts), constructs all pairwise clique intersections *directly*, and folds by closed-neighborhood containment instead of complementary-neighborhood containment. All reconstructed raw and pared dimensions, exact folding-round sizes, and adjacency digests must agree.

Eight disjoint CI jobs (four primary and four independent) replay the same 203 original identities, and a final job checks source partition completeness and agreement between the methods. The complete cohort has seven groups sharing a pair \((|V(P_4)|,|E(P_4)|)\), with group sizes 7, 7, 3, 2, 2, 2, 2. The degree multiset differs between every two members of each group, certifying **203 distinct fourth-iterate isomorphism types**. No new P4 dimension pair coincides with the 308 previously reconstructed cases. These statements do **not** assert pairwise nonisomorphism of the 511 original graph classes at all further stages.

## Fourteen ordinary retractions and complete-ear extensions

The certificate archive supplies complete explicit bijections \(P_4(H)\longrightarrow P_4(G)-x\), where \(G\) is a ten-vertex original and \(H\) is one of two still-unresolved nine-vertex originals.

| Nine-vertex McKay \(H\) | Ten-vertex McKay \(G\) |
|---:|---|
| **251628** | 6957744, 6958193, 7294013, 7455349, 7700052, 9717675, 9763078 |
| **260040** | 7453718, 7464163, 7465249, 7465986, 7471002, 9731190, 10792568 |

For \(H=251628\), the reference P4 has 1,034 vertices and 467,517 edges, and each host P4 has 1,035 vertices and 467,519 edges. For \(H=260040\), the reference P4 has 1,227 vertices and 658,528 edges, and each host P4 has 1,228 vertices and 658,530 edges. Each host has one distinguished degree-two vertex \(x\), whose two neighbors are *nonadjacent*.

The [ear verifier](ears.py) checks each certificate from the original nine- and ten-vertex graph6, including all-P4 adjacency SHA-256, full little-endian \(16\)-bit coordinate permutation and its digest, every edge and nonedge of the induced reference copy, an independently colored complementary-graph GraphMatcher confirming the *specific* map, the exact two nonadjacent attachment neighbors, and an ordinary retraction fixing the embedded reference on all target vertices and preserving **every original host edge**. These are complete finite proof certificates rather than matching invariant guesses.

The original all-iterate [complete-ear theorem](../snub_ear_all_iterates_homotopy_v1.md), authenticated by its immutable Git blob SHA, applies because the two singleton neighborhoods are disjoint anticomplete complete sets. Therefore for each pair \((G,H)\) above and all \(j\ge0\),

\[
\Delta(P_{4+j}(G))\simeq\Delta(P_{4+j}(H))\vee S^1.
\]

Consequently **the fourteen ten-vertex originals are not K-null**, regardless of the eventual behavior of their nine-vertex references. Their **K-divergence remains indeterminate**, since the references 251628 and 260040 are still unresolved. No root census verdicts are changed.

## Reproduce from the census repository

Use Python 3.12 and NetworkX 3.6.1:

    python -m research.order10_p4_203_ears_v1.verify audit
    python -m unittest research.order10_p4_203_ears_v1.test_verify -v
    python -m research.order10_p4_203_ears_v1.ears

The CI workflow [order10-p4-203-ears-v1.yml](../../.github/workflows/order10-p4-203-ears-v1.yml) runs all eight separate replay shards, the fourteen-ear proof, mutation tests, and an exact independent final aggregation. Its artifacts preserve complete per-case source IDs and computed collision degree profiles.

This is a *proof-only research archive*; the authoritative indeterminate lists remain at **3 nine-vertex** and **1,052 ten-vertex** original graphs. Any future class promotion requires a separate proof and explicit census update.
