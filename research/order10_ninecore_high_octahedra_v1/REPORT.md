# Two new nine-core divergence proofs by raw third-iterate octahedral retractions

**Status:** Complete, positive, independently replayable certificates for two
nonisomorphic stiff nine-vertex cores in the frozen v9 unresolved census.
No existing census verdict is modified by this proof archive.

## The retractions

For each nine-vertex graph \(G\) below, there is a complete ordinary
graph retraction \(K^3(G)\to O_d\), with \(O_d=\overline{dK_2}\).
The projection is specified at **every** vertex of the raw third
clique graph, with integer-mask canonical labeling at each iterate.

| Representative original ten-vertex McKay index | Nine-core graph6 | \(|V(K^3(G))|\) | \(|E(K^3(G))|\) | Retract | Represented originals |
|---:|---|---:|---:|---|---:|
| 5418647 | `HCrlvhz` | 60 | 1,361 | \(O_5\) | 116 |
| 6974529 | `HEh~dzm` | 56 | 1,201 | \(O_6\) | 235 |
| **Total** | | | | | **351** |

The raw \((|V|,|E|)\) sequences are

- `HCrlvhz`: \((9,22),(15,71),(21,150),(60,1361)\).
- `HEh~dzm`: \((9,23),(13,54),(20,137),(56,1201)\).

The induced \(O_5\)'s missing edges are
\[
(0,50),\ (2,29),\ (6,32),\ (10,42),\ (13,44).
\]
The induced \(O_6\)'s missing edges are
\[
(0,53),\ (4,43),\ (7,35),\ (12,38),\ (21,40),\ (24,41).
\]
The complete 60- and 56-coordinate projections are archived in
[certificates.json](certificates.json). The verifier checks that they
fix their respective induced targets and that **all** 1,361 and 1,201
source edges map to edges or equal image vertices.

## Why this proves divergence

A maximal clique of \(O_d=\overline{dK_2}\) chooses one vertex from each
complementary pair; two choices are disjoint precisely when all \(d\)
coordinates differ. Consequently \(K(O_d)\cong O_{2^{d-1}}\).
The graphs \(O_5\) and \(O_6\) are therefore \(K\)-divergent, and
Neumann-Lara's Retraction Theorem implies both original cores are
\(K\)-divergent.

## The 351 exact isomorphism lifts

The frozen [nine-core class index](../../reports/order10_core_index_v1/classes.tsv)
contains 116 and 235 originally unresolved ten-vertex members of the
two stiff-core isomorphism classes. The verifier authenticates both
this index and the v9 list by their exact Git blob hashes.
For *every* one of the 351 original indices, it verifies the archived
class membership, the fully unclassified v9 row with pared order nine
and three `- - -` fields, and an **independent exact graph isomorphism**
between its stored pared graph6 and the certified nine-core representative.

Behavior-preserving dominated-vertex paring, already recorded by the
historical census, now lifts these two positive proofs to all 351
original ten-vertex graphs.

**Hence a separate, versioned update may reduce the unresolved
population from 7,920 to 7,569, removing only the 351 certified
positive cases.** No conditional classification is promoted.

## Independent reproduction

From the census repository root:

```bash
python -m pip install networkx==3.6.1
python research/order10_ninecore_high_octahedra_v1/verify.py --self-test
```

The verifier recomputes \(G,K(G),K^2(G),K^3(G)\) with two independent
maximal-clique enumerators (NetworkX and bitset Bron--Kerbosch),
independently reconstructs the induced octahedral targets and total maps,
tests deliberate certificate mutations, and checks all 351 isomorphisms.
It does not import any pycliques search engine or infer homotopy from
Betti numbers.

## Scope

These positives were discovered by induced-matching enumeration in
complements and full graph-retraction CSP checks. The \(O_3,O_4\)
searches and the 132-vertex exceptional third iterate include
resource-limited cases; their negative or incomplete outcomes are
not evidence of convergence. Only the positive maps and their
351 independently verified lifts are asserted.

Earlier octahedral divergence proofs and the Retraction Theorem are
discussed in the repository's
[prior O4 certificate archive](../order10_four_o4_lift_v1/summary.md).
