# Connected graph clique-behavior census

This repository classifies **connected, unlabeled, simple graphs** through
order 10. All classifications use a pinned revision of the Python monorepo
[`pycliques-project`](https://github.com/rvf0068/pycliques-project).
The earlier pre-clockwork-fix experiment is retained in Git history; the
current stage framework uses clean, stable directories.

## Codespaces commands

Start once by checking the existing baseline (all connected graphs through
8 vertices, with the **snub disphenoid as the only indeterminate graph**):

```bash
bash scripts/stage.sh baseline
```

Then execute each desired stage with a single command:

| Order | Command | Work performed |
|:--|:--|:--|
| 9 | `bash scripts/stage.sh 9 initial` | Classify all 261,080 connected graphs, bound 30 |
| 9 | `bash scripts/stage.sh 9 c10` | On non-conjecturally-indeterminate inputs, check whether K(G) retracts to the complement of C10 |
| 9 | `bash scripts/stage.sh 9 bound60` | Rerun the usual classifier with bound 60 only on still-indeterminate graphs not conjectured divergent |
| 9 | `bash scripts/stage.sh 9 bound70` | Classify only the 9-vertex cases still indeterminate and not conjectured divergent at bound 70; rebuild the conjectured surface-reference file |
| 10 | `bash scripts/stage.sh 10 initial` | Classify all 11,716,571 connected graphs, bound 30, using the registered order-9 surfaces |
| 10 | `bash scripts/stage.sh 10 c10` | Check K(G) retraction to the complement of C10 on still-indeterminate graphs excluding conjecturally divergent |
| 10 | `bash scripts/stage.sh 10 homotopy` | Compute the homotopy type of **G only**, for still-indeterminate graphs that are **not conjecture-dependent** and whose completely pared graph has **exactly ten vertices** |
| 10 | `bash scripts/stage.sh 10 bound70` | Run the usual classifier at bound 70 **only** for graphs selected by the restricted order-10 homotopy stage whose `pycombtop` verdict is exact and contractible or a wedge of circles |


Run the stages for each order in order. The 10-vertex initial stage requires
the final order-9 surface reference file refreshed automatically by stage `9 bound70`.

The initial census uses **10,000 graphs per batch for order 9** and
**100,000 per batch for order 10**. A run started with a different batch
size cannot be resumed in the same directory: its manifest guards against
mixed settings. For a fresh order-10 run after an earlier 5,000-graph-batch
attempt, remove only `runs/order10/initial/` before launching the stage again.
The final partial order-10 batch contains fewer than 100,000 graphs.

Each command is repeatable: an interrupted initial run skips completed
batches; an interrupted later stage skips completed graph records. Do not
change the pinned upstream revision while resuming an **incomplete stage**.

### Updating pycliques-project between stages

The initial census and every completed post-stage are historical, immutable
inputs. Their manifests retain the exact `pycliques-project` revision used
for those computations. A **new** post-stage may use a newer revision:
`scripts/staged.py` validates each historical stage against its own saved
manifest rather than requiring its revision to match today's installed code.
The new stage records its own revision, the initial summary checksum, and the
checksums of prerequisite-stage summaries.

For example, once `10 initial` and `10 c10` are completed and committed:

```bash
bash scripts/update_pycliques.sh
bash scripts/stage.sh 10 homotopy
bash scripts/stage.sh 10 bound70
```

Commit the changed `config/pycliques_commit.txt` along with the new-stage
results. **Do not rerun an old stage** after changing the pin: its existing
manifest will reject the new inputs, intentionally. Do not update the pin
during a partially completed stage. The updated homotopy and bound-70 stages
operate only on non-conjectural still-indeterminate graphs with completely
pared order ten, without recomputing the initial classifications or the
completed C10 retraction stage.

The initial census runner still forbids changing versions or parameters in
an existing initial-run directory. Its configuration and the historic
results are never rewritten by an upgrade.

## Working results and detailed records

The working clique-behavior files at the repository root are:

- [`indeterminate_order_9.txt`](indeterminate_order_9.txt)
- [`indeterminate_order_10.txt`](indeterminate_order_10.txt)

They are automatically updated following each completed stage or partially
completed post-stage run. Their six columns are the original graph
index, pared order, pared graph6, certificate rule, target status, and target
label. Conditional references stay listed until an independent proof
classifies them. Incomplete computations do not count as proofs of convergence
or divergence.

The order-10 homotopy stage additionally generates **`homotopy_order_10.tsv`**
at the repository root. One row per completed eligible graph reports its
original source index, original graph6, pared graph6, exactness and limit
flags, a readable **certified** homotopy type when available, sphere
multiplicities as JSON, the underlying `pycombtop` verdict, and the reason.
Inexact results are explicitly marked `not certified`; their Betti numbers
are not misrepresented as homotopy types. The table uses tab separators
and proper quoting for reasons containing tabs or newlines.

The normal `bash scripts/stage.sh 10 homotopy` command regenerates this TSV
on exit, including after normal interruption. Only completed JSON records
appear in a partial export; resume the same command to fill the remaining
rows. After an abrupt interruption or to rebuild it from saved records
without recomputation, run:

```bash
.venv/bin/python scripts/export_homotopy.py
```

The TSV is a derived convenience file: the authoritative records remain in
`runs/order10/homotopy/records/`.

Each stage has a stable directory with a manifest, per-graph data, and
a summary:

```text
runs/
  baseline-through8-bound30/    # previously validated baseline
  order9/
    initial/
    c10/
    bound60/
    bound70/
  order10/
    initial/
    c10/
    homotopy/
    bound70/
```

Initial census verdicts are immutable: post-stages write new records rather
than overwriting prior results. All records use **original** source indices and
original graph6 for recomputation. The c10 stage stores independently
verified retraction maps. The homotopy stage examines only non-conjectural graphs whose completely
pared graph has order ten (no dominated vertices) and whose behavior remains
indeterminate after the C10 stage. Graphs pared to smaller orders, conjecture-
dependent cases, and graphs classified by C10 are excluded. It stores
`is_exact`, `is_limited`, the stated type, and the reason from `pycombtop`.
A Betti-only result is not accepted as a wedge-of-spheres or contractibility
certificate.

The final order-9 bound-70 stage regenerates
[`config/conjectured_surfaces_order9.tsv`](config/conjectured_surfaces_order9.tsv)
listing the remaining original nine-vertex graphs satisfying
`pycliques.surfaces.is_surface`, with graph6 labels. For the order-10
classifier these are loaded using
`register_reference_graph(graph, status=ReferenceStatus.CONJECTURED, label=graph6)`.
They are never silently treated as proven divergent. A surface classified at
bound 70 is removed from the conjectural reference file, which is pinned by
its checksum in the order-10 initial manifest.

Order 10 uses a **selective** bound-70 stage only after the homotopy
analysis. It continues to require completely pared order ten, excludes
conjecturally divergent graphs, and admits only
`pycombtop` verdicts marked **exact**, **not limited**, with either an empty
wedge (contractible) or exclusively positive-dimensionality-one sphere
multiplicities (wedges of circles). Betti-only or limited outputs never
qualify. The stage does **not** reclassify all order-10 graphs.

## Save progress

Review results before committing. The new stages do **not** automatically
push to GitHub. For example:

```bash
git add runs/order9/ indeterminate_order_9.txt config/conjectured_surfaces_order9.tsv
git commit -m "Record staged order-9 classification"
git push
```

For order 10, replace `order9` and `indeterminate_order_9.txt` with
`order10` and `indeterminate_order_10.txt`. Some stage paths will not yet
exist; use `git add -A` selectively after inspecting `git status`.
Review `history/bash_history` before committing: interactive shell history
may contain sensitive commands or credentials.

## Provenance and reproducibility

`scripts/stage.sh` is the normal entry point.
`scripts/run_census.sh` remains the low-level initial runner.
`scripts/staged.py` implements the selective stages and maintains the working
indeterminate lists. Each stage records a manifest and uses atomic
per-graph files. `pycliques-project` is pinned by
`config/pycliques_commit.txt`; updating it creates a new experiment rather
than reinterpreting old results.

The original order-9 bound-30 run with a mid-run clockwork fix and its
migration records remains available in the repository's earlier commits,
but is not the source of the new staged census.
