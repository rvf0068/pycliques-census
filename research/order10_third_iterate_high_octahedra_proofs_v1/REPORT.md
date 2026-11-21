# Positive raw third-iterate octahedral retractions: stiff ten-vertex cores

This versioned archive contains **complete ordinary graph retractions**
\[
K^3(G)\longrightarrow O_d,\qquad d\ge 4,
\]
for previously unclassified stiff connected ten-vertex graphs. Every
original McKay index is checked against the frozen v9 population.

## Six independently discovered positive cores

| Original McKay index | graph6 | Target | \(|K^3(G)|\) | \(|E(K^3(G))|\) |
|---:|---|---|---:|---:|
| 5502890 | `I?bFjy|}o` | \(O_5\) | 60 | 1,361 |
| 6555024 | `I?o~Dxz~_` | \(O_5\) | 60 | 1,361 |
| 6946005 | `I?qbUY}|o` | \(O_4\) | 53 | 964 |
| 6954458 | `I?qbUxv~_` | \(O_4\) | 53 | 982 |
| 6954725 | `I?qbUy}xo` | \(O_4\) | 53 | 962 |
| 6954734 | `I?qbUy}|o` | \(O_4\) | 53 | 973 |

The precise opposite pairs and complete source-to-target projections
are stored in [certificates.json](certificates.json). In particular,
the verifier checks all source edges, allowing adjacent vertices to
map to adjacent **or equal** vertices, and fixes each induced target
pointwise. The target has exactly the prescribed \(d\) nonedges.

Since \(K(O_d)\cong O_{2^{d-1}}\), every \(O_d\) with \(d\ge3\)
is \(K\)-divergent. Neumann-Lara's Retraction Theorem therefore proves
the \(K\)-divergence of each displayed graph \(G\).
No conclusion comes from a failed bounded search or from computing
homology.

## Reproduction

```bash
python -m pip install networkx==3.6.1
python research/order10_third_iterate_high_octahedra_proofs_v1/verify.py --self-test
```

The verifier authenticates the exact Git blob of v9, checks each
ten-vertex source's fully unclassified status, and rebuilds every
raw clique iterate using two independent maximal-clique methods:
NetworkX and a separate bitset Bron--Kerbosch implementation.
It independently checks the complete target and projection edge
constraints, plus adversarially modified certificates.

**Scope:** This positive-proof archive does not change the frozen
v9 census or mark any other source as divergent. Further verified
positive proofs, if found in the systematic v9 search, may be added
before the archive is merged. Later, a separate versioned index change
can remove exactly the independently proved indices from the working
indeterminate list.
