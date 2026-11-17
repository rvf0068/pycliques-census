# Clique-graph target retraction experiment: verified conclusions

Completed independently in GitHub Actions run
[44186571739](https://github.com/rvf0068/pycliques-census/actions/runs/44186571739)
on November 17, 2026, with all required verification checks successful.

This separately pinned experiment concerns *only* the third completely pared
clique iterates of two unresolved nine-vertex stiff cores. The original
ten-vertex classes represented by these cores are not reclassified.

| Stiff core ID | Third pared order | Betti profile over F2 | Original order-10 members |
| ---: | ---: | --- | ---: |
| 6914104 | 37 | reduced H3 rank 1, other ranks through H5 zero | 219 |
| 6962151 | 40 | reduced H4 rank 1, other ranks through H5 zero | 242 |

## Homological pruning

For K(susp(C4)) we recover O4, already proved not to be a retract of
either host by the preceding experiment (PR #22). For 5 <= n <= 20,
an exact boundary-matrix computation gives

    dim Htilde_2(Delta(K(susp(Cn))); F2) = 1.

Both hosts have zero Htilde_2, so cannot retract onto any of these
targets. For n >= 21 the target has 2n > 40 vertices.

The number of vertices of K(Cn^c) is the Perrin number Pn,
i.e. the number of maximal independent sets of an n-cycle.
A maximal independent set corresponds to a cyclic binary word with
neither adjacent ones nor three consecutive zeros. The associated
three-state transfer matrix has characteristic polynomial t^3-t-1,
giving Pn = P(n-2)+P(n-3), and:

| n | 8 | 9 | 10 | 11 | 12 | 13 | 14 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| Pn | 10 | 12 | 17 | 22 | 29 | 39 | 51 |

For n >= 14, Pn >= 51, so the target is too large for either host.

For 8 <= n <= 13, independent target calculations give:

| Target | Exact obstruction / disposition |
| --- | --- |
| K(C8^c) | reduced beta2 = 1, homologically impossible for both hosts |
| K(C9^c) | reduced beta3 = 4, exceeds the 37-vertex host's rank 1, and the 40-vertex host's rank 0 |
| K(C10^c) | reduced beta3 = 1, admissible **only for core 6914104** |
| K(C11^c) | reduced beta5 = 1, homologically impossible for both hosts |
| K(C12^c) | target complement has 46 edges; every induced 29-vertex complement subgraph has at least 73 edges in the 37-vertex host and at least 57 in the 40-vertex host |
| K(C13^c) | 39 vertices exceeds the first host; 663 edges exceeds the 40-vertex host's 601 |

The induced-complement-edge lower bound is elementary: if a host
complement has e edges and the omitted vertex set has size r, the
complement induced on the remaining vertices has at least e minus
the sum of the r largest complement degrees. This does not require a
branch-and-bound search or an unproved complexity assumption.

## The sole remaining target: K(C10^c)

K(C10^c) has 17 vertices, 110 edges and reduced third Betti number one.
The frozen graph6 labeling of the 37-vertex host comes from
[runs/order10/core9-structure-v1/records/06914104.json](../../runs/order10/core9-structure-v1/records/06914104.json),
iterate index 3. The independently constructed target graph6 is
`P~~~z}~f{^y~o~y^}Z~q^~Y{`.

- The ISMAGS induced-subgraph search found exactly **24 distinct vertex sets**.
- A separate VF2 search checked **960 labeled induced embeddings**, representing exactly the same 24 vertex sets.
- The standalone domain-reduction retraction solver fully exhausted all 24 copies with **166 states** and **142 candidate assignments** in total; every result was negative.
- Independently, the pinned general graph retraction engine also exhausted all 24, with the same total of **166 states** and **142 assignments**; no configured resource bound was reached.
- Each search fixes the target pointwise and permits edges to be mapped to edges **or equal** vertices, as required by the graph-morphism convention.

Consequently, neither of the two third pared iterates retracts onto any
`K(susp(Cn))` for n >= 4 nor onto any `K(Cn^c)` for
n >= 8. This is a complete negative result for these precisely stated
families, **not** a proof of convergence or nondivergence of either
nine-vertex core or of its represented original ten-vertex graphs.

## Independent verification

The code, immutable source references and CI workflow live in this
pull request. To reproduce in a Codespace or Linux checkout, run:

```bash
bash scripts/bootstrap_core9_three_target_v1.sh
.venv-core9-three-v1/bin/python scripts/core9_clique_targets_v1.py run
.venv-core9-three-v1/bin/python scripts/core9_clique_targets_v1.py verify
.venv-core9-three-v1/bin/python scripts/core9_clique_targets_v1.py report
```

The successful workflow uploaded the complete manifest and two
machine-readable JSON result records as the artifact
[core9-clique-target-retractions-v1](https://github.com/rvf0068/pycliques-census/actions/runs/44186571739).
The accompanying [source-and-artifact checksums](artifact_checksums.md)
allow a reviewer to compare exact source and saved outputs.
No prior census run, historical proof, or original verdict was changed.
