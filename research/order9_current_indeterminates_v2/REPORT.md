# Certified order-nine index v2 — five previously proved divergences

This is a **census synchronization**, not a new theorem or a new retraction
discovery. The historical 54-row working file is retained byte-for-byte as
[`indeterminate_order_9_v1.txt`](../../indeterminate_order_9_v1.txt).
The corrected root and
[`indeterminate_order_9_v2.txt`](../../indeterminate_order_9_v2.txt)
are identical and contain **49** original McKay indices:
**36 conjecture-dependent** and **13 otherwise indeterminate**.

| Order-nine McKay index (zero-based) | Historical graph6 | Already certified by | Date/proof |
|---:|---|---|---|
| 242316 | `HCrlvhz` | Raw \(K^3(G)\to O_5\) | [PR #44](https://github.com/rvf0068/pycliques-census/pull/44) |
| 248687 | `HEher^{` | Raw \(K^3(G)\to O_4\) | [PR #39](https://github.com/rvf0068/pycliques-census/pull/39) |
| 250693 | `HEhutzm` | Isomorphic to the \(K^3\to O_4\) seed `HQqvUx}` | [PR #42](https://github.com/rvf0068/pycliques-census/pull/42) |
| 252075 | `HEh~dzm` | Raw \(K^3(G)\to O_6\) | [PR #45](https://github.com/rvf0068/pycliques-census/pull/45) |
| 255141 | `HEnfbzm` | Certified \(K^3\to O_4\) seed | [PR #42](https://github.com/rvf0068/pycliques-census/pull/42) |

These five are also identified as proved exclusions in the older
[49-case non-octahedral research record](../order9_non_octahedral_clique_targets_v1/REPORT.md).
The record's frozen 54-case input must not be mistaken for the current
nine-vertex index.

## McKay-index and isomorphism safeguards

The self-contained verifier authenticates the exact Git blob of v1;
checks the original indices and graph6 strings against the immutable
*initial nine-vertex census's* indexed input; and rejects accidental
substitutions of a different graph6 encoding merely because it appears
similar. It independently verifies all three direct raw-third-iterate
octahedral projections from the earlier merged scripts, the two
additional pared-third-iterate O4 projections, and graph isomorphism
for index 250693 by checking every possible adjacency/nonadjacency
under the explicit permutation \((4,2,3,0,1,5,6,7,8)\).

The verifier also checks that **none** of the retained nine-vertex
stiff-core rows is isomorphic to any of eleven historical proved
divergent nine-core models. Differences in graph6 labels are not
regarded as evidence of nonisomorphism. All five removed graphs are
stiff (no closed neighborhood is contained in that of another vertex).

The old 54 rows, earlier stages, historical reports and original proof
sources are not altered. Search and historical replay scripts that
require the original 54-case input must use the frozen v1 list, rather
than silently reinterpreting the v2 root.

## Clarification of the ten-vertex class lift (PR #50)

[PR #50](https://github.com/rvf0068/pycliques-census/pull/50) did
**not** discover either of the order-nine retractions again. Its
new certified contribution was the explicit full-isomorphism lift
of the already-proved nine-core results to **116 + 235 = 351**
previously indeterminate *ten-vertex* original McKay graphs.
The underlying nine-core facts had been proved in PRs #44 and #45.
The class lift remains valid. The authoritative order-ten index
advanced separately in PR #53, and must not be altered by this
nine-vertex maintenance action.

## Reproduce

From the repository root with `networkx==3.6.1`:

```bash
python research/order9_current_indeterminates_v2/verify.py --self-test
```
