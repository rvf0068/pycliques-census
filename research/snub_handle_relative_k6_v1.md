# Sixth clique iterate: a cone-bridge dismantling theorem

## Result and scope

Let \(S\) be the snub disphenoid, graph6 `GQyuzw`, and let
\(G\) be any of the six stiff nine-vertex cores

\[
2317843,\ 3148541,\ 3505942,\ 4952669,\ 4953338,\ 5601875.
\]

These represent **710** still-indeterminate original connected
ten-vertex graphs. Then

\[
\boxed{\Delta(K^6(G))\simeq\Delta(K^6(S))\vee S^1.}
\]

More precisely, **\(K^6(S)\) is an induced subgraph of
\(K^6(G)\)**, and there is a distinguished vertex \(c\)
in \(K^6(G)\) such that

- \(K^6(G)-c\) dismantles, by deleting vertices with
  dominated closed neighborhoods, onto the induced copy of
  \(K^6(S)\);
- the open neighborhood of \(c\) in \(K^6(G)\) is the
  disjoint union of two nonempty complete subsets, with
  no edges between them.

In particular,

\[
|K^6(G)|\ge |K^6(S)|+1.
\]

For the cores **2317843, 3148541, 4952669**, there is
also the finite *relative* order bound

\[
1\le |K^6(G)|-|K^6(S)|\le3.
\]

None of these statements requires knowing the numerical orders
of \(K^5(S)\) or \(K^6(S)\).

