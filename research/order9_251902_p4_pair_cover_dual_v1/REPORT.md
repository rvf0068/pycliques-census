# McKay 251902: an exact complement-edge covering obstruction at the fourth pared iterate

## Main theorem

Let G be connected-nine original McKay 251902, graph6 HEhvvzm, and
X=P4(G), the fourth completely dominated-vertex-pared clique iterate.
Independent reconstruction gives 461 vertices and 94,642 edges.
Write H=complement(X), which has 11,388 edges.

**Theorem.** No collection of at most five edges of H has endpoints
dominating all of H. Consequently, there is **no ordinary graph
retraction** X -> O5, where O_d is the complement of d disjoint edges.

Together with the earlier exact domination certificate from merged
[PR #76](https://github.com/rvf0068/pycliques-census/pull/76), excluding
O3 and O4 for this fourth iterate, every ordinary octahedral
retraction X -> O_d would require **d >= 6**.

This result excludes complement-dominating induced O5 targets, not
necessarily all induced O5 subgraphs of X. It does not imply clique
convergence or any final classification of G or its 150 remaining
connected-ten original dependents.

## Elementary proof independent of numerical optimization

For each edge uv of a graph H, define its **pair neighborhood**

    C(uv) = N_H[u] union N_H[v].

Let nonnegative weights w_x, indexed by vertices of H, satisfy

    W = sum_x w_x,
    M = max_{uv edge H} sum_{x in C(uv)} w_x.

If d edges have endpoints dominating H, the union of their pair
neighborhoods is all of V(H). Thus the total weight is bounded by
the sum of their individual coverage weights:

    W <= d M.

This holds even if the edges share endpoints or are not an induced
matching. Our saved integer dual has

    W = 50,893
    M = 9,990

and therefore 5 M = 49,950 < 50,893. At least six complement
edges are required to dominate H.

To connect this to ordinary octahedral retractions, let T=O_d be
an induced retract of X. Since O_d has no universal vertex, its
vertex set must dominate H: otherwise some v outside T is adjacent
in X to every target vertex, and an ordinary retraction fixing T
would have to send v to a universal vertex of T, a contradiction.

The d antipodal pairs of O_d are d edges of H, and their endpoints
are exactly V(T). They must therefore dominate H. The integer
pair-cover bound implies d >= 6, proving the theorem.

**Special retractions need no separate exclusion here.** They are
ordinary retractions with extra properties. Thus our ordinary
retraction exclusion automatically excludes any special retraction
onto the same O_d. The existence of a *special octahedron* as an
induced subgraph is a different question and should not be conflated
with the existence of a retraction.

## Fully checkable integer certificate

The complete proof is certificate.json. It contains 461 nonnegative
integer weights encoded as little-endian unsigned 16-bit values,
one per vertex of the normalized P4 graph (0,...,460). The maximum
stored edge-pair closed-neighborhood load is 9,990, and the total
weight is 50,893.

No floating-point computation or optimization solver is required to
check the saved certificate: verify.py independently computes P4
from the original graph6, checks the exact edge-set SHA-256

    e09bfabf7e7a2ab4af810f09c16942b6e64a9dfba9e5027f9cd62a5bee66efb1

and checks **every one of the 11,388 complement edges** by
direct integer summation over N_H[u] union N_H[v].

The verifier reuses the independent NetworkX-only P4 reconstruction
from the already merged PR #76, including frozen nine-v7 McKay
source identities and historical Git blob integrity checks.
Its optional --public mode also compares each original clique graph
and each paring stage with pinned public pycliques algorithms.
A tiny O3 self-test checks the pair-neighborhood formula on the
complement of three disjoint edges, where the lower bound is sharp.

The new weights were discovered using a fractional linear program
with one constraint per **complement edge**, rather than the older
vertex-domination LP. The floating-point result was rounded down to
integers and then **independently verified exactly**; its discovery
method and numerical tolerances are not part of the proof.

## Reproduction

From the census repository root, with Python 3.12 and NetworkX 3.6.1:

    python -m research.order9_251902_p4_pair_cover_dual_v1.verify

For public-pycliques validation (merged pycliques-project PR #36 pinned):

    python -m research.order9_251902_p4_pair_cover_dual_v1.verify --public

Both reject optimized Python execution, which would bypass
proof-critical assertions. Dedicated CI runs both.

## Research direction and limitations

The authoritative unresolved counts remain **six original nine-vertex**
and **1,681 original ten-vertex** graphs (nine-v7 / ten-v18).
This proof is an exact *O5-specific negative* at P4 and cannot be
used to infer that no O6, O7 or later-iterate octahedral retraction
exists. The next unseeded search should focus on dimensions d>=6,
using both the coaffine engine and complement-dominating induced
matching generation, with explicit budgets and verified positive
certificates only.

For the other two fourth iterates covered by PR #76, the same
pair-neighborhood LP gives fractional lower bounds close to 4.05
and 4.21, respectively, which do **not** raise their previously
certified minimum dimension five; these are not new results.
