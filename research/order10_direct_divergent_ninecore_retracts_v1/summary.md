# Nine newly certified K-divergent stiff ten-vertex graphs

These are nine NEW positive graph-retraction certificates; none
has a dominated vertex. All nine were in the frozen v4 list.

Their targets are two independently verified connected
2-coaffine suspensions: core 10768817 (HUZ~v~}) and
core 11363569 (HUzrv~}). They are K-divergent by
Larrion--Neumann-Lara--Pizana (2009), On expansive graphs,
Theorem 4.6. Neumann-Lara's Retraction Theorem implies
that a graph retracting onto a K-divergent graph is
also K-divergent (see Edge contraction and edge removal
on iterated clique graphs, 2013).

All 2,403 frozen stiff ten-vertex sources were independently
screened against all SIX previously proved divergent
nine-vertex cores, allowing deletion of any one source vertex
and checking every exact induced isomorphism and all
possible weak-morphism images of the removed vertex.
Edges may map to edges OR equal vertices. The search found
31 induced target copies but only NINE distinct graphs
admitting a retract. Their complete ten-to-nine projection
and nine-to-ten induced section maps are stored in
certificates.json and new_divergent.tsv.

| Original McKay index | Graph6 | Divergent nine-core target |
|---:|---|---:|
| 10768894 | ICpU}z~~o | 10768817 |
| 11363661 | ICrUqz~~o | 11363569 |
| 11372238 | ICrVrz^vo | 11363569 |
| 11475102 | ICrr~r^vo | 11363569 |
| 11519660 | ICxu}z^vo | 10768817 |
| 11541397 | ICzr~r^vo | 11363569 |
| 11655985 | IEr]vz}}o | 10768817 |
| 11660877 | IEznvj^vo | 10768817 |
| 11716425 | IUzrv~}~_ | 11363569 |

**Nine new graphs are proved K-divergent.** Negative searches
against these six models are NOT proofs of K-convergence.

| Remaining core order | Indeterminate originals (v5) |
|---|---:|
| 8 (snub disphenoid) | 2,092 |
| 9 (29 stiff classes) | 3,738 |
| 10 (stiff original) | 2,394 |
| TOTAL | 8,224 |

The old v4 index and all earlier run/report data remain intact.
The new v5 index differs only by removal of these nine
exact original indices, retaining all 8,224 other records.

Reproduce with Python and NetworkX 3.6.1:

    python scripts/direct_divergent_ninecore_retracts_v1.py verify
    python -m unittest discover -s tests -p test_direct_divergent_ninecore_retracts_v1.py -v

The verifier checks frozen source hashes and rebuilds the
complete v4 index, then regenerates all positive and negative
finite-family checks and every committed byte of v5.
