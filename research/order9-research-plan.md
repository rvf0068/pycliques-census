# Order-9 continuation: timeboxed bound 200 and clockwork pilot

This document concerns **54 still-unknown original connected nine-vertex
graphs** in the completed historical census: **18** whose current behavior is
unresolved without conjectural references, and **36** whose prior reasoning
depends on the unproved snub-disphenoid divergence conjecture.

The historical order-9 counts were: 63 initially unresolved; 4 subsequently
proved by C10 retractions, 2 settled at bound 60 (one convergent and one
divergent), and 3 proved divergent at bound 70. The new stage must not silently
reclassify the 36 conditional cases as divergent.

## Independent environment

The original `config/pycliques_commit.txt`, `.deps/pycliques-project` and
all historical `runs/order9/*` remain unchanged.

```bash
cd /workspaces/pycliques-census
bash scripts/bootstrap_order9.sh
PY=.deps/pycliques-project-order9/.venv/bin/python

# Validate historical selection without writing a manifest or result
$PY scripts/order9_bound200.py --dry-run

# One batch (three original graphs) at a time:
$PY scripts/order9_bound200.py

# Finish all 18 nonconjectural cases with restart support:
$PY scripts/order9_bound200.py --all

# Then, separately, all 36 conditional cases:
$PY scripts/order9_bound200.py --group conjectured --all
```

Resources: bound **200**, `tries=9`, `retraction_depth=2`,
**120 s** and **4096 MiB** per individual classification, independent worker
processes, 3 originals per batch. Each record is written atomically; a
TIMEOUT, BOUND_EXCEEDED, ERROR or INDETERMINATE is **not** a proof. The immutable
manifest hashes the cohort, runner, worker, verifier, dependencies and
prior-stage summaries. Do not modify code or settings mid-run; use a new
stage directory/version instead. The separate stage does **not** overwrite
root-level indeterminate files or old summaries.

Positive supported certificates are serialized using merged v3 JSON proof
records and can be independently replayed using
`certificate_records_v3.verify_record`. Unsupported positive rules are
labeled `not_serialized` and require independent replay before publication.

## Clockwork-retraction pilot

All currently unclassified nonconjectural order-9 originals have reduced
mod-2 Betti-1 zero, also at their first two pared clique iterates. Since a
divergent clockwork has homotopy type S^1, there can be **no retraction** from
any of these graphs/iterates to a divergent clockwork. This is a genuine
homology obstruction: an induced graph-retraction gives a split injection
on the clique-complex homology.

Eight of the **conditional** order-9 cases have mod-2 Betti-1 exactly one
both at the original and second pared clique iterate. These are selected
in `scripts/order9_clockwork_pilot.py`. It uses the existing pycliques
`find_divergent_clockwork_retract` search, with independent witness checks.
The pilot tests potential induced clockwork targets of 9 or 10 vertices,
max 3000 candidate subsets, 8 retraction targets, 20,000 backtracking
states, 100,000 assignments, and 25 seconds of wall-clock time per graph.

```bash
$PY scripts/order9_clockwork_pilot.py --all --per-case-timeout 25 \
    --max-candidates 3000 --output order9-clockwork-pilot.json
```

The result distinguishes `FOUND`, `EXHAUSTED`, `LIMIT_REACHED`,
`TIMEOUT`, `ERROR` and homology filter failures. An exhausted result is
exhaustive **only within the stated target-order bound**; a candidate cap
hit means the search is incomplete. In particular, enumerating 9-subsets of
a 21-vertex graph requires examining 293,930 possibilities, so a
3000-subset pilot cannot prove nonexistence.

## Homotopy type of *all* 261,080 order-9 connected graphs

The independent repository `rvf0068/pycliques-homotopy-census` **already
implements** a restartable per-original census of homotopy types of Delta(G)
and Delta(K(G)), also clique-Helly flags and certified-vs-Betti-only
distinction, for *every* connected graph of order 9. Its published `runs/`
folder is not populated yet. Do not duplicate that code in this repo.

Run in the homotopy-census Codespace after setting up its original
dependency version, with its repository instructions and validation:

```bash
bash scripts/run.sh 9
.venv/bin/python scripts/validate.py --stage 9
```

The output contains individual graph6 strings, original indices,
`status_g, htype_g, betti_g`, `status_kg, htype_kg, betti_kg`, Helly
flags and comparison statuses. An exact wedge-of-spheres certification
is a **homotopy-type statement**; merely having a sphere's Betti vector is
not. In particular, the nonconjectural order-9 unresolved inputs currently
show the mod-2 homology of S^2, but this alone does not prove they are
homotopy equivalent to S^2.

After both runs, join by (order, original index, graph6), and look for
clique-null or convergent originals with certified noncontractible homotopy
type, and for any mismatches between Delta(G) and Delta(K(G)).

## Results of the initial PR CI experiments (2026-11-06)

**Bound 200:** The first three nonconjectural originals
(indices 208409, 242316, 248687) all remain `BOUND_EXCEEDED`.
A separate independent maximal-clique count at the third pared iterate
showed that **all 18** nonconjectural cases require **more than 200**
cliques to construct the fourth clique iterate. Ten had counts between
250 and 500; eight exceeded 500. The bound-200 stage is thus mainly
a reproducible baseline and may still find certificates through other
rules. A future new stage should evaluate an explicitly versioned,
selective bound around 500, combined with faster paring and a timeout,
without mutating the bound-200 manifest.

**Generic clockwork search:** Eight conditional order-9 cases were
tested at their second pared clique iterate with at most 3000 induced
candidate subsets and 25 seconds per graph. Seven timed out and one
reached the candidate limit after checking all 3000 candidates. None
produced a positive clockwork-retraction certificate. These limits
are *not* a proof of nonexistence.

**Small-target clockwork search:** New script
`scripts/order9_clockwork_targeted.py` generated **13 distinct
nonisomorphic theorem-certified divergent clockwork targets of orders
9 and 10**, restricted to three segments, two crown vertices per
segment, and core sizes (1,1,1) or (2,1,1). It exhaustively tried
these 13 targets on **all eight** conditional order-9 candidates at
their second pared clique iterate. All tests completed in 0.8--1.6
seconds per graph, with **no** retraction. This rules out only these
13 targets, **not all** divergent clockworks. The targeted method
is a good candidate for broader opt-in use; the brute-force
induced-subgraph scan is not.

**Homotopy of remaining order-9 graphs:** In the independent
`pycombtop` classifier pilot, **every one of the 54 remaining originals
and their first clique graphs** received certified exact wedge-of-spheres
types, and the types agreed in all 54 cases:
- 46 originals: type S^2;
- 8 originals: type S^1 wedge S^2.

This is a *complete homotopy classification of the 54 unresolved
clique-behavior cases only*, not the complete set of 261,080 connected
nine-vertex graphs. The latter still requires the independent
`pycliques-homotopy-census` order-9 stage. The separate workflow's
artifacts contain all 54 original-indexed homotopy records.

Reproducible CI:
- Brute pilot: https://github.com/rvf0068/pycliques-census/actions/runs/42318974615
- Targeted pilot and 54 exact homotopy records:
  https://github.com/rvf0068/pycliques-census/actions/runs/42319826584

These are observations and computational certificates, not a proof
that clique-nullity or clique divergence is determined by homotopy type.
