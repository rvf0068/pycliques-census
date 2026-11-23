# Certified obstruction to small divergent retractions at the third pared iterate

## Research status

This is a **new exact negative theorem about specified retraction classes**,
not a classification of any original graph as K-convergent or K-divergent.

For the three remaining connected nine-vertex McKay originals from the
**immutable nine-v9 census**, put \(X_i=P_3(G_i)\), the third completely
pared clique iterate.

| Original McKay | Original graph6 | \(|V(X_i)|\) | \(|E(X_i)|\) |
|---:|---|---:|---:|
| **249576** | `HEhfvzu` | 53 | 1,044 |
| **251628** | `HEhvVn{` | 55 | 1,156 |
| **260040** | `HQyvex}` | 58 | 1,289 |

**Theorem.** For each of the three graphs \(X=P_3(G)\), there is
**no ordinary retraction** onto any induced \(T\subseteq X\) with

\[
  |V(T)|\le9,\qquad \Delta(T)\le |V(T)|-3.
\]

The cases of order eight and nine are established by the two
complete enumerations below. The cases \(|V(T)|\le7\) are already
excluded by their independently certified fact that there are
**no external double covers of size at most seven**.
In particular, none retracts onto an induced snub
disphenoid, whose graph6 is `GQyuzw` and whose degree sequence
is \(4,4,4,4,5,5,5,5\).

This is stronger than screening only finitely many *selected*
snub embeddings. It excludes **all** targets in both stated classes.

## General local-degree obstruction

For any finite graph \(X\), let \(H=\overline X\). A vertex subset
\(S\subseteq V(X)\) is an *external \(r\)-cover* if

\[
  |N_H(x)\cap S|\ge r\quad\text{for every }x\notin S.
\]

Here \(N_H(x)\) denotes the **open** neighborhood, and the
vertices chosen in \(S\) are exempt from this requirement.

**Lemma.** If \(T\subseteq X\) is induced, \(|V(T)|=t\), and there is
an ordinary retraction \(r:X\to T\), then \(V(T)\) is an external
\((t-\Delta(T)-1)\)-cover of \(\overline X\).

**Proof.** For any \(x\notin T\), let \(v=r(x)\in V(T)\). Every
\(u\in N_X(x)\cap V(T)\) satisfies \(r(u)=u\), since a retraction
fixes the target pointwise. Because weak graph morphisms send
edges either to edges or to equal vertices, \(u\in N_T[v]\).
Consequently
\[
 |N_X(x)\cap V(T)|\le |N_T[v]|
       \le \Delta(T)+1.
\]
The remaining \(t-\Delta(T)-1\) or more vertices of \(T\)
are nonneighbors of \(x\) in \(X\), hence neighbors in
\(H=\overline X\). \(\square\)

For \(t=8,\Delta(T)\le5\), **an external 2-cover of size 8 is
necessary**, regardless of the isomorphism type of \(T\).

## Complete integer enumeration

Let \(z_v\in\{0,1\}\) indicate whether \(v\in S\). The external
2-cover condition is exactly

\[
  2z_x+\sum_{v\in N_H(x)}z_v\ge2
       \quad\text{for every }x\in V(H).
\]

Together with \(\sum_v z_v=8\), these are pure **integer**
finite constraints. The independently implemented branch-and-bound
solvers enumerate every solution of those constraints, rather
than trusting an LP or mixed-integer solver's numerical status.

| McKay | \(\gamma^{\mathrm{ext}}_2(\overline {P_3(G)})\) | All 8-element external 2-covers |
|---:|---:|---|
| **249576** | **9** | **None** |
| **251628** | **8** | **Exactly one**: \(\{2,8,25,27,31,38,43,54\}\) |
| **260040** | **8** | **Exactly one**: \(\{0,6,31,37,43,46,52,55\}\) |

The vertices in the sets above use the exact independently
normalized \(P_3\) labels documented by the SHA-256 graph digests
in the verifier. An explicit size-nine external 2-cover for
McKay 249576 is
\(\{1,14,16,22,35,42,45,47,48\}\).
The complete absence of a size-eight cover and this explicit
size-nine cover establish the minimum **exactly nine**.

### Why the search exhausts all possibilities

