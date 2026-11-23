# Exact ten-vertex low-degree retraction obstruction at the third pared iterate

## Statement

Let \(G_i\) be one of the **three currently indeterminate original
nine-vertex McKay graphs** in the immutable nine-v9 census, and put
\(X_i=P_3(G_i)\), the third completely pared clique iterate. Let
\(O_d=\overline{dK_2}\) as elsewhere in this project.

**New theorem.** No \(X_i\) retracts onto any induced ten-vertex
graph \(T\) satisfying \(\Delta(T)\le7\). Combined with the already
merged [PR #82](https://github.com/rvf0068/pycliques-census/pull/82),
we obtain the uniform theorem

\[
\boxed{\text{If }\ |V(T)|\le10
\text{ and }\Delta(T)\le |V(T)|-3,
\text{ then }T\text{ is not an ordinary retract of }X_i.}
\]

This is a theorem about *a specific class of retracts from \(P_3\)*.
It neither classifies the K-behavior of the original graphs nor
rules out divergent retracts of larger order or different degree.

| Original McKay | graph6 | \(P_3\) order | \(P_3\) edges |
|---:|---|---:|---:|
| 249576 | `HEhfvzu` | 53 | 1,044 |
| 251628 | `HEhvVn{` | 55 | 1,156 |
| 260040 | `HQyvex}` | 58 | 1,289 |

The three source graph6 strings and the **exact normalized \(P_3\)
edge SHA-256 digests** are checked by the already certified
[PR #82 reconstruction verifier](../order9_p3_eight_vertex_obstruction_v1/verify.py).

## Two exact necessary conditions for an ordinary retraction

Let \(X\) be a simple graph, \(H=\overline X\), and let
\(S\subseteq V(X)\) induce the proposed retraction target \(T=X[S]\).
Write \(t=|S|\).

**Lemma 1 (open double domination).** If \(X\) retracts onto \(T\)
and \(\Delta(T)\le t-3\), then

\[
 \tag{1}
 |N_H(x)\cap S|\ge2
 \quad\text{for every }x\in V(X),
\]

**including every chosen target vertex**.

**Proof.** For \(x\in S\), the degree bound gives at least
\((t-1)-(t-3)=2\) nonneighbors in \(S\).
For \(x\notin S\), fix the retraction \(r\) and set \(y=r(x)\in S\).
Every \(u\in N_X(x)\cap S\) must belong to \(N_T[y]\) because
\(r(u)=u\) and graph morphisms preserve adjacency or collapse edges.
Since \(|N_T[y]|\le\Delta(T)+1\le t-2\), at least two target
vertices are nonneighbors of \(x\), proving (1). \(\square\)

Condition (1) is **stronger** than the external double-cover condition
used in PR #82 because it also includes vertices of \(S\).
It is not an ad hoc assumption on the target.

**Lemma 2 (necessary fixed-target images).** Under the same
hypotheses, for every outside vertex \(x\notin S\) there is
some \(y\in S\) such that

\[
 \tag{2}
 N_H(y)\cap S\ \subseteq\ N_H(x)\cap S.
\]

**Proof.** Necessarily \(y=r(x)\). For each \(u\in S\),
if \(xu\in E(X)\) then \(yu\in E(X)\), or \(u=y\).
Contraposing, if \(u\in N_H(y)\cap S\), then \(xu\notin E(X)\),
and therefore \(u\in N_H(x)\cap S\). \(\square\)

The unary target-image condition (2) is **necessary but not
sufficient** for a retraction: it checks compatibility with
the fixed target, not between all pairs of outside vertices.
Consequently, finding no set satisfying (1) and (2) proves
a retraction impossible, whereas finding one does not prove
a retraction exists.

## Complete finite result

Two independently implemented integer enumerators exhaust all
cardinality-10 subsets satisfying (1), then independently test
(2) on **every** candidate. Their results agree exactly.

| McKay | Open 2-dominating subsets \(S\), \(|S|=10\) | Satisfying both necessary conditions (1) and (2) |
|---:|---:|---:|
| **249576** | **2,161** | **0** |
| **251628** | **12,822** | **0** |
| **260040** | **17,620** | **0** |
| **Total** | **32,603** | **0** |

Hence there is **no ordinary retraction** from any of the three
third pared iterates onto a ten-vertex induced graph with maximum
degree at most seven. This uses no homology assumptions and
requires no negative conclusion from a time-limited solver.

## Completeness and independent verification

Condition (1) is the integer 0-1 system

\[
 \sum_{v\in N_H(x)}z_v\ge2
 \quad(x\in V(X)),\qquad
 \sum_{v\in V(X)}z_v=10,\qquad
 z_v\in\{0,1\}.
\]

Unlike the external double-cover constraints, **selected vertices
do not exempt their own rows**. This matters for the degree bound.
The two proof programs use exact integer bitmasks and no floating-point
optimizations:

- The [Python verifier](verify.py) branches on an undecided vertex
  from the most restrictive currently deficient row. It performs
  forced selections when the available neighbor count equals the
  remaining deficit.
- The [C++17 verifier](enumerate.cpp) branches on a highest-global-gain
  vertex, independent of the Python branch rule. Its orchestration
  is in [replay_cpp.py](replay_cpp.py).
- Both use a rigorously safe optimistic bound. If the remaining
  deficient rows have total deficit \(D\), and an undecided
  vertex \(v\) can cover at most
  \(g(v)=|N_H(v)\cap U|\) currently deficient rows \(U\),
  then the sum of the greatest \(b\) gains, where \(b\) is the
  number of remaining selection slots, upper bounds the
  remaining total coverable deficit. A branch is impossible
  only if this **upper bound is smaller than \(D\)**.
- If all constraints are satisfied **before ten vertices have
  been selected**, the solvers explicitly enumerate all
  exact-size completions among the not-yet-excluded variables.
  This is essential for McKay 251628 and 260040, where smaller
  open double covers are known to exist.
- Each accepted ten-element set is rechecked row-by-row against
  (1). Every set is then tested against (2) for every outside
  vertex and every proposed image \(y\in S\).
- The Python enumerator is independently compared to direct
  brute-force combination enumeration on random small graphs,
  including situations where a smaller cover exists. A separate
  sample check compares its bitset unary condition to ordinary
  NetworkX closed-neighborhood containment.

Both search trees visit both outcomes of every unforced binary
choice. There is no time limit in the Python proof. The optional
C++ program has a safety timeout, but any such timeout exits with
a nonzero status and is explicitly **INCONCLUSIVE** rather than
interpreted as an absence proof. The CI accepts only a complete
`EXHAUSTIVE` result containing the expected counts.

The full P3 source is recomputed from the immutable original graph6
strings and its exact digest checked, rather than trusting a stored
edgelist. The positive conclusion is independently established from
the integer counts **32,603** and the exact absence of any unary
survivor.

## Reproduction

From the census repository root:

```sh
python -m pip install networkx==3.6.1
python -m research.order9_p3_ten_vertex_obstruction_v1.verify
```

With a C++17 compiler installed:

```sh
python -m research.order9_p3_ten_vertex_obstruction_v1.replay_cpp
```

Optional independent public-pycliques check of all P0-P3 stages
before the new Python proof:

```sh
python -m research.order9_p3_ten_vertex_obstruction_v1.verify --public
```

The verifier rejects optimized Python (`python -O`) to prevent
bypassing its proof-critical assertions.

## Next research priorities

An exploratory order-eleven open-double-domination search reached
resource limits after discovering numerous eligible subsets; that
result is **inconclusive** and is not included in the theorem.
The next possible improvements are better exact covering bounds
or stronger target-neighborhood filtering integrated into subset
construction, not simply more random octahedral embeddings.

The authoritative nine-v9 and ten-v20 indeterminate lists remain
unchanged by this proof-only contribution: **3** and **1,311**
original graphs, respectively.
