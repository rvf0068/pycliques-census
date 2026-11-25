# Full certified divergent-reference screen against known unresolved ten-vertex P4 graphs

## Research objective

Let P0(X) be complete closed-neighborhood dominated-vertex paring and
P(j+1)(X) = P(K(Pj(X))). Given a historically **proved** K-divergent
graph H of order at most nine, a complete graph isomorphism

    P_i(H) isomorphic to P_4(G),   0 <= i <= 3,

is an unconditional K-divergence proof for any ten-vertex G.
The depths do not need to match. The previous PR #96 compared the same
reference depths against unresolved ten-vertex P3 and verified zero
exact matches in the completed bounded search.

The current extension compares the archived *fourth* pared iterates
against the full previously authenticated historical reference corpus.

## Avoid recomputing dense fourth iterates

Three merged, independently certified proof archives already contain
exact full fourth-iterate vertex and edge counts for **210 distinct**
still-unresolved ten-v25 P3-equivalence class representatives:

| Frozen proof archive | Already reconstructed P4 graphs |
| --- | ---: |
| ten-v24 positive-only 41..55 P3 pilot | 180 |
| independent recovery of the 26 formerly 750-facet-capped P4 cases | 26 |
| four additional exact fourth-iterate links to pending nine-vertex cores | 4 |
| **Total** | **210** |

The archived shapes are checked against their **code-pinned immutable
Git blob identities**, the current ten-v25 original graph6 records and
the exact global ten-P3 class index. The new code does not assume
equal order/edge counts imply isomorphism.

The historical P3 reference reconstruction permits no more than
750 maximal cliques at the last stage. Exactly **202** of the 210
stored ten-P4 shapes have <=750 vertices and can therefore possibly
match a completely reconstructed reference P3 under this bound. The
other eight are explicitly **outside this bounded comparison scope**,
not excluded as potential isomorphism targets by this bounded search.

To reduce work, each reference P0..P3 is reconstructed only as far as
its documented resource budgets permit and first compared with the
202 target *dimension pairs*. A ten-P4 host graph is fully
reconstructed only when a reference iterate has **exactly the same
number of vertices and edges**.

When a dimension collision occurs, the new proof uses the already
merged independent P4 reconstruction (NetworkX and independent BK
maximal-clique enumeration and complete multi-round paring), then the
complete cross-depth graph isomorphism algorithm and a saved explicit
vertex permutation. A later separate CI job independently rebuilds
both sides and checks all edges and nonedges, including a
label-constrained complementary-graph GraphMatcher.

## Historical divergent reference input

Reuse the **10,155**-source authenticated historical inventory builder
of merged PR #96: 10,104 certified initial/later-stage source records
and 51 further already proved nine-vertex promotions. Reference
stiff P0 classes are deduplicated by actual isomorphism within eight
deterministically disjoint shards, retaining the complete proof
provenance of each source.

An input digest is never obtained by trusting an unverified downloaded
artifact: the 10,155-source inventory and 210-target host-index jobs each
publish their SHA-256 through a successful CI job output, which every
independent shard and final verifier check. A **separate independent
inventory-audit runner** re-enumerates all 10,155 proved sources from
the historical graph6/verdict archive and checks the complete inventory
SHA-256. Each shard additionally archives every original McKay
source key it processed; the final replay rejects missing, duplicated
or misassigned source keys. Positives on the eight out-of-bound hosts
are explicitly rejected. No previous source record,
census stage or historical positive certificate is altered.

## Explicitly inconclusive resource limits

Each original reference is attempted through depths P0, P1, P2, P3.
The existing reference reconstruction has a 250-vertex intermediate
limit and a 750-maximal-clique cap. A genuine algorithmic integrity
assertion (including a disagreement between independent enumerators)
**fails the proof CI**, rather than being silently counted as a limit.
A timeout during a necessary exact graph isomorphism is separately
recorded and cannot become a nonisomorphism verdict.

The 210-graph known ten-P4 reference catalogue is itself a finite,
verified subset: other surviving ten-vertex classes are not included
unless the fourth iterates are independently reconstructed first.
This is a **positive-only search**, not a certificate of convergence
or an unrestricted negative result.

## Reproduction

Run the dedicated workflow:

    .github/workflows/order10-full-nine-p4-crossdepth-v1.yml

For local checks in the census repository root, with Python 3.12 and
NetworkX 3.6.1:

    python -m unittest research.order10_full_nine_p4_crossdepth_v1.test_search -v
    python -m research.order10_full_nine_p4_crossdepth_v1.search hosts --output /tmp/ten-p4-hosts.json

The full historical source build also requires the existing pinned
historical census input and pycliques bootstrap, which the CI workflow
automatically restores in its isolated source-index job.

Then the eight authenticated reference shards process disjoint slices
of the source corpus; the final verifier independently reconstructs
and checks every **positive full bijection**.

If the search finds a new exact isomorphism, its target remains in the
authoritative census pending a separate explicit *certified* promotion.
The current nine-v9 and ten-v25 lists and the 500 already known
conditional nine-core dependencies are not changed by the search.
