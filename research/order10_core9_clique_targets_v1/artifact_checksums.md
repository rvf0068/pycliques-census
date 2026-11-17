# Authenticated workflow artifact fingerprints

CI run: https://github.com/rvf0068/pycliques-census/actions/runs/44186571739

Artifact name: core9-clique-target-retractions-v1

These are SHA-256 digests of the •exact byte streams• downloaded from the successful GitHub Actions run. The JSON files themselves are regenerated from code and frozen inputs, and the `verify` action independently recomputes the complete records.

| File | SHA-256 |
|---|---|
| `manifest.json` | `cc3727fe146b61adc710a9eb7bde5fcb7e0fa2ca685aee486a645408f1fffabd` |
| `records/06914104.json` | `6c1e427f1b1b94c2e91fc82f3b6cd62eb53323b99441135b7b7789f24d268f7a` |
| `records/06962151.json` | `e4a99f81797528d399e9c3a477dc4a3efdf70ccb7dc7f018d9bab388a14805c5` |

Archive ZIP digest as downloaded: `c46d895c540c38352008094d8a34719855f593d27e0cc5eea22a6fffdb4b62b1`.

Verification command after downloading and extracting the artifact:

```bash
sha256sum manifest.json records/06914104.json records/06962151.json
.venv-core9-three-v1/bin/python scripts/core9_clique_targets_v1.py verify --output .
```

A negative finite search is scoped to retractions onto the explicitly checked clique-graph target families, not all possible divergent retracts or the graph's clique behavior.
