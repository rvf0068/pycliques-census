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
