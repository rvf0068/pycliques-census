# Certified census promotion: order 9 v5 and order 10 v16

## Scope and status

This promotion reviews the certified results through merged PRs **#63** and
**#64** and the independent 80-member McKay-260910 lift proof assembled in
**PR #65**. The 80-member certificate is included directly on this branch so
the resulting index is independently reviewable even while PR #65 is open.
No historical snapshot, completed census run or general-purpose
`pycliques` implementation is edited by this promotion.

The new authoritative unresolved files are:

| Order | Previous frozen version | Previous | Proven removals | New version | Remaining |
|---|---|---:|---:|---|---:|
| 9 | [v4](../../indeterminate_order_9_v4.txt) | 12 | 2 | [v5](../../indeterminate_order_9_v5.txt) | **10** |
| 10 | [v15](../../indeterminate_order_10_v15.txt) | 2,541 | 200 | [v16](../../indeterminate_order_10_v16.txt) | **2,341** |

The root `indeterminate_order_9.txt` and
`indeterminate_order_10.txt` are **byte-identical** to v5 and v16
respectively. The immutable predecessor lists are authenticated using
their exact Git blob hashes; the independent verifier enforces that
**every retained original row is unchanged** and that no excluded source
is missing a complete positive proof.

## Order nine: exactly two further solved graphs

| Original connected-nine McKay index | graph6 | Complete proof |
|---:|---|---|
| 208409 | `HCZTf\}` | `P4(F_{4,5})` (202 vertices, 16,289 edges) retracts to `O9` |
| 260910 | `HUZvvzu` | `P3(G)` (132 vertices, 7,880 edges) retracts to `O15` |

The full maps, exact graph-construction checks, and independent
public-`pycliques` replays are in
[the F45 proof](../order9_f45_o9_v1/REPORT.md)
and [the McKay 260910 proof](../order9_260910_o15_v1/REPORT.md).
Both results are proved in merged PR #64. By the retraction theorem,
the divergence of octahedra `O_d` for `d>=3`, and preservation of
clique behavior under dominated-vertex dismantling,
both original graphs are **K-divergent**.

The ten genuinely unresolved connected-nine graphs are:

| McKay | graph6 |
|---:|---|
| 249436 | `HEhff^{` |
| 249574 | `HEhfvx}` |
| 249576 | `HEhfvzu` |
| 250814 | `HEhuvzm` |
| 251628 | `HEhvVn{` |
| 251759 | `HEhvtzm` |
| 251902 | `HEhvvzm` |
| 253650 | `HEjer~{` |
| 254369 | `HEjfvx}` |
| 260040 | `HQyvex}` |

No one of these ten is a flag triangulation of a closed surface.

## Order ten: 200 disjoint exact positive certificates

### 120 formerly conditional F45 dependencies

All 120 records in v15 with reference
`HCZTf\}` have now been unconditionally proved divergent. This does
**not** simply promote a former conjectural status: the independent
[`lift120.py`](../order9_f45_o9_v1/lift120.py) replays a positive
witness for every original McKay index, comprising:

| Complete certificate | Records |
|---|---:|
| Exact reference isomorphism | 72 |
| Ordinary retraction | 35 |
| Non-triangle edge deletion chain with certified downstream | 10 |
| Admissible inverse-cutpoint extension | 3 |
| **Total** | **120** |

The target's divergence was separately proved by the `P4 -> O9`
certificate from PR #64.

### 80 additional McKay 260910 / O15 lifts

The independently certified [80-member lift](../order9_260910_o15_v1/lifts80_report.md)
exhaustively screened the 2,568-original frozen v14 index, retaining
complete maps for each of the following positive mechanisms:

| Complete certificate | Records |
|---|---:|
| Isomorphism of the completely pared graphs | 62 |
| Ordinary retraction onto McKay 260910 | 14 |
| Isomorphism of second completely pared clique iterates | 4 |
| **Total** | **80** |

**Historical documentation note.** The linked `lifts80_report.md` is the
original **proof-only PR #65 report**. Its statements that indexes have not
yet been promoted refer to that separate historical PR, *not* to this
current v16 promotion PR #66. The report is preserved unchanged so the
complete archived proof remains reproducible; the actual 80 removals occur
in the new v16 file and are independently audited here.

