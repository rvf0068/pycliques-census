# A persistent circle attachment in six snub-retracting cores

## Theorem (finite, exact, independently reproducible)

Let S be the eight-vertex snub disphenoid `GQyuzw`. Let G be
any of the six nine-vertex stiff cores below. For EVERY j=0,...,4,
K^j(S) is isomorphic to a recorded **induced** subgraph of K^j(G),
and as clique complexes:

**Delta(K^j(G)) is homotopy equivalent to Delta(K^j(S)) wedge S^1.**

This is a theorem **only for these five finite iterates**. It does
**not** imply K-divergence, K-convergence, or the same clique behavior
at all future iterates. The snub's divergence remains conjectural.

| j | Order K^j(S) | Order K^j(G) | Exact attachment type |
|---:|---:|---:|---|
| 0 | 8 | 9 | 1 vertex, link is two disjoint cliques |
| 1 | 12 | 14 | 2 adjacent vertices, disjoint nonempty cone links |
| 2 | 20 | 21 | 1 vertex, link is two disjoint cliques |
| 3 | 56 | 58 | 2 adjacent vertices, disjoint nonempty cone links |
| 4 | 1076 | 1077 | 1 vertex, link is two disjoint cliques |

## Complete six-core witness table

| Nine-core ID | Graph6 | Ten-vertex originals | K4 extra-link clique sizes |
|---:|---|---:|---|
| 2317843 | `HCRSv\}` | 70 | 1 + 1 |
| 3148541 | `HCY]Yzr` | 114 | 1 + 1 |
| 3505942 | `HCZIt~u` | 133 | 1 + 82 |
| 4952669 | `HCpumzi` | 86 | 1 + 1 |
| 4953338 | `HCpunzi` | 196 | 1 + 62 |
| 5601875 | `HCvVZpt` | 111 | 1 + 34 |

These six distinct classes represent **710** original ten-vertex
graphs. Their K-behavior remains unresolved, as does that of S.

## Proof of the homotopy equivalence

We use two elementary simplicial gluing lemmas, valid whenever the
old graph X is connected. First, add one vertex x with link the
disjoint union of two nonempty complete subgraphs A,B of X.
Then Delta(X+x) is Delta(X) union the cone on
Delta(A) disjoint union Delta(B). Both pieces of that link
are contractible. Contracting each component within its mapping
cylinder shows Delta(X+x) is homotopy equivalent to
Delta(X) wedge S^1.

Second, add adjacent vertices x,y to X so their sets of old
neighbors P,Q are disjoint and the clique complexes of X[P]
and X[Q] are each cones. The closed simplicial stars of x and y
are contractible and intersect in the closed star of edge xy,
also contractible. Their union B is therefore contractible.
Its intersection with Delta(X) is precisely the disjoint union
Delta(X[P]) disjoint union Delta(X[Q]). The same homotopy-pushout
argument proves Delta(X+x+y) equivalent to Delta(X) wedge S^1.

Each recorded even-level link is checked to consist of exactly
two induced complete components. Each odd-level attachment is
checked to have an edge xy, disjoint nonempty supports in X,
and explicit universal vertices in both supports (cone apices).
These are *stronger* witnesses than homology calculations.

## Proof of each induced embedding

At level zero, independently verify an eight-vertex induced snub
by testing all pairwise adjacencies, not only edges. To pass
from j to j+1, enumerate all maximal cliques of both graphs.
For every source maximal clique Q, its image has **exactly one**
maximal target extension. Distinct source cliques have distinct
extensions, and their intersection graphs agree on *every pair*
of old vertices (including nonedges). The resulting map is thus
an induced copy of K^(j+1)(S). Repeat through j=4.

At j=4 the checker avoids creating the 1077-vertex clique graph:
the integer bitsets of the 1076 and 1077 third-iterate facets
give the exact pairwise intersections, and therefore all edges,
nonedges, and both parts of the new vertex's link.
All explicit vertex maps and cone/component witnesses are stored
in certificates.json, together with source graph6 and class IDs.

## Why the divergence question remains open

The five verified cases suggest a recurrence: one extra vertex
in even iterates, two adjacent extras in odd iterates. Such a
uniform bound at *every* iterate would imply equality of
K-convergence/divergence behavior with the snub, but no induction
hypothesis preserved under K has yet been proved. In particular,
these finite equalities cannot be used as a divergence certificate.

## Reproduction

From pycliques-census, with its pinned historical environment:

```bash
bash scripts/bootstrap_special_k3_v5.sh
.venv-special-k3-v5/bin/python scripts/core9_snub_handle_iterates_v1.py verify
.venv-special-k3-v5/bin/python -m unittest discover -s tests -p 'test_core9_snub_handle_iterates_v1.py' -v
```

The verifier checks the frozen source SHA-256, all original classes,
all five embeddings and links, and byte-for-byte identity of
every versioned output. No historical results are modified.
