# A convergent two-clique attachment with the same 1,2,1,2,... pattern

This elementary comparison prevents an invalid leap from the finite
six-core snub calculations to clique divergence.

**Proposition.** For every `n >= 5`, let `L_n` be the graph obtained
from the chordless cycle `C_n` by adjoining a new vertex `x`
adjacent to `v_0` and `v_2` (cyclic indices). Then

```text
K²(L_n) ≅ L_n,
|K^(2r)(L_n)| = n+1,    |K^(2r+1)(L_n)| = n+2
```

for every integer `r >= 0`. Thus **L_n is K-convergent**, despite
its persistent extra vertex on even iterates and two extra vertices
on odd iterates relative to the K-fixed cycle `C_n`.

**Proof.** Since `n >= 5`, `L_n` has no triangles. Its maximal
cliques consist of the cycle edges
`e_i = {v_i, v_(i+1)}`, plus `a = {x,v_0}` and `b = {x,v_2}`.
The induced vertices `e_0,...,e_(n-1)` of `K(L_n)` form `C_n`.
Vertex `a` is adjacent exactly to `e_(n-1),e_0,b`, while `b`
is adjacent exactly to `e_1,e_2,a`.

The maximal cliques of `K(L_n)` are precisely:

- `F_0 = {a,e_(n-1),e_0}` and `F_2 = {b,e_1,e_2}`;
- `F_i = {e_(i-1),e_i}` for all `i != 0,2`;
- `F_x = {a,b}`.

For distinct `i,j`, `F_i` meets `F_j` exactly when
`i` and `j` are consecutive cyclically. The additional clique
`F_x` meets exactly `F_0` and `F_2`. Therefore the intersection
graph of these `n+1` maximal cliques is isomorphic to `L_n`,
with `F_i` corresponding to `v_i` and `F_x` corresponding to
`x`. Hence `K²(L_n) ≅ L_n`; the claimed periodic orders follow
from the formula for `K(L_n)`. QED.

**Relation to the six snub cores.** Their exactly verified finite
orders through `K⁴` show the same alternating difference `+1,+2,+1,+2,+1`
from the snub iterates, and in each case an extra circle appears in
the clique-complex homotopy type. These similarities alone cannot prove
divergence: `L_n` supplies a K-periodic counterexample to such a
general inference.

The stronger research problem is to find a genuine unboundedness
certificate for one of the six snub-related cores, or a structural
theorem showing that their attachment process remains controlled
by the corresponding snub iterates for **all** iterations.
