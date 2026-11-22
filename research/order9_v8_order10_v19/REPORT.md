# Certified nine-v8 and ten-v19 census promotion

## Result

Merged PR #78 proves that the connected-nine McKay graph **251902**
(`HEhvvzm`) is K-divergent, by a complete ordinary graph retraction
from its fourth completely pared clique iterate onto the 17-dimensional
octahedral graph `O17 = complement(17 disjoint edges)`.

The positive source proof, including the **complete 461-vertex
retraction** and its independent replay, is preserved under
`research/order9_251902_p4_o17_v1/`.

The authoritative indeterminate counts consequently change by
**one** original graph of order 9 and **150** original graphs of order 10:

| Connected order | Frozen prior index | Prior count | New index | New count | Exact removals |
|---|---|---:|---|---:|---:|
| 9 | nine-v7 | 6 | nine-v8 | **5** | 1 |
| 10 | ten-v18 | 1,681 | ten-v19 | **1,531** | 150 |

The two authoritative root lists are byte-for-byte copies of
the new v8/v19 snapshots. Neither versioned predecessor is modified;
all retained data rows remain **exactly unchanged**.

## Mathematical reason for the 150 ten-vertex consequences

For an order-ten original graph whose completely pared core is
isomorphic to the nine-vertex graph 251902, dominated-vertex
dismantling preserves iterated clique-graph behavior. Such a graph
therefore inherits K-divergence from its core, whose P4 retracts
onto O17 by merged PR #78.

The frozen ten-v18 index contained exactly **800** originals with
a pared core of order 9, and **881** with a pared core of order 10.
The new promotion removes the 150 nine-core members of the
McKay 251902 family and *no other* original.

Consequently the ten-v19 population is precisely
**650** pared-nine originals and **881** pared-ten originals.
The remaining five nine-vertex source families are:

| Nine-vertex McKay | graph6 | Remaining ten-vertex original dependents |
|---:|---|---:|
| 249576 | HEhfvzu | 141 |
| 251628 | HEhvVn{ | 147 |
| 251759 | HEhvtzm | 129 |
| 254369 | HEjfvx} | 91 |
| 260040 | HQyvex} | 142 |
| **Total** | | **650** |

No new claim is made for those five nine-vertex sources, for the
881 ten-vertex stiff sources, or for the six previously identified
ten-vertex flag-sphere triangulations.

## Independent, exhaustive, checkable promotion audit

The authoritative proof is `verify.py`, which independently:

1. Confirms the immutable nine-v7 Git blob
   `6f1e05d6b6bb0f1b4f2638ad73a7163f26ab0345`
   and immutable ten-v18 Git blob
   `9dba1f3359d6e90fbda1026d672173fa2461b460`.
2. Checks both mutable root files are byte-identical to the
   new nine-v8 and ten-v19 snapshots.
3. Reads all original McKay rows with strict six-field
   validation, duplicate detection, ascending-index enforcement
   and graph6 order checks. It verifies the frozen six-to-five
   transition removed exactly McKay 251902 and no others.
4. Independently enumerates all **800** frozen ten-v18
   nine-pared originals, checks exact graph isomorphism of their
   graph6 cores to the source of the positive O17 proof,
   and verifies every discovered map edge by edge.
5. Finds exactly **150** such originals, checks that these
   (and only these) were removed from the frozen ten-v18
   file, and that every remaining source row is byte-identical.
6. Validates all **150 explicit original identities, source rows,
   target graph6 strings and nine-vertex isomorphism bijections**
   stored in `promotion_manifest.json`, independently checking
   each of their 81 ordered adjacency/non-adjacency relations.

Neither the source graph6 matching nor the decision which originals
to delete is taken from the saved manifest. The manifest is an
additional independently validated witness of the promotion.

The optional `--proofs` mode also reconstructs the complete
461-vertex P4 host from the original McKay graph6, checks the
exact normalized P4 labeled-edge SHA-256, validates that the
34 target vertices induce O17, that the retraction fixes all
target vertices and that the complete projection preserves
all **94,642** edges. It also replays the source's own 150
ten-v18 lift audit. With `--public`, the original proof is
rechecked by public pycliques.

All proofs are exact finite checks; no randomized negative
search or time-limited solver result is promoted.

## Historical compatibility

The prior v7/v18 proof remains unchanged. The new
`replay_v18.py` redirects only the *mutable working root*
reads of the original historical verifier to its two
frozen v7/v18 snapshots. The earlier workflow is adapted to
use this wrapper, preserving full old verification against
historical inputs.

The current-root regression tests and the legacy nine-index and
core9 cross-reference entry points now point to the certified
latest roots. Historic audit source files, earlier snapshots and
positive witnesses are unchanged.

## Reproduction

From the census repository root, with Python 3.12 and NetworkX 3.6.1:

    python -m research.order9_v8_order10_v19.verify
    python -m research.order9_v8_order10_v19.verify --proofs
    python -m research.order9_v8_order10_v19.replay_v18
    python -m unittest discover -s tests -p test_current_root_index.py -v

With the pinned public `pycliques` library installed:

    python -m research.order9_v8_order10_v19.verify --proofs --public

Proof-critical Python assertions are not bypassable under optimized
execution; the verifier deliberately rejects `python -O`.
Dedicated GitHub Actions jobs replay the exact delta,
full O17 proof, historical v7/v18 certification, and current-root
regression tests.

## Research priority

The next five unresolved connected-nine McKay graphs are
**249576**, **251628**, **251759**, **254369**, **260040**.
The dual-weight-based native coaffine ordering that first produced
251902 -> O17 is worth generalizing to their P4 graphs.
A limited search or absent small target is not a proof of
convergence or K-nullity. No further nine/ten census records
should be removed without complete positive certificates.
