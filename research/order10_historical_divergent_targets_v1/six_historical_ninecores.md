# Independently screened historical divergent nine-core certificates

The original order-nine census, retraction stage, bound-60 and
bound-70 stages proved the clique divergence of six particular
stiff nine-vertex cores which subsequently appeared in the
post-v3 order-ten core cross-reference. Their **historical positive
evidence** is indexed in
[reports/order10_core9_crossref_v1/matches.tsv](../../reports/order10_core9_crossref_v1/matches.tsv).

The following exact mod-2 Betti computations use raw iterates:
no dominated-vertex deletion occurred in these examples.
All reported groups outside the indicated nonzero dimension,
up to homological dimension five, vanish.

| Proven divergent core | Graph6 | Δ(G) | Δ(K(G)) | Δ(K²(G)) |
|---:|---|---|---|---|
| 6938923 | `HEht}pl` | β₂=1 | β₂=1 | β₂=1 |
| 6939350 | `HEht~bl` | β₂=1 | β₂=1 | β₂=1 |
| 7454135 | `HEnb~jl` | β₂=1 | β₂=1 | β₂=1 |
| 9678187 | `HQyuzpt` | β₂=1 | β₂=1 | β₂=1 |
| 10768817 | `HUZ~v~}` | β₃=1 | β₅=1 | order exceeds limit 40 |
| 11363569 | `HUzrv~}` | β₂=1 | β₄=1 | order exceeds limit 40 |

**These are homology statements**, not assertions that each
clique complex is homotopy-equivalent to the corresponding sphere.

The two third completely pared K-iterates of our unresolved
cores `6914104` (37 vertices) and `6962151`
(40 vertices) have reduced mod-2 Betti vectors supported
only in dimension three and dimension four, respectively,
through degree five. Thus the first four rows are
homologically forbidden as ordinary graph retracts in
iterates 0,1,2, and almost all of the last two rows are also
forbidden. The remaining unexcluded graphs are already
treated by earlier versioned retraction experiments:

- `HUZ~v~}` itself is the repeated-suspension target
  `C_5^c * O_2` checked in PR #24.
- `K(HUzrv~})` is isomorphic to `C_14^c`,
  excluded by PR #22.

Therefore these six previously identified stiff cores,
even after two raw clique iterations where the order
bound permits, give no **new** proven divergence witness
via an ordinary retraction from either of the two host
third iterates.

The complete reproducible calculation is the test
`test_historical_six_divergent_nine_cores_and_first_iterates`
in `tests/historical_divergent_targets_v1_cases.py`.
It reconstructs each graph from the exact frozen graph6,
constructs maximal-clique intersection graphs explicitly,
checks the absence of dominated vertices, computes all
mod-2 simplex boundary ranks with the pinned library and
verifies the one stated graph isomorphism. This concise
six-core screen is **independent of the larger 10,104-source
catalog computation**.

Do not infer from these exclusions that any unresolved
original ten-vertex graph is K-convergent or K-nondivergent.
