# ten-v24: positive-only fourth-iterate reference search

The current snapshot contains **626** unresolved stiff ten-vertex
originals. The global exact third-iterate index of merged PR 87
groups 623 of these into **522** isomorphism classes. The other
three remain explicitly over the third-iterate reconstruction limits.

This pilot selects representatives whose third completely pared
clique iterate \(P_3(G)\) has **41 to 55 vertices**. It independently
reconstructs \(P_4(G)\) by integer-bitset dominated-vertex folding
and a Bron--Kerbosch maximal-clique enumerator independently
cross-checked with NetworkX. Each candidate is checked for exact
P4 isomorphism to five previously certified divergent graphs:

| Reference McKay | Graph6 | P4 vertices / edges | Certified retraction |
|---:|---|---|---|
| 10223405 | ICXnRi^uo | 182 / 14,298 | O12 |
| 10775850 | ICpVUjx\|_ | 188 / 15,083 | O12 |
| 10223467 | ICXnRjZmo | 151 / 8,413 | O6 |
| 11104269 | ICpdupvZo | 160 / 9,258 | O6 |
| 11563706 | IEhfe^{zO | 159 / 9,276 | O6 |

The original retraction witnesses and independent checks appear in
[order10_fourth_oct_v1](../order10_fourth_oct_v1/REPORT.md).
Any new positive exact P4 isomorphism to one of these references
proves K-divergence by transporting the already certified
ordinary graph retraction.

## Complete pilot results (GitHub Actions run 45460379020)

The twelve original search shards completed successfully and produced a
complete [206-case results archive](results.json). Every selected graph
belongs to a *different certified P3 isomorphism class* in the merged
global ten-v23 index.

| Explicit outcome | Original P3 class representatives |
|---|---:|
| Reconstructed completely through the fourth pared clique iterate | **180** |
| Explicit fourth-iterate maximal-clique cap (751st facet) | **26** |
| P4 with the same vertex/edge counts as any of the five divergent sources | **0** |
| Collisions of (P4 vertex count, P4 edge count) among completed cases | **0** |
| **Total selected, P3 orders 41–55** | **206** |

Thus all **180** completed fourth iterates have pairwise different
((|V(P_4)|,|E(P_4)|)) signatures, immediately proving they are
**pairwise nonisomorphic**. Their signatures also differ from each of
the five certified divergent fourth-iterate references: no reference
isomorphism proof arises in this finite range.

The **26** over-cap graphs are explicitly inconclusive; none has been
declared K-convergent or non-divergent. No census rows were removed.

The unusually small McKay **10820813**, graph6 `ICp`fpv~_`,
has (P_3) with 43 vertices/625 edges but (P_4) with only
**70 vertices/1,830 edges**, making it a particularly promising
subject for a *new* retraction search rather than reference-isomorphism
comparison. The full 206-case table also provides a rational ordering
for later targeted octahedral-retraction investigations.

The [archive audit](verify_results.py) validates all 206 source
identities, counts, resource flags, and uniqueness of signatures.
The CI workflow also **reconstructs every selected source again in
its original shard**, then compares the entire new result record to
its saved archive entry. A positive classification would still
require a complete separately verified isomorphism or retraction.

## Resource bounds and epistemic status

- Cap at **750 maximal cliques** at each iteration. Any over-bound
  fourth iterate is recorded as P4_FACET_CAP and remains inconclusive.
- **24 seconds per graph** for the fourth-iterate and possible
  graph-isomorphism calculation. Timeout is inconclusive.
- First compare necessary invariants (order, size, degree sequence
  and Weisfeiler--Lehman hash). A collision is never a positive proof.
- Any actual match is decided by an exact NetworkX GraphMatcher
  on the complementary graphs, with a saved complete vertex
  permutation checked on every edge and nonedge.
- A negative match is only a proof of nonisomorphism to these
  five specified references, not of clique convergence.
- Twelve interleaved CI shards cover every selected representative
  exactly once. Complete records are stored in workflow artifacts.

A known ten-v24 O12 positive is used as an adversarial
regression test, together with a control having a different P4 size.
No current classification list is modified by this pilot; additional
divergent cases will require independent replays and a versioned
census update.

## Reproduction

Requires Python 3.12 and NetworkX 3.6.1. From repository root:

- python -m unittest research.order10_p4_reference_pilot_v24.test_search -v
- python -m research.order10_p4_reference_pilot_v24.search plan
- python -m research.order10_p4_reference_pilot_v24.search run --shards 12 --shard 0 --output /tmp/p4-shard-0.json

Run the last command for all shard indices 0 through 11.
The [workflow](../../.github/workflows/order10-p4-reference-pilot-v24.yml)
does that and uploads results, printing any complete positive
bijections in the corresponding job logs.
