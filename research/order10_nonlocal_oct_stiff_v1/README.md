# Octahedral retraction search for the 1,043 unresolved stiff ten-cores

This is a **positive-only** bounded experimental search, using the current
`pycliques` library at pinned commit
`7ae36ffe67fb2e9bbafc68e97347aabcf757c2dc`. The selection is
restricted to the **1,043 unconditional stiff order-ten** entries
(`pared_order=10`, `- - -`) in immutable
`indeterminate_order_10_v11.txt` (Git blob
`34023e9323945c4a6e5e1249c37ba955ba62473f`).

All source data, histories, and census classification files remain unchanged.

## Verified results (21 November 2026)

Two read-only GitHub Actions runs have completed successfully:

- [Pilot, 192 cores](https://github.com/rvf0068/pycliques-census/actions/runs/44934260657):
  zero found, all 192 bounded outcomes inconclusive.
- [Full screen, 1,043 cores](https://github.com/rvf0068/pycliques-census/actions/runs/44934373159):
  **0 new certified retractions**, 1,043 inconclusive, zero errors or
  per-original timeouts. All eight jobs passed. The eight uploaded JSON
  artifacts contain every trial, search status, and reconstructed order.

On the full screen, 1,038 source cores yielded at least one induced
candidate target, with **3,219 fixed-target retraction tests**.
All 3,219 solver outcomes were `EXHAUSTED`; those are valid negative
results **for those particular embedded targets only**. Four sources
reached the 450-vertex clique-iterate cap before reconstruction
of their third pared iterate; no per-original process timed out.

The selected target dimensions were 3, 4, 5, 6, 8, and 10; search
depths were 0, 1, 2, and 3, with up to 160 randomized restarts per
target/depth, 1,200 CSP search states, and 8 seconds per source.
Although this covers every stiff ten-core, the **search itself is not
exhaustive**, and no convergence or nondivergence claim follows.

## Independent exact follow-up for smaller third iterates

A separately implemented, NetworkX-only exhaustive complement-pair
enumeration and constraint solver examined all **257** source cores
whose reconstructed completely pared third clique iterate has
at most 40 vertices. It enumerated:

| Dimension | All induced targets | Complement-dominating targets |
| ---: | ---: | ---: |
| 3 | 3,129,095 | 238,026 |
| 4 | 627,187 | 485,573 |
| 5 | 5,223 | 18 |
| 6 | 2,866 | 0 |
| 7 | 952 | 4 |
| 8 | 134 | 104 |

The exact maximum induced-octahedron dimensions in these
257 graphs are distributed as follows: 3 (one graph),
4 (203), 5 (52), and 8 (one).
Every one of the 723,725 complement-dominating induced octahedra
was tested and rejected as a retraction target; no search timed out.
An induced octahedron with an external vertex adjacent to every
target vertex cannot be a retract, so the domination filter is
mathematically necessary. Consequently, **none of these 257
particular completely pared third iterates retracts onto any
induced `O_d` for `d >= 3`**. This does not classify the
original 10-vertex graphs as convergent, and does not exclude
retractions at later iterates or onto other targets.

In particular, McKay index **11651780** (`IEnb~jl|o`)
has a third pared iterate of order 27 with an induced `O_8`,
yet none of its induced octahedra is a retraction target.
The 33-member same-pared-third-iterate class represented by
McKay **7002338** also has no induced octahedral retract
at that level. All exact computation scripts, per-graph
counts, and the eight GitHub artifact JSON files are preserved
in an accompanying downloadable research bundle.

## Reproduction of the pycliques screen

With `networkx==3.6.1` and the pinned `pycliques-project`
installed from the pinned SHA:

```sh
python research/order10_nonlocal_oct_stiff_v1/sweep.py plan \
  --shard 0 --shards 8
python research/order10_nonlocal_oct_stiff_v1/sweep.py run \
  --shard 0 --shards 8 --limit 0 --max-depth 3 --bound 450 \
  --dimensions 3,4,5,6,8,10 --restarts 160 --states 1200 \
  --timeout-sec 8 --output /tmp/order10-oct-shard0.json
python research/order10_nonlocal_oct_stiff_v1/sweep.py verify \
  --input-results /tmp/order10-oct-shard0.json
```

`limit=0` means the entire shard; all eight shards cover all
1,043 cases. Each positive record, if any, stores the original
graph6, constructed host graph6, antipodal pairs, and complete
retraction map for independently replayable verification.

**No updated indeterminate list is justified by these negative
search outcomes.** A new classification version requires
independently certified positive proof witnesses.
