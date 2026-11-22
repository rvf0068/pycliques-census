# Certified nine-v9 and ten-v20 census promotion

## Main result

The two *complete ordinary graph retraction* certificates in merged
[PR #80](https://github.com/rvf0068/pycliques-census/pull/80) prove
K-divergence of these connected nine-vertex original McKay graphs:

| Nine-vertex McKay | graph6 | Certified retraction | Ten-vertex original dependent graphs |
|---:|---|---|---:|
| **251759** | `HEhvtzm` | `P4 -> O15` | **129** |
| **254369** | `HEjfvx}` | `P4 -> O13` | **91** |
| **Total** | | **2 proofs** | **220** |

Here \(O_d=\overline{dK_2}\). Both complete source projections are
independently verified on every fourth-iterate vertex and every
original host edge. They are not merely induced octahedra, nor
conclusions from bounded searches.

The corresponding **exact census promotion** removes two original
nine-vertex McKay indices and exactly 220 original ten-vertex McKay
indices with pared nine-vertex cores isomorphic to one of these
two divergent sources.

| Order | Immutable previous snapshot | Previous originals | New snapshot | Remaining indeterminate originals |
|---|---|---:|---|---:|
| 9 | nine-v8 | 5 | nine-v9 | **3** |
| 10 | ten-v19 | 1,531 | ten-v20 | **1,311** |

Both authoritative working root files are byte-identical to
their new v9/v20 snapshots. The previous versions remain frozen
and unchanged, as do *all retained original records*.

## Remaining unresolved sources

| Original nine-vertex McKay | graph6 | Ten-vertex originals with an isomorphic pared-nine core |
|---:|---|---:|
| 249576 | `HEhfvzu` | 141 |
| 251628 | `HEhvVn{` | 147 |
| 260040 | `HQyvex}` | 142 |
| **Total** | | **430** |

Of the remaining 1,311 ten-vertex originals, exactly **430**
have a nine-vertex pared core, and the other **881** have a
ten-vertex pared core. No additional original in either class
is reclassified in this PR.

## Fully checkable, independent removal audit

The authoritative finite verification is
`research/order9_v9_order10_v20/verify.py`.
Its steps are:

1. Validate frozen nine-v8 Git blob
   `446d7ddba6bdb7f4738730f7de0386bea6546df7`
   and frozen ten-v19 Git blob
   `cf8047698eb63f8b80ed7104f8cc4307d093fc09`.
2. Parse and validate every census row (exact six-field
   format, no conditional classification, ascending *unique*
   original McKay indices, and matching graph6 orders).
3. Check the roots agree byte-for-byte with v9/v20; validate
   the exact source nine-v8 graph6 identities and the entire
   five-to-three deletion set; ensure all three surviving rows
   were retained verbatim.
4. Independently enumerate every one of the 650 frozen ten-v19
   originals having a nine-vertex pared core; search exact graph
   isomorphisms to **both** proved divergent nine-original
   sources. All isomorphism mappings are checked edge by edge,
   including nonadjacency, and no original may belong to both
   divergent families.
5. Recompute the exact **129 + 91 = 220** removals, require
   that the ten-v20 data removes those *and only those*, verify
   that every one of the 1,311 remaining original rows is
   byte-identical, and verify the invariant 881 stiff-core
   originals.
6. Independently validate all **220 individually saved
   explicit nine-vertex bijections** in
   `promotion_manifest.json`, including the original index,
   the frozen source row, nine-core graph6 and the appropriate
   positive O15/O13 retraction certificate.

The saved promotion manifest is **not used to select** any
deletion: an independent NetworkX GraphMatcher enumeration
derives the promoted set before the manifest is inspected.
The manifest is additional, explicit, vertex-level evidence.

Optional `--proofs` runs the **separate** complete NetworkX
projection verifier from merged PR #80: all **403** image
assignments for P4 -> O15 and all **394** image assignments
for P4 -> O13 are validated. For each graph it reconstructs
every pared clique iterate from original graph6 and checks
the exact full graph digest, target octahedral induced graph,
pointwise fixation, and every source edge image. It also
independently recomputes the original 220 ten-v19 lifts.
With `--public`, all positive source proofs are independently
verified through the pinned public pycliques implementation.

No limited negative search is used to promote a classification.

## Historical preservation

The predecessor v8/v19 verifier is preserved exactly and
replayed via `replay_v19.py`, which substitutes only frozen
nine-v8 and ten-v19 contents when the earlier verifier
reads the *mutable* authoritative working root files.

The previous v7/v18 and v6/v17 auditors remain available
behind their earlier historical wrappers. Current-root unit
tests and historical CI entry points are adapted, with no
modifications to frozen historical snapshots or positive
retraction certificates.

## Reproduction

From the census repository root, Python 3.12 and NetworkX 3.6.1:

```sh
python -m research.order9_v9_order10_v20.verify
python -m research.order9_v9_order10_v20.verify --proofs
python -m research.order9_v9_order10_v20.replay_v19
python -m unittest discover -s tests -p test_current_root_index.py -v
```

With pinned public pycliques:

```sh
python -m research.order9_v9_order10_v20.verify --proofs --public
```

Optimized Python execution (`python -O`) is rejected by
the verifier, since its assertions are proof-critical.

## Next research priority

The three remaining nine-v9 original McKay graphs are
**249576**, **251628**, and **260040**. Their fourth completely
pared clique iterates have **685**, **1,034**, and **1,227**
vertices respectively. The public native coaffine solver
currently accepts at most 512 vertices. A separately tested
2,048-vertex exploratory build was computationally slow and
found no witness under *bounded* search trials; no negative
classification follows from those limits.

Improving propagation and trying alternative positive
retraction techniques should take priority over interpreting
limited searches as non-divergence.
