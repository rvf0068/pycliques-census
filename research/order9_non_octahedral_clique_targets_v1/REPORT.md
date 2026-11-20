> **Provenance and qualification (2026-11-20).** This is an archived report recovered
> from the preceding interrupted research session. Its independent replay was reported
> successful *in that session*; the underlying `verify_all_dbg.py` and complete per-copy
> JSON evidence were **not available in this GitHub change**. Consequently this PR
> preserves a detailed historical research record and independently audits a smaller
> set of structural claims; it is **not** a fresh independent replay of every
> 48-case negative certificate. The companion `summary.json` records precise scope,
> exclusions, and a genuinely incomplete `P_3` search at index 260910.
>
> The historical root `indeterminate_order_9.txt` still has 54 entries; the 49
> studied here exclude five *subsequently proved* divergent cases: McKay indices
> **242316** (PR #44), **248687** (PR #39), **250693** (isomorphic to the
> `HQqvUx}` core in PR #42), **252075** (PR #45), and **255141** (PR #42).
> No original census classification or working index is edited.

# Non-octahedral clique-target retractions in the nine-vertex census

## Recovered state after message-delivery timeout (20 November 2026)

**Scope.** We test ordinary graph retractions, with adjacent vertices allowed to map to adjacent **or equal** vertices, from completely pared clique iterates \(P_j\), \(0\le j\le3\), of the **49** unresolved connected nine-vertex graphs onto the known divergent *non-octahedral* families

- \(K(\operatorname{Susp}(C_n))\), \(n\ge5\);
- \(K(C_n^c)\), \(n\ge8\), where \(C_n^c\) is the complement of a chordless \(n\)-cycle.

The eight-vertex snub disphenoid is **not** assumed divergent. There are 36 snub-conditional nine-vertex records and 13 other unresolved records. The 49 records reduce to 22 third-iterate representative classes, of which 21 cover 48 records and one is index **260910**.

**Verified result.** For the 48 smaller records, none of \(P_0,P_1,P_2,P_3\) retracts to either named target family. The proof uses exact homological obstructions, necessary induced-subgraph obstructions, and finite exhaustive searches, not merely unsuccessful timeboxed searches. **Index 260910 is still incomplete at \(P_3\)** and has not been classified. No newly proved clique divergence was found.

`verified_summary.json` reports `"status":"VERIFIED"`; the replay in `verify_all_dbg.py` independently passed, with \(\approx 37\) seconds wall time on Python 3.13.5 / NetworkX 3.6.1. An earlier timeout occurred during additional replay, not during a discovery of a positive retraction.

## Reconstruction and finite checks

- The original 49 McKay records are grouped by their pared iterate. There are 94 distinct earlier-iterate cases and 22 third-iterate representatives. The 28 snub-related records share an independently established isomorphism class at \(P_3\).
- At \(P_0\) there are no order-admissible nonoctahedral targets. At \(P_1\) and \(P_2\), **143** target-host checks are exhaustive, with **483** induced target vertex sets, **109** surviving elementary projection-domain pruning, and **zero** retractions.
- Exact mod-two homology obstructs many remaining targets. A relative simplicial boundary computation shows \(\widetilde\beta_2(\Delta(K(\operatorname{Susp}(C_n))))=1\) for all \(n\ge5\); the proof uses \(3n\) mixed edges, \(6n\) mixed triangles and \(3n\) mixed tetrahedra, with boundary ranks \(3n-1\) and \(3n\). The first and second nonzero target ranks for \(K(C_n^c)\) are separately reproduced by exact clique-complex calculations.
- For the **21** smaller third-iterate representatives, a complement-induced-matching search proves **no induced \(O_8\)**. Conversely the targets \(K(C_n^c)\) for \(12\le n\le17\) each have an induced \(O_8\), with an explicit matching witness saved for every \(n\). This excludes those six targets as induced subgraphs and therefore as retracts. Larger targets exceed these hosts' orders.
- An independent induced-path/cycle-anchor enumeration excludes **every** \(K(C_{11}^c)\) from all 21 third-iterate representatives. It uses the fact that the complement of \(K(C_{11}^c)\) has two disjoint eleven-vertex components, including an induced \(C_{11}\). An embedding would require a complement-induced \(C_{11}\) with eleven common neighbors in the host; the finite audit finds none.
- The only third-iterate hosts with suitable third homology for \(K(C_{10}^c)\) are indices **208409, 249436, 248936, 250814**. The first two have no required complement-induced ten-cycle with a pair of compatible outside vertices (44,522 and 162,599 ten-cycles enumerated). The latter two have respectively **24 and 608** induced copies of the complete target, and every ordinary retraction CSP was exhausted. No target was a retract.
- The retraction machinery passed positive-control tests for graphs constructed to retract onto \(K(\operatorname{Susp}(C_5))\), \(K(\operatorname{Susp}(C_6))\), \(K(C_8^c)\) and \(K(C_{11}^c)\).

## Outstanding large case: McKay index 260910

\(P_3\) has **132 vertices and 7,880 edges**. The bounded search records in `large_case_260910_bounded.json` explicitly say `TIMEOUT`, not `EXHAUSTED`. In particular a partial \(K(C_{10}^c)\) search enumerated 81 candidate induced copies with no feasible domain so far, which is *not* a proof of absence. Several other candidate target classes were also time-limited. The exact high-degree homology needed for useful further pruning is not complete.

`domination_260910.json` records a separate optimization experiment, but it is not a certified unsatisfiability or non-retraction proof.

## Reproduce

Requirements: Python 3.13.5 (or compatible), NetworkX **3.6.1**, plus the bundled scripts/data. Run from this directory:

```bash
python verify_all_dbg.py
```

The debug verifier prints the completion of each stage and checks that the previously saved JSON records are reproduced. Its concluding line begins `VERIFIED`. The underlying modular checks include `matching_witness.py`, `kc11_cycle_anchor.py`, `kc10_cycle_screen.py`, and `targets_search.py`. A timeout or pattern limit must never be promoted into a negative conclusion.

The `previous/` and `cond/` directories provide the prerequisite nine-core and snub-dependent reconstruction code and frozen evidence. Historical census lists and GitHub classifications are **unchanged**.

**Mathematical caveat:** These results exclude only the named target families and only through the third pared clique iterate. They do not imply \(K\)-convergence or exclude more general divergent retracts or later-iterate phenomena.