# Nine-vertex McKay 253650: P4 retracts onto O12; 242 exact v16 lifts

## Original nine-vertex theorem

Let G be connected-nine McKay graph **253650**, graph6 \`HEjer~{\`.
Write P0(G) for the completely pared graph and
P(j+1)(G) for the completely pared clique graph K(Pj(G)).
The independently reconstructed sequence has orders
**9, 14, 19, 40, 259** and edges **23, 61, 119, 601, 28,890**.

The graph P4(G) admits a complete ordinary graph retraction onto an
induced O12. Its twelve antipodal pairs (sparse labels in the
independent clique-index numbering) are:

    (1,205) (2,90) (20,226) (26,212)
    (29,213) (43,165) (50,171) (59,217)
    (66,106) (69,287) (78,123) (107,146)

The entire 259-image projection is preserved in \`certificate.json\`.
Encoding: a 259-byte array in ascending **host-label** order;
each byte is the ordinal of the corresponding projection image in
\`target_order\` (the 24 sorted target labels); base64 serialized.
The host labels may be sparse after paring, so never use them directly
as array offsets. The independent verifier reconstructs every iterate,
checks the exact 28,890-edge SHA-256 digest, induced O12 shape,
pointwise fixation and all 28,890 edge images. An optional
\`--public\` mode repeats the construction using public pycliques
functions and two separate witness verifiers.

Since octahedral graphs O_d, d>=3, are K-divergent, the retraction theorem
and behavior-preservation under dominated-vertex dismantlings imply
that **McKay 253650 is K-divergent**.

## 242 exact v16 original ten-vertex consequences

The frozen v16 ten-vertex unresolved census has **242 original graphs**
whose certified completely pared graph on nine vertices is
isomorphic to \`HEjer~{\`. Each such original ten-vertex graph is
therefore also K-divergent.

\`lift_v16_certificate.json\` preserves **242 full bijections** from the
original nine-vertex source to the stored nine-vertex pared core.
The verifier \`verify_lifts_v16.py\` does not trust the saved hit list:
it checks the exact frozen v16 Git blob hash, independently enumerates
**all 2,341** v16 records, uses NetworkX isomorphism to derive precisely
the 242 hits, checks every saved original index/graph6 row and every
saved bijection edge-by-edge, and invokes the positive O12 proof.

These 242 represent distinct *original ten-vertex indices*, not
242 different nine-vertex isomorphism types. They have 138 distinct
saved graph6 encodings of the same nine-vertex core. These are
unconditional consequences of the known behavior-preservation
theorem, not an inference from a conjectural reference.

## Commands

    python research/order9_253650_o12_v1/verify.py
    python -m research.order9_253650_o12_v1.verify_lifts_v16

With public pycliques installed:

    python research/order9_253650_o12_v1/verify.py --public
    python -m research.order9_253650_o12_v1.verify_lifts_v16 --public

All checks reject optimized Python, which would otherwise remove
proof-critical assertions. The dedicated GitHub workflow checks
standalone NetworkX, pinned public pycliques and historical census
identity. No authoritative or historical census file is modified by
this proof-only PR.

Mathematical background: Neumann-Lara's retraction theorem for
clique-graph dynamics; Frías-Armenta--Neumann-Lara--Pizaña,
"Dismantlings and iterated clique graphs",
Discrete Mathematics 282 (2004), 263--265.