The Python search stores selected vertices \(S\) and excluded
vertices \(E\). At each search state it applies two sound
forced-selection rules:

1. If a vertex \(x\) is excluded but needs \(q\) more neighbors
   in \(H\), and exactly \(q\) of its neighbors remain undecided,
   all those neighbors must be selected. If fewer remain, the
   branch is impossible.
2. If \(x\) is undecided and too few undecided \(H\)-neighbors
   remain to meet its requirement without selecting \(x\),
   then \(x\) must be selected.

For pruning, let \(U\) be the currently deficient row set and
\(d_x\in\{1,2\}\) its remaining deficits. An undecided vertex
\(v\) can contribute at most

\[
  g(v)=|N_H(v)\cap U|
       +\mathbf1_{v\in U}
       +\mathbf1_{v\in U,\ d_v=2}
\]

units toward those deficits: at most one to each neighboring
row, and at most two to its own row. If the sum of the
largest \(b\) values \(g(v)\), where \(b\) is the remaining
vertex-selection budget, falls below \(\sum_{x\in U}d_x\),
**no completion is possible**. This bound overcounts
possible simultaneous gains, so its pruning is rigorously safe.

Otherwise, a fresh undecided variable is branched as
*selected* or *excluded*. The recursion exhausts the whole
binary search tree, with no resource-dependent negative
status. A separately completed at-most-seven search ensures
that enumeration at size eight cannot omit smaller solutions.
Every reported solution is checked against the original
integer constraints.

The independent Python implementation also tests its exact
enumerator against **direct combination enumeration on random
small graphs**. A separately authored C++17 integer solver,
built independently, reproduces the complete counts
**0, 1, 1** and finds **no qualifying snub-degree-pattern
target**. A time limit in this optional C++ replay always
raises an error and cannot be mistaken for an exhaustive
negative result.

## The unique candidates are ruled out by homology

For McKay 251628 and 260040 the sole eight-element external
2-cover induces a **5-regular** graph on eight vertices.
Its complement has exactly two connected components, each
a four-cycle. Thus both unique targets are isomorphic to

\[
  T=\overline{C_4\sqcup C_4}
    =\overline {C_4}*\overline {C_4},
\]

where the last operation is graph join. Since
\(\overline {C_4}\cong 2K_2\), its clique complex is
homotopy equivalent to \(S^0\). The clique complex of the
join is the simplicial join, so

\[
  \Delta(T)\simeq S^0*S^0\simeq S^1.
\]

In particular \(H_1(\Delta(T);\mathbb F_2)\ne0\).
This has been separately checked using exact triangle-boundary
elimination.

For each entire \(P_3\) host, the same independent chain-level
algorithm gives **zero** \(H_1\) over \(\mathbb F_2\):

| McKay | P3 edges | Vertices | Number of triangles | Exact rank of \(\partial_2\) over \(\mathbb F_2\) | \(\beta_1\) |
|---:|---:|---:|---:|---:|---:|
| 249576 | 1,044 | 53 | 10,453 | 992 | **0** |
| 251628 | 1,156 | 55 | 12,507 | 1,102 | **0** |
| 260040 | 1,289 | 58 | 14,776 | 1,232 | **0** |

For a connected graph's flag complex, the exact formula is

\[
  \beta_1 = |E|-|V|+1
            -\operatorname{rank}_{\mathbb F_2}(\partial_2).
\]

Any retraction of clique complexes would yield maps
\(i_*:H_1(T)\to H_1(X)\) and \(r_*:H_1(X)\to H_1(T)\)
with \(r_*i_*=\mathrm{id}\); hence \(i_*\) would be
injective. But \(H_1(X)=0\) and \(H_1(T)\ne0\),
a contradiction.

Together, the integer enumeration and homology calculation
**exclude every eight-vertex induced target of maximum degree
at most five**, not merely copies of the snub.

## Reproducible, original-input-only verification

The proof requires only graph6 strings from the **immutable
nine-v9 census** (blob
`d18a7a843be935f3a7fe911691dd1c86dac2addd`).
The verifier first independently reconstructs the successive
completely pared clique graphs, checks exact stage sizes and
edges, and checks exact normalized labeled \(P_3\) edge hashes.
No stored \(P_3\), saved target, previous witness map,
integer-programming result or randomized target search is used
to determine the result.

