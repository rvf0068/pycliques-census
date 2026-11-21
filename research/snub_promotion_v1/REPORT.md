# Certified snub divergence promotion: nine v3 and ten v11

As of 21 November 2026, the independent certificate in
[pycliques-project](https://github.com/rvf0068/pycliques-project/blob/main/docs/snub_o24_retraction.md)
establishes a graph retraction `K^4(S) -> O_24` for the snub disphenoid
`S` (graph6 `GQyuzw`), giving **proved K-divergence of S** by the
retraction theorem.

This versioned audit removes **exactly** the cases whose earlier
`conjectured_divergent` certificate names `snub_disphenoid` and whose
original **graph6 structure** independently supports the indicated
inference. Other cases are unchanged byte-for-byte:

| Source | Previously indeterminate | Snub-dependent positives | Now indeterminate |
| --- | ---: | ---: | ---: |
| Order 9 v2 -> v3 | 49 | 36 | 13 |
| Order 10 v10 -> v11 | 7,219 | 4,389 | 2,830 |

Order nine: 25 direct snub references, nine retractions, one triangle-free
edge removal, one admissible inverse-cutpoint extension.

Order ten: 2,092 direct references, 2,018 retractions, 227 triangle-free
edge removals, and 52 inverse-cutpoint extensions.

The **120** ten-vertex cases depending on the different unresolved
`HCZTf\\}` graph and the **2,710** otherwise-indeterminate cases remain
in v11. The 13 order-nine v3 cases are all otherwise indeterminate.

## Independent replay

Run from the census root with NetworkX installed:

```sh
python research/snub_promotion_v1/verify.py
python -m unittest discover -s research/snub_promotion_v1 -p test_verify.py -v
```

`verify.py` checks pinned Git blob hashes of v2/v10, exact indexed
deletions, unchanged retained rows, and a finite positive-proof chain for
**every removed row**. Its implementation uses NetworkX alone; it does
not call the `pycliques` classifier, use cached retraction projections,
or infer negatives from failed searches.

The proof checker searches induced eight-vertex snub targets exhaustively
within each saved pared graph, checks every edge under the fixed-target
projection, and certifies any closed-neighborhood fold or intervening
triangle-free edge removal and local-bridge inverse-cutpoint construction.
In particular, ten-vertex index **7453299** needs a nested chain:
delete a triangle-free edge, fold a dominated vertex, apply an admissible
inverse-cutpoint extension, then fold to the snub. Each step is verified.

The previous versioned proof verifiers are **immutable**. The
`replay_historical.py` harness makes them see their frozen versioned
root snapshot during replay without changing any repository file.
It does not replace the current-index checks in `verify.py`.

The results of nonlocal octahedron searches on the remaining thirteen
nine-vertex cores are handled separately in
[`order9_nonlocal_oct_sweep_v1/`](../order9_nonlocal_oct_sweep_v1/README.md).
Only a new independently replayed positive witness can justify any later
census removal.
