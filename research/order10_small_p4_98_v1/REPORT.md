# Certified fourth completely pared iterates of 98 small-P3 ten-vertex classes

## Scope and mathematical conclusion

Let P0(G) be complete closed-neighborhood dominated-vertex paring and
P(i+1)(G) = P(K(Pi(G))), with K the maximal-clique intersection graph.

The immutable ten-v25 unresolved source contains 622 stiff ten-vertex
originals, of which 619 have reconstructed P3 in **521 exact P3 classes**;
three further cases have documented P3 resource limits. This note
certifies *all 98 current P3-class representatives with |P3| <= 40*.

For each of those 98 original connected ten-vertex graphs, the new
archive supplies exact counts, all fourth-iterate fold-round sizes,
the complete canonical P4 adjacency-matrix SHA-256, and the number of
maximal cliques of P3. Both verification programs independently
reconstruct P4 **starting at the original ten-vertex graph6**, not from
a notebook-produced or hand-edited intermediate graph.

**Theorem.** The 98 P4 graphs are all completely reconstructed and
stiff. They are **pairwise nonisomorphic**. Moreover, no P4 graph from
this 98-case cohort shares its (vertex-count, edge-count) pair with
any of the 210 earlier reconstructed P4 representatives from the
ten-v24 pilot, the capped-case rescue, and the later four proof-only
nine-core links.

**Proof.** The verifier reconstructs each original graph and its first
three clique iterates by the prior independently proved P3 algorithm.
At stage four it checks the NetworkX and pivoted bitset
Bron--Kerbosch enumerators, constructs the complete intersection graph
on all maximal cliques, and performs genuine complete dominated-vertex
folding rounds. It checks each final graph is stiff and verifies the
SHA-256 of every vertex's canonical full adjacency bitmask serialized
in minimal-length little-endian rows.

The second verifier reconstructs the same P3 from the original source,
independently enumerates the P4 maximal cliques, reconstructs every
pairwise clique intersection *directly*, and folds by *closed*
neighborhood inclusion instead of complement-neighborhood inclusion.
For each round it verifies every deleted vertex has an undeleted
terminal dominator and tests the final graph for stiffness.
Each saved original graph6, P3/P4 dimension, round list and full
adjacency digest must be reproduced. Both reconstruction routes agree
on **all 98** complete matrices.

The 98 fourth iterates have 92 distinct (order, edge-count) pairs.
Exactly four groups repeat one pair, with group sizes **3, 3, 2,
and 2**, respectively. Within each group all degree multisets are
different, which proves nonisomorphism. All 98 saved dimension pairs
are different from those of the 210 previously certified P4 graphs.
The latter is a dimension obstruction only; it does not compare
unreconstructed fourth iterates. QED.

## Sizes

| Fourth-iterate size | Cases |
| --- | ---: |
| At most 100 vertices | 5 |
| 101–200 | 40 |
| 201–500 | 52 |
| Greater than 500 | 1 |
| **Total** | **98** |

The smallest is original McKay **11708411**:
P3 has 15 vertices and 84 edges; K(P3) has 40 vertices and
694 edges; after one round of ten valid folds, P4 has **30 vertices
and 390 edges**.

The largest is McKay **11651780**:
P3 has 27 vertices and 320 edges; K(P3) has 1,074 vertices and
571,125 edges; after one round of 64 valid folds, P4 has
**1,010 vertices and 504,797 edges**.

These values are exact graph invariants, not a proof of eventual
clique divergence or convergence.

## Source authentication and independent proof

The frozen source identities are independently pinned in verify.py
to their Git blob IDs:

- indeterminate_order_10_v25.txt;
- research/order10_p3_global_v23_index/certificates.json; and
- exploratory_results.json, the immutable 98-case imported local
  computation used as a *claim to be independently replayed*.

The current root must be the frozen ten-v25 source, and the global
P3 archive determines exactly which P3 representatives remain
indeterminate. No index is accepted based on a disconnected list of
98 alleged originals. The full 521-host index is recomputed and
the saved 98 indices must be precisely the complete subset whose
P3 order is at most 40.

The two reconstruction programs share only the earlier certified P3
graph constructor and immutable source validation. Their fourth-stage
clique-intersection and dominated-vertex deletion procedures are
separate. Exact per-case graph6, full adjacency SHA, raw and pared
order/edge counts, and fold rounds all have to agree.

Adversarial tests corrupt a recorded SHA, a paring round, and a P3
shape; also test malformed adjacency masks, path-graph folding,
source scope and optimized Python execution. The dedicated CI runs
both complete 98-case verification routines independently.

## Reproduction

From the census repository root with Python 3.12 and NetworkX 3.6.1:

    python -m unittest research.order10_small_p4_98_v1.test_verify -v
    python -m research.order10_small_p4_98_v1.verify
    python -m research.order10_small_p4_98_v1.independent_verify

The GitHub Actions workflow is:

    .github/workflows/order10-small-p4-98-v1.yml

It runs both full independent proof jobs separately, preserves the
logs as artifacts, and refuses optimized proof execution.

## Next investigation and classification discipline

Previously certified fourth iterates cover 210 current P3 classes.
These new 98 cover a disjoint further cohort, so the total known P4
dimensions increase to **308 of the 521** reconstructible current
P3 classes. The other **213** P3 classes (typically having at least
41 or 56 P3 vertices depending on the older pilot window) are the
next candidates for targeted fourth-iterate reconstruction.

This note does NOT assert an exact isomorphism of any P4 to an
already divergent nine-vertex reference, nor any new K-divergence or
K-convergence conclusion. A subsequent classification requires an
independent ordinary retraction/divergence certificate or a complete
cross-depth positive isomorphism to a previously proved target.
The authoritative nine-v9 and ten-v25 indeterminate lists remain at
**3** and **1,052**, with **500** existing conditional dependencies.
