# Raw \(K^3\) of McKay graph 252075 retracts directly onto \(O_6\)

**Graph:** `HEh~dzm`, connected nine-vertex McKay index **252075**.

**New exact result:**

\[
\boxed{K^3(G)\ \longrightarrow\ O_6=\overline{6K_2}
\quad\text{is a graph retraction.}}
\]

This is an **unconditional proof of K-divergence**, by the Retraction
Theorem and \(K(O_d)\cong O_{2^{d-1}}\) for \(d\geq3\).

## Explicit, unpared certificate

No dominated-vertex reduction is necessary. The raw clique-graph
orders and edge counts are:

| Iterate | Vertices | Edges |
|---|---:|---:|
| \(G\) | 9 | 23 |
| \(K(G)\) | 13 | 54 |
| \(K^2(G)\) | 20 | 137 |
| \(K^3(G)\) | **56** | **1,201** |

Label maximal cliques at each stage in increasing order of their
vertex-set bitmask, and construct the clique graph by nonempty
intersections.

In \(K^3(G)\), the twelve vertices

\[
T=\{0,4,7,12,21,24,35,38,40,41,43,53\}
\]

induce \(O_6\); the exact six complementary matching edges are

\[
\{0,53\},\ \{4,43\},\ \{7,35\},\ \{12,38\},\ \{21,40\},\ \{24,41\}.
\]

The retraction \(r:V(K^3(G))\to T\) is given by its images in source
vertex order \(0,1,\ldots,55\):

```text
0, 0, 0, 0, 4, 4, 4, 7, 4, 4,
0, 0, 12, 0, 0, 0, 21, 7, 4, 7,
4, 21, 21, 21, 24, 4, 4, 4, 4, 40,
24, 24, 24, 35, 35, 35, 38, 41, 38, 38,
40, 41, 38, 43, 38, 38, 35, 35, 38, 40,
35, 35, 35, 53, 38, 38
```

The standalone verifier checks that \(r(t)=t\) for all \(t\in T\);
that \(K^3(G)[T]=O_6\); and that, for **every one of the 1,201
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
python scripts/core9_252075_o6_divergence_v1.py verify
python scripts/core9_252075_o6_divergence_v1.py certificates --output /tmp/252075-o6.json
python -m unittest discover -s tests -p test_core9_252075_o6_divergence_v1.py -v
```

The older frozen census reported this index as indeterminate
after bounded searches through the second iterate, which cannot
contradict this new third-iterate certificate. Historical stage files
are not changed in this proof-only pull request. Any future census
lift must authenticate original-to-pared provenance independently.
