# Certified ten-v24: three further K-divergent stiff ten-vertex graphs

## The theorem

Let \(P_0(G)=P(G)\), and \(P_{j+1}(G)=P(K(P_j(G)))\), where
\(P\) denotes complete closed-neighborhood domination paring.
By the dismantling theorem of Frías-Armenta, Neumann-Lara and
Pizaña, paring preserves eventual clique behavior.

**Three previously unresolved stiff connected ten-vertex McKay graphs
are now proved K-divergent.** Each has its completely pared fourth
clique iterate exactly isomorphic to that of ten-vertex
**McKay 10223405** (graph6: ICXnRi^uo), which has a complete previously
certified ordinary graph retraction onto \(O_{12}=\overline{12K_2}\).
See the [published O12 retraction proof](../order10_fourth_oct_v1/REPORT.md).
As \(K(O_d)\cong O_{2^{d-1}}\), this proves divergence by
Neumann-Lara's Retraction Theorem.

| New original McKay | Graph6 | P1 order | P2 order | P3 vertices / edges | P4 vertices / edges |
|---:|---|---:|---:|---|---|
| **11495390** | ICvbvZs{g | 17 | 21 | 42 / 629 | **182 / 14,298** |
| **11533866** | ICzbrn[n_ | 17 | 25 | 43 / 657 | **182 / 14,298** |
| **11556387** | IEhevrm~? | 17 | 21 | 42 / 629 | **182 / 14,298** |

The proven reference has P3 order 37 and P4 order 182 with 14,298
edges. All original graph6 identities and all five stage dimensions
are recorded in the [positive proof archive](certificates.json).

## Uniquely specified complete 182-vertex isomorphisms

The initial discovery independently reconstructed the fourth iterates
using NetworkX and obtained complete bijections by exact
color-refined backtracking, checked on every ordered vertex pair.

The new independent verifier specifies the same entire vertex map
canonically, avoiding an arbitrary 182-element literal array.
For each new P4 graph \(X\) and the reference P4 graph \(Y\), compute
vertex degree colors \(c(v)=\deg(v)\) jointly in both graphs, then one
round of 1-dimensional Weisfeiler--Lehman refinement:
\[
 c'(v)=\bigl(c(v),\{\!\{c(w):w\in N(v)\}\!\}\bigr).
\]
The same refined color palette is used on both graphs. **Each of the
182 vertices has a different refined color** and the two refined
color sets agree, so there is a uniquely determined complete
182-coordinate color-matching map.

The [independent verifier](verify.py) reconstructs every coordinate
of this map and verifies **all 182 squared ordered vertex pairs**
for adjacency and nonadjacency. It also verifies the complete
SHA-256 of this vertex permutation, which is stored separately for
each source in certificates.json, and confirms the map with
label-constrained NetworkX GraphMatcher. Thus no WL-signature
matching is substituted for an actual graph-isomorphism proof.

Both reference and source P4 graphs are rebuilt from the original
graph6 using independent bitset Bron--Kerbosch maximal-clique
enumeration and integer-mask dominated-vertex paring, with NetworkX
clique-enumerator crosschecks at every stage. Complete canonical
host graph6 SHA-256 digests are also authenticated.

The historical full retraction of the reference onto O12, including
its entire map, is archived in
[order10_fourth_oct_v1/o12_certificates.json](../order10_fourth_oct_v1/o12_certificates.json).
CI replays its original verifier with the pinned public pycliques
version, establishing the complete independent proof chain.

## Exact census advancement and historical preservation

Each of the three new sources is a **singleton** in the immutable
[ten-v23 P3 global equivalence index](../order10_p3_global_v23_index/README.md).
The new indeterminate_order_10_v24.txt removes exactly those three
six-field rows from immutable ten-v23, leaving every other record
unchanged.

| Original partition | ten-v23 | ten-v24 |
|---|---:|---:|
| Pared to unresolved nine-vertex cores | 430 | **430** |
| Stiff ten-vertex original cores | 629 | **626** |
| **All unresolved connected ten-vertex originals** | **1,059** | **1,056** |

The authoritative ten-vertex working root now agrees byte-for-byte
with ten-v24. Nine-v9 is unchanged at three unresolved originals.
Historical ten-v23 direct-retraction and global P3 class proofs are
replayed with read-only aliases to their original **frozen ten-v23**
input, without editing the current root. Among the 626 surviving stiff
originals are 522 previously certified reconstructible P3 classes
(489 singletons and 33 nontrivial classes with 134 members) and
three resource-limited cases.

## Reproduction and limitations

From the repository root with NetworkX 3.6.1, run the Python modules:

- python -m research.order10_p4_o12_lifts_v24.verify
- python -m unittest research.order10_p4_o12_lifts_v24.test_verify -v
- python -m research.order10_p4_o12_lifts_v24.replay_v23 all
- python -m unittest discover -s tests -p test_current_root_index.py -v

The historical reference replayer is
research/order10_fourth_oct_v1/verify_o12.py, using the previously
pinned pycliques installation.

An exploratory discovery screen examined third pared iterates with
41--50 vertices against five earlier certified P4 references,
subject to explicit maximal-clique/resource bounds. The three new
proofs arose from the O12 reference. Other candidates without found
isomorphisms or retractions remain **indeterminate**; negative,
resource-limited and timed-out screens imply no convergence verdict.
