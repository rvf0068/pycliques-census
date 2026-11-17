# Certified order-ten divergence via special-O4 core classes

This is a **positive-certificate extension**, not a fresh search of every
original ten-vertex graph. Every recorded source graph is verified
against the initial order-ten census and supplied with an explicit
dominated-vertex deletion transcript and a vertex bijection to a
certified nine-vertex core.

| Core ID | Core graph6 | Class members | Direct v5 | Lifted by dismantling |
|---:|---|---:|---:|---:|
| 6938923 | `HEht}pl` | 23 | 4 | 19 |
| 6939350 | `HEht~bl` | 110 | 21 | 89 |

**Total: 133 original indices, including 25 directly
positive v5 indices and 108 additional indices lifted
by the published dominated-vertex theorem.**

The 11 positive exact-graph6 records all have
independently replayed special-`O_4` witnesses at the third
completely pared clique iterate. Their graphs fall into the two
isomorphism classes listed above.

## Proof scope

For an original ten-vertex graph `X`, each recorded fold
deletes a vertex `v` whose closed neighborhood is contained in
that of an identified dominator `u`. The stored bijection
identifies the final stiff graph with the certified nine-vertex
representative `C`. The dismantling theorem of Frías-Armenta,
Neumann-Lara and Pizaña ensures `X` and `C` have identical
K-convergence/divergence behavior. The special octahedron in
`K^3(C)` proves `C` K-divergent, hence `X` K-divergent.

**The certificate does not assert that the unpared original
graph itself contains a special octahedron in its third iterate.**
The level-3 statement is about the completely pared core sequence.
The negative results for other cores do not imply convergence.

Reference: [M. E. Frias-Armenta, V. Neumann-Lara, M. A. Pizana, Dismantlings and iterated clique graphs, Discrete Mathematics 282 (2004)](https://www.sciencedirect.com/science/article/pii/S0012365X04000561).

## Reproduction

`members.tsv` contains all original graph6 encodings, explicit
dominated folds, their resulting graph6, and verified vertex maps
onto the class representative. `classes.tsv` identifies the
positive isomorphism classes. `manifest.json` freezes inputs,
algorithms, evidence and output hashes.

```bash
.venv-special-k3-v5/bin/python scripts/special_octahedron_class_lift_v1.py verify
```
