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
| 10 | `bash scripts/stage.sh 10 s1divergence` | On the **282** exactly-`S^1` graphs, look for divergent clockwork reductions of `K²(G)` or `K³(G)`, then search for the verified triangular-cover/clockwork-pair certificate |
| 10 | `bash scripts/stage.sh 10 bound70` | Run the usual classifier at bound 70 **only** for the eligible exact contractible/circle-wedge cases not already proved divergent by `s1divergence` |
| 10 | `bash scripts/stage.sh 10 bound120` | Reclassify at bound 120 **only** the six eligible cases left `INDETERMINATE` by the completed bound-70 stage |
| 10 | `bash scripts/stage.sh 10 easycovers` | Independently verify finite double-cover divergence certificates for the remaining easy-homotopy cases |
| 10 | `bash scripts/stage.sh 10 bound120-timeboxed` | One five-graph batch of remaining **original** ten-vertex, dominated-vertex-free graphs, including conjecture-dependent ones, with 600-second per-graph wall-clock limits |
| 10 | `bash scripts/stage.sh 10 bound120-timeboxed-v2` | Restart the same 2,742-graph cohort at bound 120 with optimized octahedra and first-retraction search, checking the four proven divergent targets on both pared `G` and pared `K(G)` |


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
bash scripts/stage.sh 10 s1divergence
bash scripts/stage.sh 10 bound70
bash scripts/stage.sh 10 bound120
bash scripts/stage.sh 10 easycovers
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
    s1divergence/
    bound70/
    bound120/
    easycovers/
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

The new order-10 `s1divergence` stage has its own manifest and atomic per-graph
records. It selects only the 282 original ten-vertex graphs for which the
certified `homotopy` verdict is **exactly one** `S^1` (not a wedge of two
circles, nor `S^1` with any other sphere). Already retraction-certified or
conjecture-dependent graphs and those with smaller completely pared order
remain excluded. The stage checks `K^2(G)` and `K^3(G)` for *divergent*
clockwork structure (a merely induced clockwork subgraph is not a proof),
then searches connected triangular double covers and admissible
coaffine-clockwork-pair morphisms, as in the verified example
`IEjdnpy^O` (original index 11628670). Both checks have explicit
resource budgets. A negative result or a resource limit is recorded as
`INDETERMINATE`, never as proof of convergence.

A `DIVERGENT` record includes a replayable JSON certificate and is
accepted only after independent verification with the upstream theorem
checkers. Run `.venv/bin/python scripts/verify_s1_divergence.py` to
independently replay every positive certificate after the stage. Successfully
proved divergent graphs disappear from root `indeterminate_order_10.txt`;
**all 2,126 original homotopy records and `homotopy_order_10.tsv` remain
unchanged**, including any subsequently proved divergent cases.
The selective bound-70 stage uses these positives as exclusions. Do not
change `pycliques-project` while this stage is incomplete.

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
conjecturally divergent graphs **and graphs now certified divergent by
`s1divergence`**, and admits only
`pycombtop` verdicts marked **exact**, **not limited**, with either an empty
wedge (contractible) or exclusively positive-dimensionality-one sphere
multiplicities (wedges of circles). Betti-only or limited outputs never
qualify. The stage does **not** reclassify all order-10 graphs.

The separate order-10 `bound120` stage continues **only** the six exact
contractible/circle-wedge cases recorded `INDETERMINATE` by the completed
`bound70` stage. It uses the unchanged `classify_clique_behavior` classifier
with `bound=120` and its default iteration limit (completely pared iterates).
Its cohort is derived from prior immutable records, not a hand-maintained
index list. The run refuses incomplete `bound70` results, records its own
manifest and per-graph verdicts, supports interruption/resumption, and
updates the root indeterminate file without altering earlier stages.

### Versioned restart: `10 bound120-timeboxed-v2`

The original `bound120-timeboxed` results remain immutable and are **not**
reinterpreted with the new upstream code. The new v2 stage deliberately
restarts from batch zero and rechecks **every** original ten-vertex graph
without a dominated vertex which was unresolved before the timeboxed stages,
including all conjecture-dependent references. It uses the same cohort
selection as v1, explicitly excluding v1 and v2 results from selection so
that no existing graph is skipped just because it was examined already.

The new pinned `pycliques-project` revision makes three changes:

1. Replace the special-octahedron auxiliary-nonedge-graph clique enumeration
   by the equivalent maximal-clique/antipode backtracking criterion.
2. Make the first-witness `retracts` decision avoid eagerly listing
   automorphisms of the entire host. The full retraction generator is retained.
3. Check retractions to the suspensions of `C5`, `C6`, `C7` and the
   complement of `C8` on **only** the completely pared original `G0` and
   its first completely pared clique iterate `G1`, before the expensive
   special-octahedron test. No later iterates are used for these four
   retraction targets.

