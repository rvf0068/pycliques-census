# Early-iterate retraction obstructions for the remaining nine-sphere

The nine-vertex flag sphere `HCZTf\}` (original order-nine McKay index
208409) is still **K-behavior indeterminate**. Its raw clique graphs
have orders 9, 14, 23, 56, ... . This is a bounded exact screen of
certain targets in its **first two** clique iterates, not a statement
about eventual K-convergence or K-divergence.

## Exact induced targets and local obstructions

For a graph retraction \(r:X\to T\) fixing an induced target \(T\),
every outside vertex \(v\notin T\) must have a possible image
\(t\in T\) adjacent or equal to every vertex of \(N_X(v)\cap T\).
Equivalently the finite set

\[
D_v=\bigcap_{w\in N_X(v)\cap T}N_T[w]
\]

must be nonempty. Therefore an outside vertex with \(D_v=\varnothing\)
is an **unconditional obstruction** to a graph retraction.
We use graph morphisms that send edges to edges **or equality**.

The script enumerates all induced target vertex sets by NetworkX VF2,
deduplicates graph automorphism labelings, independently checks each
induced graph isomorphism, and produces the complete vertex set and
one obstructed outside vertex for each candidate. There are no state
limits or timeout deductions.

| Source | Target | Distinct induced copies | Locally obstructed |
|---|---|---:|---:|
| \(K(G)\) | snub `GQyuzw` | 2 | 2 |
| \(K(G)\) | divergent `HEher^{` | 0 | 0 |
| \(K^2(G)\) | divergent `HEht}pl` | 12 | 12 |
| \(K^2(G)\) | divergent `HQyuzpt` | 44 | 44 |
| \(K^2(G)\) | snub `GQyuzw` | 76 | 76 |
| \(K^2(G)\) | \(K(\text{snub})\) | 6 | 6 |
| \(K^2(G)\) | divergent `HEher^{` | 0 | 0 |
| \(K^2(G)\) | \(K(\texttt{HEher^{})\) | 0 | 0 |
| \(K^2(G)\) | \(K(\texttt{HEht}pl)\) | 0 | 0 |
| \(K^2(G)\) | \(K(\texttt{HQyuzpt})\) | 0 | 0 |
| **Total** | | **140** | **140** |

The snub is still only conjecturally divergent, whereas `HEher^{`,
`HEht}pl`, and `HQyuzpt` have separately certified divergence.
Neither the proven nor conjectural target families retract from these
specified iterates. A non-retraction from a small iterate **does not**
preclude a divergent retraction at a later iterate or onto another
target.

## Reproduce

From a census checkout with NetworkX 3.6.1:

```bash
python scripts/hcztf_retraction_screen_v1.py run > /tmp/hcztf-screen.json
python scripts/hcztf_retraction_screen_v1.py verify \
  --file /tmp/hcztf-screen.json
python -m unittest discover -s tests -p test_hcztf_retraction_screen_v1.py -v
```

The generated JSON records the induced vertices and obstructed vertex
for each of the 140 copies, and is checked against an independently
recomputed result. No census classification or historical result has
been changed.
