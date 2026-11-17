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
projection/inclusion arrays). A retraction is accepted as an independent
**divergence** certificate only when its target is verified isomorphic to one
of the explicitly proven reference graphs (octahedron, suspensions of
`C5`, `C6`, `C7`, or complement of `C8`). Other retractions must attach a
separate verifiable target proof in a future schema and remain
`not_serialized` here. For Helly convergence it stores the exact
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


## Local v3 benchmark: 153 unresolved graphs without an S² summand

This new stage is designed for an Ubuntu computer with about 7.4 GiB of RAM.
It selects the **153** still-unresolved original order-10 graphs whose
certified homotopy types are `S^1` (115), `S^3` (35), or
`S^1 wedge S^3` (3), via the frozen
[`config/homotopy_no_s2_order10.tsv`](config/homotopy_no_s2_order10.tsv)
index. The selection was cross-checked by an independent exact mod-2
second-homology computation on each completely pared graph; homology alone
is *not* used to certify an arbitrary homotopy type.

**Do not run or modify any historical census stage.** The original
`config/pycliques_commit.txt`, `scripts/staged.py`, and
`runs/order10/bound120-timeboxed-v2/` remain untouched. V3 uses an
**independent uv environment** with its own commit pin at
`config/pycliques_commit_v3.txt`:

```bash
cd ~/Python/pycliques-census
git pull --ff-only
bash scripts/bootstrap_v3.sh
bash scripts/stage.sh 10 bound120-timeboxed-v3 plan
```

The setup places the v3 dependency in `.deps/pycliques-project-v3`,
with a `.venv-v3` symlink to its uv-managed environment. Your historical
`.venv` remains available, and you do **not** need to deactivate it:
the v3 launcher selects `.venv-v3/bin/python` explicitly.

The benchmark has a **fixed clique bound of 120**, a **120-second wall-clock
timeout**, a **2,048 MiB Linux virtual-memory limit per worker**, **one
worker at a time**, and **five graphs per batch** (31 batches). Each graph
has an atomic JSON checkpoint and a timestamped method/iterate diagnostic
trace; interrupted or resource-limited runs are not classified as
mathematical convergence or divergence.

Start with one five-graph batch:

```bash
bash scripts/stage.sh 10 bound120-timeboxed-v3 next
```

Repeat `next` to resume where you stopped. After checking the initial
results, run all remaining batches with:

```bash
bash scripts/stage.sh 10 bound120-timeboxed-v3 all
```

For one zero-based batch index, replace `next` with `0`, `1`, etc.
For long local sessions, use `tmux` and prevent automatic suspend.

The stage writes frozen metadata to
`runs/order10/bound120-timeboxed-v3/manifest.json`, results under
`records/`, per-batch files under `batches/`, a partial
`progress.json`, and a final `summary.json` when every graph is processed.
It also writes **`indeterminate_order_10_v3.txt`**, removing only
independently replayed positive v3 results from the prior 8,648-graph
working list. The original `indeterminate_order_10.txt` is deliberately
not modified, since its historical manifest checksums must remain valid.

The certificate serializer replays special-octahedron, explicitly proven
retraction targets, and eventual clique-Helly witnesses. Positive
classification indications with no portable witness are recorded as
`INDETERMINATE`, with the upstream verdict retained for diagnosis.
`TIMEOUT`, `BOUND_EXCEEDED`, and `ERROR` are likewise **not proofs**.
Once a stage has started, do not change its code, upstream pin, cohort,
or resource limits. For any different limits, start a separate versioned
experiment with a new stage directory.

Audit all positive results by reconstructing their entire clique-iterate
chains:

```bash
bash scripts/stage.sh 10 bound120-timeboxed-v3 verify
```

Review and commit deliberately after a batch:

```bash
git status --short
git add runs/order10/bound120-timeboxed-v3/ indeterminate_order_10_v3.txt
git commit -m "Record local v3 clique-behavior benchmark"
git push
```

If `git status` shows unrelated files, review them before committing.


## Exact core-isomorphism index after order-10 v3

The completed order-10 v3 stage leaves 8,533 original graph indices
unresolved. Many have isomorphic completely pared cores. This independent,
read-only index selects the smallest original index as representative
of each isomorphism class. Graph6 strings are not canonical identifiers:
a structural fingerprint only reduces comparisons; every actual merge
is checked by NetworkX exact graph isomorphism.

No historical result, conjectural-reference status, homotopy certificate,
or previous-stage manifest is modified. No new clique-behavior verdict is
inferred. The original-source and post-v3 lists are checked against all
153 saved v3 statuses, but mathematical certificates must be replayed
separately with the v3 verify command.

From the repository root:

    .venv/bin/python scripts/core_isomorphism_index.py build
    .venv/bin/python scripts/core_isomorphism_index.py verify

Output is written under reports/order10_core_index_v1/:

- assignments.tsv: each active original index mapped to representative.
- classes.tsv: each representative, core graph6, and full member indices.
- summary.md: readable class-size distribution and biggest classes.
- manifest.json: SHA-256 checksums of source, implementation, and outputs.

A completed index is immutable: re-running build verifies it byte-for-byte,
and changed inputs require a new versioned output folder. The dedicated
GitHub Actions workflow also creates the full index and publishes an artifact.

After reviewing the output, commit it with:

    git add reports/order10_core_index_v1/
    git commit -m "Record order-10 post-v3 core-isomorphism index"
    git push origin main

Always use SSH rather than HTTPS for fresh GitHub clones and remotes,
for example git@github.com:rvf0068/pycliques-census.git.

## Core9 representative benchmark (new, independent stage)

The post-v3 exact isomorphism index contains **35 distinct completely pared
order-nine core classes**, representing 4,038 original order-10 graphs.
The new core9 benchmark computes **one nine-vertex representative per
class**, using the existing pinned v3 pycliques-project environment.

Inputs are frozen by the previously committed
reports/order10_core_index_v1/{classes.tsv,assignments.tsv,manifest.json}
and by hashes of the worker, runner, certificate and tracing implementations.
The runner regenerates the expected exact index in memory, verifies
the committed index byte-for-byte, and rejects changed dependencies or
parameters on resume. No previous run or working list is modified.

From the Lenovo checkout, after merging the PR:

    cd ~/Python/pycliques-census
    git switch main
    git pull --ff-only
    bash scripts/core9.sh plan
    bash scripts/core9.sh next

Check the first five representatives and their diagnoses. To continue:

    bash scripts/core9.sh all
    bash scripts/core9.sh verify

The stage runs five representatives per batch, one worker at a time;
the fixed limits are **120s**, **2 GiB virtual memory**, and
**clique bound 120** per core, with retraction depth two.
All statuses, elapsed time, peak resident memory (if available), last
root iterate and attempted criteria are written to
runs/order10/core9-benchmark-v1/. The generated report.md is a
readable summary. Execution can be interrupted and resumed.

Positive core certificates are serialized and independently replayed
against their precise nine-vertex representative, checking the full
clique-iterate chain. Unknown/conditional witnesses, timeouts, errors
and bound exceedances are **not proofs**. Conjectural reference graphs
are never used for positive classifications.

**Important:** the benchmark records conclusions about the pared cores
only. It does **not** automatically change the classification of the
original ten-vertex graphs or the 8,533-entry unresolved list.
Any later transfer of results to original members requires a separately
documented mathematical argument and validated source-to-core paring.

After verification, commit only the new stage:

    git add runs/order10/core9-benchmark-v1/
    git commit -m "Record 35 order-nine core benchmark results"
    git push origin main

