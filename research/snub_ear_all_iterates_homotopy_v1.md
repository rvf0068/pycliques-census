# A complete-ear theorem for every iterated clique graph

## Main theorem

Throughout, a **complete** is a nonempty set of pairwise
adjacent vertices, while a **clique** is an inclusion-maximal
complete, as customary in the clique-graph literature.
A graph is connected unless otherwise specified.

**Theorem (all-iterate complete-ear formula).**
Let \(X\) be a finite connected graph. Let
\(A,B\subseteq V(X)\) be nonempty disjoint complete
subsets with no edge between them. Obtain \(Y\) from
\(X\) by adjoining a new vertex \(x\) with

\[
N_Y(x)=A\mathbin{\dot\cup}B.
\]

Then, **for every integer \(j\ge0\)**,

\[
\boxed{\Delta(K^j(Y))\simeq
       \Delta(K^j(X))\vee S^1.}
\]

In particular, the extra circle survives *all* clique-graph
iterations, regardless of whether any of the iterates
is clique-Helly, contractible, convergent or divergent.

**Corollary (six snub-related nine-vertex cores).**
Let \(S\) be the snub disphenoid, graph6
`GQyuzw`. For each of the stiff cores

\[
2317843,\ 3148541,\ 3505942,\
4952669,\ 4953338,\ 5601875
\]

the theorem applies to the exact induced eight-vertex
copy of \(S\) and the ninth vertex. Thus

\[
\boxed{\Delta(K^j(G))\simeq
\Delta(K^j(S))\vee S^1\quad
\text{for every }j\ge0.}
\]

These six nine-vertex stiff cores represent
**710** still-indeterminate original ten-vertex
graphs. The statement is about the nine-vertex
cores, **not** the homotopy type of every unpared
original ten-vertex graph. The corollary does
**not** prove that \(S\) or \(G\) is
K-divergent. The original ten-vertex census
verdicts remain unchanged.

## Preliminary results (proved independently in earlier stages)

We use three elementary lemmas; the prior stages contain
full proofs and replayable finite certificates.

