# Non-special retractions and homology restrictions for snub clique iterates

This report examines **all** graph retractions from the first four **raw**
clique iterates of the snub disphenoid \(S\) (graph6 `GQyuzw`) onto the
families of octahedra, graph suspensions of cycles, and complements of cycles.
It does not establish clique convergence or divergence.

The exact counts are saved in [results.json](results.json); the independent
reconstruction, mod-2 boundary reduction, induced-subgraph enumeration, and
retraction CSP are in `scripts/snub_retractions_homology_v1.py`.

## Mathematical filter

For a graph retraction \(r:X\to Y\), the induced simplicial map has a
simplicial section, so \(\Delta(Y)\) is a topological retract of
\(\Delta(X)\). Thus in each degree and for every coefficient field,

\[
\widetilde H_j(\Delta(Y);\mathbb F_2)
\hookrightarrow
\widetilde H_j(\Delta(X);\mathbb F_2).
\]

The standard target homotopy types are:

- \(\Delta(O_d)\cong S^{d-1}\), with \(O_d\) the complement of \(d\)
  disjoint edges.
- \(\Delta(\operatorname{Susp}(C_n))\cong S^2\) for \(n\ge4\).
- \(\Delta(C_n^c)\) is the independence complex of \(C_n\):
  \(S^{k-1}\vee S^{k-1}\) if \(n=3k\),
  \(S^{k-1}\) if \(n=3k+1\), and \(S^k\) if \(n=3k+2\)
  (for the relevant \(n\ge5\)). The verifier independently checks
  these mod-2 Betti groups for \(5\le n\le15\).

The computation gives

| Raw iterate | Vertices | Edges | Exact positive-degree mod-2 Betti information |
|---|---:|---:|---|
| \(S\) | 8 | 18 | \(\widetilde\beta_2=1\), all other degrees zero |
| \(K(S)\) | 12 | 46 | \(\widetilde\beta_2=1\), all other degrees zero |
| \(K^2(S)\) | 20 | 136 | \(\widetilde\beta_2=1\), all other degrees zero |
| \(K^3(S)\) | 56 | 1,196 | \(\widetilde\beta_1=\widetilde\beta_2=\widetilde\beta_3=0\); higher degrees uncomputed |

The first three Betti calculations enumerate **all** faces of their clique
complexes and reduce all boundary matrices over \(\mathbb F_2\).
For \(K^3(S)\), the exact low-dimensional computation enumerates
13,120 triangles, 85,368 tetrahedra, and 365,272 five-vertex cliques;
the ranks of boundaries in degrees 2, 3, and 4 are respectively
1,141, 11,979, and 73,389. These imply precisely the stated vanishing
through degree three. No claim is made about \(\widetilde H_j\) for \(j\ge4\),
integral torsion, or the full homotopy type of \(K^3(S)\).

## Complete retraction searches on S, K(S), K²(S)

Homology rules out \(O_d\) for \(d\ne3\), and all \(C_n^c\), \(n\ge5\),
except \(n=8,10\). The suspended-cycle targets remain admissible in
homology; those fitting the host are all explicitly checked.

| Host | Induced \(O_3\) copies | Induced \(\operatorname{Susp}(C_5)\) copies | Induced \(C_8^c\) copies | Induced \(C_{10}^c\) copies |
|---|---:|---:|---:|---:|
| \(S\) | 0 | 0 | 0 | — |
| \(K(S)\) | 0 | 8 | 0 | 0 |
| \(K^2(S)\) | 142 | 176 | 60 | 12 |

Numbers count **different induced vertex sets**, not copies distinguished
only by automorphisms of the target. Every one of the displayed copies
has been checked for a total graph retraction, and none admits one.
Suspensions of \(C_n\) for \(n\ge6\) (up to the number of available host
vertices) have no induced copies in the first three raw iterates.

Thus **none** of these three graphs retracts onto an octahedron \(O_d\)
with \(d\ge3\), a suspension of \(C_n\) for \(n\ge4\), or \(C_n^c\)
for \(n\ge5\).

## Complete structural search on K³\(S\)

Homology eliminates \(O_3,O_4\), all cycle suspensions, and all cycle
complements \(C_n^c\) whose mod-2 homology lies in degrees 1, 2, or 3.
The remaining targets are handled by complementary-graph patterns:

| Target class | Induced candidates | Verified graph retractions |
|---|---:|---:|
| \(O_5\) | 2,128 | 0 |
| \(O_6\) | 0 | 0 |
| \(C_{14}^c\) | 27,982 | 0 |
| \(C_{15}^c\) | 20 | 0 |
| \(C_n^c\), \(n\ge16\) | 0 | 0 |

An induced \(O_d\) is exactly an induced matching of size \(d\) in the
complement. The implementation enumerates all induced matchings of size
5 and proves there are none of size 6; therefore no \(O_d\), \(d\ge6\),
can occur as an induced subgraph.

An induced \(C_n^c\) is exactly a chordless cycle \(C_n\) in the complement.
The implementation enumerates **all** chordless cycles, without a length
cutoff. None has length 16 or greater. All 27,982 length-14 and
20 length-15 induced targets fail full retraction checking. No CSP
search hit its state budget; a budget hit would have caused a loud
failure, never `EXHAUSTED`.

Therefore **\(K^3(S)\) also has no graph retraction onto any member of
the three named families** (in the ranges above).

## Interpretation

A special octahedron is not required by these searches: every embedding
is tested for a **general graph retraction** (adjacent vertices may map
to adjacent or equal vertices). An induced subgraph without a valid
retraction gives no divergence theorem.

For the known clique-divergent targets among these families, such a
retraction in any iterate would prove the snub disphenoid clique-divergent.
The absence of these specific retractions, even exhaustively through
\(K^3(S)\), **does not prove the snub disphenoid convergent or
nondivergent**. It leaves \(K^4(S)\), other divergent retracts, and
non-retraction divergence mechanisms entirely open.

## Reproduce

From the `pycliques-census` root, using the existing pinned monorepo
environment:

```bash
bash scripts/bootstrap_core9cover_v2.sh
.venv-core9cover-v2/bin/python scripts/snub_retractions_homology_v1.py verify
.venv-core9cover-v2/bin/python -m unittest discover -s tests -p test_snub_retractions_homology_v1.py -v
```

The `verify` command recomputes all boundary ranks and all exhaustive
retractions and compares its entire deterministic JSON output with
`results.json`. The historical census statuses and all previous
experiments are left unchanged.
