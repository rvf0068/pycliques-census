# Certified nine-v7 and ten-v18 census promotion after merged PR #73

## Executive result

The proof-only PR #73 certifies complete retractions from the fourth
completely pared clique iterates of three original nine-vertex McKay
graphs onto induced octahedra, hence proves them K-divergent:

| Original McKay (order 9) | Graph6 | Retraction | Exact dependent ten-originals |
|---:|---|---|---:|
| 249436 | HEhff^{ | P4 -> O10 | 141 |
| 249574 | HEhfvx} | P4 -> O12 | 82 |
| 250814 | HEhuvzm | P4 -> O14 | 121 |
| **Total** | | 3 proven divergent | **344** |

These three sources had been among the nine remaining in the immutable
nine-v6 snapshot. All 344 ten-vertex original McKay graphs were among
the immutable ten-v17 survivors and have completely pared nine-vertex
cores isomorphic to one of these newly certified divergent graphs.
The behavior-preservation theorem for dominated-vertex dismantling
therefore proves all 344 ten-vertex originals K-divergent.
No other behaviors or conjecture-dependent statuses have been changed.

| Order | Previous frozen | Previous count | Latest snapshot | Latest count | Removed |
|---|---|---:|---|---:|---:|
| 9 | indeterminate_order_9_v6.txt | 9 | indeterminate_order_9_v7.txt | **6** | 3 |
| 10 | indeterminate_order_10_v17.txt | 2,025 | indeterminate_order_10_v18.txt | **1,681** | 344 |

The root working indices are exact byte-for-byte copies of the latest
snapshots. Frozen v6 and v17 and every preceding historical list and
its underlying proofs remain unmodified.

## Six remaining nine-vertex sources

| Original McKay | Pared graph6 | Ten-original descendants still unresolved |
|---:|---|---:|
| 249576 | HEhfvzu | 141 |
| 251628 | HEhvVn{ | 147 |
| 251759 | HEhvtzm | 129 |
| 251902 | HEhvvzm | 150 |
| 254369 | HEjfvx} | 91 |
| 260040 | HQyvex} | 142 |
| **Total** | | **800** |

Among the 1,681 surviving ten-originals, exactly **800** have a
nine-vertex pared core; the remaining **881** have a ten-vertex pared
core. Six of the latter are the previously identified flag
triangulations of the sphere. They remain indeterminate, as do all
six remaining nine-vertex sources. The exact negative octahedral
audits from PRs #71 and #72 are not claims of convergence.

## Two layers of independent verification

**Positive mathematical proofs.** PR #73 stores full fourth-iterate
retraction certificates in
research/order9_three_p4_retractions_v1/certificate.json.
Each witness fixes the target pointwise and preserves every source
edge up to identifying its endpoints. Its independent NetworkX
verifier reconstructs every iterate and validates exact labeled-edge
SHA-256 digests, induced octahedra, and total projections.
A pinned public-pycliques replay and unseeded native rediscovery
also passed CI in PR #73.

**Exact promotion audit.** This folder's verify.py does *not* trust
the 344-line promotion manifest to choose records. It independently
reads all 2,025 original v17 entries, constructs each of the 1,144
nine-vertex pared graphs, tests complete graph isomorphism against
the three source cores, verifies every returned vertex bijection
edge by edge, and checks that the resulting three disjoint families
have exactly 141, 82 and 121 original indices. It verifies every
removed index and source row in promotion_manifest.json, confirms
that each retained row is unchanged, and checks the two historical
source Git blob hashes:

- nine-v6: 48ed753696a2ff3e509c11fc550c64ddb500d675
- ten-v17: 57b97f4b0d4e0b66c2cfc9748826911a55a19e60

It also tests that current root files equal their latest snapshots
and that none of the 881 stiff ten-core graphs was silently removed.

## Historical compatibility and reproducibility

The immutable v6/v17 verifier remains unchanged. Instead,
replay_v17.py supplies the archived v6/v17 contents when that
historical verifier reads the two mutable working roots, just
as its predecessor replay_v16.py already handled older roots.
Existing current-root regression tests and their CI checks now
follow v7/v18 while keeping independent historical count checks.

From the repository root, with NetworkX 3.6.1:

    python -m research.order9_v7_order10_v18.verify
    python -m research.order9_v7_order10_v18.verify --proofs
    python -m research.order9_v7_order10_v18.replay_v17 --families --surfaces
    python -m unittest discover -s tests -p test_current_root_index.py -v

With pinned public pycliques installed, also run:

    python -m research.order9_v7_order10_v18.verify --proofs --public

All proof scripts fail closed under optimized Python. The corresponding
workflow runs the exact promotion delta and complete retraction
replay, and exercises the frozen v6/v17 historical verifier.

## Research priority after this promotion

The remaining six connected-nine original graphs are
249576, 251628, 251759, 251902, 254369 and 260040. The
native coaffine backend from pycliques-project PR #36 is effective
under diversified vertex ordering, but previous bounded searches
for these six have not yet produced positive or exhaustive negative
certificates. New fourth-iterate or non-octahedral divergence
certificates are the next priority; no bound-limited run should
be promoted as a theorem.
