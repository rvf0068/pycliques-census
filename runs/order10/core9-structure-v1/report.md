# Targeted structural investigation: 29 unresolved order-nine cores

This report records **no new clique-behavior classification**.
Mod-2 first Betti numbers are exact for each stored flag complex;
zero rules out a *connected triangular double cover of that iterate*,
but does not establish convergence. Induced clockworks are candidate
subgraphs only, never divergence certificates for their hosts.
Truncated maximal-clique counts give lower bounds, not estimates.

| Core ID | Members | Built prefix | b1(F2), G0.. | G_last maximal cliques | Clockwork observations | Seconds | Status |
|---:|---:|---|---|---|---:|---:|---|
| 2317843 | 70 | G0..G3 | 1,1,1,1 | >=513 | 0 | 0.68 | OK |
| 3148541 | 114 | G0..G3 | 1,1,1,1 | >=513 | 0 | 0.62 | OK |
| 3505942 | 133 | G0..G3 | 1,1,1,1 | >=513 | 0 | 0.62 | OK |
| 3663513 | 72 | G0..G3 | 0,0,0,0 | 355 | 0 | 0.68 | OK |
| 4929602 | 82 | G0..G3 | 0,0,0,0 | >=513 | 0 | 0.68 | OK |
| 4952669 | 86 | G0..G3 | 1,1,1,1 | >=513 | 0 | 0.57 | OK |
| 4953338 | 196 | G0..G3 | 1,1,1,1 | >=513 | 0 | 0.57 | OK |
| 4972358 | 223 | G0..G3 | 0,0,0,0 | >=513 | 0 | 0.68 | OK |
| 5418647 | 116 | G0..G3 | 0,0,0,0 | >=513 | 0 | 0.62 | OK |
| 5519188 | 141 | G0..G3 | 0,0,0,0 | 440 | 0 | 0.72 | OK |
| 5601875 | 111 | G0..G3 | 1,1,1,1 | >=513 | 0 | 0.53 | OK |
| 5645085 | 207 | G0..G3 | 0,0,0,0 | >=513 | 0 | 0.57 | OK |
| 6912818 | 63 | G0..G3 | 0,0,0,0 | 502 | 0 | 0.68 | OK |
| 6914104 | 219 | G0..G3 | 0,0,0,0 | 250 | 0 | 0.68 | OK |
| 6923397 | 82 | G0..G3 | 0,0,0,0 | 322 | 0 | 0.57 | OK |
| 6923598 | 141 | G0..G3 | 0,0,0,0 | >=513 | 0 | 0.68 | OK |
| 6938156 | 130 | G0..G3 | 1,1,1,1 | >=513 | 0 | 0.57 | OK |
| 6938971 | 117 | G0..G3 | 0,0,0,0 | 260 | 0 | 0.57 | OK |
| 6939156 | 129 | G0..G3 | 0,0,0,0 | 416 | 0 | 0.57 | OK |
| 6946361 | 121 | G0..G3 | 0,0,0,0 | 266 | 0 | 0.57 | OK |
| 6957324 | 147 | G0..G3 | 0,0,0,0 | >=513 | 0 | 0.57 | OK |
| 6958650 | 150 | G0..G3 | 0,0,0,0 | 492 | 0 | 0.57 | OK |
| 6962151 | 242 | G0..G3 | 0,0,0,0 | 299 | 0 | 0.78 | OK |
| 6974529 | 235 | G0..G3 | 0,0,0,0 | >=513 | 0 | 0.62 | OK |
| 7275185 | 91 | G0..G3 | 0,0,0,0 | 402 | 0 | 0.78 | OK |
| 7315343 | 41 | G0..G3 | 1,1,1,1 | >=513 | 0 | 0.57 | OK |
| 7316198 | 142 | G0..G3 | 0,0,0,0 | >=513 | 0 | 0.62 | OK |
| 7363619 | 75 | G0..G3 | 0,0,0,0 | >=513 | 0 | 0.98 | OK |
| 10760192 | 62 | G0..G2 | 0,0,0 | 132 | 0 | 0.67 | OK |

## Observations

- Fully probed cores: 29 of 29 recorded.
- Last-iterate WL/size signature collisions: 3 core entries.
- Matching WL hashes are only candidate pairs, not graph isomorphism.
- An observed clockwork is not a verified retraction from the host.

## Identical last-iterate fingerprints (not asserted isomorphic)

- 4929602, 4972358, 5645085

## First Betti number vectors

| b1(G0),...,b1(Glast) | Cores |
|---|---:|
| (0, 0, 0) | 1 |
| (0, 0, 0, 0) | 20 |
| (1, 1, 1, 1) | 8 |

## Next experiments

Prioritize candidates by original membership, exact last-iterate
clique count, and structural obstacles. Cover-based divergence
search is relevant only at iterates with positive H^1(F2).
Test specific verified retractions only when a candidate target
is actually identified; avoid promoting bounded searches to proofs.
