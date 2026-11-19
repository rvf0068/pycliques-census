# Exact relative fifth clique iterate without constructing \(K^5(S)\)

## Theorem

Let \(S\) be the snub disphenoid (graph6 `GQyuzw`). Let
\(G\) be any of the following six unresolved stiff nine-vertex cores:
`2317843`, `3148541`, `3505942`, `4952669`, `4953338`, and
`5601875`. These represent **710** still-indeterminate original
ten-vertex graphs. Then

\[
|K^5(G)|=|K^5(S)|+2
\qquad\text{and}\qquad
\Delta(K^5(G))\simeq\Delta(K^5(S))\vee S^1.
\]

In fact \(K^5(S)\) is an **induced** subgraph of \(K^5(G)\).
The two extra vertices are adjacent, their neighborhoods in
\(K^5(S)\) are disjoint, and both neighborhoods have cone clique
complexes.

These are exact mathematical statements, not estimates. We **do not
calculate** the potentially huge number \(|K^5(S)|\), and we do not
claim K-divergence. This extends the proved finite result for
\(0\le j\le4\) in [merged PR #29](../research/order9_snub_handle_iterates_v1/summary.md)
by one further iteration.

## General two-clique extension lemma

**Lemma.** Let \(X\) be a finite connected graph and let \(A,B\)
be two nonempty, disjoint cliques (maximal complete subgraphs are *not*
assumed). Suppose there are **no edges** from \(A\) to \(B\), and
neither \(A\) nor \(B\) is a clique of \(X\) (i.e. neither is
inclusion-maximal complete in \(X\)). Let \(Y\) be obtained by
adjoining a vertex \(x\) with \(N_Y(x)=A\cup B\). Then:

1. The maximal cliques of \(Y\) are exactly those of \(X\), plus
   \(A\cup\{x\}\) and \(B\cup\{x\}\).
2. Thus \(K(X)\) is an induced subgraph of \(K(Y)\), and \(K(Y)\)
   has exactly two further vertices \(a,b\), joined by an edge.
3. The sets of neighbors of \(a,b\) inside \(K(X)\) are disjoint,
   nonempty, and their clique complexes are cones.
4. Therefore \(\Delta(K(Y))\simeq \Delta(K(X))\vee S^1\), and
   \(|K(Y)|=|K(X)|+2\).

**Proof.** Every inclusion-maximal complete subset of \(Y\) not
containing \(x\) is a maximal clique of \(X\). Conversely, every
maximal clique \(Q\) of \(X\) stays maximal in \(Y\). If it were
enlarged by \(x\), then \(Q\subseteq A\cup B\), and since there are
no cross-edges between \(A,B\), we would have \(Q\subseteq A\)
or \(Q\subseteq B\). Maximality of \(Q\) in \(X\) would imply
\(Q=A\) or \(Q=B\), contradicting the hypotheses. The only
maximal cliques of \(Y\) containing \(x\) are
\(A\cup\{x\}\) and \(B\cup\{x\}\). This proves (1) and (2).

The old-vertex neighbors of \(a\) in \(K(X)\) are precisely
\[
P_A=\{Q\in K(X):Q\cap A\ne\varnothing\};
\]
analogously define \(P_B\). If a maximal clique \(Q\) belonged to
both sets, then it would contain two adjacent vertices, one from \(A\)
and one from \(B\), impossible. So \(P_A\cap P_B=\varnothing\).
Choose a maximal clique \(R_A\in K(X)\) containing \(A\).
It lies in \(P_A\) and intersects every other member of \(P_A\)
at a vertex of \(A\). Thus \(R_A\) is universal in the induced
graph \(K(X)[P_A]\), whose clique complex is a cone. The same
argument applies to \(P_B\).

Since \(a\) and \(b\) both contain \(x\), they are adjacent.
Their closed stars have contractible union: their intersection is the
closed star of \(\{a,b\}\), as no old vertex is adjacent to both.
This union meets \(\Delta(K(X))\) exactly in the disjoint union of
the two nonempty contractible complexes
\(\Delta(K(X)[P_A])\) and \(\Delta(K(X)[P_B])\).
The graph \(K(X)\) is connected because \(X\) is connected.
The homotopy-pushout or two-component gluing formula therefore gives
\(\Delta(K(Y))\simeq\Delta(K(X))\vee S^1\). QED.

## Six concrete, independently checked nonmaximality witnesses

The exact fourth-iterate certificates in [PR #29](../research/order9_snub_handle_iterates_v1/certificates.json)
already prove that \(X=K^4(S)\) is an induced subgraph of
\(Y=K^4(G)\) and that the unique new vertex has link
\(X[A\cup B]\), the **disjoint union of two nonempty complete
graphs** on \(A,B\).

The only new hypothesis needed for the lemma is that neither
\(A\) nor \(B\) be maximal in \(X\). Each witness below is a
vertex of \(X\) outside the indicated component, adjacent to
**every vertex of that component**. The labels use the reproducible
lexicographic sorting of maximal cliques of \(K^3(S)\) and are
checked through exact facet intersection bitsets; no fifth clique
graph is constructed.

| Core ID | \(|A|\) | Witness extending \(A\) | \(|B|\) | Witness extending \(B\) | Original ten-vertex members |
|---:|---:|---:|---:|---:|---:|
| 2317843 | 1 | 0 | 1 | 1 | 70 |
| 3148541 | 1 | 0 | 1 | 243 | 114 |
| 3505942 | 1 | 0 | 82 | 243 | 133 |
| 4952669 | 1 | 0 | 1 | 243 | 86 |
| 4953338 | 1 | 243 | 62 | 0 | 196 |
| 5601875 | 1 | 0 | 34 | 534 | 111 |
| **Total** | | | | | **710** |

Connectedness of \(K^4(S)\) is independently checked by a union-find
over its maximal-clique incidence representation. That suffices for
the homotopy gluing lemma without enumerating the maximal cliques of
\(K^4(S)\), whose number is \(|K^5(S)|\).

## What remains open

We have the relative circle-wedge formula **through \(j=5\)** for
these six nine-vertex cores, not for all \(j\). The analogous
\(K^6\) statement requires control of maximal cliques of
\(K^5(S)\) and the two new adjacent vertices in \(K^5(G)\).
The two-clique extension lemma alone does not supply this next step.

The convergent two-periodic family in
[the cycle-handle note](snub_handle_cycle_analogue.md) shows why
an alternating difference of one/two vertices is **not** by itself
a divergence certificate. No existing status in
`indeterminate_order_10_v4.txt` changes.

## Reproduction

From the current census checkout:

```bash
bash scripts/bootstrap_special_k3_v5.sh
.venv-special-k3-v5/bin/python scripts/core9_snub_relative_k5_v1.py verify
.venv-special-k3-v5/bin/python -m unittest discover -s tests -p 'test_core9_snub_relative_k5_v1.py' -v
```

The verifier reads the committed prior K⁴ certificate by **pinned
SHA-256**, reconstructs all 1,076 old K⁴ vertices as K³ maximal
cliques, checks connectedness, reproduces each link/nonmaximality
witness, and compares against the six recorded entries. Historical
results are not modified.
