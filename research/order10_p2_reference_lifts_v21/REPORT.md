# Certified ten-v21: 83 new divergences through exact P2 isomorphisms

## Main theorem

For each of the **83** connected order-ten original McKay graphs \(G\)
listed individually in [certificates.json](certificates.json), a graph
\(H\) among **seven already certified divergent nine-vertex originals**
satisfies the explicit graph isomorphism

\[
P_2(G)\cong P_2(H).
\]

Here \(P_0(X)=P(X)\) is complete sequential dominated-vertex paring,
and \(P_{i+1}(X)=P(K(P_i(X)))\). All 83 saved bijections are
independently checked against *every pair of vertices*, both adjacent and
nonadjacent, after recomputing P2 directly from the frozen original
graph6 records, without using stored intermediate graphs.

The dismantling theorem of Frías-Armenta, Neumann-Lara and Pizaña,
*Dismantlings and iterated clique graphs*, Discrete Mathematics **282**
(2004), 263–265, shows that complete dominated-vertex paring preserves
eventual clique behavior. Therefore any \(G\) with \(P_2(G)\cong P_2(H)\)
shares the \(K\)-divergence of the already proved \(H\). These 83 proofs
are unconditional, positive, and involve **no** failed bounded search
inference.

## Proven source graphs

| Nine-original McKay | Graph6 | Source's archived unconditional K-divergence proof | New ten-originals |
|---:|---|---|---:|
| 249436 | `HEhff^{` | [Three P4 retractions](../order9_three_p4_retractions_v1/REPORT.md), \(P_4\to O_{10}\) | 11 |
| 249574 | `HEhfvx}` | [Three P4 retractions](../order9_three_p4_retractions_v1/REPORT.md), \(P_4\to O_{12}\) | 9 |
| 250814 | `HEhuvzm` | [Three P4 retractions](../order9_three_p4_retractions_v1/REPORT.md), \(P_4\to O_{14}\) | 18 |
| 251759 | `HEhvtzm` | [Full O15 projection](../order9_251759_p4_o15_v1/certificate.json) | 20 |
| 251902 | `HEhvvzm` | [Full O17 projection](../order9_251902_p4_o17_v1/certificate.json) | 14 |
| 253650 | `HEjer~{` | [Full O12 projection](../order9_253650_o12_v1/certificate.json) | 4 |
| 254369 | `HEjfvx}` | [Full O13 projection](../order9_254369_p4_o13_v1/certificate.json) | 7 |
| **Total** | | | **83** |

Each \(O_d=\overline{dK_2}\). The source proofs were independently
certified in earlier merged PRs #69, #73, #78 and #80. The new
contribution is the **83 original-ten to proved-source P2 equivalences**,
not a rediscovery of those source retractions.

## New certified census snapshot

The immutable **ten-v20** snapshot contains 1,311 original McKay
entries. The **ten-v21** snapshot removes **exactly** the 83 original
indices listed in the explicit certificate. It leaves every other
six-field record **verbatim unchanged**, and the working root
`indeterminate_order_10.txt` is now byte-identical to
`indeterminate_order_10_v21.txt`.

| Class of unresolved originals | ten-v20 | ten-v21 |
|---|---:|---:|
| Ten-originals pared to unresolved nine-vertex cores | 430 | **430** |
| Stiff ten-vertex cores | 881 | **798** |
| **Total ten-vertex indeterminate originals** | **1,311** | **1,228** |

The certified nine-v9 index remains **three**. None of the 83 removed
cases belongs to the 430 nine-core families. The historical ten-v20
file, all its predecessors, and every earlier proof archive remain
unchanged.

## Verification and reproducibility

[verify.py](verify.py) is a second, independent Python 3.12 and
NetworkX 3.6.1 verifier, not the discovery program. It:

1. Authenticates the frozen v20 Git blob with SHA
   `89f8f18bd236e6d7fa1e7ca928aa5418af061de4`.
2. Checks the current mutable root and certified v21 are byte-identical,
   every old/new original row is well formed and sorted, and every
   surviving record is exactly the historical old row.
3. Checks the **exact 83-index deletion set** equals the certificate;
   no additional indices are removed and no conjectural case is
   accidentally reclassified.
4. Authenticates each of the seven original nine-source graph6 strings
   and its **exact** archived proof path against an independent, fixed list
   and frozen historical order-nine census rows. It then directly invokes
   the four previously merged independent proof verifiers for all seven
   positive P4-to-octahedron retractions (three + two + one + one). Each
   verifier reconstructs the original P4 graph, checks the exact octahedral
   target and the **complete edge-preserving projection**, including
   pointwise fixation. Merely finding graph6 text in a report is not
   accepted as a divergence certificate.
5. Reconstructs \(P_2(G)\) independently for all seven references and
   all 83 ten-originals, applying verified sequential
   closed-neighborhood-dominated-vertex deletions.
6. Compares maximal-clique sets returned by NetworkX and a **separate
   Bron–Kerbosch implementation** at each clique-graph iteration.
7. Verifies all 83 saved P2 bijections are permutations preserving
   **all ordered pairs**, not merely graph degree signatures, clique
   counts, or a Weisfeiler–Lehman hash. A separate NetworkX
   GraphMatcher independently confirms each isomorphism.
8. Recomputes the exact seven family counts, checks immutable v20/v21
   partition 430+881 → 430+798, and rejects `python -O` so
   proof-critical assertions cannot be bypassed.

A separate [replay_v20.py](replay_v20.py) runs the untouched historical
v20 verifier, redirecting only the mutable ten-root read to the frozen
ten-v20 file. This ensures historical 220-lift audits remain valid
without changing their proof code.

From the census checkout root:

```sh
python -m pip install networkx==3.6.1
python -m research.order10_p2_reference_lifts_v21.verify
# The first command also replays all seven P4 octahedral source proofs.
python -m research.order10_p2_reference_lifts_v21.replay_v20
python -m unittest discover -s tests -p test_current_root_index.py -v
```

The [new CI workflow](../../.github/workflows/order10-p2-v21.yml)
runs the independent 83-certificate replay, historical replay and
current-root regression. The historical v20 workflow separately runs
its unchanged proof logic against its immutable snapshot.

## Limitations and next priorities

The theorem settles 83 previously indeterminate **original** ten-vertex
graphs but does not establish classification for the remaining 1,228.
It should not be conflated with an exhaustive P2 isomorphism
classification of all 798 remaining stiff cores against every possible
divergent source.

The immediate next computational targets are additional positive P2/P3
equivalences to proved divergent references and complete ordinary
retractions on the smaller distinct P2/P3 core classes. Inconclusive
bounded octahedral or expansive-target searches must not remove census
records.
