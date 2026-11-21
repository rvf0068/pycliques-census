# Eighty further ten-vertex K-divergence proofs from McKay 260910

**Positive result.** McKay 260910 (graph6 `HUZvvzu`) has a complete
ordinary retraction of its third completely pared clique iterate onto
`O_15`. The full 132-entry projection and its independent full
verification are archived in the parent
[O15 proof](REPORT.md) and [certificate](certificate.json).
Consequently, every graph that retracts onto that original source,
or has an exactly isomorphic completely pared clique iterate, is also
K-divergent.

## New original ten-vertex results

An exhaustive positive-only sweep of all **2,568 original rows** in the
frozen order-ten v14 unresolved snapshot found exactly **80** new
unconditional K-divergence certificates:

| Proof mechanism | Number |
| --- | ---: |
| Completely pared graph is exactly isomorphic to `HUZvvzu` | 62 |
| Completely pared graph ordinarily retracts onto `HUZvvzu` | 14 |
| Second completely pared clique iterate is isomorphic to P2(`HUZvvzu`) | 4 |
| **Total** | **80** |

For every direct isomorphism, the [saved certificate](lift_v14_certificate.json)
contains the full vertex bijection. For every retraction it contains the
complete host-to-target projection and target-to-host inclusion. For each
P2 comparison it contains an exact bijection of two 21-vertex graphs
with 176 edges. All 80 source graph6 strings and original McKay indices
are retained verbatim.

The original snapshot is authenticated by Git blob
`3ee92e02891b3046059241d4a2304794b0e34380`. Every one of the
80 frozen entries has status `- - -`, not an earlier conjectural
dependency. This positive cohort is disjoint from the 27 certified
v14-to-v15 positives of census PR #63 and the 120 previously
conditional F45 reference dependencies.

## Replay without trusting the search

Run the [independent verifier](verify_lifts_v14.py) with the same
public `pycliques` pin as the O15 source proof:

```sh
PYTHONHASHSEED=0 python research/order9_260910_o15_v1/verify_lifts_v14.py
PYTHONHASHSEED=0 python research/order9_260910_o15_v1/verify_lifts_v14.py --full
```

The first command checks the O15 source itself, the original v14
identities, all 80 complete maps against every edge (and every
nonedge for graph isomorphisms), and an independent NetworkX
reconstruction of each exceptional P2 isomorphism. The `--full`
option repeats all eight original-vertex-index shards using public
`pycliques` and requires the identical 80 entries with **zero
skipped** graphs.

Eight independent exploratory CI shards were successful. The
subsequent verification workflow is
`.github/workflows/order9-260910-lifts-v14-certify.yml`.

## Status of the census

The working root has **not** been modified. Subject to the separate
proof and index-promotion reviews:

- Merged v14: **2,568** unresolved order-ten originals.
- Proposed census PR #63 removes 27: **2,541**.
- F45/O9 proof PR #64 upgrades 120 historical conditional dependencies:
  **2,421**.
- These 80 new, disjoint McKay260910/O15 positives would bring the
  unresolved order-ten total to **2,341**.
- The two independently proved nine-vertex positives McKay 208409
  and 260910 reduce unresolved order nine from 12 to **10** when
  separately promoted.

These reductions are not represented as merged or authoritative while
the parent PRs remain open. No negative search, timeout or approximate
graph invariant is used to classify any graph.
