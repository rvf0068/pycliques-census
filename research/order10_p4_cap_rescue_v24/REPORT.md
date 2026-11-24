# Recovering all 26 previously capped fourth pared clique iterates (ten-v24)

## Scope and principal results

The merged ten-v24 P4 reference pilot (PR #89) compared the
third-iterate class representatives with \(41\le|P_3|\le55\).
There were exactly **206** representatives, of which 180 had
complete fourth iterates and 26 exceeded the historical **750
maximal-clique cap**.

This note reconstructs **all 26 formerly capped cases**, using two
independent maximal-clique enumerators and mathematically complete
closed-neighborhood folding rounds. The largest fourth clique graph
requires **4,282 maximal cliques** of its third pared iterate.

Among the 26 newly reconstructed fourth iterates, two pairs have
identical (vertex count, edge count) signatures. Exact verification
distinguishes them:

| Former P3 representatives | Fourth-iterate vertices / edges | Result |
|---|---|---|
| McKay **7044680**, **11614797** | 685 / 199,283 | **P4 isomorphic**, complete 685-vertex map |
| McKay **6927388**, **10302846** | 686 / 199,305 | **P4 nonisomorphic**, different degree sequences |

All other 22 newly reconstructed fourth iterates have different
order-and-size signatures. Every reconstructed fourth iterate
contains at least 685 vertices, while the 180 earlier complete
fourth iterates had at most 643. Thus no unexamined collision
between these two cohorts exists.

**Theorem.** The 206 previously certified distinct P3 isomorphism
classes in this window determine exactly **205 distinct P4
isomorphism classes**. There is one two-member P4 class,
represented by McKay 7044680 and 11614797, and 204
singleton P4 classes.

In particular, although their third pared iterates are
nonisomorphic and even have **different vertex counts**
(53 versus 55), their completely pared fourth clique
iterates are exactly isomorphic.

## Consequence for original connected graphs

The frozen global P3 index (PR #87) proves that the
P3 class represented by McKay 7044680 contains **17**
original connected ten-vertex graphs, whereas
McKay 11614797 is a **singleton** P3 class. Their newly
certified P4 isomorphism merges all **18 original graphs**
into one common fourth-iterate isomorphism class.

This is useful for reducing future retraction and clique-behavior
investigations: one exact fourth-iterate representative now
suffices to study their common subsequent behavior. **It is not
yet a divergence or convergence classification.**

## Complete reconstruction method

Each of the 26 source graph6 strings is read from the immutable
[PR #89 archive](../order10_p4_reference_pilot_v24/results.json),
with its **Git blob hash pinned**. The P3 class certificates
and original representatives are likewise pinned to the frozen
[global third-iterate archive](../order10_p3_global_v23_index/certificates.json).

The verifier recomputes P3 from each original graph6 with the
already certified independent third-iterate code and checks the
exact P3 order and size. It then enumerates *all* maximal
cliques of P3 by:

1. NetworkX `find_cliques`; and
2. A separate, pivoted integer-bitset Bron--Kerbosch implementation.

The complete sorted clique lists must agree. There is an
explicit 6,000-facet safety cap; **every** one of the 26
graphs finishes strictly below this cap.

The complete raw fourth clique graph is generated using
intersections of its maximal-clique vertex masks. These
adjacency masks are used for a sequence of *complete*,
simultaneous paring rounds.

### Why every folding round is valid

For a graph \(X\), write \(N_X[u]\) for the closed
neighborhood and \(C_X(u)\) for its complement
(the other vertices that are not adjacent to \(u\)).
Then

\[
N_X[u]\subseteq N_X[v]
\quad\Longleftrightarrow\quad
C_X(v)\subseteq C_X(u).
\]

The verifier marks every vertex \(u\) whose closed
neighborhood is contained in a larger one, breaking
ties between equal closed neighborhoods by original
vertex index. Every selected dominator has a strictly
smaller lexicographic pair (number of complement
nonneighbors, vertex index), so following these arrows
terminates in a survivor. Inclusion is transitive:
every marked \(u\) is directly dominated by its
eventual surviving representative in the graph at
the beginning of the round. This survivor remains
available during sequential deletion of all marked
vertices, and neighborhood containment is preserved
as other marked vertices disappear. Hence each
simultaneous round is a genuine sequence of ordinary
dominated-vertex folds.

**Completeness:** Repeat the round until no vertex
has a dominator. The verifier also checks all ordered
remaining pairs by direct closed-neighborhood
containment. The result is stiff and the paring
completely finished.

In particular, some cases require **two rounds**
(such as McKay 7044680, with 76 deletions in the
first round and 22 in the second). Treating a single
round as a complete paring would be incorrect.
The [adversarial tests](test_verify.py) also exercise
this distinction on the four-vertex path.

## Complete positive isomorphism certificate

The [certificate archive](certificates.json) stores
an explicit full map of **all 685 canonical P4
vertices**, from the P4 of McKay 7044680 to that of
McKay 11614797. Its encoding is little-endian
unsigned 16-bit integers followed by Base64; the
complete map bytes have SHA-256

`bd2a5bb6713fa5dc02d55b906f58b4567fe425b57add9efd2dfb0f95a0a3e363`.

The independent verifier first checks that the map is
a bijection, then tests **every edge and nonedge**:

\[
uv\in E(P_4(G_{7044680}))
\quad\Longleftrightarrow\quad
\varphi(u)\varphi(v)\in E(P_4(G_{11614797})).
\]

As an additional cross-check, it runs a separately
implemented NetworkX GraphMatcher on the two
*complementary* fourth iterates, with unique vertex
colors constraining the match to precisely the saved
permutation. Thus the proof does not depend on finding
some accidental alternative isomorphism.

The other repeated dimension signature, shared by
McKay 6927388 and 10302846, is *not* evidence of
isomorphism: their degree multisets are different.
Consequently the table above exhausts all P4
equivalence relations in this 206-class window.

## The largest newly recovered graph

McKay **11708820**, third-iterate order 42,
previously hit the 750-facet limit. The exact
fourth-iterate reconstruction gives:

| Graph | Vertices | Edges |
|---|---:|---:|
| \(K(P_3)\) | 4,282 | 9,033,001 |
| \(P_4\) | **3,928** | **7,595,356** |

A single batch of 354 valid dominated-vertex folds
gives a graph verified stiff on every ordered pair.
The large graph is still *indeterminate* as to clique
behavior, but its fourth-iterate size is now known
exactly rather than resource-limited.

## Reproduction and classification discipline

From the census repository root with pinned
NetworkX 3.6.1:

```sh
python -m unittest research.order10_p4_cap_rescue_v24.test_verify -v
python -m research.order10_p4_cap_rescue_v24.verify
```

The [GitHub Actions workflow](../../.github/workflows/order10-p4-cap-rescue-v24.yml)
repeats all 26 graph reconstructions and the complete
685-vertex map with independent clique enumeration,
round-by-round fold verification, mutation tests,
and an optimized-execution guard.

**No census rows, historical snapshots, or clique-behavior
verdicts change**. The complete result reduces the
number of independent fourth-iterate targets to study,
but does not establish \(K\)-divergence for any new
original graph.