The 80 have been cross-checked against the *merged v15 snapshot*: each
original index is still present there with exactly the same graph6 and
an unconditional `- - -` record. The sets of 120 and 80 are disjoint;
the 80 also have no overlap with the 27 previously deleted in PR #63.
The [complete 80-member certificate](../order9_260910_o15_v1/lift_v14_certificate.json)
and independent [replayer](../order9_260910_o15_v1/verify_lifts_v14.py)
are committed on this promotion branch and reviewed separately in PR #65.

Therefore the new exact unresolved population is

```
2,541 - 120 - 80 = 2,341
```

All remaining 2,341 original ten-vertex records have target-status
`-` (none depends on an unresolved conjectural reference).
Of these, **1,386** pare to nine vertices and **955** are stiff ten-vertex
graphs. These are *unresolved* by the certified methods to date:
the promotion does not assert convergence or divergence for them.

### Outstanding flag surfaces

Using the exact condition that every open vertex neighborhood induces a
cycle of length at least four, none of the ten unresolved nine-vertex
cores is a flag triangulation of a closed surface. Among the 2,341
unresolved original ten-vertex graphs, exactly **nine** are such surfaces:

| McKay index | graph6 |
|---:|---|
| 6499365 | `I?ovUqv\o` |
| 8559181 | `ICQbQrvno` |
| 9804321 | ``ICR`tlmv_`` |
| 10185592 | `ICXmdbj\o` |
| 10472553 | `ICZTeYj^_` |
| 10803453 | ``ICp`epv~_`` |
| 11031156 | `ICpderm\o` |
| 11138607 | `ICperXumW` |
| 11548392 | `IEherhmmO` |

Each has 10 vertices, 24 edges, 16 triangular faces, and each
vertex link is a cycle, so its clique complex is a triangulated
2-sphere. This is checked directly by the new `--surfaces` mode.
The remaining 2,332 unresolved ten-vertex entries do not have
clique complexes that are closed 2-manifolds.

## Historical progress audited

The earlier snapshots are kept frozen. The sequential unresolved
population is:

| Order 9 snapshot | Count | New proofs since prior |
|---|---:|---:|
| v1 | 54 | -- |
| v2 | 49 | 5 |
| v3 | 13 | 36 (snub cohort) |
| v4 | 12 | 1 (McKay 248936 / O12 P2 lift) |
| **v5** | **10** | **2 (O9 and O15)** |

| Order 10 snapshot | Count | New proofs since prior |
|---|---:|---:|
| pre-v3 | 8,648 | -- |
| v3 | 8,533 | 115 |
| v4 | 8,233 | 300 |
| v5 | 8,224 | 9 |
| v6 | 8,223 | 1 |
| v7 | 8,124 | 99 |
| v8 | 7,932 | 192 |
| v9 | 7,920 | 12 |
| v10 | 7,219 | 701 |
| v11 | 2,830 | 4,389 (snub) |
| v12 | 2,788 | 42 |
| v13 | 2,787 | 1 |
| v14 | 2,568 | 219 |
| v15 | 2,541 | 27 |
| **v16** | **2,341** | **200** |

The total certified ten-vertex reduction from the preserved pre-v3
working census is **6,307** original graphs. This summary concerns
previously *indeterminate* original graphs, not every original graph in
the full 11,716,571-graph order-ten connected census.

## Reproduction and review gates

The compact [promotion manifest](promotion_manifest.json) lists every
excluded original index, its frozen six-column row, the proof mechanism,
and the exact nine-vertex source identities.

Run these commands from the census repository root:

```sh
python -m research.order10_current_indeterminates_v16.verify
python -m research.order10_current_indeterminates_v16.verify --surfaces
PYTHONHASHSEED=0 python -m research.order10_current_indeterminates_v16.verify --f45
PYTHONHASHSEED=0 python -m research.order10_current_indeterminates_v16.verify --o15
PYTHONHASHSEED=0 python -m research.order10_current_indeterminates_v16.replay_v15 --public
PYTHONHASHSEED=0 python -m research.order10_current_indeterminates_v16.replay_v14
```

The `--f45` and `--o15` modes require the pinned public
`pycliques-project` dependency and NetworkX. The optional
`--o15-full` mode repeats the exhaustive frozen v14 screening;
the archived PR #65 CI separately completed that screen.

The dedicated new CI workflow checks the promoted indices, sphere
census, both proof families, historical versions and unchanged roots.
Older workflow replays are redirected to their **frozen** predecessor
inputs without editing those proofs. The promotion is ready for
consideration only once all new and triggered historical checks pass.