All manually cloned GitHub repositories should use SSH.

## Historical order-9 cross-reference for the 35 order-9 pared cores

The 35 nine-vertex representatives in the post-v3 order-10 core index
can be matched against **all 261,080 connected nine-vertex graphs** from
the exact original McKay/pyg6data graph6 dataset. The new script
`scripts/core9_crossref.py` performs this match using a degree-sequence
prefilter followed by exact graph isomorphism (not graph6 text equality).

It then reads the original order-9 census chunks and every completed
historical order-9 stage (C10, bound 60 and bound 70), rather than
relying on the original or current unresolved list alone. It records
the first positive historical verdict, the stage, its stated rule/reason,
its precise source file, and whether the graph is in the final unresolved
list. A separate TSV lists only those cores still unresolved historically.

From the repository root, using the unchanged separately pinned
witness-capable v3 environment:

    bash scripts/bootstrap_v3.sh
    .venv-v3/bin/python scripts/core9_crossref.py build
    .venv-v3/bin/python scripts/core9_crossref.py verify

The new immutable output directory is
`reports/order10_core9_crossref_v1/` with `matches.tsv`,
`unclassified.tsv`, `summary.md`, and `manifest.json`.
The manifest hashes the compressed original 9-graph dataset,
frozen source files, later stage records, and all generated outputs.
Re-running build refuses to overwrite changed data.

**The cross-reference is read-only.** It does not edit any old census
stage, reclassify any original ten-vertex graph, or claim that a
historical verdict is a newly replayed certificate. In particular,
the four new positive core9 certificates were already historically
classified in the order-9 bound-60/70 stages; this tool makes such
duplication visible *before* running further experiments.

After verifying the cross-reference, optionally commit only its
newly generated directory:

    git add reports/order10_core9_crossref_v1/
    git commit -m "Record verified order-9 historical cross-reference"
    git push origin main

Keep manually cloned GitHub repositories on SSH remotes.

## Targeted structural investigation of the 29 unresolved nine-vertex cores

The frozen historical cross-reference confirms that only **29** of the 35
nine-vertex pared core classes remain unresolved (3,738 original order-10
graph members). The new `core9-structure-v1` stage inspects these cores,
not the already classified six. It is independent of all previous stages.

From the repository root with the separate pinned v3 environment:

    bash scripts/core9_structure.sh plan
    bash scripts/core9_structure.sh next
    bash scripts/core9_structure.sh all
    bash scripts/core9_structure.sh verify

Use `next` to do five representatives; `all` resumes the remaining
batches without repeating completed records. Results are under
`runs/order10/core9-structure-v1/` with per-core JSON records,
`progress.json`, an immutable manifest, `summary.json`, and a human
readable `report.md` when all 29 have been processed.

Every probe is a separate process with 45 seconds and 2 GiB virtual
memory limits. It reconstructs only the pared iterates genuinely
constructed by the original bound-120 core benchmark, comparing
their orders and edge counts against the saved traces. One core
(10760192) exceeds the bound at G3; all others at G4.

The stage saves the actual graph6 of each constructed iterate, exact
mod-2 first Betti numbers of its clique complex, triangle and degree
data, complement components, exact-or-capped maximal-clique counts
(up to 512, recorded explicitly as lower bounds if truncated),
and a bounded search for divergent induced clockwork subgraphs.
Induced clockworks and coaffinations are **observations**, not
proofs of divergence of the containing graph. A zero mod-2
first Betti number rules out connected triangular double covers
of that iterate, not all possible divergence methods.

No `CONVERGENT` or `DIVERGENT` verdict is issued by this stage.
It does not change historical classifications or certify any
of the original ten-vertex members. A `verify` command independently
recomputes the saved finite Betti and clique-count observations.

After examining the report and checking the result, commit only
the new versioned output directory:

    git add runs/order10/core9-structure-v1/
    git commit -m "Record targeted structural diagnostics for 29 nine-cores"
    git push origin main

## Targeted core9 follow-ups: covers, larger bound, and exact G2 matches

The frozen 29-core structural analysis permits three complementary follow-ups:

- Exactly eight completely pared nine-vertex cores have first Betti number
  1 over GF(2) in all computed iterates. Search the single nontrivial
  triangular double-cover class of their initial nine-vertex cores,
  with explicit clockwork-pair morphism/size/state limits.
- Exactly five cores whose last constructed iterate has at most 300
  maximal cliques receive a separate **350-clique-bound** classification
  attempt. Convergence/divergence is accepted only with a replayable
  v3 witness and full pinned clique-iteration-chain verification.
- Cores 4929602, 4972358, and 5645085 have exactly isomorphic
  pared second clique iterates; explicit vertex bijections are saved and
  independently verified. Thus all their subsequent pared iterates are
  isomorphic, even though their clique behavior remains unresolved.

These computations form the independent, immutable
`runs/order10/core9-followup-v1/` stage. Nothing in earlier stages
or in the original 10-vertex classification is changed.

After merging the PR, in the repository root:

    bash scripts/core9_followup.sh plan
    bash scripts/core9_followup.sh iso
    bash scripts/core9_followup.sh next
    bash scripts/core9_followup.sh all
    bash scripts/core9_followup.sh verify
    cat runs/order10/core9-followup-v1/report.md

`next` runs up to four pending cases; `all` resumes the rest. Each task
gets a separate worker with a 75-second wall clock and 2-GiB
address-space cap. Resource failures, negative results in a bounded
cover family, and exhausted clique bounds do **not** constitute
convergence or nondivergence proofs. A positive covering certificate
is serialized and checked by the published theorem verifier; a
positive larger-bound classification is replayed through the complete
pared iterate chain. The actual committed v3 pin and all source,
parameter, script and result hashes are recorded.

After verifying, commit only this new output directory:

    git add runs/order10/core9-followup-v1/
    git commit -m "Record verified targeted core9 follow-up experiments"
    git push origin main

## Three nine-vertex graphs retracting onto the snub disphenoid

Order-nine indices **232592, 233586, 244584** (respectively core
classes 4929602, 4972358, 5645085) have explicit graph retractions
onto induced eight-vertex snub disphenoid graphs (`GQyuzw`).
On all three original graph6 labelings the retraction is the identity
except vertex `2` maps to vertex `1`; these vertices are nonadjacent,
so this is not a dominated-vertex fold. Exact target isomorphisms and
the prior second-iterate isomorphism maps are independently checked in
`reports/order9_snub_retractions_v1/`.

    .venv/bin/python scripts/verify_order9_snub_retractions.py

This observation does **not** prove divergence of the snub disphenoid
or of the three retracting nine-vertex graphs, and does not classify
the 512 original ten-vertex graphs represented by their core classes.


## Post-PR14 coaffine-cover experiment on eight nine-vertex cores

This independent stage uses the improved `pycombtop` search from
`pycliques-project` commit
`005f6cc06a3bf1332bf6e729af73eea8ff26a40d`. It does **not**
change the historical v3 environment, pin, or previously committed results.

The 16 tasks compare two parameterized families for each of the eight
previously indeterminate nine-vertex completely pared core classes:

- **Baseline:** historical `m<=3,n=0`, source order at most 18,
  maximum 100,000 candidate assignments, now using the AC-3 solver.
- **Expanded:** `m<=4,n<=2`, source order at most 42,
  maximum 500,000 candidate assignments, using the same solver.
  Results record the actual eligible `(m,n)` pairs determined by the
  triangular double cover's deck radius. Nominal but ineligible sources
  are not counted as tested.

