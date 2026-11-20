# Raw \(K^3\) of McKay graph 242316 retracts directly onto \(O_5\)

**Graph:** `HCrlvhz`, connected nine-vertex McKay index **242316**.

**New exact result:**

\[
\boxed{K^3(G)\ \longrightarrow\ O_5=\overline{5K_2}
\quad\text{is a graph retraction.}}
\]

This is an **unconditional proof of K-divergence**, by the Retraction
Theorem and \(K(O_d)\cong O_{2^{d-1}}\) for \(d\geq3\).

## Explicit, unpared certificate

No dominated-vertex reduction is necessary. The raw clique-graph
orders and edge counts are:

| Iterate | Vertices | Edges |
|---|---:|---:|
| \(G\) | 9 | 22 |
| \(K(G)\) | 15 | 71 |
| \(K^2(G)\) | 21 | 150 |
| \(K^3(G)\) | **60** | **1,361** |

Label maximal cliques at each stage in increasing order of their
vertex-set bitmask, and construct the clique graph by nonempty
intersections.

In \(K^3(G)\), the ten vertices

\[
T=\{0,2,6,10,13,29,32,42,44,50\}
\]

induce \(O_5\); the exact five complementary matching edges are

\[
\{0,50\},\ \{2,29\},\ \{6,32\},\ \{10,42\},\ \{13,44\}.
\]

The retraction \(r:V(K^3(G))\to T\) is given by its images in source
vertex order \(0,1,\ldots,59\):

```text
0, 0, 2, 2, 0, 0, 6, 2, 2, 2,
10, 0, 0, 13, 0, 2, 42, 42, 0, 0,
10, 0, 0, 0, 10, 0, 10, 10, 10, 29,
32, 32, 32, 32, 32, 10, 29, 29, 2, 2,
2, 42, 42, 44, 44, 44, 44, 32, 32, 32,
50, 32, 32, 44, 44, 32, 44, 32, 44, 32
```

The standalone verifier checks that \(r(t)=t\) for all \(t\in T\);
that \(K^3(G)[T]=O_5\); and that, for **every one of the 1,361
source edges** \(uv\), either \(r(u)=r(v)\) or \(r(u)r(v)\) is a
target edge.

The tests perform a wholly separate raw clique-graph reconstruction
using bitset Bron--Kerbosch maximal-clique enumeration, with the
NetworkX clique generator disabled during the independent replay.
The tests also reject an altered fixed image, an invalid outside
image, and an altered target.

## Reproduction

From the \`pycliques-census\` root with NetworkX 3.6.1:

```bash
python scripts/core9_242316_o5_divergence_v1.py verify
python scripts/core9_242316_o5_divergence_v1.py certificates --output /tmp/242316-o5.json
python -m unittest discover -s tests -p test_core9_242316_o5_divergence_v1.py -v
```

The older frozen census reported this index as indeterminate
after bounded searches through the second iterate, which cannot
contradict this new third-iterate certificate. Historical stage files
are not changed in this proof-only pull request. Any future census
lift must authenticate original-to-pared provenance independently.
