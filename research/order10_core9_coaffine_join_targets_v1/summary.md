# K-divergent coaffine-join target census: exact negative result

**Source:** third *completely pared* clique iterates of the stiff
nine-vertex graphs `HEhev^{` (core 6914104; 37 vertices) and
`HEhvfzm` (core 6962151; 40 vertices).

**Evidence:** independent run and full bounded replay in
[GitHub Actions 44192083811](https://github.com/rvf0068/pycliques-census/actions/runs/44192083811),
November 17, 2026. All regression tests and the read-only workflow
passed. Source and output hashes are recorded in
[artifact_checksums.md](artifact_checksums.md), and all ten result
counts are frozen in [target_counts.tsv](target_counts.tsv).

## A mathematical source of new certified K-divergent targets

Define T(n,r) = C_n^c * O_r for n>=5 and r>=1. The graph
`O_r` is the complement of r disjoint edges; `*`
denotes the graph join.

**Proposition.** Every T(n,r) is K-divergent.

**Proof.** Write T(n,r)=susp(C_n^c * O_(r-1)) (O_0 denotes
the empty join factor). The graph C_n^c is connected for n>=5.
Rotating its vertices by one position is an automorphism taking
each vertex to a distinct nonneighbor. Swapping the two endpoints
of each of the r-1 pairs of O_(r-1) is an automorphism with
the same property. Their union is a 2-coaffination of the join,
which remains connected. The suspension/2-coaffination theorem
[LNP09, Theorem 4.6] makes T(n,r) expansive, hence K-divergent. QED.

**Proposition (homotopy types).** The clique complex of T(n,r)
is homotopy equivalent to the r-fold suspension of Ind(C_n).
In particular,

- if n=3k, its homotopy type is a wedge of two S^(k-1+r);
- if n=3k+1, it has homotopy type S^(k-1+r);
- if n=3k+2, it has homotopy type S^(k+r).

**Proof.** The clique complex of C_n^c is the independence
complex Ind(C_n); the clique complex of O_r is S^(r-1).
Clique complexes send graph joins to topological joins.
The standard cycle-independence-complex homotopy computation
then gives the displayed formulas. QED.

The original historically certified divergent core 10768817,
graph6 `HUZ~v~}`, is exactly T(5,2).
The first clique graph of the other certified suspension core
`HUzrv~}` is isomorphic to C_14^c; the latter was already
excluded as a retract by the prior named-target stage.

## Exact homology-matched target lists

Only targets with a single nonzero reduced mod-2 homology
group, of rank one, in the already certified host dimension are
chosen. Each target's Betti vector is *also* computed by
independent GF(2) simplex boundary reduction.

| Host stiff core | Exact host reduced mod-2 Betti | Selected (n,r) |
|---:|---|---|
| 6914104 | beta3=1, beta0,beta1,beta2,beta4,beta5=0 | (5,2), (7,2), (8,1), (10,1) |
| 6962151 | beta4=1, beta0,beta1,beta2,beta3,beta5=0 | (5,3), (7,3), (8,2), (10,2), (11,1), (13,1) |

The selection is exhaustive within this specifically described
rank-one homology-matched family. No conclusion is drawn about
hypothetical target homology in degrees **above five**, as the
host Betti numbers there were not certified by this experiment.

## Complete induced-target and graph-retraction search

The complement of T(n,r) is the disjoint union of an n-cycle
and r independent edges. The checker exhaustively enumerates
all induced chordless n-cycles in each host complement and
all disjoint collections of r complement edges with no
cross-incidences. Every resulting target subgraph is
independently rechecked by graph isomorphism.

For an ordinary graph retraction onto an induced target T,
every outside vertex x must map to some t in T satisfying

    N_G(x) intersect T  subset  N_T[t].

This necessary condition rejects most candidates immediately.
The remaining cases are checked by two independent complete
ordinary graph-retraction solvers, respecting adjacency *or
equality* of image vertices.

| Host | Target | Induced copies | Failing local condition | Completely rejected CSPs |
|---:|---|---:|---:|---:|
| 6914104 | T(5,2) | 821 | 820 | 1 |
| 6914104 | T(7,2) | 629 | 0 | 629 |
| 6914104 | T(8,1) | 704 | 704 | 0 |
| 6914104 | T(10,1) | 71 | 71 | 0 |
| 6962151 | T(5,3) | 0 | 0 | 0 |
| 6962151 | T(7,3) | 0 | 0 | 0 |
| 6962151 | T(8,2) | 0 | 0 | 0 |
| 6962151 | T(10,2) | 0 | 0 | 0 |
| 6962151 | T(11,1) | 0 | 0 | 0 |
| 6962151 | T(13,1) | 0 | 0 | 0 |

Across the first host, the standalone complete solver examined
**3,208 states**, independently matched by the pinned general
retraction solver, and found **no** retraction. All 2,225
induced targets were eliminated. The second host contains none
of the six proposed induced target shapes.

**Conclusion.** Neither third pared iterate retracts onto any
member of these ten homology-matched certified K-divergent
coaffine-join target families. The conclusion is about *these*
ordinary graph retractions only, not about clique convergence
or K-divergence of either nine-vertex core.

The 219+242=461 represented original ten-vertex graphs remain
unclassified by this stage. No historical census verdict or
earlier proof record was modified.

## Reproduction

Run after cloning the PR and pinning pycliques-project:

```bash
bash scripts/bootstrap_core9_three_target_v1.sh
.venv-core9-three-v1/bin/python scripts/core9_coaffine_join_targets_v1.py plan
.venv-core9-three-v1/bin/python scripts/core9_coaffine_join_targets_v1.py run
.venv-core9-three-v1/bin/python scripts/core9_coaffine_join_targets_v1.py verify
.venv-core9-three-v1/bin/python scripts/core9_coaffine_join_targets_v1.py report
```

The full 831-KiB record for core 6914104, the smaller second
record, and the provenance manifest are included in the
[successful workflow artifact](https://github.com/rvf0068/pycliques-census/actions/runs/44192083811).
Every result is replayed in a separately bounded subprocess;
the repository CI uses read-only credentials.
