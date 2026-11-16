# Post-PR14 AC-3 covering search on eight nine-vertex cores

All claims are about *completely pared nine-vertex core graphs*;
no conclusion is transferred automatically to the represented ten-vertex graphs.
EXHAUSTED means precisely the finite double-cover / clockwork-source family
recorded in the manifest, not absence of clique divergence.

| Core ID | Original ten-graph members | Deck radius | Baseline | Expanded | New eligible clockwork pairs | Expanded assignments |
|---:|---:|---:|---|---|---|---:|
| 2317843 | 70 | 4 | EXHAUSTED | EXHAUSTED | [[2, 1], [2, 2], [3, 1], [3, 2]] | 360 |
| 3148541 | 114 | 4 | EXHAUSTED | EXHAUSTED | [[2, 1], [2, 2], [3, 1], [3, 2]] | 324 |
| 3505942 | 133 | 4 | EXHAUSTED | EXHAUSTED | [[2, 1], [2, 2], [3, 1], [3, 2]] | 396 |
| 4952669 | 86 | 4 | EXHAUSTED | EXHAUSTED | [[2, 1], [2, 2], [3, 1], [3, 2]] | 288 |
| 4953338 | 196 | 4 | EXHAUSTED | EXHAUSTED | [[2, 1], [2, 2], [3, 1], [3, 2]] | 360 |
| 5601875 | 111 | 4 | EXHAUSTED | EXHAUSTED | [[2, 1], [2, 2], [3, 1], [3, 2]] | 342 |
| 6938156 | 130 | 4 | EXHAUSTED | EXHAUSTED | [[2, 1], [2, 2], [3, 1], [3, 2]] | 366 |
| 7315343 | 41 | 4 | EXHAUSTED | EXHAUSTED | [[2, 1], [2, 2], [3, 1], [3, 2]] | 396 |

## Interpretation

Both configurations use the same new pinned AC-3 implementation.
The baseline reproduces the old finite family with the optimized search.
The expanded configuration searches R_(2m)^n with additional n=1,2
subject to actual cover radius and source-order restrictions.
A configuration setting alone does not imply a family member was eligible.
Certificates, if found, are rechecked independently against the base core.
No positive certificate is inferred from a bounded negative search.
