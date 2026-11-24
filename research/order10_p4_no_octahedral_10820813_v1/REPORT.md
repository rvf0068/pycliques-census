# No octahedral retraction in the first five pared iterates of McKay 10820813

**Certified scope.** This is an exact finite proof that **each** of the
first five completely pared clique iterates, \(P_0,P_1,P_2,P_3,P_4\), of
the ten-vertex graph McKay **10820813**, graph6
``ICp`fpv~_``, admits **no ordinary graph retraction onto any induced
octahedron \(O_d=\overline{dK_2}\) with \(d\geq3\)**. This statement
does **not** determine whether the original graph is \(K\)-divergent,
convergent, or periodic, and it does not exclude retractions onto
nonoctahedral targets or from later iterates.

## 1. Exact host

Write \(P_0=P(G)\), and let \(P_{i+1}=P(K(P_i))\), where
\(P\) repeatedly removes vertices with their closed neighborhoods
contained in another vertex's closed neighborhood.

The archived original graph6 is pinned simultaneously to certified
ten-v24 and the 206-case P4 pilot from merged PR #89.
The proof verifier independently reconstructs every iterate, comparing
a sorted bitset Bron--Kerbosch maximal-clique list with the NetworkX
maximal-clique list *at each stage*, then applying complete integer-bitset
paring.

| Host | Vertices | Edges |
|---|---:|---:|
| \(P_0\) | 10 | 25 |
| \(P_1\) | 17 | 83 |
| \(P_2\) | 26 | 189 |
| \(P_3\) | 43 | 625 |
| Raw \(K(P_3)\) | 223 | 18,159 |
| \(P_4\) | **70** | **1,830** |

The reconstructed canonical labeled P4 graph6 has SHA-256
`c26ee7c369318b01c0598b0ef7270b406c538bfd0ec34f5152c1ff649a3f3873`.
Its complement \(H=\overline{P_4}\) has 70 vertices and 585 edges.

## 2. The earlier pared iterates

The same **complete** induced-matching enumeration and sound
singleton-domain obstruction were also run on each earlier iterate.
The result is considerably stronger than the initial fourth-stage
claim:

| Stage | Edges in complement | Induced \(O_2\) | Induced \(O_3\) | Complement-dominating \(O_3\) | Refuted by propagation |
|---|---:|---:|---:|---:|---:|
| \(P_0\) | 20 | 15 | 0 | 0 | 0 |
| \(P_1\) | 53 | 115 | 0 | 0 | 0 |
| \(P_2\) | 136 | 360 | 3 | 0 | 0 |
| \(P_3\) | 278 | 5,907 | 4,392 | 4,224 | **4,224** |

None of \(P_0,P_1,P_2,P_3\) contains even an induced \(O_4\),
so this exhausts all dimensions \(d\geq3\) at those stages.
The 168 remaining induced \(O_3\) subgraphs of \(P_3\) fail
the necessary complement-domination condition. The proof verifier
reconstructs and screens **every** candidate, rather than trusting
these summary counts alone.

## 3. The exhaustive reduction and obstruction

**Lemma 1 (complement-induced matching).** For any finite simple graph \(X\), an induced \(O_d\)
on \(2d\) vertices of \(X\) is exactly an induced matching of
\(d\) edges of \(\overline{X}\). In particular, enumerating all induced matchings in the
complement of a stage finds every possible octahedral-retraction
target at that stage.

*Proof.* Each of the \(d\) antipodal pairs is a nonedge in
\(X\), hence an edge in \(\overline{X}\). All pairs of vertices from
different antipodal pairs are adjacent in \(X\), hence nonadjacent
in \(\overline{X}\). These are precisely the induced-matching conditions,
and conversely they imply the octahedral adjacency pattern. \(\square\)

**Lemma 2 (necessary domination).** If \(r:X\to O_d\)
is an ordinary graph retraction onto such an induced target \(T\),
then \(T\) dominates \(\overline{X}\).

*Proof.* Every target vertex is in its own closed neighborhood in
\(\overline{X}\). For any \(x\notin T\), suppose \(r(x)=a_i\) and denote
its antipode by \(b_i\). Because \(r(b_i)=b_i\), the source edge
\(xb_i\) would map to the nonedge \(a_ib_i\), violating even
the weak graph-morphism convention allowing an edge to collapse.
Thus \(xb_i\) is **not** an edge of \(X\), meaning
\(xb_i\) is an edge of \(\overline{X}\). \(\square\)

**Lemma 3 (sound singleton-domain obstruction).** For any finite simple
host graph \(X\), write \(H=\overline{X}\) and fix an induced
octahedron \(T\) in \(X\) with ordered antipodal pairs
\((a_i,b_i)\). Every retraction fixing \(T\) must map each
outside vertex \(x\) into

\[
D_x=\{a_i:xb_i\in E(H)\}\cup
    \{b_i:xa_i\in E(H)\},
\]

while \(D_t=\{t\}\) for target vertices. Whenever \(xy\)
is an edge of \(X\), if \(D_x=\{a_i\}\), deleting
\(b_i\) from \(D_y\) preserves every possible retraction.
The analogous rule applies to every antipodal endpoint. If repeated
deletions empty any domain, no such retraction exists.

*Proof.* The domain restrictions follow from the fixed antipodal
target vertices as in Lemma 2. The only nonedges between vertices
of \(O_d\) are its antipodal pairs; equal images are permitted.
Consequently, if the edge \(xy\) is mapped by a retraction with
\(r(x)=a_i\), one necessarily has \(r(y)\ne b_i\).
Iterating sound deletions cannot remove any value used by a valid
retraction. An empty domain contradicts its existence. \(\square\)

### Exhaustive enumeration

The independent Python and C++20 verifiers enumerate every induced
matching in \(H\), prune targets failing the **necessary**
domination condition, then apply Lemma 3 until a contradiction or
a nonempty fixed point.

| Target | Induced copies | Dominate \(H\) | Direct forced conflict | Further propagation conflict | Unrefuted |
|---|---:|---:|---:|---:|---:|
| \(O_3\) | 387,428 | 22 | 22 | 0 | **0** |
| \(O_4\) | 472,762 | 205,024 | 166,199 | 38,825 | **0** |
| \(O_5\) | 14,304 | 144 | 140 | 4 | **0** |
| \(O_6\) | 491 | 0 | 0 | 0 | **0** |
| \(O_7\) | 2 | 0 | 0 | 0 | **0** |
| \(O_8\) | 0 | 0 | 0 | 0 | **0** |

As additional enumeration consistency checks, the complement contains
exactly 585 induced \(O_1\) and 41,878 induced \(O_2\).
Every matching is generated once, in strict lexicographic order of
its component edges. At every stage the enumeration intersects
the set of remaining compatible higher-indexed edges. No sampling,
time boxing, or probabilistic isomorphism test is involved.

**Theorem.** For \(G\) equal to McKay 10820813, none of
\(P_i(G)\), \(0\leq i\leq4\), admits an ordinary graph
retraction onto an induced \(O_d\), \(d\geq3\).

*Proof.* Lemmas 1--3 apply verbatim to the complement of **each**
pared iterate. The earlier-stage table exhausts \(P_0\)--\(P_3\):
there is no induced \(O_3\) in the first two stages; the three
induced \(O_3\) in \(P_2\) fail complement domination; and
all 4,224 dominating \(O_3\) subgraphs of \(P_3\) are rejected
by sound singleton propagation. None of these earlier stages has
an induced \(O_4\), excluding all larger dimensions there.

For \(P_4\), Lemma 1 exhausts all possible induced octahedral targets,
and Lemma 2 eliminates all targets that fail to dominate \(H\).
For every remaining target of dimensions 3, 4, or 5, the full
singleton propagation of Lemma 3 encounters an empty domain; the
independent verifiers agree on the count of direct and iterated
contradictions. No target of dimensions 6 or 7 dominates \(H\).
There is no induced \(O_8\), hence there can be no induced
\(O_d\) for \(d\geq8\), since any eight antipodal pairs of
such a target would induce an \(O_8\). \(\square\)

## 4. Independent certification and reproduction

The [proof certificate](certificates.json) records immutable census and
P4 pilot Git blobs, exact sizes and matching counts for **all five**
pared stages, labeled P4 SHA-256, and all finite target screens. The [Python verifier](verify.py) reconstructs the host
from the original graph6 using independently checked maximal-clique
lists, enumerates induced matchings of its complement using integer
bitsets, and performs complete singleton propagation. The
[independent C++20 verifier](verify_independent.cpp) uses a separate
implementation of induced-match enumeration and propagation from
a sorted complement edge list, itself exported only from the
SHA-pinned reconstructed P4 graph. It does not call the Python
enumerator or propagation code.

From the census repository root with NetworkX 3.6.1:

```sh
python -m unittest research.order10_p4_no_octahedral_10820813_v1.test_verify -v
python -m research.order10_p4_no_octahedral_10820813_v1.verify \
  --export-complement /tmp/mckay10820813_p4_complement.txt

g++ -O2 -std=c++20 -Wall -Wextra \
  research/order10_p4_no_octahedral_10820813_v1/verify_independent.cpp \
  -o /tmp/mckay10820813_cpp_verify
/tmp/mckay10820813_cpp_verify < /tmp/mckay10820813_p4_complement.txt
```

Both verifiers must independently obtain the exact rows above and
return a nonzero exit code if any unrefuted target survives. Positive
and mutation regression tests ensure the propagation rule does not
incorrectly claim that \(O_3\) cannot retract onto itself.

**Limit.** This proof rules out *the ordinary octahedral-retraction method*
in all five pared stages through the fourth. In particular, it cannot justify
removing McKay 10820813 from the indeterminate census. Future work
should consider retractions at \(P_5\) or beyond, different divergent
targets, and more general coaffine morphisms.
