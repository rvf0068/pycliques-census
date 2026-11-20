# Exact \(O_4\)-retraction certificates resolve 192 more ten-vertex cases

## Two nonisomorphic divergent nine-vertex graphs

The nine-vertex graphs with graph6 strings `HQqvUx}` and `HEnfbzm`
are **not isomorphic**, but each has a certified ordinary graph retraction
from its **completely pared third clique iterate** onto an induced
\(O_4=\overline{4K_2}\). Each certificate reconstructs the clique iterates,
replays every dominated-vertex fold, verifies the induced target, and
checks the complete map against every host edge (allowing equal images).

| Seed | Pared iterate orders \(P_0,P_1,P_2,P_3\) | \(P_3\) edges | Induced \(O_4\) target vertices |
|---|---|---:|---|
| `HQqvUx}` | 9, 13, 19, 41 | 607 | 0, 1, 10, 11, 31, 36, 37, 39 |
| `HEnfbzm` | 9, 16, 23, 70 | 1728 | 0, 2, 13, 22, 39, 41, 49, 51 |

By the Retraction Theorem and behavior-preserving dominated-vertex
paring, both are **unconditionally K-divergent**. The divergent target
is explicit: \(K(O_4)\cong O_8\) and successive octahedral iterates
have unbounded order.

## Isomorphism expansion, from 19 to 192

The first search found four nine-vertex graph6 strings:
`HQqvUx}` (six original cases), `HEhutzm` (four),
`HEht}rl` (three), and `HEnfbzm` (six).
The first three strings are **isomorphic**; thus even the original
19-case result required only two nonisomorphic proofs.

A broader exact audit of the frozen v7 working list found **147 distinct
nine-vertex graph6 strings**, all isomorphic to one of the two seeds.
These strings occur in **192 original ten-vertex records** previously
marked indeterminate without conditional reference.

The script `scripts/order10_four_o4_lift_v1.py` verifies each
isomorphism with NetworkX `is_isomorphic`, not merely a shared
degree sequence or triangle count. It authenticates the exact v7 Git blob
and checks the original indices and historical status of every one of the
192 excluded records. Earlier original-to-pared certificate provenance
remains in the immutable census stages.

The authoritative `indeterminate_order_10.txt` now equals
`indeterminate_order_10_v8.txt`, containing exactly **7,932**
remaining graphs, down from 8,124. The **4,509 conditional cases are
unchanged**. The first nine-vertex sphere `HCZTf}` and the
snub-disphenoid-dependent cases retain their previous statuses.

## Reproduce and audit

Run from `pycliques-census` repository root with NetworkX 3.6.1:

```bash
python scripts/order10_four_o4_lift_v1.py verify
python scripts/order10_four_o4_lift_v1.py certificates --output /tmp/two-o4-class-certificates.json
python -m unittest discover -s tests -p test_order10_four_o4_lift_v1.py -v
python -m unittest discover -s tests -p test_current_root_index.py -v
```

The dedicated workflow independently checks the full two-map proof,
all 147 nine-vertex isomorphisms, every previous index, the current
v8 root, and tampered-certificate rejection. It protects every
previous versioned list and all stage artifacts. A failed or bounded
retraction search is never treated as proof of nondivergence.
