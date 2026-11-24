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
