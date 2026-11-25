# Bounded coaffine search for the ten oversized third iterates

## Proven obstruction: no coaffine automorphisms

Let \(X=P_3(G)\) and \(H=\overline X\). A coaffination of \(X\) is an automorphism \(\sigma\) such that \(\sigma(v)\notin N_X[v]\) for every \(v\), equivalently \(\sigma(v)\in N_H(v)\).

**Lemma.** If \(H\) has a vertex \(v\) whose degree differs from that of every neighbor \(w\in N_H(v)\), then \(X\) has no coaffination.

**Proof.** An automorphism of \(X\) also preserves \(H\), and hence preserves \(\deg_H\). Therefore it cannot map \(v\) to any neighbor in \(H\), contrary to the definition of coaffinity. \(\square\)

The source builder reconstitutes all ten exact third-iterate graphs from the frozen current ten-v25 graph6 and the previously certified 521-class index. It checks the specified vertex, its degree, and the degrees of every complement neighbor.

| Original McKay | \(|V(P_3)|\) | \(|E(P_3)|\) | Witness \(v\) | \(\deg_H(v)\) | Degrees of complement neighbors |
| ---: | ---: | ---: | ---: | ---: | :--- |
| 11713770 | 95 | 4099 | 11 | 9 | 7, 8, 12 |
| 11611429 | 119 | 6412 | 7 | 8 | 6, 9, 11, 15 |
| 11708546 | 140 | 8822 | 8 | 13 | 10, 11, 12, 14 |
| 11709142 | 140 | 8824 | 8 | 11 | 12, 13, 14, 15, 16 |
| 11713984 | 169 | 12897 | 15 | 11 | 9, 12, 13, 14, 16, 25 |
| 11595632 | 182 | 14175 | 0 | 23 | 14, 16, 18, 24, 25, 27, 28, 34, 37 |
| 11656793 | 216 | 19663 | 1 | 32 | 21, 22, 23, 24, 26, 27, 28, 29, 30, 35, 37, 41, 42 |
| 11505012 | 226 | 21693 | 4 | 18 | 10, 16, 17, 19, 20, 21, 22, 23, 24, 25, 26, 28, 30 |
| 11367777 | 240 | 22724 | 0 | 15 | 13, 21, 25, 29, 30 |
| 11623375 | 266 | 28046 | 0 | 16 | 15, 21, 23, 29 |

This excludes **coaffine automorphisms**, not coaffine **weak endomorphisms**. An ordinary retraction \(r:X\to T\) to an octahedron \(T=O_d\), followed by an antipodal coaffination \(\tau:T\to T\) and inclusion, generally gives a **noninjective** coaffine endomorphism \(i\circ\tau\circ r\) of \(X\). The lemma does not exclude these retractions or classify clique behavior.

## Native search without new algorithms

The workflow checks out the existing pycliques-project monorepo pinned to commit f8eb9b9f2c71d79f9394571df98155f9de568785 (merged PR #55), installs its package, and explicitly builds its existing C++17 coaffine solver. No monorepo code is modified. On each authenticated \(X=P_3(G)\), it invokes the public general coaffine-endomorphism and unseeded octahedral-retraction APIs with the native backend, fiber value ordering, 100,000 search states and a 25-second limit each.

An **EXHAUSTED** general result rules out *all* coaffine weak endomorphisms and consequently all retractions to targets admitting such endomorphisms, including \(O_d\) and complement cycles. A **FOUND** general result is checked on every vertex and every source edge. A **FOUND** octahedral result is independently checked as an ordinary retraction onto an induced \(O_d\), fixing each target vertex and preserving every source edge. A positive octahedral witness at depth three proves clique divergence and would warrant a separate census-promotion PR.

**LIMIT_REACHED is always inconclusive.** A general coaffine endomorphism does not, by itself, establish clique divergence.

## Reproduction and classification discipline

The five disjoint two-graph CI shards authenticate the exact original graph6, full P3 adjacency SHA-256, solver commit and all graph morphism witnesses. A separate aggregation job rejects missing or duplicate shards and independently rechecks every positive map.

The canonical indeterminate lists are untouched: 3 nine-vertex and 1,052 ten-vertex original graphs. Existing fourth-iterate coverage remains 511 of 521 third-iterate classes; these ten fourth iterates are not materialized by this bounded experiment.