Both searches retain the original cover and clique graph size limits
and the unique connected triangular double cover's cohomology class.
Any found positive certificate is independently replayed. An
`EXHAUSTED` search covers only **this finite family**, not every
possible divergence mechanism or convergence behavior. None of the
core-only conclusions automatically transfers to the original
ten-vertex graphs.

From `pycliques-census`:

    bash scripts/bootstrap_core9cover_v2.sh
    bash scripts/core9cover_v2.sh plan
    bash scripts/core9cover_v2.sh next
    bash scripts/core9cover_v2.sh all
    bash scripts/core9cover_v2.sh verify
    bash scripts/core9cover_v2.sh replay
    cat runs/order10/core9-cover-ac3-v2/report.md

`next` runs four pending tasks, `all` resumes the rest, and
`replay` reruns the completed successful searches to corroborate
reported negative results as computations. Each task has a 90-second
wall-clock and 2-GiB address-space limit. Atomic records, a
byte-hashed immutable provenance manifest, summary, and readable report
appear under `runs/order10/core9-cover-ac3-v2/`.

After reviewing and verifying:

    git add runs/order10/core9-cover-ac3-v2/
    git commit -m "Record post-PR14 baseline and expanded core9 covering searches"
    git push origin main

## Covering investigation on the first two pared clique iterates (v1)

The eight nine-vertex cores with mod-2 first Betti number one in their
saved sequences are investigated further on **G1** and **G2**, where
`G1` and `G2` denote the *completely pared* iterates produced by
`pycliques.small.CliqueSequence`. These are not the raw iterates.
The new stage independently reconstructs them from the frozen initial
cores with the already merged, pinned post-PR14 code and checks exact
graph isomorphism against the saved graph6 for each.

Sixteen tasks (G1 and G2 for each of eight cores) use the unique connected
triangular double cover of each saved iterate. The source family uses
clockwork parameters `m=2..3`, `n=0..2`, source order at most 42,
actual deck-radius eligibility, an AC-3 coaffine-morphism search,
and explicitly bounded cover/clique graphs. Search workers have a
120-second wall-clock and 2-GiB address-space limit.

From the **pycliques-census repository root**, after merging the PR:

    bash scripts/bootstrap_core9cover_v2.sh
    bash scripts/core9iterate_v1.sh plan
    bash scripts/core9iterate_v1.sh next
    bash scripts/core9iterate_v1.sh all
    bash scripts/core9iterate_v1.sh verify
    bash scripts/core9iterate_v1.sh replay
    cat runs/order10/core9-cover-iterates-v1/report.md

`next` executes up to four pending tasks, `all` resumes all pending
batches, and `verify` rechecks saved records and independent positive
certificates. `replay` re-executes every completed successful or
exhausted search with the **same worker-level time and memory limits**.
A negative `EXHAUSTED` result applies only to the recorded finite
cover/clockwork family; it is not evidence of convergence. A verified
positive certificate is initially a conclusion about the *pared iterate*
alone. The stage does **not** automatically assign divergent status to
the original nine-vertex core or its represented ten-vertex members.

The stage is immutable by a manifest of source graph6, SHA-256 code and
upstream record hashes, pinned dependency SHA and search limits. It
preserves all previous `runs/` and `reports/` directories. After
reviewing the generated report and replay:

    git add runs/order10/core9-cover-iterates-v1/
    git commit -m "Record verified covering searches on pared G1/G2 cores"
    git push origin main

## Snub-disphenoid special-octahedron obstruction through K³

The snub disphenoid `S` is the eight-vertex graph `GQyuzw`,
whose clique complex is a triangulated sphere. The fundamental group
of the clique complex is preserved by the clique graph operator
(Larrión–Pizaña–Villarroel-Flores, *European Journal of
Combinatorics* 30 (2009), 288–294), so no new simply-connectivity
claim should be inferred from the density of its fourth iterate.

A distinct, exact finite computation verifies that **none** of
`S, K(S), K²(S), K³(S)` has a *special octahedron* in the sense of
`pycliques.retractions.find_special_octahedron_witness`. The checker
independently enumerates all maximal cliques, and for each clique either
finds an empty antipode domain or a pair of antipode domains with no
adjacent representatives. This is a complete negative certificate
**for those four finite graphs only**. The corresponding maximal-clique
counts are 12, 20, 56 and 1,076. At the third iterate, only four
of the 1,076 maximal cliques have all nonempty antipode domains, and
all four have a pairwise obstruction.

Run in the repository root:

    bash scripts/bootstrap_core9cover_v2.sh
    .venv-core9cover-v2/bin/python scripts/check_snub_special_octahedra.py
    .venv-core9cover-v2/bin/python -m unittest discover -s tests -p test_snub_special_octahedra.py -v

The program cross-checks with the separately implemented optimized
special-octahedron finder in the pinned `pycliques-project` library.
It also independently reconstructs and compares each clique iterate.
This is **not** a clique-divergence verdict for `S` or any core, nor
does it exclude a special octahedron in `K⁴(S)` or other divergent
mechanisms. The historical classification of the 29 unresolved cores
and all existing conjectural snub dependencies are unchanged.

## Homology filters and general retracts of the snub disphenoid (v1)

The new independent [snub retraction/homology report](reports/snub_retraction_homology_v1/report.md)
studies all *raw* clique iterates of the snub disphenoid through
`K³(S)`, looking for **arbitrary graph retractions**, not just special
octahedra, onto octahedra, suspensions of cycles, and complements of cycles.

Exact mod-2 homology eliminates most possible target dimensions before
search. In `K³(S)`, the computed low-dimensional Betti numbers vanish
in degrees 1, 2 and 3; this does **not** determine its homotopy type.

The remaining finite searches are exhaustive, with all negative
retraction conclusions replayable from the committed
`reports/snub_retraction_homology_v1/results.json`. Notably, `K³(S)`
has 2,128 induced `O_5` copies and no retractions onto them, no induced
`O_6`, 27,982 induced `C_14^c` copies and 20 induced `C_15^c`
copies, and no retractions onto those either. The complement's full
chordless-cycle enumeration excludes larger cycle-complement targets.

The result is **not** a proof of convergence or nondivergence, nor
does it classify the snub-dependent order-nine or order-ten cores.

    bash scripts/bootstrap_core9cover_v2.sh
    .venv-core9cover-v2/bin/python scripts/snub_retractions_homology_v1.py verify
    .venv-core9cover-v2/bin/python -m unittest discover -s tests -p test_snub_retractions_homology_v1.py -v

Only the new versioned research script, report, tests, and CI workflow
are modified in this investigation. Earlier stages remain immutable.

## General homology-guided targeted retractions (v1)

A separate, resumable postpass can now examine **all remaining order-nine
and order-ten indeterminate pared graphs** and their first three completely
pared clique iterates. Its general algorithms are in the pinned
`pycliques-project` monorepo; the census runner does no specialized
graph-theory search itself.

Crucially, exact reduced mod-2 Betti numbers are **computed once and
persisted** in `runs/orderN/targeted-retractions-v1/homology_cache/`.
They are automatically reused by every later search on the same encoded
graph. If full homology exceeds the configured face budget, a bounded
degree-3 attempt is made; if even that fails, the saved rank profile is
unknown. No missing Betti number is silently treated as zero.

Run from this repository root after merging the pinned monorepo change:

