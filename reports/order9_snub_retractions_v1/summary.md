# Three nonisomorphic nine-vertex graphs retract onto the snub disphenoid

This is an independently checkable observation about **graph retractions**,
not a proof that any graph is clique-divergent.

Let \(S\) be the eight-vertex snub disphenoid graph, encoded in the
order-10 core index by graph6 `GQyuzw` (class `2317572`).
For the connected nine-vertex graphs at zero-based McKay/pyg6data indices
`232592`, `233586`, and `244584`, their original graph6 encodings are:

| Order-9 index | Original graph6 | Order-10 pared-core class | Original order-10 members |
|---:|---|---:|---:|
| 232592 | `HCprnzy` | 4929602 | 82 |
| 233586 | `HCpvVn{` | 4972358 | 223 |
| 244584 | `HCvbvZu` | 5645085 | 207 |

The three nine-vertex graphs are pairwise nonisomorphic (the classes
were identified by exact graph isomorphism in the frozen census).

## Proposition (explicit retractions)

Each graph \(G\) retracts onto an induced copy of the snub disphenoid.
Using vertex labels \(0,\ldots,8\) from the **original order-nine graph6**
encoding, the same formula works in all three cases:

\[
r: G\longrightarrow G-\{2\},\qquad
r(2)=1,\quad r(v)=v\quad(v\ne 2).
\]

**Proof.** The three adjacency lists satisfy

\[
N_G(2)=\{5,6,7,8\}
\subseteq N_G(1)=\{4,5,6,7,8\},
\qquad 1\not\sim 2.
\]

Thus every edge \(2w\) maps to the edge \(1w\); every other edge is
fixed. Hence \(r\) is a graph morphism and is the identity on the
induced subgraph \(G-\{2\}\). In all three cases the recorded bijection
\(\varphi:G-\{2\}\to S\) preserves **edges and nonedges**, so the
induced target is isomorphic to \(S\). Consequently \(S\) is isomorphic
to a retract of each \(G\). \(\square\)

The identification \(2\mapsto 1\) is between **nonadjacent** vertices,
so it is *not* the usual deletion of a vertex dominated by another
vertex in the closed-neighborhood (fold) sense. This explains how the
graphs can survive the earlier completely-pared-core calculation yet
have these proper graph retracts.

For independent verification, the companion `certificates.json`
contains the original graph6 encodings, the retraction formula, and
explicit bijections of each eight-vertex induced target onto `GQyuzw`.
The verifier checks every edge of the source, that the retraction fixes
its induced image, that each bijection is a genuine graph isomorphism,
and that the indices match the frozen historical census. It also
cross-checks the separately certified pairwise isomorphisms

\[
G_2(232592)\cong G_2(233586)\cong G_2(244584)
\]

of the **completely pared second clique iterates**, stored in
`runs/order10/core9-followup-v1/isomorphism.json`.

Run from the repository root:

```bash
python scripts/verify_order9_snub_retractions.py
```

**Scope of the result.** The existence of these graph retractions does
not certify convergence or divergence for any of the three graphs.
In particular, the snub disphenoid's clique divergence is a standing
conjecture in this census, not an established theorem. Nor does the
retraction alone classify the original ten-vertex graphs represented by
the three classes (82 + 223 + 207 = 512 original graphs).
