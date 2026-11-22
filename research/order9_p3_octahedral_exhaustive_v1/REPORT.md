# Exhaustive negative audit: no octahedral retract of P3 for the nine v6 residual nine-cores

## Scope and result

Let `P0(G)` be the result of exhaustively deleting dominated vertices of `G`,
and `P(j+1)(G)` the completely pared clique graph of `Pj(G)`.
We independently reconstructed `P3` for **all nine** remaining nine-vertex
McKay graphs in immutable `indeterminate_order_9_v6.txt` (merged PR #70).

**Verified finite negative result:** For each of these nine graphs, **no**
ordinary graph retraction `P3(G) -> O_d` exists for **any** `d >= 3`,
where `O_d` is the complement of `d` disjoint edges. This is an exhaustive
negative result **only for the third completely pared iterate and only for
this retraction family**. It does **not** prove clique convergence, rule out
other retraction targets, or exclude octahedral retractions at `P4` or later.
The nine-v6 / ten-v17 unresolved counts stay **9 / 2,025**.

| McKay | P3 vertices | P3 edges | Distinct induced O_d (d≥3) | Complement-dominating | Max d | Octahedral retractions |
|---:|---:|---:|---:|---:|---:|---:|
| 249436 | 52 | 963 | 40,875 | 14,526 | 4 | 0 |
| 249574 | 36 | 496 | 15,938 | 2,683 | 4 | 0 |
| 249576 | 53 | 1,044 | 131,368 | 26,967 | 6 | 0 |
| 250814 | 38 | 533 | 13,442 | 3,043 | 4 | 0 |
| 251628 | 55 | 1,156 | 267,540 | 34,860 | 5 | 0 |
| 251759 | 43 | 701 | 48,223 | 8,949 | 5 | 0 |
| 251902 | 41 | 641 | 40,984 | 12,234 | 5 | 0 |
| 254369 | 40 | 626 | 28,622 | 4,081 | 5 | 0 |
| 260040 | 58 | 1,289 | 389,255 | 54,319 | 5 | 0 |
| **Total** | | | **976,247** | **161,662** | | **0** |

No branch of any target retraction CSP hit its state limit. Source identity
is checked against the **frozen v6**, not an editable current-root list.
Both positive certificates and limits would cause the audit to fail rather
than be silently classified as negative.

## Mathematical completeness argument

1. **Induced octahedra.** Let `E` be the nonedges of a simple graph `X`.
   Build an auxiliary *compatibility graph* `C(X)` whose vertices are the
   nonedges `{a,b}` and whose edges join pairs `{a,b}`, `{c,d}` of four
   distinct vertices with all four cross edges present in `X`.
   Any induced `O_d` (d≥3) corresponds exactly to a `d`-clique in `C(X)`:
   its vertices are its unique antipodal nonedges. Every clique of size
   at least three is contained in a maximal clique. Enumerating every
   maximal clique and all of its subsets of size ≥3, with deduplication,
   therefore enumerates **every** induced octahedron without omissions.

2. **Necessary complement domination.** If `r:X->T=O_d` is a retraction
   and an external vertex `v` is adjacent to every vertex of `T`,
   then `r(v)=t` would force `t` to be adjacent or equal to every
   vertex of `T`, including its antipode `tau(t)`, a contradiction.
   Consequently the intersection of the *open* neighborhoods of the
   target vertices must be empty. A failure of this condition is a
   rigorous rejection of that target, but passing it is not a proof.

3. **Exact fixed-target constraints.** Fix the target `T` with antipodal
   involution `tau`. A graph retraction must fix `T` pointwise. For an
   external vertex `v`, the possible images are **exactly**
   `D(v) = {t in T : v not adjacent to tau(t)}` as far as edges from
   `v` to the fixed target are concerned. The only forbidden pair of
   images for an arbitrary edge `uv` is `(t,tau(t))`. These constraints
   characterize ordinary graph homomorphisms under the convention that
   adjacent vertices may have the same image. Singleton propagation
   removes a forbidden antipodal value from each neighboring domain;
   minimum-domain backtracking then explores every remaining choice.
   The verifier explicitly distinguishes a positive witness, complete
   exhaustion, and a **resource-limit exception**.

Together, these three steps prove that the completed zero-hit searches
exclude every `P3 -> O_d` retraction, including targets not found by
heuristic amplification. The independent construction builds `K(G)` as
the intersection graph of inclusion-maximal cliques, then exhaustively
folds closed-neighborhood-dominated vertices.

## Validation and reproduction

The verifier checks exact order/size, compatibility enumeration counts,
source graph6 from immutable nine-v6, complement domination, and all
fixed-target CSPs. Its standalone self-test compares 250 randomized
`O3`-plus-at-most-three-vertex examples against a brute-force retraction
oracle (including both positive and negative cases). Optional `--public`
independently reconstructs each `P3` through pinned public `pycliques` and
checks graph isomorphism. All records are derived, not hardcoded projection
maps. `python -O` is rejected.

```sh
python -m pip install networkx==3.6.1
python research/order9_p3_octahedral_exhaustive_v1/verify.py --self-test
python research/order9_p3_octahedral_exhaustive_v1/verify.py --case 249574
# With pinned public pycliques also installed:
python research/order9_p3_octahedral_exhaustive_v1/verify.py --public
```

## Next mathematical work

The source `McKay 253650` was proved divergent by a **fourth**-iterate
`O12` retraction in PR #69 despite no earlier proof. Accordingly the
negative `P3` results here are **not** evidence that these nine cores
converge. Investigate `P4` using the reusable coaffine-retraction and
complement-dominating octahedral searches in `pycliques`, prioritizing
cores with the largest ten-vertex family lift and feasible iterate size.
Treat timeouts and bounded search limits as indeterminate, never exhaustive.
