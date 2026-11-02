# Pycliques census: connected graphs through order 10

A reproducible **research workspace for determining clique behavior of connected,
unlabeled, simple graphs on at most ten vertices**. This is not a fork of
[`rvf0068/pycliques-project`](https://github.com/rvf0068/pycliques-project):
it installs a separately pinned revision of that monorepo and records
experimental data, commands, and source provenance here.

**Stage 1 is a correctness check through order 8**, not the endpoint of the
project. Later stages are the substantially more expensive order-9 and
order-10 censuses, followed by additional targeted classification attempts.
**Disconnected graphs are out of scope.** No time is spent enumerating or
deriving their clique behavior.

## Start a GitHub Codespace

1. Open this repository on GitHub and choose **Code → Codespaces → Create
   codespace on main**.
2. Codespaces automatically runs `scripts/bootstrap.sh`, which installs the
   pinned `pycliques-project` and all its workspace packages using its
   `uv.lock`. It also runs `scripts/setup_history.sh`.
3. Open a fresh Bash terminal. The default Python environment and
   `small-behavior` command are now available without manual installation:

   ```bash
   python -c 'import pycliques, pycombtop, pyg6data; print(pycliques.__file__)'
   small-behavior --help
   ```

4. Run the **initial validation through order 8**:

   ```bash
   bash scripts/run_census.sh
   ```

5. Inspect `runs/baseline-through8-bound30/summary.json`. The validator
   checks every connected source graph and its recorded verdict, confirms
   complete order coverage, and checks whether the historical result is
   reproduced. It **does not** change any verdict to make it match expectations.
6. Commit the generated `runs/` files and `history/` files after checking them:

   ```bash
   git add runs/ history/
   git commit -m "Record baseline connected clique-behavior census through order 8"
   git push
   ```

**Historical expectation, not a precomputed answer:** All connected graphs
through order 8 should be classified except the order-8 snub disphenoid,
original zero-based index `10829`, original graph6 `GQyuzw` (historically
`conjectured_divergent`, **not** a proof of divergence). This is a regression expectation, not a precomputed classification result.
If the expected result is not reproduced, validation writes the actual
unresolved cases and exits unsuccessfully. The new census has **not** yet been
executed in Codespaces.

## Continue to orders 9 and 10

Do these as **new runs**, retaining the successfully committed order-8 baseline.
`MIN_ORDER` and `MAX_ORDER` select only the desired orders. Existing previous
orders are not recomputed.

```bash
# Order 9: 261,080 connected graph isomorphism types
MIN_ORDER=9 MAX_ORDER=9 BATCH_SIZE=1000 \
  RUN_DIR="$PWD/runs/order9-bound30" bash scripts/run_census.sh

# Order 10: 11,716,571 connected graph isomorphism types
MIN_ORDER=10 MAX_ORDER=10 BATCH_SIZE=5000 \
  RUN_DIR="$PWD/runs/order10-bound30" bash scripts/run_census.sh
```

These runs may take considerable CPU time and disk space. To stop them, interrupt
the script; rerun **the exact same command** to skip completed chunks. For
Codespaces interruptions, batches are finalized only after a successful
`small-behavior` invocation. The filesystem needs to remain available;
committing checkpoint files regularly is strongly recommended.

A later experiment with a larger clique bound must have its own run directory:

```bash
MIN_ORDER=10 MAX_ORDER=10 BATCH_SIZE=5000 CLIQUE_BOUND=40 \
  RUN_DIR="$PWD/runs/order10-bound40" bash scripts/run_census.sh
```

**Important:** This launches a new census of all order-10 inputs at bound 40;
it does not automatically filter to unresolved graphs from bound 30. We can
add a separate staged-cohort runner later. Do not pay the high cost of a full
bound-40 run unless its purpose is clear.

### Resume an interrupted order-9 run after the clockwork fix (November 2026)

This is a **one-time, opt-in audited carry-forward** for an order-9 run
interrupted at indices 250000–259999 by the upstream clockwork-recognizer
exception. It avoids reclassifying the first 250,000 connected graphs, while
explicitly recording that the completed chunks were produced by an earlier
revision of `pycliques-project`.

The upstream fix is `da9ef9b0b76648d221b687487483da56603ccdff`.
Its only classifier-code change rejects an invalid three-segment triangle
*before* an independent verifier would otherwise raise. Previously completed
classifications are thus unaffected by this correction.

**Preserve your existing `runs/order9-bound30` directory.** After pulling the
latest census repository changes, in the Codespace run:

```bash
git pull --ff-only
bash scripts/update_pycliques.sh da9ef9b0b76648d221b687487483da56603ccdff

.venv/bin/python maintenance/prepare_order9_resume.py \
  --old "$PWD/runs/order9-bound30" \
  --new "$PWD/runs/order9-bound30-after-clockwork-fix"

MIN_ORDER=9 MAX_ORDER=9 BATCH_SIZE=10000 CLIQUE_BOUND=30 \
  RUN_DIR="$PWD/runs/order9-bound30-after-clockwork-fix" \
  bash scripts/run_census.sh
```

The preparation script checks the original run manifest, requires the exact
old and new upstream revisions, independently checks the graph6 input hash,
verifies all completed verdict files, completion markers, and unresolved
sidecars, and copies each file with a SHA-256 check. It never edits the
original run. The new directory contains `chunk_lineage.json` with
per-file checksums and exact provenance. The new run's `manifest.json`
binds that lineage file by SHA-256, and the final validator rechecks the
inherited bytes and reports their origin in `summary.json`.

The resulting census is explicitly **mixed provenance**: original commit
`ce401a3e7c52d11392a8a5d04e39e48e9486328d` produced the completed
prefix, and the fixed commit produced the remaining suffix. Do not describe
all of its rows as having been computed with the fixed revision. For a
strictly single-version census instead, select an **empty** new `RUN_DIR`
and run the full order-9 census from index zero.

### Next post-pass: retraction of K(G) onto the complement of C10

After validating the completed **order-9** census, examine only the unresolved
graphs that are **not** conditional on the conjectured divergence of the snub
disphenoid. The cohort is drawn from the saved original-indexed graph6 records
and cross-checked against the six-column unresolved file.

The completed baseline currently has **63 indeterminate graphs**, of which
**36** are marked `conjectured_divergent`; the remaining **27** are tested.

A graph of order nine cannot itself retract onto a graph with ten vertices.
The intended test is whether the **clique graph** `K(G)` retracts onto
`complement_of_cycle(10)`. This is not among the default fast classifier
tests, although `pycliques.retractions` provides bounded retraction search.

```bash
git pull --ff-only
bash postpasses/run_clique_retract_comp_c10.sh
```

Results are written into
`runs/order9-bound30-after-clockwork-fix/postpasses/clique_retract_comp_c10/`.
Each eligible graph receives its own atomic, resumable JSON result containing
the original source index, exact `K(G)`, and optionally a verifiable
retraction map. The post-pass has its own manifest containing hashes of
its source, the original census summary, unresolved cohort, and the exact
pinned `pycliques-project` revision. It never modifies existing census
classifications.

The repository-root **[indeterminate_order_9.txt](indeterminate_order_9.txt)**
is the easy-to-access *current working cohort*: the wrapper refreshes it
atomically after each post-pass invocation, including interrupted runs.
It starts with the original 63 indeterminate cases and removes only cases
with a verified `RETRACTION_FOUND` certificate. The 36 snub-dependent
cases remain in the working file, as do any ordinary negative, untested,
or resource-limited cases. Its six-column format and original graph indices
are unchanged. The original
`runs/order9-bound30-after-clockwork-fix/order9/indeterminate_order_9.txt`
is an immutable census snapshot and must not be edited by post-passes.

If you already invoked the original Python post-pass command directly,
update the root working file without repeating the computation:

```bash
.venv/bin/python postpasses/refresh_indeterminate_order9.py
```

For higher-budget experiments with a distinct `--output-dir`, use the
shell wrapper with the same option to refresh from that experiment. Preserve
the separate, immutable result directories for provenance.

Three outcomes have different meanings:

- `RETRACTION_FOUND`: an independently checked retraction onto an induced
  copy of `complement_of_cycle(10)`, with the maps included.
- `NO_RETRACTION`: all induced target copies were exhausted or `K(G)`
  is too small; this is only a negative result for this **particular** test.
- `INCONCLUSIVE`: one or more search budgets were exhausted; a larger
  search is needed before claiming a negative.

The default limits are 1,000 different induced target vertex sets, 100,000
search states, and 1,000,000 tested assignments *per target embedding*.
A stopped post-pass can be resumed with the identical command; completed
graph records are skipped. For a new experiment with larger budgets, choose
a **new** `--output-dir` so provenance is not mixed.

After completion, inspect
`.../postpasses/clique_retract_comp_c10/summary.json` and commit the
new post-pass directory. This is separate from the original order-9 census
and should not be mistaken for a new full enumeration.

### Connected graph census sizes

| Order | Unlabeled connected simple graphs |
|---:|---:|
| 1 | 1 |
| 2 | 1 |
| 3 | 2 |
| 4 | 6 |
| 5 | 21 |
| 6 | 112 |
| 7 | 853 |
| 8 | 11,117 |
| 9 | 261,080 |
| 10 | 11,716,571 |

Sources: Brendan McKay's [graph data](https://users.cecs.anu.edu.au/~bdm/data/graphs.html)
and [OEIS A001349](https://oeis.org/A001349). Only one representative per
connected graph isomorphism type is processed.

## What gets committed, and why

The repository intentionally does **not** ignore the following generated data:

- `runs/<run-name>/manifest.json`: exact `pycliques-project` commit,
  `uv.lock` SHA-256, input dataset SHA-256, Python and installed package
  versions, CLI bound, batch size, and a checksum of the runner scripts.
- The source graph6 datasets are identified by SHA-256 in the manifest;
  source indices are retained in the verdict files, without redundant
  graph-index inventories. The validator re-reads the source data independently.
- `runs/<run-name>/orderN/chunks/*.tsv.gz` (orders 6–10): deterministic,
  gzip-compressed verdicts in resumable, index-addressable chunks.
- `runs/<run-name>/orderN/unresolved_chunks/` and `completed/` (orders
  9–10): pared-unresolved sidecars and atomic completion markers for each
  successfully processed batch.
- `runs/<run-name>/orderN/logs/*.log`: per-chunk CLI output.
- `runs/<run-name>/orderN/indeterminate_order_N.txt`: current unresolved
  **pared** graphs, produced by `small-behavior`. This is not the original
  graph6 source inventory.
- `runs/<run-name>/summary.json`: exact streaming validation and unresolved
  original graph6 records.
- `history/experiment_commands.tsv`: time and parameters of every run of
  `scripts/run_census.sh`, including the upstream revision.
- `history/bash_history`: interactive Bash history from Codespaces terminals.

`history/bash_history` is plain text and **can contain sensitive shell
commands or tokens**. Review and redact it before committing, especially to a
public repository. The experiment-command TSV intentionally records only
non-secret research parameters. No command history is pushed automatically.

Intermediate `*.partial` and `*.tmp` files, `.deps/`, `.venv/`, and Python
caches remain ignored. A missing or incomplete batch is rerun. All completed
results can be committed using ordinary Git; no `git add -f` is necessary.

**Git storage warning for order 10:** Even compressed, millions of verdicts
may produce a large repository. Individual 5,000-graph chunk files remain
small; the entire history can still become cumbersome. Commit incrementally
and consider Git LFS or released archives after measuring actual sizes.
Do not commit monorepo dependency checkouts or virtual environments.

## Updating pycliques in the Codespace

The Codespace starts with `pycliques` **already installed**. It is installed
from a pinned source revision, not from an automatically moving `main` branch,
so a census can always be reproduced.

To upgrade deliberately to the latest `pycliques-project/main`:

```bash
bash scripts/update_pycliques.sh
```

This fetches the new commit, updates `config/pycliques_commit.txt`, and
reinstalls the monorepo with its matching `uv.lock`. `python`,
`small-behavior`, and the notebook kernel use the updated environment.
Check the new pinned SHA and commit it:

```bash
python -c 'import pycliques; print(pycliques.__file__)'
git add config/pycliques_commit.txt
git commit -m "Update pinned pycliques-project revision"
git push
```

To select a specific fetched revision, instead run
`bash scripts/update_pycliques.sh <commit-or-tag>`.

**Never mix results from different versions in one run directory.** The
manifest compares the exact upstream commit, lockfile, dataset hashes,
runner source, bounds, and other parameters. If any differ, the runner
refuses to resume and instructs you to select a new `RUN_DIR`. Earlier
committed runs remain valid and traceable.

## Working notes and methodology

- Orders 1–5 are taken from the connected graphs in the NetworkX graph
  atlas, because `small-behavior`'s bundled connected datasets begin at 6.
  They are still classified with the current fast classifier.
- Orders 6–8 run `small-behavior --no-lookup --no-skip-dominated --bound 30`
  (or the requested `CLIQUE_BOUND`) using the pinned `pycliques` revision.
  The `--no-lookup` option prevents old unresolved files from influencing
  the verdict, and `--no-skip-dominated` ensures all connected source
  graphs receive a definitive or indeterminate verdict.
- For orders 9–10, `scripts/stream_connected.py` calls the **same**
  `classify_clique_behavior(graph, bound=...)` routine, but streams the
  `pyg6data` dataset in a single pass. Repeated `small-behavior --start/--end`
  calls would re-read the gzip dataset from the beginning for every batch,
  which becomes prohibitively expensive for 11.7 million graphs. The large
  orders instead record deterministic gzipped verdict chunks, gzipped pared
  unresolved sidecars, and `.done` markers; resuming skips finished batches.
  Only completed chunks are used to rebuild the unresolved cohort.
- This is only the **fast classification baseline**. It does not yet run
  `small-behavior-theorem26`, homotopy classification, retraction post-passes,
  or triangular-cover searches. Those should be later, recorded experiments
  on unresolved cohorts, with separate outputs and parameters.
- A finite search that has not found a certificate is `INDETERMINATE`, not
  evidence that the graph converges or diverges.
- The streaming validator checks all input indices against the pinned source,
  checks completeness of every verdict chunk and unresolved cohort, and
  records actual unresolved graph6 values. It enforces the snub-only
  **historical benchmark only for orders through 8 included in a run**;
  it never presumes that orders 9 or 10 have no other unresolved cases.
- A fresh run with changed source code, dependency revision, batch size, or
  parameters gets a new directory so partial results are never miscombined.

## Quick CI test and programmatic validation

GitHub Actions runs a small connected census through order 6 when repository
scripts change. You can repeat that smoke test in a Codespace:

```bash
MAX_ORDER=6 BATCH_SIZE=100 RUN_DIR="$PWD/runs/smoke-order6" \
  bash scripts/run_census.sh
```

Validate a completed run again:

```bash
python scripts/validate.py --run-dir runs/baseline-through8-bound30
```

For exploratory runs, `--no-expect-snub` writes the actual results without
asserting the historical order-8 benchmark.

