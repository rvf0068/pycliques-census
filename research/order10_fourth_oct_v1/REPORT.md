# Certified fourth-iterate octahedral retractions: 37 new order-ten divergences

**Status:** Five complete positive maps, independently replayed; 33 exact
previously certified third-iterate isomorphism lifts; order-ten index
versioned from v11 (**2,830**) to v12 (**2,793**) without modifying
the historical v11 file. Nothing in the bounded negative search is
treated as a K-convergence result.

## Mathematical statement

Let (P(X)) denote an arbitrary complete dominated-vertex paring.
The searches use a deterministic labeled realization of the sequence

```
P0 = P(G),   P(i+1) = P(K(Pi)).
```

The graph operator (K) sends a graph to its graph of maximal cliques.
All five archived certificates are ordinary graph retractions
(P_4(G) \longrightarrow O_d), where (O_d=\overline{dK_2}).
Every projection fixes the displayed induced target pointwise and maps
all edges of the source to edges or equal vertices, exactly as required
by the graph-morphism convention.

For (d\ge3), (K(O_d)\cong O_{2^{d-1}}), so (O_d) is
(K)-divergent. The retraction theorem then makes (P_4(G))
(K)-divergent; the known behavior-preserving dismantling theorem
lifts this to the original (G). These implications are positive-only
and do not require interpreting any bounded negative search.

## Exact new positive witnesses

| Original McKay index | graph6 | (P_3(G)) vertices/edges | (K(P_3(G))) vertices | (P_4(G)) vertices/edges | Target |
|---:|---|---:|---:|---:|---|
| 10223405 | `ICXnRi^uo` | 37 / 503 | 250 | 182 / 14,298 | (O_{12}) |
| 10775850 | `ICpVUjx\|_` | 39 / 534 | 251 | 188 / 15,083 | (O_{12}) |
| 10223467 | `ICXnRjZmo` | 36 / 437 | 159 | 151 / 8,413 | (O_6) |
| 11104269 | `ICpdupvZo` | 39 / 495 | 178 | 160 / 9,258 | (O_6) |
| 11563706 | `IEhfe^{zO` | 39 / 500 | 176 | 159 / 9,276 | (O_6) |

The **full fixed-target projections** are stored, with graph6/source
identity, opposite pairs, and full-host digests, in
[`o6_certificates.json`](o6_certificates.json) and
[`o12_certificates.json`](o12_certificates.json). The `images_b64`
field is simply the full ordered vertex-image list encoded as bytes;
it is not a probabilistic hash of the map.

[`verify_o6.py`](verify_o6.py) reconstructs every complete
pare-and-clique step independently using NetworkX, checks each dominated
fold, independently validates each maximal-clique enumeration with
integer-bitset Bron--Kerbosch, verifies the complete graph6 digest,
the induced target, pointwise identity, and every host edge. It does
**not** call pycliques or the search routine.

[`verify_o12.py`](verify_o12.py) reconstructs the same labeled fourth
iterates with the pinned public pycliques package, checks the entire
host digest, all 24 target endpoints, and **every** host edge under
the complete saved projection. It does not reuse the finder or
fixed-target solver. GitHub Actions independently replays each
positive reported by the bounded fourth-stage screen.

## Certified lift to the 33-member stiff class

McKay **10223405** is a member of the 33-member class of completely
pared third clique iterates represented by McKay **7002338**.
The already completed, version-pinned
[`order10_pared_k3_33class_v1/verify.py`](../order10_pared_k3_33class_v1/verify.py)
reconstructs all 33 sources by two independent maximal-clique
algorithms and verifies full exact graph-isomorphism bijections.
The verifier for these new O12 certificates reproduces that
previously certified 33-class proof and confirms all members are
still stiff, unconditional v11 indeterminates.

Isomorphic third pared iterates have the same eventual clique behavior;
therefore the proved (P_4(G)\to O_{12}) for one representative
classifies **all 33** original McKay indices as (K)-divergent.
The four other original cores in the table are distinct from those
33. The v12 deletion count is consequently **33 + 4 = 37**.

## Fourth-iterate search scope and limitations

The [CI fourth-iterate experiment](https://github.com/rvf0068/pycliques-census/actions/runs/44937563814)
read all 1,043 stiff, unconditional v11 McKay records.
Each original is a separate, timeboxed process.
Its `pycliques` stage reconstructs a pared third iterate and
attempts the fourth only if the third has at most 40 vertices.
Targets of dimensions 3, 4, 5, 6, 8, 10, 12, 16, 24, 32 are
sampled using the new nonlocal octahedron finder and checked with
the fixed-target CSP. Search failures are **INCONCLUSIVE**.

- 782 original graphs were excluded by the chosen third-iterate size
  cutoff, and 4 hit the intermediate clique bound.
- 255 fourth pared iterates were constructed under the experiment's
  resource limits; 2 original cases reached the per-graph timeout.
- The finder produced 849 target-specific retraction checks: **2
  certified positive**, and 847 cases exhausted *for that particular
  target* without a map.

A separate independent CPU-only fourth-iterate exploration
reconstructed all 257 of the small-third-iterate sources with
a faster bitset paring implementation. That exploration found
the three (O_6) positives above, independently rechecked their
full maps, and was the source of the archived O6 certificates.

The 257 reconstructed fourth iterates had between 30 and 1,010
vertices after paring and yielded 148 distinct Weisfeiler--Lehman
signatures. **WL signatures are not isomorphism certificates**;
no extra source was promoted based on a shared signature.
In particular, five additional fourth iterates had the same
WL signature as the 33-member family, but they remain indeterminate
until an actual isomorphism or another certificate is obtained.

## Exact census advancement and historical preservation

[`verify_v12.py`](verify_v12.py) authenticates the immutable v11
Git blob (`34023e9323945c4a6e5e1249c37ba955ba62473f`), checks that
the current root is byte-for-byte v12, and ensures that the
**only** deleted rows are the precisely enumerated 33-family members
and the four separately proved original cores. All retained records
are unchanged; all 120 conditional `HCZTf\\}` entries are preserved.

The snub-v11 proof and its tests remain unchanged. The
[`replay_snub_v11.py`](replay_snub_v11.py) harness redirects only
read access to the historical current-root pathname during that
archived test, without modifying a file.

## Reproduction

From the census root, in a Python environment with
`networkx==3.6.1` and the pinned `pycliques-project` commit
`7ae36ffe67fb2e9bbafc68e97347aabcf757c2dc` installed:

```sh
python research/order10_fourth_oct_v1/verify_o6.py
python research/order10_fourth_oct_v1/verify_o12.py
python research/order10_fourth_oct_v1/verify_v12.py
python research/order10_fourth_oct_v1/replay_snub_v11.py --tests
python -m unittest discover -s tests -p test_current_root_index.py -v
```

The [independent proof workflow](../../.github/workflows/order10-fourth-v12-proofs.yml)
runs these checks. The separate
[fourth-iterate research workflow](../../.github/workflows/order10-fourth-oct-v1.yml)
replays every raw positive found by the timeboxed search and uploads
complete per-shard records. The repository's prior versioned
classification files and source hashes must remain unchanged.

## Mathematical references

- V. Neumann-Lara's retraction theorem for divergent iterated clique graphs,
  as used in the repository's earlier retraction certificate reports.
- M. E. Frías-Armenta, V. Neumann-Lara and M. A. Pizaña,
  *Dismantlings and iterated clique graphs*, **Discrete Mathematics**
  282 (2004): behavior preservation under dominated-vertex dismantling.