This extends the exact homotopy comparison through \(j=5\) from
[PR #29](order9_snub_handle_iterates_v1/summary.md) and
[PR #30](snub_handle_relative_k5_v1.md) to every \(0\le j\le6\).
The theorem concerns **clique-complex homotopy**, not an
unconditional K-convergence or K-divergence certificate.

## General cone-bridge theorem

Use the clique-graph literature convention: a *complete*
is a nonempty pairwise-adjacent vertex set, and a *clique*
is an inclusion-maximal complete.

**Theorem.** Let \(Z\) be a finite, connected graph. Let
\(P,Q\subseteq V(Z)\) be disjoint nonempty subsets such that
both induced subgraphs \(Z[P]\) and \(Z[Q]\) have a universal
vertex. The two induced graphs are not required to be
complete, and there may be edges between \(P\) and \(Q\).

Form \(W\) from \(Z\) by adjoining two adjacent vertices
\(a,b\), with

\[
N_W(a)\cap V(Z)=P,\qquad
N_W(b)\cap V(Z)=Q.
\]

Then:

1. \(K(Z)\) embeds as an **induced** subgraph of \(K(W)\).
2. The clique \(\{a,b\}\) represents a distinguished
   vertex \(c\in V(K(W))\). The graph \(K(W)-c\)
   folds onto the embedded \(K(Z)\).
3. \(N_{K(W)}(c)\) is the disjoint union of two nonempty
   complete subsets, with no edges between them.
4. Consequently,
   \[
   \boxed{\Delta(K(W))\simeq\Delta(K(Z))\vee S^1.}
   \]

The theorem gives an exact vertex-count formula. Write
\(\mathcal M(H)=K(H)\) for the maximal cliques of \(H\)
(the notation is used here only for clarity). Define

\[
t_P=|\{T\in K(Z[P]):T\notin K(Z)\}|,\qquad
t_Q=|\{T\in K(Z[Q]):T\notin K(Z)\}|.
\]

Then

\[
|K(W)|=|K(Z)|+1+t_P+t_Q.
\]

If **both** \(P,Q\) are complete, each contributes
at most one additional maximal clique, so the order
difference lies in \(\{1,2,3\}\).

### Proof

Let \(p\) and \(q\) be universal vertices of
\(Z[P]\) and \(Z[Q]\), respectively. Every maximal
complete subset of \(P\) contains \(p\); every maximal
complete subset of \(Q\) contains \(q\).

**Step 1: enumerate the maximal cliques of \(W\).**
Because \(a\) and \(b\) are adjacent and have no
common neighbor in \(Z\), \(\{a,b\}\) is a clique
of \(W\). The other cliques containing \(a\) are
exactly

\[
\{a\}\cup T,\qquad T\in K(Z[P]),
\]

and analogously the other cliques containing \(b\)
are \(\{b\}\cup U\) with \(U\in K(Z[Q])\).
A clique \(D\in K(Z)\) remains maximal in \(W\)
unless \(D\subseteq P\) or \(D\subseteq Q\).

**Step 2: exhibit an induced copy of \(K(Z)\).**
For every \(D\in K(Z)\), define its unique maximal
extension in \(W\) by

\[
\iota(D)=
\begin{cases}
D\cup\{a\},&D\subseteq P,\\
D\cup\{b\},&D\subseteq Q,\\
D,&\text{otherwise}.
\end{cases}
\]

Each is a maximal clique of \(W\), and distinct
\(D\)'s give distinct extensions. We must check
both adjacency and *nonadjacency* in their
intersection graphs. If two old cliques acquire
the new common vertex \(a\), both lie in \(P\),
hence already contain \(p\) and already intersect.
The same holds for \(b\) using \(q\). No other
new common intersections arise. Therefore
\(D\cap D'\ne\varnothing\) if and only if
\(\iota(D)\cap\iota(D')\ne\varnothing\), proving
that \(\iota(K(Z))\) is induced in \(K(W)\).

**Step 3: describe all additional clique-graph vertices.**
Besides \(c=\{a,b\}\), the vertices outside the
induced old copy correspond precisely to
\(\{a\}\cup T\) for \(T\in K(Z[P])\setminus K(Z)\)
and \(\{b\}\cup U\) for
\(U\in K(Z[Q])\setminus K(Z)\).
This gives the count formula.

**Step 4: verify dominated-vertex deletions after
removing \(c\).** Let \(e_T\) be one of the new
vertices represented by \(\{a\}\cup T\), with
\(T\in K(Z[P])\setminus K(Z)\). Since \(T\)
is complete but not maximal in \(Z\), choose a
clique \(D_T\in K(Z)\) strictly containing \(T\).
It cannot lie wholly in \(P\), by the maximality
of \(T\) in \(Z[P]\), nor wholly in \(Q\).
Thus the old embedded vertex \(\iota(D_T)=D_T\)
is present in \(K(W)-c\).

Every neighbor of \(e_T\) in \(K(W)-c\) is
also adjacent to \(D_T\):

- An old embedded vertex meeting \(e_T\) must
  meet \(T\subseteq D_T\), unless it is an
  \(a\)-side vertex, handled next.
- Every clique of \(W\) on the \(a\)-side contains
  \(p\), and \(p\in T\subseteq D_T\).
  Hence \(D_T\) intersects all \(a\)-side cliques.
- No \(b\)-side clique meets \(e_T\), since
  \(P\cap Q=\varnothing\).

Also \(D_T\) meets \(e_T\) itself. Thus
\[
N_{K(W)-c}[e_T]\subseteq N_{K(W)-c}[D_T].
\]
The identical argument treats every new \(b\)-side
vertex. Delete them all, in any order, keeping
their old dominators. The resulting graph is the
induced copy of \(K(Z)\). This is a verified
**graph dismantling**, not merely a homotopy
equivalence.

**Step 5: attach the bridge vertex \(c\).**
The cliques of \(W\) that meet \(\{a,b\}\)
are exactly its \(a\)-side and \(b\)-side
cliques. Every two \(a\)-side cliques share
\(a\), and every two \(b\)-side cliques share
\(b\). A clique on one side is disjoint from
any clique on the other, because its old vertices
lie in \(P\) or \(Q\), and \(P\cap Q=\varnothing\).
Thus the link of \(c\) consists of two disjoint
nonempty simplices.

The old graph \(K(Z)\) is connected because
\(Z\) is connected, and the dominated-vertex
deletions show that \(K(W)-c\) is connected.
Coning off a union of two nonempty contractible
components in a connected clique complex adds
one circle wedge. Hence

\[
\Delta(K(W))\simeq
\Delta(K(W)-c)\vee S^1
\simeq\Delta(K(Z))\vee S^1,
\]

as required. \(\square\)

## Application to the six snub-related cores

The preceding merged certificate chain proves:

- \(X=K^4(S)\) is connected and is an induced
  subgraph of \(Y=K^4(G)\);
- \(Y=X+x\), where \(N_Y(x)=A\mathbin{\dot\cup}B\);
- \(A,B\) are nonempty complete subsets of \(X\)
  with no edges between them, and neither is a clique of \(X\);
- \(K(Y)=K^5(G)\) is obtained from \(Z=K^5(S)=K(X)\)
  by two new adjacent vertices \(a,b\), whose old
  neighborhoods are
  \[
  P_A=\{D\in K(X):D\cap A\ne\varnothing\},\qquad
  P_B=\{D\in K(X):D\cap B\ne\varnothing\}.
  \]

These neighborhoods are disjoint: a clique of \(X\)
meeting both \(A\) and \(B\) would contain
vertices joined by an edge across the two
anticomplete complete subsets, impossible.

Each is a cone. Choose a maximal clique
\(R_A\in K(X)\) containing \(A\). Every
\(D\in P_A\) intersects \(R_A\) at a
vertex of \(A\), so \(R_A\) is universal
in the induced graph \(Z[P_A]\). Similarly
\(R_B\) is universal in \(Z[P_B]\).

Finally, \(Z=K(X)\) is connected since
\(X\) is connected. All hypotheses of the
cone-bridge theorem apply **without constructing
\(Z\)**, yielding the result on \(K^6\).

| Nine-core ID | \(|A|\) | \(|B|\) | Original ten-vertex graphs | Sixth-iterate order increment |
|---:|---:|---:|---:|---|
| 2317843 | 1 | 1 | 70 | between 1 and 3 |
| 3148541 | 1 | 1 | 114 | between 1 and 3 |
| 3505942 | 1 | 82 | 133 | at least 1 |
| 4952669 | 1 | 1 | 86 | between 1 and 3 |
| 4953338 | 1 | 62 | 196 | at least 1 |
| 5601875 | 1 | 34 | 111 | at least 1 |
| **Total** | | | **710** | |

For \(|A|=|B|=1\), the corresponding
\(P_A,P_B\) consist of maximal cliques of
\(X\) containing a fixed vertex. They are
themselves complete in \(K(X)\), hence
\(t_{P_A},t_{P_B}\in\{0,1\}\), justifying
the explicit upper bound \(3\) for three
of the six cores.

## Verification and limits

The [standalone verifier](../scripts/core9_snub_relative_k6_v1.py)
first authenticates the merged PR #30 K⁵ certificate
verifier by its Git object SHA, then replays the
SHA-pinned K⁴/K⁵ evidence. Its independent
finite \(\texttt{verify_general_cone_bridge}\)
routine enumerates **all maximal cliques** of
small generic inputs, checks the embedding
against every adjacency and nonadjacency,
verifies the exact count formula, and produces
the actual closed-neighborhood domination
certificates after deleting \(c\).

The regression suite checks path, cycle-like,
noncomplete cone and reproducibly randomized
examples, plus malformed, overlapping,
disconnected and non-cone inputs.

```bash
bash scripts/bootstrap_special_k3_v5.sh
.venv-special-k3-v5/bin/python scripts/core9_snub_relative_k6_v1.py verify
.venv-special-k3-v5/bin/python -m unittest discover -s tests -p 'test_core9_snub_relative_k6_v1.py' -v
```

**No** numerical \(K^6(S)\) value has
been claimed, and no current divergence or
convergence verdict changes. In particular,
the versioned order-ten indeterminate
population remains **8,233**.

The next mathematical challenge is to find a
stronger structural invariant that survives
this bridge-deleted dismantling and controls
\(K^7\), since the clique graph operator
does not preserve arbitrary graph dismantlings
in a way that would automatically justify
another iteration.
