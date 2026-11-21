# A new complete fourth-iterate octahedral retraction (v13)

**Certified source:** McKay 10510367, pared ten-vertex graph6 `ICZVByz~_`.

An independent all-pairs maximal-clique reconstruction, using sequential
closed-neighborhood folds and exact graph isomorphism, verifies the sequence

| Pared iterate | Vertices | Edges |
| --- | ---: | ---: |
| P0 | 10 | 27 |
| P1 | 15 | 65 |
| P2 | 20 | 125 |
| P3 | 38 | 498 |
| P4 | 64 | 1,844 |

The labeled P4 host contains the displayed 12 disjoint pairs from
[`certificate.json`](certificate.json). Every two distinct target
vertices are adjacent except opposite partners, so they induce `O_12`.
The 64-entry `image_indices` array encodes the full graph retraction:
each image is the target endpoint at the indexed position. Every one
of 1,844 source edges has equal or adjacent images, and all 24 target
vertices are fixed pointwise.

The initial discovery used a mixed-integer optimization to find a
complement-dominating induced matching and then a constraint solver to
find the projection. Neither discovery algorithm is trusted by the
independent verifier. Only the complete certificate is required.

For `d >= 3`, `K(O_d) = O_{2^(d-1)}`, which is clique-divergent.
The established octahedral retraction theorem and the
behavior-preserving dominated-vertex reduction theorem imply that the
original ten-vertex graph is K-divergent.

## Reproduce

Run from the census repository root with `networkx==3.6.1`:

```sh
python research/order10_o12_dim_v13/verify.py
python -m research.order10_o12_dim_v13.replay_v12
python -m unittest discover -s tests -p test_current_root_index.py -v
```

The verifier checks the immutable v12 Git blob, exactly one removed
v12 row (10510367), all 2,787 preserved v13 records, and all 120
conditional cases; it reconstructs the entire sequence independently,
checks exact isomorphism to the archived P4, and verifies the induced
target and the complete transported projection. The historical v12
proof replay uses a read-only pathname redirection, without modifying
source files.

This is a positive-only result. Failures to find maps in other
timeboxed experiments remain inconclusive.