1. **Clique graphs preserve dominated dismantlings.**
   If \(H\) dismantles by dominated-vertex deletions
   onto \(L\), then \(K(H)\) dismantles onto a
   copy of \(K(L)\).
   See [PR #32](snub_handle_relative_k7_v1.md),
   Lemma 1.
2. **One-step complete-ear homotopy.**
   If \(Y=X+x\) with the two anticomplete
   complete link components described above,
   then
   \[
   \Delta(K(Y))\simeq\Delta(K(X))\vee S^1.
   \]
   This holds whether zero, one or both
   components are maximal in \(X\).
   See [PR #32](snub_handle_relative_k7_v1.md),
   Lemma 2.
3. **Cone-bridge dismantling.**
   If \(Z\) is connected and
   \(W=Z+a+b\), with \(ab\) an edge and
   the old neighborhoods of \(a,b\)
   disjoint, nonempty and inducing graphs
   with universal vertices, then the clique
   \(\{a,b\}\) represents a vertex \(c\)
   of \(K(W)\) with:
   \[
   K(W)-c\quad\text{dismantles onto}\quad K(Z),
   \]
   while \(N_{K(W)}(c)\) is two
   anticomplete nonempty complete subsets.
   See [PR #31](snub_handle_relative_k6_v1.md).

Here \(X+x\) denotes the actual indicated graph
extension, not an abstract graph join.

## The marked-ear/dismantling invariant

Call \(Y\) a **marked complete-ear extension
over \(X\)** if there is a distinguished
vertex \(c\in V(Y)\) such that:

- \(F=Y-c\) is connected and dismantles by
  closed-neighborhood dominated deletions
  onto an induced copy of \(X\);
- \(N_Y(c)=A\mathbin{\dot\cup}B\) for
  two nonempty complete subsets
  \(A,B\subseteq V(F)\) with no cross edges.

The key structural result is **two-step closure**.

**Proposition.** If \(Y\) is a marked
complete-ear extension over connected \(X\),
then \(K^2(Y)\) is a marked
complete-ear extension over \(K^2(X)\).

### Proof of the two-step proposition

Let \(F=Y-c\) and write \(U=K(F)\).
The cliques of \(Y\) containing \(c\) are
exactly

\[
A\cup\{c\},\qquad B\cup\{c\}.
\]

Let \(a,b\in V(K(Y))\) denote these
two maximal cliques. They are adjacent, and
**have no common neighbor outside \(\{a,b\}\)**.
Indeed, any other clique of \(Y\) meeting
both would have to meet both \(A,B\)
(because it does not contain \(c\)),
contradicting the absence of cross edges.

Therefore \(\{a,b\}\) is a maximal
clique of \(K(Y)\), defining a distinguished
vertex

\[
c'\in V(K^2(Y)).
\]

The cliques of \(K(Y)\) other than
\(\{a,b\}\) containing \(a\) form
the **a-side**, while those containing
\(b\) form the **b-side**. Each
side is nonempty because \(F\) is connected
and both \(A,B\) are nonempty proper
subsets of \(V(F)\).

Every two a-side maximal cliques meet at
\(a\), and every two b-side maximal
cliques meet at \(b\). No a-side
maximal clique meets a b-side maximal
clique: an intersection would give a
vertex of \(K(Y)\) adjacent to both
\(a,b\), impossible. Thus

\[
N_{K^2(Y)}(c')
\]

is the disjoint union of two nonempty
**complete** subsets, with no edges
between them.

It remains to show that

\[
K^2(Y)-c'\quad\text{dismantles onto}\quad K^2(F).
\]

We distinguish how many of \(A,B\)
are maximal complete in \(F\).

**Case 0: neither is a clique of \(F\).**
Every old maximal clique of \(F\)
survives in \(Y\). The graph \(K(Y)\)
is \(U\) plus two adjacent new vertices
\(a,b\). Their old neighborhoods are

\[
P_A=\{D\in K(F):D\cap A\ne\varnothing\},
\quad
P_B=\{D\in K(F):D\cap B\ne\varnothing\}.
\]

These are disjoint and nonempty. The induced
graph \(U[P_A]\) has a universal vertex:
choose \(R_A\in K(F)\) containing
\(A\); it intersects every member of
\(P_A\). The same holds for \(P_B\).
The cone-bridge dismantling lemma
therefore gives

\[
K(K(Y))-c'\quad\text{dismantles onto}\quad K(U).
\]

**Case 1: exactly one is a clique of \(F\).**
Assume \(A\in K(F)\) and \(B\notin K(F)\);
the other case is symmetric.
The graph \(K(Y)\) is \(U\) with one
new vertex \(b\), adjacent to
the old vertex \(a\) corresponding
to the replaced maximal clique \(A\),
and to the induced cone on \(P_B\).
The singleton \(\{a\}\) is
anticomplete to \(P_B\).

We use the following **cone-plus-singleton
dismantling lemma**, proved here for completeness.

Let \(T\) be a connected graph with more
than one vertex. Let \(P\subseteq V(T)\)
be nonempty and induce a cone with
universal vertex \(p\); let
\(q\in V(T)\setminus P\) have no
neighbors in \(P\). Form \(V=T+v\)
where \(N_V(v)=P\cup\{q\}\).
Then \(\{v,q\}\) is a maximal clique
of \(V\), yielding a vertex \(d\in K(V)\).
The graph \(K(V)-d\) dismantles onto
an induced copy of \(K(T)\).

To prove this, note that the other maximal
cliques containing \(v\) are precisely
\(\{v\}\cup C\) with \(C\in K(T[P])\).
Every old clique \(D\in K(T)\)
has the unique maximal extension
\(D\cup\{v\}\) if \(D\subseteq P\),
and \(D\) otherwise; the singleton
\(\{q\}\) is not a clique in
connected \(T\) with more than one
vertex. These extensions yield an
induced \(K(T)\) copy because all
maximal complete subsets of \(P\)
contain the universal vertex \(p\).

Every additional vertex of \(K(V)-d\)
corresponds to \(\{v\}\cup C\) with
\(C\in K(T[P])\setminus K(T)\).
Choose \(D_C\in K(T)\) strictly
containing \(C\). It cannot lie
wholly in \(P\), so its old embedded
vertex is unmodified. All
\(v\)-side maximal cliques contain
\(p\in C\subseteq D_C\). Every
other old clique meeting
\(\{v\}\cup C\) meets
\(D_C\) at some vertex of \(C\).
No clique containing \(q\)
meets this \(v\)-side clique,
as \(q\) is anticomplete to \(P\).
Consequently the additional vertex
is dominated by \(D_C\) in
\(K(V)-d\). Delete all such
vertices to obtain the induced
\(K(T)\). This proves the auxiliary
lemma and therefore the asserted
dismantling in Case 1.

**Case 2: both \(A,B\) are cliques of \(F\).**
The graph \(K(Y)\) is obtained from
\(U=K(F)\) by inserting one edge
\(ab\) between two previously
nonadjacent vertices. They have no
common neighbor, so this edge lies
in no triangle. The original maximal
cliques of \(U\) remain maximal
(since \(U\) is connected, with
more than one vertex), and the
only new maximal clique is
\(\{a,b\}\). Therefore

\[
K(K(Y))-c'\cong K(U)=K^2(F),
\]

with no dominated deletions needed.

All three cases prove

\[
K^2(Y)-c'\quad\text{dismantles onto}\quad K^2(F).
\]

Since \(F\) dismantles onto \(X\),
Lemma 1 shows \(K^2(F)\) dismantles
onto \(K^2(X)\). Concatenating
the fold sequences gives the
required marked extension over
\(K^2(X)\). Connectedness follows
from that of the final base.
\(\square\)

## Proof of the main theorem

At \(j=0\), the graph \(Y=X+x\)
is itself a marked complete-ear extension
over \(X\) (with no preliminary folds).

By the two-step proposition, for every
integer \(m\ge0\), the graph
\(K^{2m}(Y)\) is a marked complete-ear
extension over \(K^{2m}(X)\).

For even \(j=2m\), delete the marked
vertex \(c\). The remainder
dismantles onto \(K^{2m}(X)\).
The marked vertex is attached
along two anticomplete nonempty
complete subsets; the elementary
two-component cone-attachment formula
therefore yields

\[
\Delta(K^{2m}(Y))
\simeq
\Delta(K^{2m}(X))\vee S^1.
\]

For odd \(j=2m+1\), the one-step
complete-ear homotopy lemma gives

\[
\Delta(K^{2m+1}(Y))
\simeq
\Delta\bigl(K(K^{2m}(Y)-c)\bigr)
\vee S^1.
\]

Because clique graphs preserve
dominated dismantlings, the first
factor is homotopy equivalent to
\(\Delta(K^{2m+1}(X))\).
Thus the same formula holds for odd
\(j\). Together these cases prove
the theorem for **all** \(j\ge0\).
\(\square\)

## Exact six-core certificates and reproduction

The complete initial graph6 data and induced snub maps
are in [PR #29](order9_snub_handle_iterates_v1/certificates.json).
The new verifier independently reconstructs the original
nine-vertex cores, checks every edge **and nonedge** of their
eight-vertex induced snub, and checks the two nonempty
anticomplete **complete** components of the ninth
vertex's neighborhood.

It also rebuilds \(K^2(S)\) and \(K^2(G)\) for each
core, and finds the marked bridge and
all required closed-neighborhood dominated-fold
witnesses without relying on a large-iterate search.

The general [structural verifier](../scripts/snub_ear_all_iterates_v1.py)
authenticates the entire prior source and certificate
chain by SHA-256 and Git blob hashes. The
[regression suite](../tests/test_snub_ear_all_iterates_v1.py)
checks all three maximality cases and
independently generated examples, including
original graphs with an extra dominated
vertex in their base.

```bash
bash scripts/bootstrap_special_k3_v5.sh
.venv-special-k3-v5/bin/python scripts/snub_ear_all_iterates_v1.py verify
.venv-special-k3-v5/bin/python -m unittest discover -s tests -p 'test_snub_ear_all_iterates_v1.py' -v
```

The proof of the **universal theorem** is
combinatorial and does not depend on finite
experimental extrapolation. The finite
calculations serve to independently
verify the six concrete inputs, the
specific two-step reductions and the
implementation of the general lemmas.

## Limitations

The result compares clique-complex **homotopy
types**, not the numbers of vertices in the
iterates, and therefore does not prove
K-divergence of the snub disphenoid or
the six attached cores. No numerical
\(K^5(S)\), \(K^6(S)\) or
\(K^7(S)\) value is inferred.

The entire 8,233-case order-ten
indeterminate list and all historical
census verdicts remain unchanged.
