# Clockwork recognizer mismatch during the order-9 connected census

## Reported failure

At pinned `pycliques-project` commit
`ce401a3e7c52d11392a8a5d04e39e48e9486328d`, the 9-vertex
connected census stopped inside source indices 250000–259999 with:

```text
RuntimeError: Fast recognizer produced an invalid structure:
A triangle meets three distinct clockwork segments.
```

**Do not mark the graph divergent.** The independent verifier rejected the
proposed decomposition. No false certificate should be accepted.

## Precise cause

In `packages/pycliques/src/pycliques/clockwork.py`,
`_recognize_clockwork_fast` checks only triangles contained in `C_nodes`
when rejecting triangles across three segments. Later,
`verify_clockwork_structure` checks *all* triangles, including those formed
by vertices of the crown or a mixture of crown and core vertices.
Consequently the fast routine can return a candidate that the verifier
rejects, and `recognize_clockwork_detailed` raises an exception.

## Required upstream fix

Replace the existing `for a, b, c in itertools.combinations(C_nodes, 3):`
check in `_recognize_clockwork_fast` by the following:

```python
    # Keep this condition consistent with verify_clockwork_structure.
    # It applies to crown, core, and mixed triangles alike.
    segment_of = {
        vertex: i
        for i in range(s)
        for vertex in B_segs[i] | C_segs[i]
    }
    for a, b, c in itertools.combinations(G, 3):
        if G.has_edge(a, b) and G.has_edge(b, c) and G.has_edge(a, c):
            if len({segment_of[a], segment_of[b], segment_of[c]}) == 3:
                return False, (
                    f"Triangle ({a},{b},{c}) spans three distinct clockwork segments."
                )
```

Keep the independent `verify_clockwork_structure` call unchanged; **never**
treat a failed verification as evidence of clockwork divergence. The direct
recognizer is a sufficient test for a *proposed* decomposition, and the
independent verifier provides the final acceptance condition. The correction
can be implemented as a narrow additional fast-rejection condition rather
than silently suppressing verifier errors.

## Required tests

- Construct the 9-vertex graph
  `clockwork_graph([1, 1, 1], [[0], [0], [0]], 2, [0, 1])`:
  its three identity crown matchings create a triangle meeting all
  three crown segments, while the core has no corresponding triangle.
  Confirm `_recognize_clockwork_fast(G)` returns `(False, reason)`
  with `"triangle"` in the reason, and
  `recognize_clockwork(G, fallback_enabled=False)` returns a negative
  result **without raising**.
- Check known valid clockwork constructions continue to return verified
  decompositions and their former classifications.
- Run the original order-9 failing graph6 fixture (to be obtained below)
  through `classify_clique_behavior` to verify it does not raise, and
  inspect the actual verdict and certificate.
- Run the upstream `test_clockwork.py` and `test_small.py` suites and CI.

If this exact constructed fixture does not reproduce the fast-positive
failure, retain it as a structural-negative test, then capture a test for
the actual graph6 failing in the user's run. Avoid broad exception
suppression or lowering the certification standard.

## Locate the actual graph

Before updating the upstream pinned commit, in the `pycliques-census`
Codespace:

```bash
.venv/bin/python maintenance/locate_clockwork_failure.py \
  --order 9 --start 250000 --end 260000 --bound 30 \
  2>&1 | tee history/order9-clockwork-failure.log
```

The diagnostic prints original connected-census source index, graph6 and
the unmodified traceback. It writes no `runs/` files and therefore does
not corrupt or mark any partial chunk complete. When using the pipeline,
inspect the output for `CLASSIFICATION ERROR`: `tee` alone may otherwise
mask the Python process exit code. For precise exit status use
`set -o pipefail` first.

## Preserve completed computation

Do not delete `runs/order9-bound30`. At the moment of the traceback,
the first 25 complete 10,000-graph chunks, indices `0..249999`, have
already been committed to `.done` markers and associated verdict and
unresolved sidecar files; the incomplete `250000..259999` chunk will be
replayed by the existing runner. It is correct that the original
`manifest.json` refuses to combine revised upstream binaries with those
prior chunks. Updating `pycliques-project` normally requires a **new**
run directory unless a separate, documented and validated chunk migration
procedure explicitly accounts for both upstream versions. Merely editing
the manifest to force resume would misrepresent provenance.

A source-level fix with only this additional rejection does not alter
results from previously *completed* chunks: any graph taking the new
rejection path would have raised under the old verification path. Still,
any reuse must record both versions per chunk and validate the migration.

The new standalone diagnostic lives under `maintenance/` rather than
`scripts/`; the manifest currently hashes `scripts/*`, so adding this
diagnostic does not change its run source hash.
