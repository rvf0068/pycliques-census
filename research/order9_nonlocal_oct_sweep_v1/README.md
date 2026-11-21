# Read-only bounded octahedral sweep for 13 remaining nine-vertex graphs

This research postpass uses the **existing, unmodified** public
`pycliques` implementation (nonlocal induced-octahedron search and fixed
target retraction solver). It does not mutate the current census or any
historical record. Run in a Python environment where the current
`pycliques-project` package is installed.

```sh
python research/order9_nonlocal_oct_sweep_v1/sweep.py plan
python research/order9_nonlocal_oct_sweep_v1/sweep.py run \
  --max-depth 4 --bound 1600 --dimensions 4,5,6,8,10,12 \
  --restarts 150 --states 2000 --timeout-sec 90 \
  --output /tmp/order9-octahedral-sweep.json
python research/order9_nonlocal_oct_sweep_v1/sweep.py verify \
  --input-results /tmp/order9-octahedral-sweep.json
```

Each case runs in a separate time-limited subprocess. The searches at
each selected pared iterate use a deterministic seed derived from its
McKay index, iterate depth, and target dimension. A retraction is accepted
only after `verify_retraction_witness` checks the full map. Positive
records store their graph6-labeled host, all antipodal pairs and all image
vertices so the exact proof can be replayed; `verify` reconstructs
each iterate afresh and rechecks that map.

The report statuses **INCONCLUSIVE**, **TIMEOUT**, **ITERATE_BOUND**, and
**ERROR** do not mean non-divergence. A candidate induced octahedron
alone is not enough. The high-order graphs may require substantially
more time or better seeds, particularly McKay 260910.

An additional small-budget GitHub Actions research run is available as
an artifact for reproducibility; it is not itself a new census version.
