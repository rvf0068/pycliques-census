# Exact fractional-domination certificates for three surviving P4 cores

## Main theorem

For a finite simple graph \(X\), let \(H=\overline X\).
If \(X\) admits an ordinary graph retraction onto an induced subgraph
\(T\) **without a universal vertex**, then its target vertex set must
dominate \(H\). Hence

\[
|V(T)|\ \geq\ \gamma(H).
\]

For three remaining nine-v7 original McKay graphs, we have proved:

| Original McKay | graph6 | \(|P_4|\) | \(E(P_4)\) | Exact domination lower bound |
|---:|---|---:|---:|---:|
| 251759 | HEhvtzm | 403 | 70,679 | \(\gamma(\overline{P_4})\geq 9\) |
| 254369 | HEjfvx} | 394 | 67,229 | \(\gamma(\overline{P_4})\geq 9\) |
| 251902 | HEhvvzm | 461 | 94,642 | \(\gamma(\overline{P_4})\geq 10\) |

Therefore no \(P_4\) in this table retracts onto
\(O_3\), \(O_4\), the eight-vertex snub disphenoid, or
**any other induced target of at most eight vertices lacking a
universal vertex**. For McKay 251902, the same obstruction covers
targets of **up to nine vertices** lacking a universal vertex.

In particular, any ordinary octahedral retraction from one of
these three fourth iterates must have **dimension at least five**.
This does not exclude \(O_d\) for \(d\geq5\); it proves neither
convergence nor divergence.

## Elementary proof of the retraction-domination implication

If \(T\) does not dominate \(H\), there is a vertex \(v\notin T\)
with no \(H\)-neighbor in \(T\). Thus \(v\) is adjacent in \(X\)
to **every** target vertex. If \(r:X\to T\) were a retraction,
edge preservation (allowing adjacent vertices to be identified)
would require \(r(v)\in V(T)\) to be adjacent or equal to every
vertex of \(T\), because every \(t\in T\) is fixed by \(r\).
That would make \(r(v)\) universal in \(T\), a contradiction.

Consequently \(V(T)\) is a dominating set of \(H\), and
\(|T|\geq\gamma(H)\). Note the qualification that \(T\)
must have **no universal vertex**. We do not claim that the
bound applies to arbitrary retraction targets.

## Integer-only proof of the domination bounds

Assign a nonnegative integer weight \(w_v\) to each vertex
of \(H\), and set \(M=10,000\). The saved certificate proves

\[
\sum_{v\in N_H[u]}w_v \leq M
\quad\text{for every }u\in V(H).
\]

For any dominating set \(D\) in \(H\), summing these inequalities
for \(u\in D\) and noting that each vertex is covered at least
once gives

\[
\sum_{v\in V(H)} w_v
\leq\sum_{u\in D}\sum_{v\in N_H[u]}w_v
\leq M|D|.
\]

Thus every dominating set has
\(|D|\geq\lceil\sum_v w_v/M\rceil\).

The complete **fixed integer certificates** are stored in
`certificate.json`, with weights encoded as a little-endian
unsigned 16-bit array indexed by the sorted, normalized
fourth-iterate vertices. They have the following *exact*
integer invariants:

| Original McKay | Scale \(M\) | Sum \(\sum_vw_v\) | Maximum \(\sum_{v\in N_H[u]}w_v\) | Certified \(\gamma(H)\) bound |
|---:|---:|---:|---:|---:|
| 251759 | 10,000 | **80,129** | 9,997 | **9** |
| 254369 | 10,000 | **81,026** | 9,995 | **9** |
| 251902 | 10,000 | **99,341** | 9,995 | **10** |

All maxima are below \(M\). Neither the proof nor its
verification relies on LP tolerances, numerical optimization
status, branch-and-bound output, or unverified floating-point
arithmetic. Linear programming was used **only to discover**
dual-feasible weights; each coordinate was rounded down before
the exact arithmetic check.

In fact, if \(X=P_4(G)\) and \(H=\overline X\), the verifier
uses the identity

\[
N_H[u] = V(X)\setminus N_X(u).
\]

Therefore the integer load at each vertex is calculated exactly
as \(\sum_vw_v-\sum_{v\in N_X(u)}w_v\); the script checks
**every vertex** rather than sampling neighborhoods.

## Independent reconstruction and provenance

The proof starts from the original graph6 strings, and computes
all four completely pared clique iterates using only NetworkX.
The exact normalized fourth-iterate edge set is verified against
a SHA-256 digest saved in each certificate. It checks the
unchanged original nine-v7 McKay index/graph6 identity against
the frozen nine-v7 Git blob
`6f1e05d6b6bb0f1b4f2638ad73a7163f26ab0345`.

With optional `--public`, the standalone proof also checks
each raw clique-graph construction against the separately
implemented public `pycliques.clique_graph`, identifying each
clique directly by its original vertex set rather than running
an impractically expensive VF2 test on dense symmetric hosts.
It similarly compares each independently pared iterate with
the public dominated-vertex paring.

The exact numeric proof requires **only** NetworkX and the saved
integer arrays; SciPy and a compiler are **not** required.
CI runs independent reconstruction and public-pycliques
cross-checks against the pinned merged PR #36 revision.

## Reproduction

With Python 3.12 and NetworkX 3.6.1, from the repository root:

```bash
python research/order9_p4_domination_dual_v1/verify.py
```

With public pycliques installed:

```bash
python research/order9_p4_domination_dual_v1/verify.py --public
```

Both reject optimized Python (`python -O`) because assertions are
proof-critical.

## Scope for the remaining census

The authoritative nine-v7 and ten-v18 indeterminate counts remain
**6 and 1,681**. These are *negative* exclusions on only the
specified P4 target sizes. They do not classify the graph or rule out
later-iterate octahedral retractions.

The other three unresolved nine-v7 cores (249576, 251628, 260040)
did not yield fractional domination bounds above 8 in this initial
LP exploration. That is **inconclusive** about their integer
domination numbers and target retractions; it must not be read as
evidence that small targets exist.
