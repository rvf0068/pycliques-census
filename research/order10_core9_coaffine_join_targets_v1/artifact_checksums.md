# Independently verified JSON evidence: SHA-256 fingerprints

GitHub Actions run: https://github.com/rvf0068/pycliques-census/actions/runs/44192083811

Published artifact: `core9-coaffine-join-targets-v1`, ID `14376907951`

| File | Exact SHA-256 |
|---|---|
| `manifest.json` | `976d6730c04a9838c84bce58456aa1348f8a28474acfdd6f85b5826edac7f1c9` |
| `records/06914104.json` | `f56e95d3a688e59554c52c2ab0504e5882647a3e5ef790bfae783a7bcfd6570f` |
| `records/06962151.json` | `4d6125183c6af3d21e9d20ecfe29210fc651b0cfe9defc4014283cd9ca9f6594` |

ZIP file SHA-256 as downloaded and inspected: `899a19a46bf813751fa9270ebc3ab7cf0abfc8c1abfff5369cbcceb72879e908`.

To check independently, download and extract the GitHub Actions artifact,
compare SHA-256 values, then verify its records under the same pinned
environment using:

```bash
sha256sum manifest.json records/06914104.json records/06962151.json
.venv-core9-three-v1/bin/python scripts/core9_coaffine_join_targets_v1.py verify --output .
```

The short [target_counts.tsv](target_counts.tsv) records every selected
(n,r) case, the induced-subgraph count, all independently rejected
full-CSPs and the SHA-256 of the sorted induced vertex sets.
The read-only CI job verifies that index row by row against freshly
regenerated complete proof records.

**Scope:** These files exclude only the ten selected rank-one
homology-matched coaffine-join targets, not all K-divergent retracts.