Run from the census repository root with Python 3.12 and
NetworkX 3.6.1:

```sh
python -m research.order9_p3_eight_vertex_obstruction_v1.verify
```

With a C++17 compiler:

```sh
python -m research.order9_p3_eight_vertex_obstruction_v1.replay_cpp
```

Optionally replay every intermediate stage against the pinned
public pycliques implementation:

```sh
python -m research.order9_p3_eight_vertex_obstruction_v1.verify --public
```

Optimized Python is explicitly rejected because the verifier
uses proof-critical assertions. The optional C++ implementation
returns a nonzero code for any timeout or malformed input.

## Extension: exclude all nine-vertex low-degree retracts

The general lemma applies just as well to a target of order
\(t=9\) with maximum degree \(\Delta(T)\le6\). Its target
vertex set must again be an external **2-cover** in the
complement of the host.

The separately implemented
[exact-size-nine proof](verify_nine.py)
enumerates **every** nine-element external 2-cover, even when
smaller external covers also exist. This is important:
McKay 251628 and 260040 have eight-element covers, so it
would be unsound to rely on a size-nine-only *minimum*
cover enumerator.

| McKay | All size-nine external 2-covers | Candidates inducing \(\Delta(T)\le6\) | Candidates passing target-neighborhood necessity |
|---:|---:|---:|---:|
| **249576** | **30** | **0** | **0** |
| **251628** | **297** | **109** | **0** |
| **260040** | **343** | **122** | **0** |

**Second exact obstruction.** If \(r:X\to T\) is a retraction
fixing every target vertex and \(x\notin T\), then its image
\(v=r(x)\in T\) must satisfy

\[
  N_X(x)\cap V(T)\subseteq N_T[v].
\]

This is necessary because every edge \(xu\) with \(u\in T\)
must map to the edge \(vu\), or collapse to \(v=u\).
The [nine-target verifier](verify_nine.py) checks *every*
possible \(v\in T\) for *every* outside vertex \(x\)
against this exact condition.

For McKay 249576, not one of the thirty qualifying
nine-element external covers induces a graph with
maximum degree at most six. For McKay 251628 and
260040, **all 109 and all 122** degree-eligible
nine-element covers fail the displayed necessary
target-neighborhood containment at some outside vertex.
Thus none can be the image of a retraction.

The nine-target enumeration uses only integral bitmasks.
Its forced-selection steps and rigorous deficit-gain
pruning bound are the same sound mathematical principles
as in the eight-target proof. Unlike the eight-target
enumerator, if all external covering constraints are
already satisfied with fewer than nine selected vertices,
it explicitly enumerates **every possible completion**
to exactly nine vertices among the remaining undecided
vertices. Consequently, smaller covers never cause
nine-element targets to be missed.

As a separate independent verification of this additional
enumeration code, its exact-k results were checked
against direct brute-force enumeration on **276 random
small graph/budget instances**, including cases with
smaller existing covers. No sampling is used in the
actual McKay proof.

The 109 and 122 degree-eligible candidates have only
three induced isomorphism types in each host; the
exclusion uses the stronger universal vertex-domain
criterion for every actual embedding, not just these
three representatives. This result does not depend on
their homology, on convergence conjectures, or on any
retraction timeout.

To reproduce the extra theorem:

```sh
python -m research.order9_p3_eight_vertex_obstruction_v1.verify_nine
```

Together, both independently checkable finite theorems,
and the exact exclusion of all external double covers with
fewer than eight vertices, prove the advertised uniform
**small-retract obstruction for all orders \(t\le9\)
with \(\Delta(T)\le t-3\)**. For \(t\le2\), that degree
condition is vacuous for nonempty simple graphs.

## Classification implications and limitations

This is **not** a proof of K-convergence or K-divergence for any
of the three unresolved originals. It eliminates the full
class of third-iterate ordinary retractions onto eight- or nine-vertex
graphs whose maximum degree is at most their order minus three, including the
already-proved K-divergent snub disphenoid.

The remaining research should focus on either larger induced
divergent retracts at \(P_3\), or certified octahedral
retractions at \(P_4\) or later, without confusing incomplete
searches with exclusion theorems. This PR is deliberately
**proof-only**: neither nine-v9 nor ten-v20 is modified.