The stage retains five graphs per batch, 120-clique bound, 600-second
wall-clock limit per graph, 6144-MiB process memory cap, process isolation,
diagnostic journaling, atomic per-graph JSON results and deterministic
manifests. Each v2 result includes `retraction_depth=2` and names the
`G0` or `G1` target in its method trace.

```bash
cd /workspaces/pycliques-census
git pull --ff-only
bash scripts/bootstrap.sh
# Run all remaining batches in sequence (resumes automatically):
bash scripts/stage.sh 10 bound120-timeboxed-v2

# Optional: run exactly one next batch, or a zero-based batch index:
bash scripts/stage.sh 10 bound120-timeboxed-v2 next
bash scripts/stage.sh 10 bound120-timeboxed-v2 1
```

By default v2 continues across batches, stopping only when all graphs are
processed, a classification/stage error occurs, or the user interrupts it
with Ctrl+C. Each graph record is saved atomically, so starting the same
command again resumes the earliest unfinished graph, including a partial
five-graph batch. The launcher's shell file is not included in the stage
manifest's implementation hashes: this orchestration-only change preserves
the validity of already committed records. An explicit `next` or numeric
batch index still processes a single batch for debugging.

The old records are under `runs/order10/bound120-timeboxed/`; the new ones
are under `runs/order10/bound120-timeboxed-v2/`. Both stages can be audited
independently. A v2 definitive verdict updates the aggregate indeterminate
file, but never changes historical stage records. On no account should the
old timeboxed stage be resumed under the new upstream revision.

### Bounded-time order-10 continuation (all homotopy types)

After committing `10 easycovers`, continue with a **new, independent**
`bound120-timeboxed` stage. Its inputs are the surviving original order-10
graphs, **including conjecture-dependent cases** but **excluding every
original graph containing a dominated vertex** (checked using
`pycliques.dominated.find_dominated_vertex`, not simply the saved
pared-order field).

```bash
# Process the next batch of five (repeat this command for each batch)
bash scripts/stage.sh 10 bound120-timeboxed

# Or specify the zero-based batch index explicitly:
bash scripts/stage.sh 10 bound120-timeboxed 3
```

The bound is **120**, the standard classifier iteration limit is unchanged,
and each graph receives at most **600 seconds of wall-clock time** in an
independent worker process. The worker is also limited to **6144 MiB virtual
memory** under Linux. When a worker times out, its whole process group is
killed and it is recorded as `TIMEOUT` rather than inferred divergent or
convergent. Other non-proofs are recorded as `INDETERMINATE`,
`BOUND_EXCEEDED` or `ERROR`.

Because the regular classifier can return immediately on a conjectured
reference or retract, this stage's **isolated worker** temporarily removes
conjectured references from the registry while retaining *proved*
references. This makes the classifier pursue its theorem-backed rules
instead of stopping at an unproved conjecture; the original code and
global reference registry are unchanged outside that worker. Definite
positive results must not depend on conjectured references.

### Timeboxed diagnostic records (new batches)

New timeboxed JSON records contain `iterates`, a compact sequence indexed
by **iteration number** (`index=0` for the original pared graph). For each
completed step the record includes the raw clique graph's `raw_order` and
`raw_edges`, and the *completely pared* iterate's `pared_order` and
`pared_edges`. If a clique-graph construction exceeded bound 120 or was
interrupted, its entry records that state rather than claiming completion.

The `methods_tried` array records attempted root-level classification rules
(clockwork, clique-Helly, special octahedra, retractions and other applicable
inference rules). Each entry gives an outcome such as `no_certificate`,
`CONVERGENT`, or `DIVERGENT`. An unfinished method has the explicit
`interrupted` outcome, **not** a failed mathematical claim;
`in_progress_method` records where the timeout occurred. The worker writes
the progress journal **during** classification, flushed to disk at each
event, so the supervisor can include it even for `TIMEOUT` or `ERROR`.

For example, a record may include:

```json
{
  "iterates": [
    {"index": 0, "pared_order": 10, "pared_edges": 25},
    {"index": 1, "raw_order": 15, "raw_edges": 60,
     "pared_order": 15, "pared_edges": 60, "status": "completed"}
  ],
  "methods_tried": [
    {"method": "clockwork", "outcome": "no_certificate", "seconds": 0.01},
    {"method": "local_bridge_contraction", "outcome": "interrupted"}
  ],
  "in_progress_method": "local_bridge_contraction"
}
```

These data are **diagnostic observations**, not proof certificates. Earlier
JSON records stay unchanged and cannot retroactively recover events that
were never logged. The original timeboxed stage's manifest is retained
when resuming after this logging-only improvement. The runner checks that
its original code hashes match the Git commit introducing the stage
(`2f58cf3`), and that the selected indices, upstream revision, preceding
stage checksums, clique bound, batch size, timeout and memory limits are
unchanged. Each new record includes its own implementation checksums.

