# Audited current census: 9 unresolved nine-vertex graphs, 2,025 ten-vertex graphs

## Executive conclusion

The previous nine-v5 current list had 10 unresolved originals because
**McKay 253650**, graph6 `HEjer~{`, was not removed after its complete
`P4 -> O12` retraction was independently certified and merged in
[PR #69](https://github.com/rvf0068/pycliques-census/pull/69).
The correct residual nine-vertex count is **9**.

The ten-v16 file likewise omitted **316** recent proved K-divergence
promotions: **242** exact pared-core isomorphisms to McKay 253650,
**71** explicit ten-to-nine retractions onto that graph, and
**three** independently proved ten-vertex flag spheres:

| Original connected-ten McKay index | Proof |
|---:|---|
| 9804321 | `P4 -> O5`, merged PR #68 |
| 10185592 | `P4 -> O6`, merged PR #67 |
| 10472553 | `P4 -> O4`, merged PR #69 |

The three categories are disjoint and each was still an unconditional
`- - -` record in frozen v16. The new counts are:

| Connected order | Prior snapshot | Count | New frozen snapshot | Count |
|---|---|---:|---|---:|
| 9 | `indeterminate_order_9_v5.txt` | 10 | `indeterminate_order_9_v6.txt` | **9** |
| 10 | `indeterminate_order_10_v16.txt` | 2,341 | `indeterminate_order_10_v17.txt` | **2,025** |

All existing historical indices, research proofs and run records remain
unchanged. Both mutable root files match their new versioned copies.

## All nine unresolved connected-nine originals

| McKay index | Pared graph6 | Remaining original connected-ten graphs having this pared core |
|---:|---|---:|
| 249436 | `HEhff^{` | 141 |
| 249574 | `HEhfvx}` | 82 |
| 249576 | `HEhfvzu` | 141 |
| 250814 | `HEhuvzm` | 121 |
| 251628 | `HEhvVn{` | 147 |
| 251759 | `HEhvtzm` | 129 |
| 251902 | `HEhvvzm` | 150 |
| 254369 | `HEjfvx}` | 91 |
| 260040 | `HQyvex}` | 142 |
| **Total** | **9 nonisomorphic cores** | **1,144** |

The residual ten-vertex census divides into **1,144** records that
completely pare to nine vertices, and **881** stiff ten-vertex graphs.
An exact graph-isomorphism check on *every* one of those 1,144
nine-core records shows each belongs to exactly one of the nine
classes in the table. There is **no tenth hidden nine-core class**
represented by the ten-vertex list. The table counts original
ten-vertex McKay indices, not unique nine-core graph6 encodings.

This means a proof of divergence for any one surviving nine-core
would simultaneously solve the corresponding entire ten-vertex
family, by the dominated-vertex dismantling theorem.

## Remaining ten-vertex flag spheres

Only **six** connected-ten originals still have clique complexes
which are flag triangulations of closed surfaces:

| McKay index | Pared graph6 |
|---:|---|
| 6499365 | `I?ovUqv\o` |
| 8559181 | `ICQbQrvno` |
| 10803453 | ``ICp`epv~_`` |
| 11031156 | `ICpderm\o` |
| 11138607 | `ICperXumW` |
| 11548392 | `IEherhmmO` |

Each has 10 vertices, 24 edges and 16 triangles. Every vertex link
is a chordless cycle, so each is a flag triangulation of `S^2`.
No remaining nine-vertex original is a closed flag surface. All other
**2,019** remaining ten-vertex originals fail the closed-surface link
criterion.

The three newly removed flag spheres have complete fourth-pared
octahedral retractions with independently verified total projections:

| McKay | Pared fourth iterate | Retract |
|---:|---|---|
| 9804321 | 202 vertices, 13,606 edges | `O5` |
| 10185592 | 262 vertices, 21,822 edges | `O6` |
| 10472553 | 365 vertices, 42,351 edges | `O4` |

Their archived verifiers and positive maps are under
`research/order10_surface_9804321_o5_v1/`,
`research/order10_surface_10185592_o6_v1/` and
`research/order10_surface_10472553_o4_v1/`.

## Source authentication and proof replay

The promotion manifest `promotion_manifest.json` records the
**exact 316 removed original McKay indices**, each frozen v16 row,
its verified theorem mechanism and its archived full certificate.

The independent `verify.py` checks:

1. Immutable v5 and v16 Git-blob hashes; current-root equality with
   the newly frozen v6 and v17 index snapshots.
2. The exact old-to-new set differences; 6-column record identity
   for *every retained graph*; and the precise disjoint **242+71+3**
   deletion set.
3. All **242** original saved nine-core isomorphism permutations,
   testing both edges and nonedges.
4. All **71** ordinary retractions: induced nine-core copies,
   pointwise fixation, and every source-edge image.
5. Exact isomorphisms of all **1,144** remaining nine-core records,
   with the nine representatives pairwise nonisomorphic.
6. An independent link-cycle screen of every remaining nine-
   and ten-vertex graph, yielding exactly the six flag spheres.
7. With `--proofs`, the full saved `P4 -> O12` positive source,
   all 313 ten-vertex lifts and the three independently saved
   sphere `P4 -> O_d` retractions. Optional `--public` repeats
   every result with the exported public `pycliques` verifiers.

The archived v16 verifier itself is unchanged. The new
`replay_v16.py` directs only its two mutable-root reads in memory
to the frozen v5 and v16 snapshots; v14 and v15 historical
replayers are likewise preserved. No result is inferred from a
failed bounded search.

### Reproduction

From the root of the census checkout, with NetworkX 3.6.1:

```bash
python -m research.order10_current_indeterminates_v17.verify --families --surfaces
python -m research.order10_current_indeterminates_v17.verify --proofs
python -m research.order10_current_indeterminates_v17.replay_v16 --surfaces
python -m unittest discover -s tests -p test_current_root_index.py -v
```

With pinned public `pycliques` installed:

```bash
PYTHONHASHSEED=0 python -m research.order10_current_indeterminates_v17.verify --proofs --public
```

The remaining cases have **not** been proved convergent or divergent.
The nine-vertex cores, then the six flag spheres and remaining 881 stiff
ten-vertex graphs, are the natural next research priorities.
