# The fifth completely pared clique iterate of McKay 10820813

## Exact finite result

For McKay **10820813**, graph6 ``ICp`fpv~_``, let
\(P_0=P(G)\) and \(P_{i+1}=P(K(P_i))\), where \(P\) denotes
complete closed-neighborhood paring. The PR #90 proof already
certified that no \(P_0,\ldots,P_4\) retracts ordinarily onto
an induced \(O_d\), \(d\ge3\).

**New certified counts:**

| Stage | Vertices | Edges |
|---|---:|---:|
| \(P_4\) | 70 | 1,830 |
| \(K(P_4)\) | 1,977 | 1,742,560 |
| \(P_5\) | **1,896** | **1,601,683** |

The graph \(P_4\) has exactly **1,977 maximal cliques**.
Exactly **81** of their vertices in \(K(P_4)\) have a
closed-neighborhood dominator that survives a single simultaneous
paring round. Deleting these 81 vertices yields a **stiff**
1,896-vertex graph, whose complement has 194,777 edges.

The frozen fourth-iterate graph6 SHA-256 is
`c26ee7c369318b01c0598b0ef7270b406c538bfd0ec34f5152c1ff649a3f3873`.
The raw \(K(P_4)\) and its completely pared residual are
separately SHA-256-pinned, using the concatenation of adjacency
rows as fixed-width little-endian integers (248 and 237 bytes
per row, respectively):

- Raw K5:
  `ed05c0dd4b6f29789913b06448ac1657975b33368240ca2b393a44e0bb40c24f`
- Completely pared P5:
  `5c1f72ed509e8e4fdc8710278aac9c944f4507b8c0fee8862e956c88f6678220`

Two completely independent maximal-clique enumerators
(NetworkX and bitset Bron--Kerbosch) recover identical sorted
facet sets at the fifth stage. The exact adjacency rule
\(q_i\sim q_j\) if and only if \(q_i\cap q_j\ne\varnothing\)
is checked on **every one of the 1,953,276 vertex pairs**
of the raw fifth clique graph.

## Why the complete 81-fold paring is valid

**Lemma (simultaneous fold certificate).** Let \(X\) be any
finite graph, and select for deletion exactly those vertices
\(u\) whose closed neighborhood \(N_X[u]\) is contained
in a strictly larger closed neighborhood, or in an equal
neighborhood represented by a smaller-index vertex.
Then all selected vertices can be removed by a sequence
of ordinary dominated-vertex deletions. If the remaining
graph is stiff, it is a complete paring of \(X\).

*Proof.* A domination arrow \(u\mapsto v\) strictly decreases
the lexicographic pair (number of nonneighbors, vertex index).
It therefore terminates at an undeleted vertex \(r(u)\).
Inclusion of closed neighborhoods is transitive, so
\(N_X[u]\subseteq N_X[r(u)]\). The terminal dominator is
present throughout the removal sequence. Removing other
vertices can only restrict both closed neighborhoods, so
the inclusion persists until \(u\) is deleted. After all
such deletions, stiffness is precisely the absence of any
further domination. \(\square\)

For this particular \(K(P_4)\), the Python proof checks the
original 81 direct surviving-dominator containments
and **every ordered pair** among the 1,896 surviving
vertices for any remaining domination.

## An induced complement-dominating octahedron of dimension 20

The archived [certificate](certificates.json) contains
**20 disjoint antipodal pairs** in canonical P5 labels.
Each pair is a nonedge in P5 and all cross-pair edges
are present, so the 40 endpoints induce
\(O_{20}=\overline{20K_2}\).

Moreover, writing \(H=\overline{P_5}\), the union of the
closed neighborhoods of these 40 endpoints in \(H\)
is the entire vertex set: they **dominate \(H\)**.

However, this particular induced \(O_{20}\) **does not
retract from \(P_5\)**. Every retraction fixing its
antipodal pairs \((a_i,b_i)\) would require each
outside vertex \(x\) to have image in

\[
D_x=\{a_i:xb_i\in E(H)\}\cup
    \{b_i:xa_i\in E(H)\}.
\]

Indeed, mapping \(x\) to \(a_i\) when \(xb_i\in E(P_5)\)
would map a source edge to the forbidden target nonedge
\(a_ib_i\); the other case is symmetric.

**Exactly 210 outside vertices have singleton domains**.
In the canonical P5 labels,

\[
87\sim458,\qquad
D_{87}=\{857\},\quad D_{458}=\{1397\}.
\]

The vertices 857 and 1397 are **antipodal** in the
same induced \(O_{20}\). Thus the actual source edge
\(87\sim458\) would be forced to a nonedge, contradicting
the graph-morphism requirement even when edge collapse
is allowed.

This is an exact *negative certificate for one specified
target only*. It does not exclude other induced octahedral
retracts in P5, different divergent targets, or later
iterations.

## A sufficient one-shore criterion for future positive searches

**Lemma.** Let \(H=\overline X\) and let
\(B=\{b_1,\ldots,b_d\}\) be an independent dominating set
of \(H\). If \(B\) has distinct private neighbors
\(a_1,\ldots,a_d\) such that the pairs \(a_ib_i\)
form an induced matching of \(H\), then \(X\) retracts
onto the induced octahedron \(O_d\) on \(A\cup B\).

*Proof.* The matching gives the required induced
octahedron. Fix its vertices pointwise. For each
\(x\notin A\cup B\), select a vertex \(b_i\in B\)
with \(xb_i\in E(H)\), which exists by domination,
and map \(x\mapsto a_i\). All outside vertices map
into the complete set \(A\) in \(X\), so edges among
outside vertices are preserved. An outside vertex
mapped to \(a_i\) is nonadjacent in \(X\) to \(b_i\),
and \(a_i\) is adjacent in \(X\) to all other target
vertices except its antipode \(b_i\). Hence every
outside-to-target edge is respected as well, while
the target is fixed pointwise. \(\square\)

This criterion is **sufficient, not necessary**.
Bounded exploratory searches did not locate such a
one-shore certificate for McKay 10820813; that is
only a search limitation, not a theorem of nonexistence.

## Independent reproduction

[verify.py](verify.py) imports only the already frozen
independent fourth-stage proof and implements the *new*
fifth-stage Bron--Kerbosch and complete paring itself.
[verify_independent.cpp](verify_independent.cpp) independently
reads the SHA-pinned 70-vertex P4 complement graph and
recomputes everything in C++20, including all folds,
stiffness, induced \(O_{20}\), domination, and the forced
antipodal conflict. It also serializes both complete
adjacency matrices for SHA-256 checks.

From the census repository root with NetworkX 3.6.1:

```sh
python -m unittest research.order10_p5_growth_10820813_v1.test_verify -v
python -m research.order10_p5_growth_10820813_v1.verify

python -m research.order10_p4_no_octahedral_10820813_v1.verify \
  --export-complement /tmp/10820813_p4_H.txt
g++ -O2 -std=c++20 -Wall -Wextra -Werror \
  research/order10_p5_growth_10820813_v1/verify_independent.cpp \
  -o /tmp/verify_p5
/tmp/verify_p5 /tmp/10820813_p4_H.txt \
  /tmp/raw_p5_adjacency.bin /tmp/p5_adjacency.bin
```

The [GitHub Actions workflow](../../.github/workflows/order10-p5-10820813-growth-v1.yml)
checks both C++ adjacency SHA-256s in a separate job,
runs positive and adversarial Python tests, and rejects
optimized proof replay.

**Classification remains indeterminate.** This note
certifies exact stage-five growth and a substantial
induced octahedral structure, not eventual clique divergence.
