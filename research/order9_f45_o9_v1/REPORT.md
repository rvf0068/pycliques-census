# A complete O9 retraction proving the divergence of F_(4,5)

**Status:** An exact, independently replayable ordinary graph retraction
of the fourth completely pared clique iterate of the nine-vertex graph
\(F_{4,5}\) onto \(O_9=\overline{9K_2}\). The original is **McKay 208409**
(graph6 `HCZTf\}`), one of the 12 unresolved graphs in the frozen v4
order-nine census. This is a positive theorem; no convergence claim rests
on a failed bounded search.

## The finite certificate

Define \(P_0(G)=P(G)\), \(P_{j+1}(G)=P(K(P_j(G)))\), where \(P\)
deletes dominated vertices sequentially to a fixed point. The graph
\(P_4(F_{4,5})\) has **202 vertices** and **16,289 edges**.

In the independent labeling defined by `verify.py`, the following
nine nonedges are the antipodal pairs of an **induced \(O_9\)**:

```text
(1,78)    (29,92)   (40,88)
(50,122)  (61,64)   (67,121)
(79,188)  (138,169) (143,196)
```

The saved [certificate.json](certificate.json) gives an explicit
projection \(r(v)\) for all **202** host vertices (the `images_b64`
field is exactly 202 unsigned bytes, encoded in base64). The independent
verifier checks that the antipodal pairs are disjoint nonedges, that
every possible cross-pair edge is present, that \(r\) has image exactly
those 18 vertices, that \(r\) fixes all target vertices, and that for
each of the **16,289 edges** \(uv\) of the host, either \(r(u)=r(v)\)
or \(r(u)r(v)\) is an edge.

This is precisely an ordinary graph retraction with the usual weak
graph-morphism convention in clique-graph theory.

## Mathematical consequence

For \(d\ge3\), the cliques of \(O_d\) are the \(2^d\) transversals
choosing one endpoint from each nonedge. Disjoint transversals occur
in exactly complementary pairs. Thus \(K(O_d)\cong O_{2^{d-1}}\), so
\(O_9\) has unbounded clique-iterate orders and is \(K\)-divergent.
By Neumann-Lara's retraction theorem, \(P_4(F_{4,5})\) is divergent.
By the dismantling-preservation theorem of Frías-Armenta,
Neumann-Lara and Pizaña (*Dismantlings and iterated clique graphs*,
Discrete Mathematics **282** (2004), 263–265), the original graph
\(F_{4,5}\) is \(K\)-divergent.

**Therefore McKay 208409 is proved \(K\)-divergent.**

## Discovery: a coaffine endomorphism, not an assumed target

Instead of first choosing an \(O_d\), search for a graph
endomorphism \(\phi:X\to X\) mapping each vertex outside its own
closed neighborhood. The ordinary graph-morphism CSP allows
adjacent vertices to map to adjacent *or equal* vertices. Its
domains are \(D(v)=V(X)\setminus N_X[v]\), with arc consistency and
minimum-remaining-values branching; all candidate solutions are
checked against every host edge.

For \(X=P_4(F_{4,5})\), the search found a nonbijective coaffine
endomorphism with **19 distinct image vertices**. Its square
\(r=\phi^2\) is idempotent, has 18 image vertices, and fixes those
18 vertices pointwise. They induce \(O_9\). The nine transpositions
of \(\phi\) on those vertices are the antipodal pairs listed above.
The final certificate uses \(r\) directly and does **not** trust
the discovery solver.

The searches at P0–P3 found no such coaffine endomorphism.
An exact separate finite check also exhausts all induced \(O_3\)
and \(O_4\) at P3 and shows neither is a retraction target.
Neither negative observation establishes convergence.

## Independent reproduction with public pycliques

The verifier first constructs F_(4,5) by its two-path definition,
independently enumerates maximal cliques using NetworkX, and
removes dominated vertices in a deterministic order. It checks
the SHA-256 of the complete 202-vertex graph6 encoding.

It then **reconstructs the entire fourth pared iterate using
public `pycliques.completely_pared_graph` and
`pycliques.clique_graph`**, transports the saved projection
through an **exact** graph isomorphism (with every pair checked),
and invokes
`pycliques.verify_induced_octahedron` and
`pycliques.verify_retraction_witness`.

Pinned environment for CI: NetworkX 3.6.1 and
`pycliques-project` commit
`782deb653b8748e1b5759389cdd2134beac69351`.

```bash
python research/order9_f45_o9_v1/verify.py
```

**No previous census file is changed by this proof-only branch.**
The new proof provides a separate path to promote the nine-vertex
case and the **120** ten-vertex rows whose historical classification
depends on `HCZTf\}`. Those 120 dependencies must be individually
replayed before changing the authoritative ten-vertex index; the
positive F45 proof alone does not certify arbitrary old census rows.
