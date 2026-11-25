# Full historical divergent-reference index against surviving ten-vertex P3 classes

## Question and mathematical criterion

Can a currently unclassified connected ten-vertex graph G have a completely
pared clique iterate isomorphic to the completely pared clique iterate of an
already **proved** K-divergent smaller graph H?

Write P0(G) for complete dominated-vertex paring and
P(j+1)(G) = P(K(Pj(G))). When P_i(G) and P_j(H) are isomorphic, the
dismantling invariance theorem implies that G and H have the same
eventual clique behavior (the depths need not coincide). A certified
K-divergent H therefore proves K-divergence of G.

**Graph dimensions, degree sequences, WL signatures, elapsed resource
limits and inconclusive isomorphism searches do not prove divergence.**
Only a fully constructed and verified all-pairs isomorphism does.

## Phase 1: authenticated complete historical inventory

The existing authenticated historical proof reader
in scripts/historical_divergent_targets_v1.py already validates the
original connected graph6 enumeration against every archived verdict and
later c10 / bound60 / bound70 stage. Rather than copying or rewriting
those proofs, the new inventory invokes that reader and requires:

- 10,096 certified initially divergent original connected graphs of
  orders 6 through 9 (including 9,864 at order nine).
- Eight further independently certified nine-vertex divergences from
  the three older post-stages (4 c10, 1 bound60, 3 bound70).
- Five further nine-vertex promotions from frozen nine-v1 to nine-v2,
  36 after the proof of snub divergence (nine-v2 to nine-v3), and ten
  subsequent proven nine-v3 to nine-v9 promotions.

**Total: 10,155 historically proved divergent source records.**

The final 51 version-difference sources use their frozen *pared*
graph6 identity (which sometimes has eight rather than nine vertices).
That is legitimate because dominated-vertex deletion preserves
K-behavior, and avoids pretending that the frozen graph6 is the original
nine-vertex encoding. Every difference and all four frozen source Git
blobs are checked in code independently of any new output artifact.

## Phase 2: the surviving stiff ten-vertex target catalogue

The immutable ten-v25 source has 622 original stiff ten-vertex cases.
The independently verified global ten-v23 third-iterate archive groups
619 surviving originals into **521 exact P3 classes**, with three
previously declared reconstruction limits.

The new script independently reconstructs all 521 class
representatives, stores their complete P3 graphs and inherited member
lists, and checks the frozen ten-v25 and global-P3 Git blob IDs.
No original census result is edited.

## Phase 3: eight reproducible proof-positive shards

The 10,155 references are partitioned deterministically into eight
nonoverlapping shards, with the exact inventory/host files authenticated
by SHA-256 digests reported independently by their successful generating
GitHub Actions jobs.

Each worker first removes dominated vertices from each historical
reference graph. It deduplicates identical **P0 isomorphism classes**
only after an actual NetworkX isomorphism check; all original source
provenance records are preserved. It then reconstructs P0, P1, P2 and
P3 (through the existing independently cross-checked NetworkX and
bitset Bron--Kerbosch enumerators).

Each reconstructed reference iterate is compared with the 521
ten-original P3 representatives. Necessary fingerprints avoid
impossible pairs, but every positive needs an exact GraphMatcher
isomorphism of graph complements, a complete vertex map, and an
explicit test of **all** edge/nonedge pairs.

The worker explicitly records any bounded clique-enumeration or
intermediate-order limit; any long isomorphism search is marked
TIME_LIMIT_INCONCLUSIVE and cannot become an accepted negative result.
The intermediate order is capped at 250 and the reused historical
dual-enumerator P3 construction has its documented 750-facet bound.
No claim of an exhaustive unbounded negative search is made.

A final independent CI job downloads all eight outputs, verifies
shard population and predecessor SHA-256 attestations, reconstitutes
each positive from its original graph6, and rechecks the saved complete
bijective map on every ordered vertex pair.

### Running the search

The dedicated workflow is:

.github/workflows/order10-full-nine-reference-v1.yml

It runs on the new PR and supports manual workflow dispatch. The
source inventory job uses the existing historically pinned pycliques
bootstrap, restoring the original frozen root aliases **only inside
the isolated CI runner**. The host, matching, and independent replay
jobs need only NetworkX 3.6.1 and the original census repository.

The final proof archive is a versioned workflow artifact named
full-divergent-nine-verified-positives-v1. It records all positive
members and every explicit incomplete/resource-limited case. Positive
results can be incorporated in a **separate** future certified v26
promotion only after their full replay passes.

All authoritative nine-v9 and ten-v25 census lists and historical
proof sources are left untouched in this proof-positive search.

## Scope and next phases

This first global index compares certified reference depths 0 through
3 with unresolved ten-vertex depth **3**. It does not yet compare all
ten-vertex fourth iterates: the ten-v24 P4 pilot already handled 206
selected classes, with the remaining large fourth-stage cases requiring
separate resource management.

After running phase 1, candidate-positive references should also be
compared across different depths, especially nine-reference P3 versus
ten-original P4, reusing the saved host and reference indices. A
complete positive proof (not an invariant collision) remains necessary.

The repository's frozen existing census data are unchanged and no
new graph has been declared convergent or divergent merely because
this search was added.
