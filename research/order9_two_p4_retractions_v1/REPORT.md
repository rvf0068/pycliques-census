# Two new positive fourth-iterate octahedral retractions

## Theorems

For any graph \(G\), let \(P_0(G)\) be its completely pared
(dominated-vertex-reduced) graph and define \(P_{j+1}(G)\) as the
completely pared clique graph of \(P_j(G)\). Write
\(O_d=\overline{dK_2}\).

**Theorem A.** Connected-nine McKay **251759**, with graph6
`HEhvtzm`, is K-divergent: its fourth pared clique iterate
admits a **complete ordinary retraction** `P4 -> O15`.

**Theorem B.** Connected-nine McKay **254369**, with graph6
`HEjfvx}`, is K-divergent: its fourth pared clique iterate
admits a **complete ordinary retraction** `P4 -> O13`.

Both conclusions use the established theorem that an octahedral
retraction at a finite clique iterate forces K-divergence,
together with preservation of clique behavior under
dominated-vertex paring. These are not statements inferred
from incomplete searches or an induced octahedron alone.

| McKay | Pared P0 vertices/edges | P1 | P2 | P3 | P4 | Ordinary retraction |
|---:|---|---|---|---|---|---|
| 251759 | 9 / 23 | 13 / 52 | 21 / 150 | 43 / 701 | **403 / 70,679** | **P4 -> O15** |
| 254369 | 9 / 24 | 13 / 54 | 17 / 99 | 40 / 626 | **394 / 67,229** | **P4 -> O13** |

The complete normalized labeled P4 edge-set SHA-256 hashes are:

- McKay 251759:
  `577c3026d1dbb08eab41ec971d03418b3e3201032ca312b7686ea02a2ba4b6f5`
- McKay 254369:
  `552af5cc777ee202f0938844f735f487de06245e9dda9dc51801ced67438b5f7`

The exact antipodal pair tables, all full projection images and
the source graph identities are stored separately in

- `research/order9_251759_p4_o15_v1/certificate.json`;
- `research/order9_254369_p4_o13_v1/certificate.json`.

The certificate files use one unsigned-byte image ordinal
for **every normalized P4 vertex** (403 or 394 respectively);
each ordinal refers to the sorted 30- or 26-vertex target list.
Thus the saved arrays are *complete projections*, not merely
induced-O_d targets.

## Independent verification

The common `verify.py` reconstructs all P0-P4 host graphs from
the two original connected-nine graph6 strings, using independent
NetworkX code. It checks every stage's vertex and edge counts and
the exact labeled P4 digest. For each case it verifies:

1. All antipodal endpoints are distinct.
2. The designated target vertices induce exactly
   \(O_{15}\) or \(O_{13}\), with no additional missing edge.
3. Every one of the 403 or 394 original host vertices has a
   valid target image, with full image set equal to the target.
4. **Every target vertex is fixed pointwise.**
5. **All 70,679 or 67,229 original host edges** map either
   to equal images or to adjacent target vertices.

This is the full definition of an ordinary graph retraction under
the weak adjacency-preservation convention used in pycliques.
The optional `--public` proof independently checks every
raw clique-graph construction and every paring against the
pinned public pycliques functions, and verifies both complete
maps with `verify_induced_octahedron` and
`verify_retraction_witness`.

## 220 additional connected-ten originals proved divergent

The verifier checks the exact original McKay source graph6
identities against **immutable nine-v8** (Git blob
`446d7ddba6bdb7f4738730f7de0386bea6546df7`).
It independently reads all **1,531** ten-v19 original records
from the immutable Git blob
`cf8047698eb63f8b80ed7104f8cc4307d093fc09`,
with strict original-index ordering and unique-record checks.

It then scans **all 650** order-nine pared cores, tests graph
isomorphism to each newly proved divergent original and
checks every returned vertex mapping edge by edge. It finds
**exactly 129** original McKay indices with core isomorphic to
251759 and **91** with core isomorphic to 254369; the families
are disjoint. All 220 originals are K-divergent.

This PR is **proof-only**, leaving the authoritative nine-v8
and ten-v19 indices (five and 1,531 indeterminate originals)
completely unchanged. Once these proofs are merged and independently
promoted into new snapshots, the counts should become
**three nine-vertex** and **1,311 ten-vertex** indeterminate
original graphs. No other case should be promoted without proof.

## From-scratch, unseeded, reproducible rediscovery

A local search using the independently reconstructed graphs
and the same C++17 native coaffine algorithm shipped in merged
pycliques-project PR #36 found:

| McKay | Vertex-order seed | Search states | Arc revisions (local edge order) | Assignments |
|---:|---:|---:|---:|---:|
| 251759 | 73 | **431** | 122,619 | 582 |
| 254369 | 19 | **2,074** | 2,213,218 | 5,244 |

At each trial, the only guide is a **general-purpose random
permutation of the original P4 vertices**: for
`rng=random.Random(seed)`, assign each normalized source
vertex an independent `rng.random()` key and sort ascending.
This does **not** supply any target vertices, antipodal pairs,
endomorphism or projection to the solver.

The `discover.py` replay explicitly compiles the pinned public
C++17 coaffine backend and calls
`find_octahedral_retraction_coaffine` with
`min_dimension=5`, `max_states=8000`,
`time_limit=30`, `backend="native"`.
All returned positive witnesses are independently reverified
using public pycliques. Deterministic state counts are expected
to match; the number of arc revisions can differ with the
equivalent edge-list iteration order.

These are **positive**, exact mathematical certificates. A
bounded result `LIMIT_REACHED` on any different ordering
would be inconclusive and is never used as a negative theorem.

The earlier integer domination bounds from merged PR #76
exclude small octahedral targets but are compatible with
the larger O15 and O13 retractions here. The successful orders
for these two hosts were randomized, unlike the dual-weight order
that found the preceding McKay 251902 P4 -> O17.

Any *special retraction* is an ordinary retraction; no separate
claim of a special retraction is needed or made.

## Reproduction

From the census repository root, install NetworkX 3.6.1 and run:

    python -m research.order9_two_p4_retractions_v1.verify

With pinned public pycliques and a C++17 compiler installed:

    python -m research.order9_two_p4_retractions_v1.verify --public
    python -m research.order9_two_p4_retractions_v1.discover

The standalone proof needs neither the native solver nor
optimization. Both workflows reject optimized Python execution
because their assertions are proof-critical.

## Research priority after this promotion

The remaining nine-v8 originals, if the above 220 ten-v19
dependents are promoted, will be **249576**, **251628**,
**260040**, with respectively 141, 147 and 142 unresolved
ten-original pared-nine dependents (430 total). Another
881 ten-original stiff cores remain indeterminate.

All three surviving P4 hosts have more than 512 vertices,
beyond the native solver's current hard limit. The next
research priority should therefore consider sound memory
and algorithmic extensions or alternative certified retractions.
