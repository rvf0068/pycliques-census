# Four nine-vertex representatives: two new O₄ divergence proofs

The nine-vertex graphs with graph6 strings
`HQqvUx}`, `HEhutzm`, and `HEht}rl`
are isomorphic. Together, they are the pared references for **13**
previously unclassified original ten-vertex graphs. The nine-vertex
graph `HEnfbzm` is nonisomorphic to this class and provides
six further original ten-vertex cases.

## Two unconditional K-divergence certificates

The standalone verifier
`scripts/order10_four_o4_lift_v1.py` reconstructs the
clique iterates using a deterministic maximal-clique ordering and
replays each closed-neighborhood dominated-vertex deletion. Denote
the completely pared graph at stage \(j\) by \(P_j\).

| Nine-vertex reference | \(\lvert P_0\rvert\) | \(\lvert P_1\rvert\) | \(\lvert P_2\rvert\) | \(\lvert P_3\rvert\) |
|---|---:|---:|---:|---:|
| `HQqvUx}` | 9 | 13 | 19 | **41** |
| `HEnfbzm` | 9 | 16 | 23 | **70** |

The complete explicit maps in the verifier retract each \(P_3\)
onto eight fixed vertices inducing \(O_4=\overline{4K_2}\).

For the first core, the eight target vertices are
\(\{0,1,10,11,31,36,37,39\}\).
For the second, they are
\(\{0,2,13,22,39,41,49,51\}\).

Both maps are verified against **every source edge**, checking that
images are adjacent or equal. The fold traces are replayed separately,
and the three representatives of the first isomorphism class are
compared by a fresh graph-isomorphism check.

Because completely paring preserves K-behavior, and the ordinary
Retraction Theorem lifts K-divergence from a retract to its host,
both nine-vertex classes are K-divergent. Indeed,
\(K(O_4)\cong O_8\), and successive octahedral clique graphs grow
without bound.

## New original ten-vertex classifications

| Pared reference graph6 | Original order-10 McKay indices | Number |
|---|---|---:|
| `HQqvUx}` | 9943619, 9943624, 9944398, 9964496, 11548395, 11548997 | 6 |
| `HEhutzm` | 6945593, 6945998, 11589592, 11589624 | 4 |
| `HEht}rl` | 6938971, 6938987, 11597205 | 3 |
| `HEnfbzm` | 10547079, 11300525, 11300543, 11652131, 11652585, 11652613 | 6 |
| **Total** | | **19** |

Historical original-to-pared provenance is preserved in the earlier
census stages; this lift independently authenticates the exact frozen
v7 records and supplies the previously missing target K-divergence proofs.

The new authoritative root is byte-for-byte
`indeterminate_order_10_v8.txt`:
**8,105 unresolved**, compared with 8,124 in v7.
The **4,509 conditional** cases have not changed. The two examples
from the previous investigation, `HCZTf\}` and the
snub disphenoid, remain unresolved; the 19 new proofs concern
previously unconditional-indeterminate cases.

## Reproduction

With NetworkX 3.6.1, from repository root:

```bash
python scripts/order10_four_o4_lift_v1.py verify
python scripts/order10_four_o4_lift_v1.py certificates --output /tmp/four-o4-proofs.json
python -m unittest discover -s tests -p test_order10_four_o4_lift_v1.py -v
python -m unittest discover -s tests -p test_current_root_index.py -v
```

The tests deliberately corrupt an edge-retraction map, a
dominated-vertex fold, and an octahedral target, requiring each to
be rejected. The dedicated GitHub Actions job independently checks
all results and protects frozen historical stages and versions.

A bounded negative candidate search was **not** used to promote any
case to a convergence or non-divergence claim.
