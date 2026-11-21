# Order-nine P2 isomorphism unlocks 219 order-ten divergences (v4/v14)

**Certified theorem.** Connected nine-vertex McKay **248936**, completely
pared graph6 `HEhev^{`, is **K-divergent**. Its second completely pared
clique iterate is exactly isomorphic to the second completely pared
clique iterate of McKay ten-vertex **10223405**, graph6 `ICXnRi^uo`.
The latter source already has an independently verified complete ordinary
graph retraction from its fourth pared clique iterate onto `O_12`,
archived in [the prior O12 certificate](../order10_fourth_oct_v1/o12_certificates.json)
and replayed by [the historical verifier](../order10_fourth_oct_v1/verify_o12.py).

The new result is *not* an inference from matching orders, degrees,
homology, or Weisfeiler--Lehman signatures. The P2 isomorphism is found
and checked against **all vertex pairs**, preserving both edges and
nonedges. The public `pycliques` reconstruction verifies each step.
An independent, direct NetworkX maximal-clique construction and
sequential dominated-vertex reduction gives the same result. The two
reference P2 graphs each have **19 vertices, 117 edges**. The two
reference P3 and P4 graphs are also independently isomorphic, with
**37 / 503** and **182 / 14,298** vertices/edges respectively.

## Why this implies divergence

Write `P(G)` for a completely dominated-vertex-pared graph and
`P_{j+1}(G)=P(K(P_j(G)))` with `P_0(G)=P(G)`.
The established dismantling theorem (Frías-Armenta, Neumann-Lara and
Pizaña, *Dismantlings and iterated clique graphs*, Discrete Mathematics
282 (2004)) implies that removing a dominated vertex preserves
eventual clique behavior. Consequently, an exact graph isomorphism
`P_2(G) ≅ P_2(H)` transfers their eventual K behavior.

In the case at hand, `P_4(H)` has an explicit retraction onto
`O_12 = complement(12 K_2)`; for `d >= 3`,
`K(O_d) ≅ O_(2^(d-1))` is clique-divergent, and the established
retraction theorem transfers this divergence to `P_4(H)`, then to
`H`. By the P2 isomorphism, nine-vertex McKay 248936 is likewise
K-divergent. **No new retraction finder or probabilistic implication is
needed** for this exact isomorphism lift.

## Exact census consequences

The [self-contained positive cohort](certificate.json), authenticated
against the frozen v3/v13 Git blobs, lists **219** previously
unclassified connected ten-vertex McKay indices. Every one has a
completely pared graph on **nine** vertices and a fully checked P2
isomorphism onto the newly certified reference. The cohort spans
**122 distinct pared graph6 encodings**, all checked individually.

- **Order nine:** immutable v3 had 13 unresolved; v4 has **12**,
  deleting only original index **248936**.
- **Order ten:** immutable v13 had 2,787 unresolved; v14 has **2,568**,
  deleting precisely the **219** verified positive originals.
- All 219 newly deleted order-ten cases were **unconditional**;
  the **120** previously conjecture-dependent references stay unchanged.
- No historical census snapshots or run results are overwritten.

## Reproduce with pycliques

The source code uses only public `pycliques` and NetworkX APIs.
The proof-replay workflow pins the same upstream commit used by the ILP
research and verifies the earlier O12 fixed-point projection separately.
For full reproduction:

```sh
python research/order10_fourth_oct_v1/verify_o12.py
python research/order9_p2_iso_lift_v1/screen.py scan
PYTHONHASHSEED=0 python -m research.order9_p2_iso_lift_v1.verify
python -m unittest discover -s tests -p test_current_root_index.py -v
```

The base P2 bijection is included in the certificate for reproducibility
under the pinned labeling. Every member's P2 isomorphism is recomputed
in the full verification; no previously saved bijection is trusted for
a new member. A bounded/excluded result would have remained unresolved,
and no negative K-convergence conclusions are drawn.

## References

- M. E. Frías-Armenta, V. Neumann-Lara and M. A. Pizaña,
  *Dismantlings and iterated clique graphs*, Discrete Mathematics
  **282** (2004), 263–265.
- V. Neumann-Lara, octahedral retraction theorem for clique-divergence,
  as cited and deployed in the archived O12-retraction proof.
