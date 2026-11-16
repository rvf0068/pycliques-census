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