```bash
bash scripts/bootstrap_targeted_v1.sh
.venv-targeted-v1/bin/python scripts/targeted_retractions_v1.py plan --order 9
.venv-targeted-v1/bin/python scripts/targeted_retractions_v1.py next --order 9
.venv-targeted-v1/bin/python scripts/targeted_retractions_v1.py all --order 9
.venv-targeted-v1/bin/python scripts/targeted_retractions_v1.py verify --order 9
.venv-targeted-v1/bin/python scripts/targeted_retractions_v1.py plan --order 10
.venv-targeted-v1/bin/python scripts/targeted_retractions_v1.py next --order 10
```

The first `next` processes five records, with per-record timeout and
memory isolation. Use repeated `next` calls or `all` as appropriate.
Existing historical census records and conjectural snub dependencies are
never changed or automatically promoted to a proven verdict. A positive
ordinary graph retraction is independently replayed, and its scope is the
pared input or specific pared clique iterate in its stored record.

The stage freezes its source list, code hash, dependency pin, and search
limits on initial execution. Thus subsequent changes cannot accidentally
mix incompatible computations in the same output directory.


## Divergent-family targeted retractions (v2; correcting the cycle bound)

The versioned v1 stage is **frozen**: its 54 completed order-nine records
and earlier order-ten pilot results must remain unchanged. In particular,
order-ten graph **2318241**, on its first completely pared clique
iterate (16 vertices), has a genuine but irrelevant graph retraction onto
the **non-divergent** complement of a 6-cycle. The v1 search included
\(\overline{C_5}\), \(\overline{C_6}\), and \(\overline{C_7}\),
so its *first* positive witness could conceal a retraction onto a genuinely
divergent target.

The v2 driver pins the **merged pycliques-project PR #17** and therefore
only searches for cycle complements \(\overline{C_n}\) with \(n\geq8\).
Its existing octahedron and suspension target families are unchanged.
V2 uses its own environment, code file, source-and-code hash manifest,
and separate result directory. No v1 artifacts are adopted or rewritten.

From `pycliques-census` (for example on the Dell):

```bash
git pull --ff-only
bash scripts/bootstrap_targeted_v2.sh
.venv-targeted-v2/bin/python scripts/targeted_retractions_v2.py plan --order 10
time .venv-targeted-v2/bin/python scripts/targeted_retractions_v2.py next --order 10 --index 2318241
.venv-targeted-v2/bin/python scripts/targeted_retractions_v2.py verify --order 10
time .venv-targeted-v2/bin/python scripts/targeted_retractions_v2.py next --order 10 --batch-size 5
```

The `next --index` option is a **single-record, timeout-isolated** rerun
that skips a previously completed record in v2. It is invalid for
`plan`, `all`, and `verify`. Ordinary `next --batch-size N` processes
the next N pending inputs; `all` resumes any remaining inputs. The
per-worker limits remain 120 seconds and 2 GiB, with bounded clique
iterations and exact cached mod-2 homology. A completed worker may still
contain `LIMIT_REACHED` for a particular family; those results are not
exhaustive negative certificates.

The corrected one-off replay of index 2318241 in `pycliques-project`
also independently enumerates every chordless cycle in the complement
of the saved 16-vertex iterate: none has length 8 or larger, so the
divergent cycle-complement search is genuinely exhausted there.

The already committed order-nine v1 results need not be repeated: their
**negative/exhausted** cycle-complement outcomes included the larger
family \(n\geq8\). For order ten, v2 is a new investigation; its results
belong under `runs/order10/targeted-retractions-v2/` only.


## Deduplicated divergent-target census (v3)