The stage is resumable: the **first incomplete five-graph batch** is
selected automatically, and completed per-graph JSON records are not
recomputed. Every batch has an atomic summary in
`runs/order10/bound120-timeboxed/batches/`; progress is in
`progress.json`, with a final `summary.json` only when the entire
eligible cohort finishes. The manifest freezes eligible original indices,
the exact upstream revision, dependency-stage summary hashes, script
hashes, bound, batch size, timeout and memory limit. An attempted resume
with changed settings or inputs is rejected rather than mixing evidence.
A Linux file lock prevents concurrent processes claiming the same batch.

Save the `runs/order10/bound120-timeboxed/` results and refreshed
`indeterminate_order_10.txt` after reviewing each batch. The initial
census and all earlier post-stage records are left unchanged.

### Certified triangular double covers

After order-10 `bound120`, run:

```bash
git pull --ff-only
bash scripts/stage.sh 10 easycovers
.venv/bin/python scripts/verify_easycovers.py
```

This stage is limited to the still-indeterminate order-10 graphs with
certified contractible or circle-wedge homotopy type, and fully pared
order 10. The cohort comes from the **completed** `bound120` records,
not hand-coded source indices. The stage never overwrites earlier records,
resumes from atomic JSON results, and records the pinned monorepo revision
and SHA-256 hashes of both the witness registry and the verifier.

The finite, independently replayable witnesses are in
[`postpasses/easy_cover_witnesses.json`](postpasses/easy_cover_witnesses.json).
The reusable checker is
[`postpasses/easy_cover_certificates.py`](postpasses/easy_cover_certificates.py).
It verifies connected triangular two-sheeted voltage covers, optional
deletions of edges in no triangle, and one of two theorem-backed criteria:

- A completely pared clique iterate is isomorphic to a clockwork graph
  independently verified to have a good segment (and hence be divergent).
- An explicitly recorded equivariant graph morphism
  `R_(2m)^n -> K^d(cover)`, with `m >= 2`, whose source and target
  automorphisms satisfy the required coaffinity radius `m+1`.
  The morphism need **not** be induced.

The first route is applied to `ICxvExyl_` after deleting its unique
non-triangle edge. The second certifies `IEhuVquZ_` using a
4-coaffine embedding of `R_6^0` in the second clique iterate of a
double cover. The verification re-computes all relevant clique graphs
from the source graph6; a graph6 name or registry entry alone proves
nothing. Existing theorems on nontriangle-edge deletion, dominated
vertices, triangular covers, clockwork divergence and coaffine
graph relations supply the mathematical implications.

**Scope:** This is a certificate-replay stage, not a general exhaustive
cover or morphism discovery search. The checker accepts witnesses for
other graphs without modification; finding such a witness is a separate
task. Failure or a missing witness must remain `INDETERMINATE`.

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

### Future-only v3 witness records and diagnostics (not a census stage yet)

The files `scripts/certificate_records_v3.py`, `scripts/timeboxed_trace_v3.py`
and `scripts/inspect_certificates_v3.py` provide the implementation for a
**future, separately versioned** stage. They do not alter the original timeboxed
stage, its frozen manifests, the existing graph records, or the historical
`config/pycliques_commit.txt` pin. A new stage must have its **own** directory,
manifest, source-hash provenance, worker and dependency revision before any
population-wide run.

The v3 JSON certificate representation contains graph6 encodings of the
original and the certified pared iterate, its iterate index, and an independently
checkable witness (special octahedron's clique/antipode indices or a retraction's
projection/inclusion arrays). For Helly convergence it stores the exact
certified iterate, which is checked for clique-Helly. Vertex-indexed arrays
avoid unportable serialized representations of clique-graph node objects.

`verify_record(record, verify_iterate=False)` checks a stored local witness
without running the search that discovered it. With `verify_iterate=True`
it also recomputes the pared clique sequence from the original graph, checks
the claimed iterate up to graph isomorphism, and validates its property.
Both steps are **positive checks only**: interrupted computations or
unsupported certificate rules are explicitly `not_serialized`; neither is
silently promoted into a proven result. A chain replay can be expensive and
may require its own resource limit, separate from the production search.

Version-3 tracing wraps named criteria such as `clique_helly`,
`fixed_target_retraction`, `special_octahedron_test`,
`special_octahedron_witness` and the structural reduction rules. Unlike the
historical v2 tracer, it never assigns meaning to callback positions in
`_default_classifiers`. The trace retains completed/unfinished method
durations and exact pared-iterate provenance.

The separate workflow `.github/workflows/certificate-v3.yml` installs an
explicit witness-capable `pycliques-project` revision into a **different**
development environment and tests record replay and tracing. For example,
with that environment activated:

```bash
python scripts/inspect_certificates_v3.py 'ICvbvy}|g' --verify-chain
```

These utilities are not a substitute for a new batch runner, a new stage
manifest, and an explicit user-approved census restart. Historical results
must continue to use the revision recorded in their own manifests.

