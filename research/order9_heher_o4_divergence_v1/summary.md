# An unconditional K-divergent nine-vertex spherical graph

## Theorem

Let \(G\) be the nine-vertex graph with McKay index **248687** and graph6
`HEher^{`. Its **third raw clique graph** \(K^3(G)\) has 60 vertices
and 1,225 edges. With maximal cliques ordered by their integer-bitmask
vertex sets at each iteration, the vertices

\[
T=\{0,5,11,21,45,47,49,53\}
\]

induce the octahedral graph \(O_4=\overline{4K_2}\).

The committed independent verifier
`scripts/core9_o4_divergence_v1.py` contains an **explicit complete
60-entry retraction map** \(r:K^3(G)\to O_4\). It checks the induced
\(O_4\) target, that \(r\) fixes each vertex of \(T\), and, for every one
of the 1,225 source edges \(xy\), that either \(r(x)=r(y)\) or
\(r(x)r(y)\) is an edge. Thus it is an ordinary graph retraction under
the accepted weak graph-morphism convention.

For \(d\geq3\), the maximal cliques of \(O_d\) correspond to binary
choices of one endpoint from each of its \(d\) nonedges. Two such
cliques are disjoint exactly if their choices are complementary.
Consequently \(K(O_d)\cong O_{2^{d-1}}\). In particular,
\(K(O_4)\cong O_8\), and successive clique iterations have unbounded
order. Thus \(O_4\) is K-divergent. By Neumann-Lara's Retraction
Theorem, \(K^3(G)\), and hence \(G\), is **K-divergent**.

This proof is unconditional, independent of conjectural divergence of
the snub disphenoid and independent of the separate exact
homotopy-equivalence work on the two nine-vertex sphere graphs.

## A complete negative O4 screen for the other sphere

For the nine-vertex graph `HCZTf\}` (order-nine McKay index
**208409**), raw \(K^3(G)\) has 56 vertices and 1,060 edges.

An induced \(O_4\) in a host \(X\) corresponds exactly to four
independent edges with no additional incidences in \(\overline X\),
i.e. an **induced matching of size four**. The script exhaustively
enumerates this finite family with no resource budget.

For each candidate, every outside vertex's possible retraction
images are restricted by its edges to the fixed target. If any domain
becomes empty, the target cannot be a retract. Otherwise, exact
arc-consistency propagation along every outside-host edge deletes
an image candidate only if no compatible image exists for the
neighbor. An empty domain at any stage also rigorously rules out
a retraction. Neither exclusion relies on exhaustive backtracking.

| Test result for K³(`HCZTf\}`) | Count |
|---|---:|
| All induced O4 targets | **359** |
| Failing initial local image domain | 101 |
| Rejected by sound arc consistency | 258 |
| Surviving target candidates | **0** |

Thus **no ordinary \(O_4\) retraction exists** at the third iterate of
this graph. This is a finite-family obstruction, not a
K-convergence or nondivergence result.

## Consequences for the order-10 census

The already certified historical order-10 v6 working index contains
**99** conjecturally divergent rows referring to `HEher^{`:

| Historical dependency | Cases |
|---|---:|
| Reference after complete paring | 63 |
| Ordinary retraction | 28 |
| Non-triangular-edge theorem | 6 |
| Inverse cutpoint extension | 2 |
| **Total** | **99** |

The new positive theorem supplies the missing proved-divergent
reference for those historical conditional arguments. These rows
can therefore be promoted only after their dependency certificates
are independently authenticated in a versioned lift. The present
retraction proof changes no historical stage records.

## Independent reproduction

With NetworkX 3.6.1 from repository root:

```bash
python scripts/core9_o4_divergence_v1.py
python -m unittest discover -s tests -p test_core9_o4_divergence_v1.py -v
```

The complete target vertices and retraction map are constants in the
script. No solver's verdict is trusted without recomputing all
1,225 edge constraints; no negative bounded search is promoted to
a positive verdict.

**References:** Neumann-Lara's clique-graph retraction theorem;
Frías-Armenta, Neumann-Lara and Pizaña, *Dismantlings and iterated
clique graphs*; Frías-Armenta et al., *Edge contraction and edge
removal on iterated clique graphs* (2013).
