# Ten-vertex flag sphere McKay 10472553 retracts from P4 to O4

The ten-vertex McKay graph **10472553**, graph6 \`ICZTeYj^_\`,
is a flag triangulation of the two-sphere in the frozen v16
unresolved census.

Its completely pared clique iterates P0,...,P4 have orders
**10, 16, 26, 63, 365** and edges
**24, 69, 186, 1,201, 42,351**.

An unseeded coaffine weak-endomorphism search produced a complete
ordinary graph retraction P4(G) -> O4 with antipodal pairs

    (0,203) (2,242) (52,163) (174,295)

Its 365-image mapping is archived, without relying on the search
solver, in \`certificate.json\`. The 365 bytes are target ordinals
in ascending host-vertex order, where the target order is
\`[0,2,52,163,174,203,242,295]\`. The independent verifier rebuilds
the host from the nine-character source graph6, checks each iterate's
size, the P4 edge-list SHA-256, total projection, target pointwise
fixation, induced O4 nonedges and all **42,351** weak-morphism
edge constraints. A public-pycliques replay independently verifies
the iterate construction, octahedron and retraction.

The finite retraction, Neumann-Lara's divergence theorem for
octahedral retracts, and dominated-vertex behavior preservation
prove **McKay 10472553 is K-divergent**.

Commands:

    python research/order10_surface_10472553_o4_v1/verify.py
    python research/order10_surface_10472553_o4_v1/verify.py --public

This is a proof-only addition. The frozen v16 snapshot and
authoritative root lists remain unchanged until a separate exact
promotion. Together with the prior two verified flag-sphere proofs
(10185592 via O6 and 9804321 via O5), this gives a total of
three newly proved divergent ten-vertex flag spheres.
