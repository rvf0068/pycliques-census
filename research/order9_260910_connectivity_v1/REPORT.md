# A certified mod-2 homology obstruction for nine-vertex McKay index 260910

**Status:** mathematically certified finite certificate, not a clique-behavior classification.
**Graph:** `HUZvvzu` (McKay index 260910). **Target:** the third
*completely pared* clique iterate, denoted \(P_3\) below. The root
`indeterminate_order_9.txt` and all earlier research records are unchanged.

## Reconstruction

Let \(P_0=\operatorname{cp}(G)\) and \(P_{j+1}=\operatorname{cp}(K(P_j))\),
where \(\operatorname{cp}\) repeatedly deletes closed-neighborhood dominated
vertices and \(K\) is the maximal-clique intersection graph.

| \(j\) | vertices | edges | nonzero reduced mod-2 Betti numbers (only \(j\le2\)) |
| ---: | ---: | ---: | --- |
| 0 | 9 | 26 | \(\widetilde\beta_2=1\) |
| 1 | 12 | 52 | \(\widetilde\beta_2=1\) |
| 2 | 21 | 176 | \(\widetilde\beta_4=1\) |
| 3 | **132** | **7,880** | see the vanishing theorem below |

The complement of the input is two induced \(C_5\)'s meeting in one
vertex, so \(\Delta(G)=\operatorname{Ind}(\overline G)\simeq S^2\).
The other two listed Betti results follow from exact GF(2) boundary
reductions, not from an unproved identification of homotopy type.
The verifier independently enumerates every maximal clique using bitset
Bron--Kerbosch, compares with NetworkX at each early iterate, and checks
the four exact graph order/size pairs.

## The 14-vertex weighted certificate

Put \(C=\overline{P_3}\), and use the labels produced by the deterministic
maximal-clique and paring routine in `verify.py`.
Define a weighted set \(A=A_3\sqcup A_1\) by

\[
 A_3=\{0,27,42,87,91,108\},\qquad
 A_1=\{24,38,45,47,51,66,68,69\},
 \qquad w|_{A_3}=3,\ w|_{A_1}=1.
\]

**Explicit finite checks:** \(A\) is independent in \(C\), and
\[
 \sum_{a\in A}w(a)=26,\qquad
 \max_{x\in V(C)}\sum_{a\in N_C(x)\cap A}w(a)=3.
\]
Every open dominating set \(D\) of \(A\) therefore satisfies
\[
 26=\sum_{a\in A}w(a)
 \le \sum_{x\in D}\sum_{a\in N_C(x)\cap A}w(a)
 \le3|D|,
\]
so \(|D|\ge9\). For an ordinary graph, a strongly independent set
is simply an independent vertex set. Consequently
\(\gamma_{\mathrm{si}}(C)\ge\gamma_0(C;A)\ge9\).

**Homology theorem.** By the known independence-complex domination bound
\[
 \eta(\operatorname{Ind}(C))\ge\gamma_{\mathrm{si}}(C)
\]
(Jinha Kim and Minki Kim, *Noncover complexes, Independence complexes,
and domination numbers of hypergraphs*, Séminaire Lotharingien de
Combinatoire 84B (2020), Theorem 2.1,
https://www.mat.univie.ac.at/~slc/wpapers/FPSAC2020/68-Kim.pdf),
the complex \(\operatorname{Ind}(C)=\Delta(P_3)\) satisfies
\[
 \boxed{\widetilde H_i(\Delta(P_3);\mathbb F_2)=0
        \quad\text{for all }0\le i\le7.}
\]
The cited version of the theorem uses **mod-2 homological**
connectivity. This report deliberately does not claim integral homology
vanishing or an exact homotopy type.

## Exact negative retraction consequences

A graph retraction \(P_3\to T\) makes \(\widetilde H_*(\Delta(T);\mathbb F_2)\)
a direct summand of \(\widetilde H_*(\Delta(P_3);\mathbb F_2)\).
Thus no graph with nonzero mod-2 homology in degrees 0 through 7
can be a graph retract of \(P_3\).

For \(T_n=K(C_n^c)\), exact GF(2) componentwise boundary calculations
(the clique complex of a join is a join of clique complexes) yield:

| \(n\) | vertices of \(T_n\) | nonzero mod-2 homology of \(\Delta(T_n)\) | retract of \(P_3\)? |
| ---: | ---: | --- | --- |
| 8 | 10 | \(\widetilde\beta_2=1\) | **No** |
| 9 | 12 | \(\widetilde\beta_3=4\) | **No** |
| 10 | 17 | \(\widetilde\beta_3=1\) | **No** |
| 11 | 22 | \(\widetilde\beta_5=1\) | **No** |
| 12 | 29 | \(\widetilde\beta_7=12\) | **No** |
| 13 | 39 | \(\widetilde\beta_7=1\) | **No** |
| 14 | 51 | not used here | not settled |
| 15 | 68 | not used here | not settled |
| 16 | 90 | not used here | not settled |
| 17 | 119 | edge-count obstruction | **No** |

For \(n=17\), the complement \(C\) has 766 edges. Any induced
119-vertex subgraph is obtained by omitting 13 vertices. The sum of the
13 largest degrees in \(C\) is 238, hence the remaining induced
subgraph has **at least 528 edges**. But
\(\overline{K(C_{17}^c)}\) has just **323 edges**, so it cannot be induced
in \(C\). For \(n\ge18\), the Perrin-count
\(|V(K(C_n^c))|\ge158>132\) rules out embeddings.

Additionally, every octahedron \(O_d=\overline{dK_2}\) for
\(3\le d\le8\) is excluded as a retract, since
\(\Delta(O_d)\simeq S^{d-1}\) and \(d-1\le7\).
Earlier independently verified results in PR #23 give
\(\widetilde H_2(\Delta(K(\operatorname{Susp}(C_n)));\mathbb F_2)\ne0\)
for every \(n\ge5\), excluding all those clique-suspension targets too.

**Remaining targets:** among \(\{K(C_n^c):n\ge8\}\), only \(n=14,15,16\)
remain possible as ordinary retraction targets at \(P_3\).
Octahedra of dimension \(d\ge9\), more general divergent targets and
later iterates have **not** been excluded. Consequently the K-behavior
of McKay index 260910 remains **indeterminate**.

## Replay

Python 3.13 (or compatible), NetworkX 3.6.1:

```bash
python -m pip install networkx==3.6.1
python research/order9_260910_connectivity_v1/verify.py --self-test
```

This is a standalone proof replay using exact integer weighted-neighborhood
checks and GF(2) boundary reductions for the *small target components*.
No external optimization solver, original per-embedding search artifacts,
or enormous \(P_3\) boundary matrix is required. The verifier also
checks corruption of the weighting and of the reconstructed graph.

This is a versioned, **nonmutating** research addition, not an update to
the historical or current census classifications.
