# Exhaustive octahedral-retraction exclusions for six surviving ten-vertex flag spheres

## Scope and status

The authoritative ten-v17 census, merged in PR #70 and unchanged by PR #71, includes six original ten-vertex flag triangulations of the sphere. We write \(P_0(G)\) for the completely dominated-vertex-pared graph and \(P_{j+1}(G)\) for the completely pared clique graph of \(P_j(G)\).

**Exact, finite negative theorem.** For each of the six graphs listed below, \(P_3(G)\) admits **no ordinary graph retraction** onto an induced \(O_d=\overline{dK_2}\) with \(d\geq3\). In addition, **McKay 10803453** admits no such retraction from \(P_4(G)\).

These exclusions concern only this particular retraction mechanism and these particular iterates. They do **not** prove clique convergence, K-nullity, or any other final clique behavior. The authoritative unresolved counts remain **9** (order nine) and **2,025** (order ten). No historical census files, indices, or earlier certificates are modified.

## All six third-iterate exclusions

| Original connected-ten McKay | Original graph6 | \(\lvert P_3\rvert\) | \(E(P_3)\) | Induced \(O_d\), \(d\geq3\) | Complement-dominating targets | Max \(d\) | Retractions |
|---:|---|---:|---:|---:|---:|---:|---:|
| 6499365 | `I?ovUqv\o` | 48 | 720 | 2,524 | 1,552 | 4 | 0 |
| 8559181 | `ICQbQrvno` | 37 | 447 | 1,367 | 1,290 | 4 | 0 |
| 10803453 | ``ICp`epv~_`` | 24 | 198 | 368 | 362 | 3 | 0 |
| 11031156 | `ICpderm\o` | 60 | 1,089 | 2,140 | 848 | 4 | 0 |
| 11138607 | `ICperXumW` | 56 | 957 | 1,603 | 628 | 4 | 0 |
| 11548392 | `IEherhmmO` | 72 | 1,548 | 2,482 | 120 | 4 | 0 |
| **Total** | | | | **10,484** | **4,800** | | **0** |

The saved positive certificates for the other three originally unresolved ten-vertex flag spheres remain separate and untouched: McKay 9804321 (P4 -> O5), 10185592 (P4 -> O6), and 10472553 (P4 -> O4). This audit does not repeat those completed proofs.

For the six residual spheres, NetworkX independently rebuilds every iterate and verifies its identity against **frozen** \(v17\), not the mutable current-root file. For \(P_3\), it builds the compatibility graph on nonedges, enumerates *all* maximal compatible families, and all their subsets of at least three nonedges, with deduplication. Each such subset is an induced octahedron. Only those satisfying the necessary complement-domination condition reach the independent fixed-target retraction CSP. No CSP reaches its state budget or returns a retraction. The exact small-graph matching counts were also independently reproduced through recursive induced-matching enumeration in the research exploration.

## A stronger fourth-iterate negative theorem: McKay 10803453

For the sphere with original McKay index **10803453**, \(P_4\) has **60 vertices and 1,339 edges**. Its complement has **431 edges**. Exhaustive vertex-domination-guided enumeration gives:

| Induced octahedron dimension | Complement-dominating targets |
|---:|---:|
| \(d=3\) | 2,129 |
| \(d=4\) | 75,480 |
| \(d\geq5\) | 0 |
| **Total** | **77,609** |

All **77,609** fixed-target retraction CSPs reject at their *first* state via singleton constraint propagation, without branching. Consequently **no** \(P_4(G_{10803453})\to O_d\) retraction exists for \(d\geq3\).

### Why the fourth-iterate enumeration is complete

Let \(X=P_4(G_{10803453})\) and \(H=\overline X\).

1. An induced octahedron \(O_d\subseteq X\) is **exactly** an induced matching of \(d\) edges in \(H\): the antipodal nonedges become matching edges, and all cross-edges must be absent in \(H\).

2. If a retraction \(r:X\to O_d\) exists, the endpoints of that induced matching **dominate the vertices of \(H\)**. Otherwise an outside vertex \(v\) has no \(H\)-neighbor among the target vertices, i.e., \(v\) is adjacent in \(X\) to every target vertex. Any image \(r(v)=t\) would then have to be adjacent or equal to its antipode \(\tau(t)\), a contradiction.

3. For any partial induced matching \(M\), let \(D(M)\) be the union of open \(H\)-neighborhoods of its endpoints. Every selected endpoint itself belongs to \(D(M)\) via its mate. If \(D(M)\ne V(H)\), choose an uncovered vertex \(v\). **Every** dominating extension must add an induced-matching edge \(ab\) (compatible with \(M\)) with \(v\in N_H(a)\cup N_H(b)\). The verifier tries **every** such edge, then recursively applies the same rule. If none is available it prunes a branch that provably has no dominating extension. It deduplicates complete targets by their exact set of complement edges. This covers every possible complement-dominating induced octahedron of every dimension, not just maximal randomly found ones.

4. For each complete target, the exact retraction solver fixes all target vertices, initially permits image \(t\) for an external \(v\) only if \(v\) is not adjacent in \(X\) to \(\tau(t)\), and enforces the forbidden antipodal images across every source edge. Unit propagation alone rejects each target. A discovered retraction or an incomplete search would **fail the audit** instead of being silently treated as negative.

In particular, merely finding induced \(O_6\) subgraphs in this graph is not enough for divergence: the complete target search shows no larger **complement-dominating** octahedron, and the smaller eligible targets do not retract.

## Reproduction and integrity

From the repository root, with NetworkX 3.6.1:

```bash
python research/order10_sphere_octahedral_exhaustive_v1/verify.py --self-test --fourth
python research/order10_sphere_octahedral_exhaustive_v1/verify.py --case 10803453
```

With the pinned public `pycliques` library installed:

```bash
PYTHONHASHSEED=0 python research/order10_sphere_octahedral_exhaustive_v1/verify.py --public --fourth
```

The standalone script does not import the implementation of clique graphs, dominated-vertex paring or retractions from `pycliques`; it reconstructs them independently with NetworkX. The optional public mode compares each intermediate graph through the explicit maximal-clique correspondence (without a pathological generic VF2 graph-isomorphism test). The fourth raw and pared iterates are also checked. The 250-example brute-force \(O_3\) extension self-test from the earlier proof methodology is replayed. Optimized Python (`python -O`) is rejected because assertions are proof-critical.

### Further research

McKay 10803453 remains mathematically unresolved; other kinds of retractions, clockwork/cover criteria, and \(P_5\) remain possible. The blind fourth-iterate search for McKay 8559181 was **resource-limited**, not exhaustive. The other five fourth iterates are not certified negative by this report. The nine surviving nine-vertex cores remain high priority because each certified divergence would resolve an entire family of ten-vertex originals.