The **v3 postpass** makes the existing order-ten v2 investigation more
efficient without editing, reclassifying, or replacing any original
record. Both v2 and v3 use the *same frozen pycliques-project commit*
(merged PR #17): only the census orchestration differs.

The frozen input contains **8,648 original indices** but **5,266 distinct
graph6 strings**. v3 stores one calculation per **identical graph6 string**,
with a deterministic map back to *all* corresponding original indices.
This is not an isomorphism-class cache: distinct graph6 encodings are never
implicitly identified.

Before any new searches, `import-v2` independently checks every completed
v2 record against its actual clique-iterate sequence, validates its homology
cache provenance, and replays positive retraction witnesses. Existing
v2 records for identical graph6 strings must agree (apart from their
original index); contradictory records make the importer fail closed.
The imported result and its exact homology-cache files are copied into a
**separate v3 results directory**, with a provenance fingerprint identifying
the original v2 record and manifest. The v2 data remain unchanged.

The deterministic v3 queue prioritizes distinct graph6 inputs whose
frozen source annotation is `-` (not already marked conjecturally
divergent), then processes the annotated conjectural-divergence group.
Results are stored under `runs/order10/targeted-retractions-v3/`.
Each new distinct graph6 input uses the same 120-second, 2-GiB isolated
worker and the same bounded search as v2.

From the `pycliques-census` root on the Dell, **after merging the v3 PR**:

```bash
git pull --ff-only
bash scripts/bootstrap_targeted_v3.sh
.venv-targeted-v3/bin/python scripts/targeted_retractions_v3.py import-v2
.venv-targeted-v3/bin/python scripts/targeted_retractions_v3.py plan
time nice -n 10 .venv-targeted-v3/bin/python scripts/targeted_retractions_v3.py next --batch-size 20
.venv-targeted-v3/bin/python scripts/targeted_retractions_v3.py verify
.venv-targeted-v3/bin/python scripts/targeted_retractions_v3.py report
```

`plan` distinguishes **completed distinct graph6 computations** from
**original input indices covered by those computations**, including exact
duplicates. `report` aggregates target-family statuses, induced target
candidates and CSP search states without counting duplicated indices
as new computations. A positive witness is stored once and can be
replayed independently on every identical graph6 input.

Run `import-v2` again if later v2 records are committed; the import is
idempotent and refuses incompatible provenance. `next` processes the
next N unique pending inputs in frozen priority order; `all` is resumable
but is not recommended for initial laptop pilots. A completed computation
may still contain `LIMIT_REACHED` for an individual target family.

The negative-search conclusion is restricted to the bounded target
families. The verifier independently reconstructs each clique-iterate
chain and verifies cached Betti metadata and positive witnesses; it does
*not* repeat all negative CSP searches. In particular, importing v2
preserves the original v2 computation provenance and its exact scope.


## Special-octahedron-first fourth-iterate postpass (v4)

The order-ten **v4** stage checks the completely pared clique iterates
(G, K(G), K^2(G), K^3(G)), i.e. **levels 0 through 3**. In contrast,
v3 only covered levels 0 through 2.

The search order at **each** level is mathematically important:

1. Find a **special octahedron** using the pinned
   `pycliques.retractions.find_special_octahedron_witness`. A positive
   certificate consists of a maximal host clique and its ordered opposite
   vertices. The independent verifier checks this witness using
   `verify_special_octahedron_witness`. By the established
   special-octahedron retraction theorem, such a certificate proves a
   retraction onto an `O_d` and thus divergence.
2. **Only if no special octahedron was found**, use the bounded retraction
   search on the three previously configured target families (octahedra,
   cycle suspensions and complements of cycles).
3. At levels 0, 1 and 2, v4 **reuses the corresponding existing v3
   retraction results** (rather than repeating the target search);
   this reuse is conditional on the full v3 iterate-chain, cache and
   witness verification. At level 3, the target-family search is new.
   Consequently, a nonspecial induced `O_d` may still yield a positive
   retraction witness even if the special-octahedron search is negative.

A special octahedron is **sufficient, not necessary**, for an octahedral
retraction. The special-octahedron search does not test merely for an
induced octahedron. Neither negative special searches nor the bounded
target-family results prove convergence.

V4 has its own frozen source/code/dependency manifest and a pinned
virtual environment. It **does not edit** v2 or v3. The v4 input cohort
is the set of **completed exact-graph6 v3 records** available at import
time. It currently prioritizes the distinct unclassified cores among
that cohort; the original index-to-graph6 aliases are preserved.

A completed v4 record may also report a `CLIQUE_BOUND_EXCEEDED` iterate
or `SKIPPED_HOST_ORDER_LIMIT` for the target search. The special
octahedron search is performed **before** applying the 80-vertex target
search limit, and can inspect pared hosts up to the 120-vertex clique
bound. The worker has a 180-second wall-clock and 2-GiB memory cap. A timeout is
**not** a negative result: a separate atomic `progress/` journal records
the last attempted level and search phase, copied into the terminal
record as `last_progress` and aggregated under `terminal_phases`.
These diagnostics cannot be interpreted as certificates. A timeout
is preserved as a terminal result under the frozen v4 budget; retrying
it with new budgets would require a separate versioned stage.

After merging v4, run in the census repository on the Dell:

```bash
git pull --ff-only
bash scripts/bootstrap_targeted_v4.sh
.venv-targeted-v4/bin/python scripts/targeted_retractions_v4.py import-v3
.venv-targeted-v4/bin/python scripts/targeted_retractions_v4.py plan
time nice -n 10 .venv-targeted-v4/bin/python \
  scripts/targeted_retractions_v4.py next --batch-size 1
.venv-targeted-v4/bin/python scripts/targeted_retractions_v4.py verify
.venv-targeted-v4/bin/python scripts/targeted_retractions_v4.py report
```

The `import-v3` action verifies all completed v3 source capsules and
records their SHA-256 fingerprints. These original source files and their
cached homology data are *read-only dependencies* of the new v4 records;
their modification or disappearance is detected during independent
verification. Running `import-v3` again can add newly completed v3
graphs, but refuses to silently replace previously imported data.
V4 reports distinct computations separately from original indices covered
and records positive special-octahedron proofs by their exact iterate
index. Do not launch a large batch before reviewing the first two K3
results, which may be significantly more expensive than v3.


## Fast special-octahedron-only K³ postpass (v5)

The v4 stage correctly discovers special-octahedron witnesses through
the **third pared clique iterate**, but even one graph may spend its
180-second worker budget on the *subsequent* K³ homology/retraction
search. In particular, the first v4 pilot, original index `5418647`
(graph6 `HCrlvhz`), timed out after the special tests completed.
This is **not** a negative retraction certificate.

The independent v5 stage **only checks special octahedra** and does
*not* compute homology or general retractions. Since a special octahedron
in a graph (X) implies that (X) retracts onto an octahedron (O_d),
each verified positive witness proves K-divergence. The reverse
implication is false: ordinary octahedral retractions may be nonspecial,
so a negative v5 result **does not prove non-divergence**.

For each **completed, independently verified v3 exact-graph6 record**
with **three fully computed pared levels**, v5 reuses the recorded
completely pared levels 0, 1, 2 and computes
only the missing completely pared (K^3(G)) from the saved level 2.
A v3 record can have top-level status `COMPLETED` while its clique
sequence ended early with `CLIQUE_BOUND_EXCEEDED` or a host-order limit.
Such records are **excluded from the v5 imported cohort** and explicitly
counted as `skipped_incomplete_v3_unique` and
`skipped_incomplete_v3_indices`; they are never treated as failed v5
calculations or negative special-octahedron searches.

It checks all four levels, stopping at the first positive
special-octahedron witness. Each positive record stores the maximal
clique and aligned antipodes, exact level, dimension and original
index, and `verify` reconstructs the relevant pared graph and replays
the witness with `verify_special_octahedron_witness`.
Negative results are scoped to the four checked graphs and are not
independently searched again during verification.

The stage uses the existing **120-clique bound**, a 120-second
per-worker limit and a 2-GiB memory cap. A clique-bound failure or
worker timeout is recorded explicitly, with an atomic phase diagnostic,
and must never be interpreted as negative evidence. No earlier files
or historical verdicts are modified. The deterministic queue prioritizes
unclassified graph6 inputs, then conjecturally divergent inputs.
Each finished distinct graph6 result covers every *exact* duplicate
original input index.

On the Dell, after merging the v5 PR:

```bash
cd ~/Python/pycliques-census
git pull --ff-only
bash scripts/bootstrap_special_k3_v5.sh
.venv-special-k3-v5/bin/python scripts/special_octahedra_k3_v5.py import-v3
.venv-special-k3-v5/bin/python scripts/special_octahedra_k3_v5.py plan

# Reproduce the graph that previously exhausted v4's 180-second budget:
time nice -n 10 .venv-special-k3-v5/bin/python \
  scripts/special_octahedra_k3_v5.py next --index 5418647

# Then run a small, resume-safe sample of distinct imported inputs:
time nice -n 10 .venv-special-k3-v5/bin/python \
  scripts/special_octahedra_k3_v5.py next --batch-size 20

.venv-special-k3-v5/bin/python scripts/special_octahedra_k3_v5.py verify
.venv-special-k3-v5/bin/python scripts/special_octahedra_k3_v5.py report
```

The current committed v3 population comprises 469 distinct cores,
representing 2,262 original indices. Running `import-v3` again
after additional verified v3 results are committed can expand the
v5 cohort without changing the frozen input list, code or parameters.
The `report` distinguishes certified divergence by first detected
iterate, exhaustive absence through K³, clique-bound failures,
timeouts and errors. Do not confuse completed distinct computations
with original indices covered by deduplication.


## Certified special-O4 divergence propagated to original order-10 graphs (core-lift v1)

The completed v5 special-octahedron sweep discovered **11 distinct positive
graph6 strings**, all at the third *completely pared* clique iterate, all
retracting onto `O_4`. The frozen
[post-v3 nine-vertex core index](reports/order10_core_index_v1/summary.md)
shows that these represent only **two nine-vertex isomorphism classes**:

| Core ID | Representative core graph6 | Original ten-vertex members | Directly positive in v5 | Additional via dismantling |
|---:|---|---:|---:|---:|
| 6938923 | `HEht}pl` | 23 | 4 | 19 |
| 6939350 | `HEht~bl` | 110 | 21 | 89 |
| **Total** | | **133** | **25** | **108** |

The separate, versioned
`scripts/special_octahedron_class_lift_v1.py` verifies the two
positive core classes and **all 133 original members**, not just the
25 original indices with exact graph6 matches to v5 positives.
For each member, it reconstructs the **original ten-vertex graph**
from the frozen initial census (not merely the pared graph6 in the
historical indeterminate list), records and checks each
closed-neighborhood dominated-vertex deletion, confirms that the
terminal graph is stiff, and supplies a complete vertex bijection
verifying exact adjacency equivalence to its certified nine-vertex
class representative. The positive v5 `K^3` special-octahedron
witnesses are also independently replayed. The old core index is
**recomputed from its original census sources and compared byte-for-byte**
with its frozen snapshot; a hash recorded in the snapshot itself is
not accepted as independent evidence.

The mathematical transfer uses Frías-Armenta, Neumann-Lara and
Pizaña, *Dismantlings and iterated clique graphs*,
*Discrete Mathematics* 282 (2004), which establishes that removing
a dominated vertex preserves clique-convergence/divergence behavior.
Thus each original graph is K-divergent because its stiff core is
K-divergent. **This does not claim that the unpared original graph
itself contains a special octahedron at its own third iterate.**
It also does not classify any other still-indeterminate graphs.

The stage writes its verified, **immutable** proof index under
`reports/order10_special_octahedron_core_lift_v1/`:
`classes.tsv` (two representatives and all positive encodings),
`members.tsv` (133 original graph6 strings, explicit folds and
isomorphism maps), `summary.md` (proof scope and totals), and
`manifest.json` (input/code/certificate/result SHA-256 fingerprints).
No existing census verdicts, original input files, or frozen v2-v5
results are changed.

The **four independently verified proof-index files are committed
in this PR**. After merging, reproduce their verification with:

```bash
cd ~/Python/pycliques-census
git pull --ff-only
bash scripts/bootstrap_special_k3_v5.sh
.venv-special-k3-v5/bin/python scripts/special_octahedron_class_lift_v1.py verify
.venv-special-k3-v5/bin/python scripts/special_octahedron_class_lift_v1.py report
```

There is no need to generate or commit the same results again.

The `build` command is idempotent: it refuses to replace or
silently repair an existing report whose bytes differ from the
recomputed evidence. The CI workflow also builds and independently
verifies the same output and publishes its four files as a downloadable
artifact for code review.


## Independently replayed historical nine-core K-divergence (167 additional originals)

The immutable order-nine cross-reference identifies six historically
K-divergent nine-vertex stiff-core classes with **300** original order-ten
members. The v5 special-O4 certificate lift already certifies **133**
of them (two classes). The separate
`scripts/historical_ninecore_lift_v1.py` independently verifies the
other **four classes and 167 original members**, without changing any
historical verdicts, stage outputs, or prior certificates.

| Nine-core representative ID | Core graph6 | Independent proof on the core | Original ten-vertex members |
|---:|---|---|---:|
| 7454135 | `HEnb~jl` | Explicit special `O_7` in *raw* K³ | 61 |
| 9678187 | `HQyuzpt` | Explicit special `O_4` in *raw* K³ | 37 |
| 10768817 | `HUZ~v~}` | Suspension of connected 7-vertex coaffine graph | 33 |
| 11363569 | `HUzrv~}` | Suspension of connected 7-vertex coaffine graph | 36 |
| **Additional** | | | **167** |

For the two special-octahedron cores, the checker independently constructs
raw K, K² and K³ by enumerating maximal cliques and their intersections
with a deterministic labeling, then checks the exact privileged maximal
clique, aligned antipodes and all induced adjacency/nonadjacency
constraints. For the other two cores, it verifies the suspension poles,
connectivity of the base, and a complete automorphism taking every base
vertex to a distinct nonneighbor. The latter uses Larrión, Neumann-Lara
and Pizaña, *On expansive graphs*, *European Journal of Combinatorics*
30 (2009), Theorem 4.6, to conclude clique divergence.

For **each of the 167 original ten-vertex members**, the script
reconstructs the initial original graph6, validates every
closed-neighborhood-dominated deletion and a complete graph isomorphism
onto the certified core. By the dismantling preservation theorem
(Frías-Armenta, Neumann-Lara and Pizaña, 2004), the divergence transfers
to each original. These 167 original indices are explicitly checked
against and disjoint from the previously certified 133, giving **300
original ten-vertex graphs with replayable positive certificates**.
The proof concerns the stiff core; it makes no false claim about raw
K³ of the original ten-vertex graph.

To produce and verify a human-readable and machine-readable JSON
proof index (no historical data modified):

```bash
cd ~/Python/pycliques-census
git pull --ff-only
bash scripts/bootstrap_special_k3_v5.sh
.venv-special-k3-v5/bin/python scripts/historical_ninecore_lift_v1.py \
  --output historical-ninecore-lift-167.json
.venv-special-k3-v5/bin/python scripts/historical_ninecore_lift_v1.py \
  --verify historical-ninecore-lift-167.json
```

The GitHub Actions workflow runs the tests, reconstructs and independently
verifies the same complete index, then publishes it as a downloadable
artifact. No expensive large-scale census run is required. The 29 other
historically indeterminate nine-core classes, together with the
remaining order-eight and order-ten core classes, remain unclassified
by these positive certificates.


## Targeted three-core divergence investigation (versioned v1 pilot)

Three unresolved stiff nine-vertex cores represent **696** original
ten-vertex graphs: core `6962151` (`HEhvfzm`, 242 members),
`6914104` (`HEhev^{`, 219 members) and
`6974529` (`HEh~dzm`, 235 members). Their earlier completely
pared iterates through level 3 have exact first mod-2 Betti number zero.
Consequently the connected triangular double-cover method (including
the optimized AC-3 search in pycombtop) is not applicable to these
particular iterates, although it remains useful on other cores.

The isolated `scripts/core9_three_target_v1.py` uses the separately
pinned optimized pycliques-project code at `a78e4d979c70b0a242fa89efd2fcf3e058c318b1`.
For each selected core it reconstructs and checks all four completely
pared iterates against the independently frozen structural dataset.
It additionally builds *raw* K^0 through K^3 with a separate maximal-clique
intersection implementation. For every constructed graph it independently
searches for special O_d by exhaustive privileged-facet/antipode
enumeration and cross-checks the library's optimized implementation.

For completely pared iterates, the stage also performs strictly bounded
retraction searches onto proven divergent target families: octahedral
graphs O_d, suspensions of cycles, and complements of cycles C_n^c
with n at least 8. The current caps are 12 target vertices, 120
patterns, 15,000 search states and 30,000 assignments *per family
per iterate*. Each core runs in a single 2-GiB worker with an 80-second
wall-time limit. Exact H_1(F_2) and graph diameter diagnostics explain
when a connected triangular double cover or a direct radius-3
coaffination cannot exist in a given iterate.

**Logical interpretation:** A verified special octahedron or retraction
to a known divergent target in a (pared) iterate certifies divergence
of that nine-vertex core. Transferring a new positive result to all
original ten-vertex members still requires independent dominated-fold
and isomorphism certificates, as in PRs #19 and #20. Negative special
searches certify only absence of special octahedra in the *specific*
examined graphs. `EXHAUSTED`, `LIMIT_REACHED`, timeouts and
other nonpositive bounded retraction-search outcomes do *not*
certify clique convergence or nondivergence. No original census
verdict is changed.

Run the new stage in an isolated environment:

```bash
cd ~/Python/pycliques-census
git pull --ff-only
bash scripts/bootstrap_core9_three_target_v1.sh
.venv-core9-three-v1/bin/python scripts/core9_three_target_v1.py plan
.venv-core9-three-v1/bin/python scripts/core9_three_target_v1.py run
.venv-core9-three-v1/bin/python scripts/core9_three_target_v1.py verify
.venv-core9-three-v1/bin/python scripts/core9_three_target_v1.py report
```

The new GitHub Actions workflow runs this bounded pilot, independently
replays the available positive witness types, verifies provenance and
publishes the three machine-readable case records as a workflow artifact.
The stage does not require regenerating historical census data.


### Verified findings from the first three-core pilot

The completed 2026-11-17 GitHub Actions pilot reconstructed all three
cores and found **no special octahedron** in any of their raw or
completely pared iterates K^0 through K^3. The independent exhaustive
facet/antipode enumeration agrees with the pinned library implementation.
All twelve *pared* graphs have diameter exactly 2 and exact
mod-2 first Betti number zero. Thus no direct radius-3
coaffination or connected triangular double cover exists in these
specific iterates.

| Core ID | Original ten-vertex members | Pared orders K^0..K^3 | Special O_d | Positive retraction |
|---:|---:|---|---|---|
| 6914104 | 219 | 9, 13, 19, 37 | none through level 3 | none found |
| 6962151 | 242 | 9, 14, 19, 40 | none through level 3 | none found |
| 6974529 | 235 | 9, 13, 20, 55 | none through level 3 | none found |

All three target-retraction families were fully exhausted on levels
0 and 1. Level 2 also exhausted several target families, but other
families reached the 120-pattern budget. At level 3, every targeted
family reached that pattern limit. None yielded a positive retraction.

The pinned manifest and complete per-core JSON diagnostics were
independently verified in CI and committed under
`research/order10_core9_three_target_v1/` (separate from frozen
`runs/` and `reports/`). The first successful run was
[GitHub Actions 44175126696](https://github.com/rvf0068/pycliques-census/actions/runs/44175126696).

**No graph in these three core classes has been classified by this
stage.** Exhaustion of a limited family of divergent targets is not a
certificate of K-convergence or K-nondivergence.


## Homology-guided non-special K³ retractions (v2)

This separately versioned experiment investigates the third **completely
pared** clique iterates of two unresolved nine-vertex stiff cores,
representing **461** original ten-vertex graphs.

### Exact reduced mod-2 Betti numbers

All faces through dimension six are enumerated and their boundary
matrices reduced over GF(2), establishing the following exact results
(in degrees 0 through 5), not merely estimated homotopy types.

| Nine-core ID | Order of pared K³ | beta_1 | beta_2 | beta_3 | beta_4 | beta_5 |
|---:|---:|---:|---:|---:|---:|---:|
| 6914104 | 37 | 0 | 0 | 1 | 0 | 0 |
| 6962151 | 40 | 0 | 0 | 0 | 1 | 0 |

Since a retraction of graphs induces a retraction of their clique
complexes, reduced homology of its target is a direct summand of
the reduced homology of its source. The script independently computes
the Betti vectors of each small named candidate target using the
pinned `pycombtop.bounded_betti.bounded_reduced_betti_mod2`.
Restricting to previously established K-divergent target families,
and independently checking all possible induced octahedra and chordless
complement cycles, gives the following precise candidate families:

| Core | Octahedra O_d | Cycle complements C_n^c | Cycle suspensions |
|---:|---|---|---|
| 6914104 | O_4 | C_11^c and C_13^c | None |
| 6962151 | O_5 | C_14^c | None |

Before the retraction search, the program exhaustively checks
all induced O_6 subgraphs in each source (there are none), and all
chordless cycles in each complement (maximum lengths 12 and 14,
respectively). Consequently no O_d with d >= 6 or cycle complement
C_n^c with n > 14 can occur as an induced target. Every suspension
of a cycle has nonzero reduced H_2 regardless of its order, so the
vanishing second Betti number excludes all those targets without
a size cutoff.

The unique induced C_14^c of the 40-vertex iterate is explicitly
tested using an independently replayed bounded graph-retraction
algorithm; its failure is not inferred from the homology obstruction
alone. The C_13^c option for the 37-vertex iterate is ruled out by
the exhaustive induced-cycle enumeration.

The new `scripts/core9_third_retractions_v2.py` enumerates these
non-special induced candidates using the separately pinned
`pycliques-project` revision
`a78e4d979c70b0a242fa89efd2fcf3e058c318b1`.
It eliminates impossible candidates with a necessary
closed-neighborhood test: for each vertex x outside a prospective
target H, there must be a target vertex t satisfying
N_G(x) intersect V(H) subseteq N_H[t]. This holds for every
retraction because vertices of H are fixed.

Only surviving targets undergo full bounded graph-retraction CSP
search. Positive witnesses are independently replayed. The precise
caps are 50,000 target patterns, 5,000 locally feasible targets,
250,000 CSP states and 500,000 candidate assignments per family.
Each core computation and independent verification uses its own
125-second, 2-GiB subprocess. Negative statuses are recomputed
exactly and remain negative only for the specifically searched
finite family; in particular no K-convergence is inferred.

Run with the existing isolated pin:

```bash
cd ~/Python/pycliques-census
git pull --ff-only
bash scripts/bootstrap_core9_three_target_v1.sh
.venv-core9-three-v1/bin/python scripts/core9_third_retractions_v2.py plan
.venv-core9-three-v1/bin/python scripts/core9_third_retractions_v2.py run
.venv-core9-three-v1/bin/python scripts/core9_third_retractions_v2.py verify
.venv-core9-three-v1/bin/python scripts/core9_third_retractions_v2.py report
```

The read-only PR CI job separately verifies and uploads the JSON proofs
as a GitHub Actions artifact. After successful verification, the
authenticated GitHub connector can commit reviewed immutable outputs under
`research/order10_core9_third_retractions_v2/` without changing
historical census files. If a positive retraction is found for
one of these cores, a separate dominated-vertex fold witness must
be replayed for every represented original ten-vertex graph.


### Verified complete result for the three named target families

The independently checked CI experiment (November 17, 2026) actually
finished **all** the homologically eligible searches. In addition,
the exhaustive structural ceiling checks show there are no induced
`O_6` subgraphs in either host, and no induced complement of a
cycle longer than 12 (core `6914104`) or 14 (core `6962151`).
Therefore the following negative conclusions hold **without any
target-size cutoff** in the three named target families.

| Third pared iterate of core | Complete octahedron tests | Complete cycle-complement tests |
|---:|---|---|
| 6914104 (37 vertices) | 1,412 induced O_4 candidates; 1,252 locally feasible retractions exhaustively rejected (7,837 CSP states); no induced O_5 or O_6 | 275 induced C_11^c candidates all fail necessary local condition; no induced C_13^c, no complement cycle longer than 12 |
| 6962151 (40 vertices) | All six induced O_5 candidates fail necessary local condition; no induced O_6 | The unique induced C_14^c is not a retract (8 CSP states); no complement cycle longer than 14 |

All cycle-suspension retractions are excluded, regardless of order,
because such a target has nonzero reduced second mod-2 homology while
both hosts have zero reduced second homology.

A short **human-checkable obstruction** for the single `C_14^c`
candidate is committed in
`research/order10_core9_third_retractions_v2/C14_obstruction.md`:
the forced retraction values of vertices 27 and 33 imply incompatible
constraints on vertex 4. The entire verified machine-readable
manifest and both per-core records are committed under the same
`research/` directory. The pull-request CI verifies and compares
the saved records **with read-only repository permissions**; it cannot
push code or data.

**Mathematical scope:** Neither third pared iterate admits an ordinary
graph retraction onto any `O_d` with d at least 3, any cycle
complement `C_n^c` with n at least 8, or any suspension of a
cycle. This rules out these familiar divergence mechanisms via
retractions, **not clique divergence itself**. All 461 represented
ten-vertex original graphs remain unclassified by this stage.


## Retractions onto clique graphs of divergent cycles and suspensions (v1)

This follow-up investigates ordinary graph retractions from the third
**completely pared** clique iterates of nine-vertex stiff cores 6914104
(37 vertices; 219 original order-ten members) and 6962151
(40 vertices; 242 original members), targeting **clique graphs** of
the established divergent families rather than the original
suspensions or complements of cycles:

- `K(susp(C_n))` for n at least 4 (suspension of the cycle);
- `K(C_n^c)` for n at least 8.

A retraction to one of these targets would certify K-divergence,
because K-divergence of a graph is preserved under the clique operator,
and divergence is inherited by a graph admitting a retraction onto
a divergent graph. Not all copies of those target graphs need be
special octahedra.

### Independent homology and finite target reduction

For n=4, `susp(C_4) = O_3` and `K(susp(C_4)) = O_4`.
The preceding versioned stage already excluded all O_4 retractions.
For n from 5 through 20, exact mod-2 boundary-matrix reduction shows
that `K(susp(C_n))` has reduced second Betti number one.
Both source third iterates have reduced second Betti number zero,
so homology rules out every such retraction. For n at least 21
these targets have 2n > 40 vertices and cannot embed.

For the cycle-complement family, the number of maximal cliques of
`C_n^c`, hence the vertices of its clique graph, is
the Perrin number `P_n` satisfying
`P_n=P_{n-2}+P_{n-3}`, with
`P_8=10`, `P_9=12`, `P_10=17`,
`P_11=22`, `P_12=29`,
`P_13=39`, and `P_14=51`.
This follows from the characterization of maximal independent sets
of a cycle as cyclic 0/1 words with no consecutive ones and no
three consecutive zeros. For n>=14, the clique graph has more
than 40 vertices and cannot occur as an induced subgraph of either
host.

Homology excludes `K(C_8^c)` (reduced beta_2=1),
`K(C_9^c)` (reduced beta_3=4), and
`K(C_11^c)` (reduced beta_5=1).
Although `K(C_{12}^c)` has only 29 vertices,
it has 46 edges in its complement. Every induced 29-vertex
subgraph of the complement of the 37-vertex host has **at least
73 edges**, and of the complement of the 40-vertex host has
**at least 57 edges**, so the target cannot embed in either.
`K(C_{13}^c)` has 39 vertices, exceeding the first
host's 37; it also has 663 edges, exceeding the second host's 601.

Thus the **only remaining homologically and structurally admissible
target** is `K(C_{10}^c)`, which has 17 vertices,
110 edges and reduced third Betti number one. It is admissible
only for the 37-vertex host (core 6914104).

### Complete finite retraction search

The new `scripts/core9_clique_targets_v1.py` builds target
clique graphs independently from sorted maximal cliques. It locates
every induced `K(C_{10}^c)` using two independent subgraph
isomorphism implementations (ISMAGS and VF2) on complements,
explicitly cross-checks their *vertex sets*, then applies two
independent retraction solvers to each candidate: its own
backtracking over necessary fixed-target domains and the general
pinned `pycliques.retractions.bounded_retraction` engine.
The latter's state/assignment caps must never be reached for an
exhaustive negative conclusion.

The stage pins the same previously verified upstream revision,
`a78e4d979c70b0a242fa89efd2fcf3e058c318b1`,
rechecks the previously committed exact host homology and
graph6 sources, isolates workers and independent full replays
within 110-second/2-GiB budgets, and never modifies historical
verdicts or earlier proof records. Pull-request CI is read-only,
uploads independently checked JSON results, and never runs PR
code with repository-write permissions.

To reproduce after the bootstrap from the previous stage:

```bash
bash scripts/bootstrap_core9_three_target_v1.sh
.venv-core9-three-v1/bin/python scripts/core9_clique_targets_v1.py plan
.venv-core9-three-v1/bin/python scripts/core9_clique_targets_v1.py run
.venv-core9-three-v1/bin/python scripts/core9_clique_targets_v1.py verify
.venv-core9-three-v1/bin/python scripts/core9_clique_targets_v1.py report
```

As always, failure to retract to these particular targets does
**not** prove K-convergence or rule out other divergent targets.


## New certified K-divergent targets: coaffine joins (v1)

The next bounded search uses a family not covered by the previous
octahedron, cycle-complement, suspension-of-cycle and first-clique-graph
target stages:

``math
T_{n,r} = C_n^c * O_r, \quad n \geq 5,\quad r\geq 1.
``

Here `O_r` is the complement of `r` disjoint edges, so
`T_{n,r}` is a repeated suspension of `C_n^c`.
Indeed `T_{n,r} = susp(C_n^c*O_{r-1})`, interpreting
`O_0` as the empty join factor. The cyclic permutation
`v -> v+1` is a nonadjacent-vertex automorphism of
`C_n^c`, while swapping each nonedge pair gives a
2-coaffination of `O_{r-1}`. Their join has a
2-coaffination, so the suspension/expansivity criterion
[LNP09, Theorem 4.6] proves each `T_{n,r}` K-divergent.

The special case `T_{5,2}` is exactly the **historically
certified divergent nine-core** `HUZ~v~}` (core 10768817).
The graph `K(HUzrv~})`, for the other historical suspension
core 11363569, is simply `C_{14}^c` and was *already*
excluded as a retract in PR #22.

The independence-complex homotopy formula for cycles yields
`Delta(T_{n,r}) = Ind(C_n)*S^{r-1}`.
Since `Ind(C_{3k})` is a wedge of two `S^{k-1}`,
`Ind(C_{3k+1})` is `S^{k-1}`, and
`Ind(C_{3k+2})` is `S^k`, the new stage enumerates
**all rank-one target members in dimensions three or four**:

| Source nine-core | Candidates in homological target family |
|---:|---|
| 6914104 (37-vertex pared K³, reduced beta3 = 1) | T(5,2), T(7,2), T(8,1), T(10,1) |
| 6962151 (40-vertex pared K³, reduced beta4 = 1) | T(5,3), T(7,3), T(8,2), T(10,2), T(11,1), T(13,1) |

These target Betti profiles are additionally checked using an
independent exact mod-2 boundary-matrix implementation.

For each pair `(n,r)`, the experiment enumerates every induced
chordless `C_n` in the **complement** of the host, then adds
`r` mutually separated induced complement edges.
This is an exact characterization of the induced
`C_n^c*O_r` patterns. Every selected graph is independently
checked by graph isomorphism. A necessary fixed-target-neighborhood
test discards impossible retractions. Remaining targets are passed to
two separately implemented ordinary graph-retraction solvers,
with their positive and nonpositive results cross-checked.

The first full structural pass gave the following exact counts:

| Host | n,r | Induced targets | Failed local test | CSP cases |
|---:|---|---:|---:|---:|
| 6914104 | (5,2) | 821 | 820 | 1 |
| 6914104 | (7,2) | 629 | 0 | 629 |
| 6914104 | (8,1) | 704 | 704 | 0 |
| 6914104 | (10,1) | 71 | 71 | 0 |
| 6962151 | (5,3), (7,3), (8,2), (10,2), (11,1), (13,1) | 0 | 0 | 0 |

No positive graph retraction was found. These findings are being
independently replayed in a new read-only CI job; its verified JSON
artifact is versioned separately from earlier census results.

```bash
bash scripts/bootstrap_core9_three_target_v1.sh
.venv-core9-three-v1/bin/python scripts/core9_coaffine_join_targets_v1.py plan
.venv-core9-three-v1/bin/python scripts/core9_coaffine_join_targets_v1.py run
.venv-core9-three-v1/bin/python scripts/core9_coaffine_join_targets_v1.py verify
.venv-core9-three-v1/bin/python scripts/core9_coaffine_join_targets_v1.py report
```

The negative conclusion is **only** about the homology-matched
rank-one coaffine joins listed above. Higher-dimensional homology
of the hosts has not been certified by this stage, so targets whose
homology lies above the verified range are not ruled out. Nor is
any clique-convergence conclusion drawn for the 461 original
ten-vertex graphs.
