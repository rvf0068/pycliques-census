# Positive-only octahedral search for stiff order-ten cores

This experiment is intentionally limited to the **1,043 unconditional stiff
order-10** entries (`pared_order=10`, `- - -`) in the immutable v11
snapshot (`indeterminate_order_10_v11.txt`). The exact Git blob is pinned
in `sweep.py`, and all McKay indices must be unique and increasing.
It does **not** silently reclassify the 120 cases conditional on
`HCZTf\\}` or any nine-vertex-pared cores.

The search reconstructs the source's dominated-vertex-pared clique iterates
through depth three with bounded maximal-clique enumeration, uses
`pycliques.find_induced_octahedron_amplified` for dimensions
3,4,5,6,8,10 and separately checks
`pycliques.find_octahedral_retraction`. Only the complete map checked
by `pycliques.verify_retraction_witness` is a proof. Every positive
retains the source graph6, reconstructed host graph6, antipodal pairs,
and the complete retraction map. The independent `verify` command
reconstructs the host and rechecks the graph retraction.

`INCONCLUSIVE`, `ITERATE_BOUND` and `TIMEOUT` are **not** proofs of
non-divergence or absence of octahedral retracts. Individual cases run
in separately timeboxed child processes; errors are explicit, not silently
converted into negative results. The script uses the existing pycliques
package, pinned to commit `7ae36ffe67fb2e9bbafc68e97347aabcf757c2dc`
in the GitHub Actions job. This changes **no** code in pycliques-project,
nor any existing census index, report, or proof archive.

## First pilot: 192 of 1043 cores

Eight shards search 24 cases each, chosen by index-striding (shard
`i` takes `entries()[i::8][:24]`). This is a pilot, **not**
a full-census sweep. Artifacts contain all records, and the CI log
prints `SEARCH_SUMMARY` with any complete positive certificates.
A manual `workflow_dispatch` run with input `limit=0` processes
all 1,043 cases, with the same bounded per-case budgets.

## Local reproduction

```sh
python research/order10_nonlocal_oct_stiff_v1/sweep.py plan --shard 0 --shards 8 --limit 24
python research/order10_nonlocal_oct_stiff_v1/sweep.py run \
  --shard 0 --shards 8 --limit 24 --max-depth 3 --bound 450 \
  --dimensions 3,4,5,6,8,10 --restarts 160 --states 1200 \
  --timeout-sec 8 --output /tmp/order10-oct-shard0.json
python research/order10_nonlocal_oct_stiff_v1/sweep.py verify \
  --input-results /tmp/order10-oct-shard0.json
```

No v12 reclassification is warranted unless new positives appear
and an independent proof replay is archived and verified.
