# Seventh clique iterate: fold preservation and two-complete attachment

## Exact relative homotopy theorem

Let \(S\) be the snub disphenoid (graph6 `GQyuzw`) and
let \(G\) be any of the six unresolved nine-vertex stiff cores

\[
2317843,\quad3148541,\quad3505942,\quad
4952669,\quad4953338,\quad5601875.
\]

Then

\[
\boxed{\Delta(K^7(G))\simeq\Delta(K^7(S))\vee S^1.}
\]

The six classes have **710 original ten-vertex members**.
The theorem compares their **nine-vertex stiff cores**; it does not
claim that the same higher-iterate homotopy formula holds for
each unpared ten-vertex original. Their clique convergence/divergence
behavior remains indeterminate.

This is proved without constructing \(K^5(S)\),
\(K^6(S)\), or \(K^7(S)\). It extends the finite
comparison through \(j=6\) proved in
[PR #31](snub_handle_relative_k6_v1.md).

We use the standard clique-literature terminology: a
*complete* is a nonempty pairwise-adjacent vertex set,
and a *clique* is an inclusion-maximal complete.

## Lemma 1: the clique operator preserves dominated folds

**Lemma.** If a vertex \(v\) of a finite graph \(H\)
satisfies \(N_H[v]\subseteq N_H[u]\) for some
\(u\ne v\), then \(K(H)\) dismantles onto
an induced subgraph isomorphic to \(K(H-v)\).

Consequently, if \(H\) dismantles onto \(F\),
then \(K(H)\) dismantles onto a copy of
\(K(F)\).

**Proof.** Every clique of \(H\) containing \(v\)
also contains \(u\): otherwise the dominating
vertex \(u\) could be added.

For each \(D\in K(H-v)\), define

\[
\iota(D)=
\begin{cases}
D\cup\{v\}, &\text{if every vertex of }D
                   \text{ is adjacent to }v,\\
D,&\text{otherwise}.
\end{cases}
\]

Each \(\iota(D)\) is a clique of \(H\).
Distinct \(D\)'s have distinct images. If two
images gain an intersection only at \(v\),
their original cliques are both contained
in \(N_H(v)\). But both then contain \(u\)
by maximality in \(H-v\), so the originals
already intersect. Hence \(\iota\) induces
a graph isomorphism between \(K(H-v)\)
and an **induced** subgraph of \(K(H)\).

Let \(C\in K(H)\) not belong to that induced
copy. Then \(v\in C\), and \(C\setminus\{v\}\)
is not a clique of \(H-v\). Choose
\(D\in K(H-v)\) strictly containing
\(C\setminus\{v\}\). The vertex \(v\)
is **not** adjacent to every vertex of \(D\);
otherwise \(D\cup\{v\}\) would strictly
contain \(C\), contradicting maximality.
Thus \(\iota(D)=D\).

Every clique of \(H\) intersecting \(C\)
at a vertex other than \(v\) also intersects
\(D\). Every clique intersecting \(C\)
at \(v\) contains \(u\in D\), because \(u\)
dominates \(v\). Therefore

\[
N_{K(H)}[C]\subseteq N_{K(H)}[D].
\]

Delete all such extra vertices \(C\), keeping
the embedded old vertices \(\iota(D)\).
They remain dominated at each deletion step.
The surviving graph is exactly
\(K(H-v)\). Iterate this argument along
any sequence of dominated deletions.
\(\square\)

## Lemma 2: a two-complete ear adds a circle under K

**Lemma.** Let \(X\) be a finite connected graph,
and let \(A,B\subseteq V(X)\) be disjoint,
nonempty **complete subsets** with no edges
between them. Let \(Y=X+x\), where \(x\)
is adjacent precisely to \(A\cup B\).
Then

\[
\boxed{\Delta(K(Y))\simeq\Delta(K(X))\vee S^1.}
\]

No maximality assumption is imposed on \(A\)
or \(B\).

**Proof.** The cliques of \(Y\) not containing
\(x\) are precisely the cliques of \(X\)
other than \(A,B\) when either happens to
be maximal. There are precisely two cliques
containing \(x\), namely
\(A\cup\{x\}\) and \(B\cup\{x\}\).
Define

\[
P_A=\{D\in K(X):D\cap A\ne\varnothing\},
\quad
P_B=\{D\in K(X):D\cap B\ne\varnothing\}.
\]

They are nonempty and disjoint. Each induces a
**cone** in \(K(X)\): if \(R_A\in K(X)\)
contains \(A\), then \(R_A\in P_A\)
intersects every \(D\in P_A\);
similarly choose \(R_B\).
As \(X\) is connected, so is \(K(X)\).
There are three cases.

**Case 1: neither \(A\) nor \(B\) is a clique
of \(X\).** Every old clique of \(X\)
remains maximal in \(Y\); the two new
cliques yield adjacent vertices \(a,b\)
of \(K(Y)\), attached to the old
\(K(X)\) along \(P_A,P_B\), respectively.
No old vertex is adjacent to both \(a,b\).
The union of their two closed simplicial
stars is contractible, and it intersects
\(\Delta(K(X))\) along two disjoint
nonempty contractible subcomplexes.
The homotopy pushout is
\(\Delta(K(X))\vee S^1\).

**Case 2: exactly one of \(A,B\) is a clique
of \(X\).** Suppose \(A\in K(X)\)
and \(B\notin K(X)\). The old maximal
clique \(A\) is replaced by
\(A\cup\{x\}\), without changing the
incidences among the old clique-graph
vertices. The only new vertex of \(K(Y)\)
is \(b=B\cup\{x\}\), whose old link
consists of \(P_B\) together with the
single old vertex corresponding to \(A\).
These two link components are disjoint
and anticomplete: an old maximal clique
meeting both \(A\) and \(B\) would
contain an edge between them, which is
forbidden. The component on \(P_B\)
is a cone and the other a singleton.
Attaching \(b\) therefore gives one
circle wedge. The opposite case is
symmetric.

**Case 3: both \(A,B\) are cliques of
\(X\).** Both are replaced by
\(A\cup\{x\}\), \(B\cup\{x\}\).
The clique graphs differ only by a new
edge between their corresponding old
vertices. Those vertices were
nonadjacent in \(K(X)\), and they have
no common old neighbor: such a
neighbor would be a clique of \(X\)
meeting both \(A,B\), again impossible.
The newly added edge therefore belongs
to no new triangle (or higher simplex)
and is an attached one-cell between
two existing vertices of the connected
\(\Delta(K(X))\). It adds one
\(S^1\) wedge.

In all cases,
\(\Delta(K(Y))\simeq\Delta(K(X))\vee S^1\).
\(\square\)

The three cases differ at the **graph** level:
\(K(Y)\) has respectively two, one,
or zero more vertices than \(K(X)\).
Consequently an unknown maximality
case does not prevent the homotopy
conclusion.

## Application to the sixth-iterate bridge

Merged PR #31 proves the following exact structural
statement for each of the six stiff cores:

\[
K^6(G)=F+c,
\]

where

1. \(F=K^6(G)-c\) dismantles onto an
   induced copy of \(Z=K^6(S)\);
2. the open neighborhood of \(c\)
   consists of two anticomplete, nonempty
   **complete** subsets \(A,B\subseteq V(F)\);
3. \(F\) is connected, because it dismantles
   onto connected \(K^6(S)\).

Applying Lemma 2 to \(F+c\) gives

\[
\Delta(K^7(G))
\simeq \Delta(K(F))\vee S^1.
\]

Applying Lemma 1 to every dominated deletion
of \(F\to Z\) gives a dominated-vertex
dismantling of \(K(F)\) onto \(K(Z)\).
In particular

\[
\Delta(K(F))\simeq
\Delta(K(Z))=
\Delta(K^7(S)).
\]

Combining these equivalences proves the theorem.

Unlike the preceding sixth-iterate theorem,
this does **not** assert that \(K^7(S)\) embeds
induced in \(K^7(G)\) in all three
maximality cases. It proves the homotopy
equivalence and also the weak order inequality

\[
|K^7(G)|\ge |K^7(S)|,
\]

because clique graphs preserve the
dismantling of \(F\) and Lemma 2
never removes more clique-graph vertices
than it adds.

## Independent verification

The [new verifier](../scripts/core9_snub_relative_k7_v1.py)
authenticates the merged PR #31 source Git blob and
replays its entire K⁴, K⁵, K⁶ certificate chain.
For separate small input graphs, it explicitly
enumerates all maximal cliques and checks
both the induced clique-graph embeddings and
the dominated-neighborhood inequalities.

The [test suite](../tests/test_core9_snub_relative_k7_v1.py)
checks all three complete-ear cases, false
domination maps, malformed attachments and
reproducibly randomized independent examples.
These finite tests supplement the general
proofs above; they are not used to extrapolate
the theorem from a finite search.

Reproduce from the census repository:

```bash
bash scripts/bootstrap_special_k3_v5.sh
.venv-special-k3-v5/bin/python scripts/core9_snub_relative_k7_v1.py verify
.venv-special-k3-v5/bin/python -m unittest discover -s tests -p 'test_core9_snub_relative_k7_v1.py' -v
```

## What remains unresolved

For the six cores the relative homotopy formula
now holds for **all eight finite iterates**
\(j=0,1,\ldots,7\).
This does not establish an all-iterate
inductive invariant, a numerical estimate of
\(|K^7(S)|\), or clique divergence.
The 710 original ten-vertex graphs in these
classes retain their indeterminate status
and the 8,233-case v4 list is unchanged.

At the next level, the graph structure
branches according to whether zero, one,
or both complete link components in \(F\)
are maximal. Controlling all three branches
under another application of \(K\)
is the main mathematical obstacle for \(K^8\).
