# Exhaustive special-octahedron exclusion at P3 for all six nine-v7 cores

## Precise theorem and limitations

Let \(P_0(G)\) denote the completely dominated-vertex-pared graph and
\(P_{j+1}(G)\) the completely pared clique graph of \(P_j(G)\).
Let \(O_d=\overline{dK_2}\).

**Theorem (finite exhaustive certificate).** None of the third pared
clique iterates \(P_3(G)\) of the six original McKay graphs in the
certified `indeterminate_order_9_v7.txt` list contains a **special
octahedron** of dimension \(d\geq3\).

Here a special octahedron is an induced \(O_d\) whose one transversal
\(C\) (one vertex from every antipodal pair) is a **maximal clique of the
host**. This is exactly the definition checked by public
`pycliques.find_special_octahedron_witness`.

| Original connected-nine McKay | graph6 | \(|P_3|\) | Edges | Host maximal cliques examined | Maximal cliques with nonempty antipode domain for every vertex | Witnesses |
|---:|---|---:|---:|---:|---:|---:|
| 249576 | HEhfvzu | 53 | 1,044 | 783 | 0 | 0 |
| 251628 | HEhvVn{ | 55 | 1,156 | 1,034 | 4 | 0 |
| 251759 | HEhvtzm | 43 | 701 | 416 | 4 | 0 |
| 251902 | HEhvvzm | 41 | 641 | 492 | 5 | 0 |
| 254369 | HEjfvx} | 40 | 626 | 402 | 23 | 0 |
| 260040 | HQyvex} | 58 | 1,289 | 1,245 | 2 | 0 |
| **Total** | | | | **4,372** | **38** | **0** |

The standalone, pure-NetworkX verifier independently reconstructs all
three pared clique iterates from each original graph6 string. It
verifies the original McKay indices and every source row against the
immutable v7 snapshot (Git blob
`6f1e05d6b6bb0f1b4f2638ad73a7163f26ab0345`), and checks the
exact iterated orders, sizes and maximal-clique counts.

## Why the search is exhaustive

For a special induced \(O_d\), its distinguished side \(C\) must be
one of the graph's inclusion-maximal complete subgraphs. The verifier
enumerates **all** such \(C\) via `networkx.find_cliques`.

For each \(v\in C\), any antipode \(a_v\) must lie outside \(C\),
be **nonadjacent** to \(v\), and be adjacent to **every** other vertex
of \(C\). Those requirements determine a finite, exact candidate
domain \(D_v\). If any \(D_v\) is empty, no special octahedron can
extend that \(C\), and the entire candidate is correctly excluded.

When all domains are nonempty, a depth-first search tries **every**
selection \(a_v\in D_v\), retaining only selections for which chosen
antipodes form a clique. Domain membership ensures that the only
missing cross-edges are the designated antipodal pairs, that all
endpoints are distinct, and that the selected \(2d\) vertices induce
\(O_d\). No search bound, random trial, timeout interpreted as
negative, or stored preselected target is used.

The verifier checks positive examples \(O_3\) and \(O_4\), and
rejects a graph obtained by joining \(O_3\) with a universal apex:
although that graph has an induced octahedron, its octahedron is
**not special** because every maximal host clique includes the apex.
The optional `--public` mode independently runs the existing
`pycliques.find_special_octahedron_witness` exact procedure on all six
constructed third iterates and requires no witness.

## Second theorem: no P3 retraction onto the snub disphenoid

Let \(S\) be the snub disphenoid graph with graph6 `GQyuzw`.
Its K-divergence was established previously by the independently
certified \(P_4(S)\to O_{24}\) retraction. A different exact
obstruction now applies to all six current nine-vertex cores.

**Theorem (finite exhaustive certificate).** None of their
\(P_3(G)\) graphs admits an ordinary graph retraction onto an induced
copy of \(S\).

| Original McKay | Distinct induced snub targets | Complete injective induced embeddings | Locally obstructed targets |
|---:|---:|---:|---:|
| 249576 | 13,902 | 111,216 | 13,902 |
| 251628 | 26,406 | 211,248 | 26,406 |
| 251759 | 1,864 | 14,912 | 1,864 |
| 251902 | 300 | 2,400 | 300 |
| 254369 | 172 | 1,376 | 172 |
| 260040 | 42,503 | 340,024 | 42,503 |
| **Total** | **85,147** | **681,176** | **85,147** |

The complete enumerator in `snub.py` uses exact bitset adjacency
constraints to enumerate **every injective induced embedding** of
\(S\) into each 40–58-vertex \(P_3(G)\). Each of the eight snub
pattern vertices is assigned to a distinct host vertex, and every
edge **and nonedge** with previously assigned pattern vertices must
be preserved. Complete embeddings are deduplicated by their exact
8-vertex target set; all eight isomorphisms of \(S\) onto a given
induced target are enumerated. No randomness or search limits appear.

### Elementary retraction obstruction

Suppose \(r:X\to T\) is an ordinary retraction fixing an induced
target \(T\cong S\). For every vertex \(v\notin T\), and every
\(w\in N_X(v)\cap T\), edge preservation (allowing equal images)
requires \(r(v)\in N_T[w]\). Therefore

\[
r(v)\in \bigcap_{w\in N_X(v)\cap T}N_T[w].
\]

For **every** one of the 85,147 induced snub targets, the independent
verifier identifies at least one outside vertex \(v\) for which this
intersection is empty. That is already enough to rule out a retraction;
no global CSP solver or additional heuristic assumption is needed.
A target that passed this necessary condition would not have been
misreported as negative: the script counts such targets separately
and requires exactly zero.

The same counts were computed independently with a separate C++17
bitset enumerator. For the three smallest \(P_3\) hosts (McKay
251759, 251902 and 254369), NetworkX VF2's complete induced
subgraph-isomorphism enumeration separately reproduces precisely
1,864, 300 and 172 distinct target vertex sets. This independent
NetworkX cross-check is included as an optional proof replay and is
exercised in CI.

Positive sanity checks use the snub graph itself, where its identity
is a retraction and the obstruction **must not** fire, and the cone
over the snub, where the original snub remains an induced target but
the outside universal apex has no possible image in \(S\).

## Mathematical scope

PR #71 already excluded ordinary graph retractions from \(P_3(G)\)
onto any induced octahedron \(O_d\), \(d\geq3\), for these same nine-core
sources. The present theorem is a **different** exclusion: absence
of special octahedra is not the same condition as absence of ordinary
retractions. Neither result proves convergence, K-nullity, or
non-divergence, and neither excludes divergence certificates at
\(P_4\) or later.

The six nine-v7 originals and their **800** ten-v18 pared-nine
dependents remain indeterminate; all **881** ten-v18 stiff-core
originals also remain unchanged. This proof-only PR does **not**
modify any index or promote any graph.

The earlier [PR #73](https://github.com/rvf0068/pycliques-census/pull/73)
found new ordinary \(P_4\) octahedral retractions through diversified
coaffine vertex orderings, so continued divergence searches should
focus especially on \(P_4\), using both the native coaffine search and
matching-based target generation.

## Reproduction

From the repository root with Python 3.12 and NetworkX 3.6.1:

```bash
python research/order9_v7_p3_special_negative_v1/verify.py
```

With the pinned public `pycliques` library installed:

```bash
python research/order9_v7_p3_special_negative_v1/verify.py --public
```

Both paths reject optimized Python execution, which would bypass
proof-critical assertions. Dedicated CI validates the independent
enumeration and the public-pycliques cross-check. Frozen and mutable
census data are untouched.
