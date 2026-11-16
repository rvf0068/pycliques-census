# Historical order-nine cross-reference for the order-ten pared cores

The 35 distinct completely pared nine-vertex representatives were
matched by actual graph isomorphism to the full 261,080-entry
McKay/pyg6data connected-nine-graph source, using its zero-based order.
No canonical identity of differently labeled graph6 encodings is assumed.

**Historical classification is about the nine-vertex core only.**
It is not a new certificate for any original ten-vertex member graph.
A positive historical verdict is recorded with its original stage
and reason; it is not upgraded to a newly replayable certificate.

## Historical status of the 35 core classes

| Historical verdict | Distinct 9-cores | Original order-10 members |
|---|---:|---:|
| DIVERGENT | 6 | 300 |
| CONVERGENT | 0 | 0 |
| INDETERMINATE | 29 | 3,738 |

## First positive historical stage

| Stage | Cores |
|---|---:|
| initial | 2 |
| c10 | 0 |
| bound60 | 1 |
| bound70 | 3 |
| - | 29 |

## The four rediscovered divergent nine-cores

| Order-10 core ID | Order-9 index | First positive stage | Witness description |
|---:|---:|---|---|
| 6938923 | 250684 | bound70 | eventually has a special octahedron (index 3, dimension 4) |
| 6939350 | 253557 | bound70 | eventually has a special octahedron (index 3, dimension 4) |
| 7454135 | 255039 | bound70 | eventually has a special octahedron (index 3, dimension 7) |
| 9678187 | 259791 | bound60 | eventually has a special octahedron (index 3, dimension 4) |

## Cores already divergent in the initial order-nine census

| Order-10 core ID | Order-9 index | Original members | Initial reason |
|---:|---:|---:|---|
| 10768817 | 260927 | 33 | [LNP09, Theorem 4.6]: graph is the suspension of a connected graph H admitting a 2-coaffination; hence it is expansive and therefore clique divergent |
| 11363569 | 261008 | 36 | [LNP09, Theorem 4.6]: graph is the suspension of a connected graph H admitting a 2-coaffination; hence it is expansive and therefore clique divergent |

## Outputs

- matches.tsv: all 35 isomorphism matches, historical verdicts, and evidence paths
- unclassified.tsv: representatives still unresolved after all historical stages
- manifest.json: frozen dataset and historical source/output SHA-256 digests

Results are reproducible and immutable. Repeated build verifies rather
than overwrites. The source census and all completed stages are read-only.
