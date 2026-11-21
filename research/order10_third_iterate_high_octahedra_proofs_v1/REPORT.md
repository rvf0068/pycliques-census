# 350 complete raw third-iterate octahedral retractions for ten-vertex stiff cores

**Proof-only archive:** All 350 full graph-retraction maps are stored in
[certificates.json](certificates.json), in increasing original McKay index
order. They are for distinct graphs fully unclassified in the frozen
v9 order-ten census. No historical classification file is changed by this
proof record.

## Mathematical theorem

For each of the **350** source graphs \(G\), there is a complete
ordinary graph retraction
\[
K^3(G)\longrightarrow O_d,\quad
O_d=\overline{dK_2},\qquad d\in\{4,5,6\}.
\]

| Induced target | Proved source graphs |
|---|---:|
| \(O_4\) | 155 |
| \(O_5\) | 74 |
| \(O_6\) | 121 |
| **Total** | **350** |

The graph \(O_d\) is K-divergent, since its maximal cliques choose one
endpoint of each of \(d\) disjoint nonedges and
\(K(O_d)\cong O_{2^{d-1}}\). Neumann-Lara's Retraction Theorem gives
K-divergence of \(K^3(G)\) from a graph retract onto \(O_d\), and
therefore K-divergence of each original \(G\).

Every certificate provides:
- the original McKay index and graph6 string;
- the exact \((|V|,|E|)\) counts of the **raw**
  \(G,K(G),K^2(G),K^3(G)\) (no intermediate paring);
- the complete list of \(d\) opposite pairs of the induced \(O_d\);
- an image for **every** vertex of \(K^3(G)\), fixing all target
  vertices and sending adjacent vertices to adjacent **or equal**
  image vertices.

## Independent finite verification

The standalone [verify.py](verify.py) authenticates the frozen v9 Git
blob, requires each indexed source to have pared order ten and the
three `- - -` unclassified fields, reconstructs all three clique
graphs, and checks the entire target and all source edges under the map.

Two **independent** maximal-clique enumerators, NetworkX's
`find_cliques` and a standalone bitset Bron--Kerbosch routine, must
agree at every iterate. Complete projections are replayed independently
of the discovering CSP solver. Mutation tests reject a broken fixed
section and an altered edge count.

Reproduce in the census repository with NetworkX 3.6.1:

```bash
python research/order10_third_iterate_high_octahedra_proofs_v1/verify.py --self-test
```

**Only the positive certificates are used as proofs.** No homology
or Betti computation is required.

## Discovery provenance and incomplete cases

The first eight-way search used the immutable 1,393-case unclassified
stiff ten-core v9 cohort. Seven whole batches finished and yielded
312 complete positive maps. The eighth, batch 3, was interrupted by an
external GitHub runner shutdown after outputting 36 complete positive
maps. All 36 are preserved in `batches/batch3_partial.json`, which
is **not** represented as a complete search. The old first-run
positive witnesses are preserved in `batches/batch0.json` through
`batch7.json` (with batch 3 partial), from
[GitHub Actions 44847590866](https://github.com/rvf0068/pycliques-census/actions/runs/44847590866).

A corrected second run of all eight batches
([GitHub Actions 44848083302](https://github.com/rvf0068/pycliques-census/actions/runs/44848083302))
completed successfully with no errors and consistent accounting.
Its batch 3 yielded 38 positive maps: the same 36 from the interrupted
job, byte-equivalent as JSON witness objects, **plus two additional**
previously unclassified stiff ten-vertex graphs:
McKay 11638656 (`IEjevL{kw`) retracts to (O_6), and
McKay 11652579 (`IEnfbzkxo`) retracts to (O_4).
The complete successful batch-3 result is preserved in
`batches/batch3_corrected.json`.

The standalone `audit_batches.py` runs alongside the independent
raw-iterate `verify.py` in CI: it authenticates every archived batch,
checks frozen-source cohort partitioning and successful-batch summaries,
compares **every archived projection** exactly with a mathematically
replayed canonical positive, verifies inclusion of the old partial
witnesses in the corrected complete batch, and detects adversarial
modification to a batch 5 or corrected batch 3 map. Thus no archived
search-result claim bypasses the proof verifier.

The original discovery scanner had flaws in deadline and skipped-core
accounting: its clock did not cover all CSP/setup work, and the
`examined` counter excluded some oversize cases. Copilot's findings
were addressed in [PR #51](https://github.com/rvf0068/pycliques-census/pull/51)
by bounding facet generation *during* clique construction, extending
deadline checks, and accounting for skipped inputs.
**Those issues do not affect the validity of a complete retraction
independently reconstructed here**, but mean that negative and
completeness statements about the first scan would not be justified.

The six original pilot cores (5502890, 6555024, 6946005, 6954458,
6954725 and 6954734) are included in the 350 total, not counted again.

## Census implications

The separate [merged nine-core O5/O6 proofs](../order10_ninecore_high_octahedra_v1/REPORT.md)
already cover 351 *other* original ten-vertex graphs with pared order
nine. These new 350 have pared order ten, hence the cohorts are
disjoint. Upon complete independent CI replay and a separate
versioned certified census index update, the two proof sets
could remove exactly \(351+350=701\) cases from the frozen 7,920
unresolved v9 population, leaving 7,219.

This archive **does not edit v9 or the authoritative root**.
The 4,509 conjecture-dependent cases are untouched. It does not
claim K-convergence for cases without positive certificates.
