# Certified ten-v22: twenty further divergent ten-vertex stiff cores

## Main result

Let \(P_0(G)=P(G)\) be complete dominated-vertex paring and put
\(P_{j+1}(G)=P(K(P_j(G)))\), where \(K(G)\) is the maximal-clique intersection
graph. The dismantling theorem of Frías-Armenta, Neumann-Lara and Pizaña,
*Dismantlings and iterated clique graphs*, Discrete Mathematics **282**
(2004), 263–265, preserves eventual clique behavior under paring.

**Twenty previously indeterminate connected ten-vertex original McKay
graphs are now proved \(K\)-divergent.** Each has a complete saved bijection
at the second or third pared clique iterate to an already proved divergent
reference. All 20 bijections are independently reconstructed from the
original graph6 and checked on **every ordered vertex pair**.

### Eighteen direct P3 equivalences with proved nine-vertex sources

| Divergent nine-vertex reference | graph6 | Previously certified divergence | New ten-originals |
|---:|---|---|---:|
| 249436 | `HEhff^{` | \(P_4\to O_{10}\) | **10** |
| 208409 | `HCZTf\}` | \(P_4\to O_9\) | **5** |
| 249574 | `HEhfvx}` | \(P_4\to O_{12}\) | **1** |
| 250814 | `HEhuvzm` | \(P_4\to O_{14}\) | **1** |
| 251902 | `HEhvvzm` | \(P_4\to O_{17}\) | **1** |
| **Total** | | | **18** |

Their positive source projections are verified by the previously merged
independent replayers under
[three P4 retractions](../order9_three_p4_retractions_v1/verify.py),
[F45 O9](../order9_f45_o9_v1/verify.py), and
[251902 O17](../order9_251902_p4_o17_v1/verify.py).
The new v22 verifier **replays the full source witnesses**; the F45 replay
is NetworkX-only and checks all 202 host images, while the three P4 and
251902 replays check every host edge under their saved projections.

### Two additional P2 equivalences and explicit source retractions

| Original ten-vertex McKay | graph6 | P2 reference | P2 order, edges | Reference's ordinary retraction |
|---:|---|---:|---:|---|
| **9813482** | ``ICR`uxv~_`` | **9312634** | 21, 144 | ten-vertex reference onto the 8-vertex snub disphenoid |
| **11657332** | `IErv^q}^g` | **11262714** | 22, 181 | ten-vertex reference onto McKay 260910 |

Both **original-graph** retractions are short and complete, not merely
homomorphisms into a non-induced target:

- For McKay **9312634** (graph6 `ICQfHz\}o`), delete source vertices
  \(1,4\), fixing the other eight and sending \(1\mapsto0\) and
  \(4\mapsto3\). The fixed eight induce the snub disphenoid, as witnessed
  by the complete source-to-snub bijection in the certificate.
- For McKay **11262714** (graph6 `ICpu}zy}W`), delete vertex \(2\),
  fix the other nine, and send \(2\mapsto1\). The nine fixed vertices
  induce McKay **260910**, again with an explicit saved graph isomorphism.

The snub disphenoid (graph6 `GQyuzw`) has the previously proved
\(K^4(S)\to O_{24}\) retraction archived in
[pycliques-project](https://github.com/rvf0068/pycliques-project/blob/main/docs/snub_o24_retraction.md).
McKay 260910 (graph6 `HUZvvzu`) has a complete \(P_3\to O_{15}\)
retraction in
[its independent certificate](../order9_260910_o15_v1/verify.py).
The v22 verifier independently checks all source and target edges,
pointwise fixation, and every vertex of the two small retractions;
it also replays the complete \(P_3\to O_{15}\) certificate. Its only
externally established divergence premise is the already merged snub
theorem.

Thus each of these two ten-originals is \(K\)-divergent as well.

## Exact immutable census promotion

| Class of original graphs still unresolved | ten-v21 | ten-v22 |
|---|---:|---:|
| Pared to one of three unresolved nine-vertex cores | 430 | **430** |
| Stiff ten-vertex pared cores | 798 | **778** |
| **All indeterminate ten-vertex originals** | **1,228** | **1,208** |

The remaining nine-v9 census is unchanged at **3** indeterminate
originals. The new immutable
[indeterminate_order_10_v22.txt](../../indeterminate_order_10_v22.txt)
removes **exactly** these 20 original McKay indices:

```text
7959206 9813482 9813863 9815528 10297283
10300042 10475768 10477617 10484202 10485646
10601010 11405876 11475405 11555266 11557504
11558565 11559200 11612071 11624622 11657332
```

Every retained six-field v21 record remains byte-for-byte identical.
The archived ten-v21 snapshot and all earlier historical snapshots are
untouched. The authoritative working root is byte-identical to v22.

## Independent proof replay

The complete positive certificate is
[certificates.json](certificates.json). Each original includes
its original graph6, exact depth, pared graph order and edge count,
reference McKay index and graph6, and **all coordinates** of a complete
isomorphism \(P_j(G)\cong P_j(H)\). Two additional complete small
retraction witnesses give the fixed target vertices, all outside images,
and the entire induced-target isomorphism.

The independent
[verify.py](verify.py) checks:

1. Frozen v21 Git blob identity `668582e463a7d5e47637a5f78663954a72867d47`.
2. The exact sorted 20-index removal from v21, with no change of any
   surviving original record; the 430+798 to 430+778 partition.
3. Reconstruct \(P_2\) and \(P_3\) from each source **and** reference's
   original graph6, without reading any saved intermediate graph.
4. Independently compare two maximal-clique enumerators (Bron--Kerbosch
   and NetworkX) at every stage; explicitly check every dominated-vertex
   deletion until the graph is stiff.
5. Validate each saved bijection as a permutation and verify **all**
   adjacencies and nonadjacencies; confirm with an independent
   NetworkX GraphMatcher.
6. Check both induced small target graphs, the saved explicit source-to-
   target isomorphisms, and every edge under the **total** ordinary
   projections.
7. Replay the previously certified P4/P3 octahedral projections for all
   five nine-vertex reference types used here; the snub theorem is
   separately established and independently documented in the monorepo.
8. Reject optimized Python, so proof-critical assertions cannot be
   silently removed.

The historical
[replay_v21.py](replay_v21.py) runs the **unchanged** full ten-v21
83-certificate audit against frozen v21 using a read-only substitution
for the mutable ten-vertex working root. Earlier historical audits
remain independently reproducible.

Reproduce from the root of this repository (Python 3.12, NetworkX 3.6.1):

```sh
python -m research.order10_p3_reference_lifts_v22.verify
python -m research.order10_p3_reference_lifts_v22.replay_v21
python -m unittest discover -s tests -p test_current_root_index.py -v
```

## Discovery scope and limitations

The exploratory sweep used the **2,357 stiff ten-core originals in
immutable ten-v8** as a pool and compared the **798 v21 survivors**
against previously proved divergent original ten-reference graphs.
A strict \(P_2\) invariant comparison suggested two positives.
A later \(P_3\) comparison, with bounded size/clique-enumeration
filters, suggested 19 positives, one overlapping a \(P_2\) candidate.
Direct comparison to proved divergent nine-reference \(P_3\) graphs
gives 18 of those proofs without an intermediate ten-source.

**Every positive was proved independently**, using full explicit
bijections and archived positive divergence results. The size cap,
invariant collisions, and unsuccessful comparisons are NOT exhaustive
negative certificates. No unexamined or failed case is reclassified.

Next priorities include possible additional positive \(P_3\) matches in
the larger deferred cases, and new retractions from the distinct
remaining stiff ten-core iterates to already proved divergent targets.
