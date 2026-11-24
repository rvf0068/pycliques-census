# Global third-iterate index for the ten-v23 unresolved stiff cores

## Purpose

This is an **equivalence index, not a clique-behavior classification**.
The immutable ten-v23 census contains 629 unresolved original McKay
graphs whose completely pared original graph has order ten. Several
originals may have isomorphic *third completely pared clique iterates*,
which means only one class representative needs subsequent expensive
fourth-iterate or targeted-retraction searches.

Let `P_0(G)=P(G)` be complete closed-neighborhood domination paring and
let `P_{j+1}(G)=P(K(P_j(G)))`. The search groups graphs by **exact
isomorphism of `P_3(G)`**, not just by an invariant collision.
This equivalence preserves eventual clique behavior under the
dismantling theorem of Frías-Armenta, Neumann-Lara and Pizaña.

## Reproducible method

`classes.py` authenticates the frozen
[indeterminate_order_10_v23.txt](../../indeterminate_order_10_v23.txt)
Git blob, checks current-root and nine-v9 consistency, reconstructs
every iterated clique graph from original graph6 with sorted integer
maximal-clique masks, and removes dominated vertices in deterministic
increasing-label order.

Degree/neighborhood-degree profiles and three-iteration
Weisfeiler–Lehman hashes are used **only as necessary isomorphism
prefilters**. The archive builder uses a **jointly color-refined
backtracking matcher**, with an explicit budget of 1,000,000 search
states per attempted comparison. Exceeding that limit raises an error,
**never** a nonisomorphism verdict or an accepted negative result.
Every accepted positive match has a complete vertex bijection saved in
[certificates.json](certificates.json).

The separate [independent verifier](independent_verify.py) never calls
the builder's fold, clique graph, or isomorphism routines. At **every**
reconstructed iterate it compares a standalone **bitset Bron–Kerbosch**
maximal-clique enumeration against NetworkX's `find_cliques`,
reconstructs the graph using **independent integer-mask
closed-neighborhood paring**, and checks each archived permutation on
**every edge and nonedge**. It additionally confirms each positive
class with NetworkX **GraphMatcher**, separate from the builder's
bounded matcher. Class separation is independently checked using
necessary graph invariants: all 525 distinct archived classes have
distinct invariant signatures, so no isomorphism between them is
possible. Regression tests deliberately corrupt the enumeration or
vertex maps and verify rejection.

## Certified exact global class results (independent CI replay passed)

All 629 current stiff ten-vertex originals were considered; **626**
completely pared third iterates were reconstructed. These fall into
**525 exact isomorphism classes**. In particular:

| Exact class category | Classes | Original graphs |
|---|---:|---:|
| Singleton | **492** | **492** |
| Nontrivial (size at least two) | **33** | **134** |
| **Reconstructed total** | **525** | **626** |

The three largest nontrivial classes have representatives
**7479384** (25 originals, pared third-iterate order 58),
**7070392** (23 originals, order 55), and
**7044680** (17 originals, order 53).
Every one of the 101 nonrepresentative graphs in the 33 nontrivial
classes has a complete saved vertex-level isomorphism to its class
representative. The independent Python builder and certificate verifier
both passed [the complete CI replay](https://github.com/rvf0068/pycliques-census/actions/runs/45437999550).

Three explicitly limited cases are not assigned to an equivalence
class: McKay 11708967 (`IQyuzz~~o`) has a 288-vertex pared second
iterate, while McKay 11715667 (`IUZu~r|zo`) and 11716441
(`IUzvrz}zo`) have more than 750 cliques in the attempted third
iterate. These are **resource limits**, not indications of divergent
or convergent behavior.

The new index leaves the authoritative nine-v9 and ten-v23
indeterminate lists *completely unchanged*.

## Reproduction

With Python 3.12 and NetworkX 3.6.1:

```sh
python -m research.order10_p3_global_v23_index.classes build --output /tmp/global-p3.json
python -m research.order10_p3_global_v23_index.classes verify
python -m research.order10_p3_global_v23_index.independent_verify
python -m unittest research.order10_p3_global_v23_index.test_classes -v
```

The archived certificate is generated using `build` and checked with
a separate bitset clique enumerator, independent paring, all-pairs
permutation checks, and GraphMatcher when using `verify`. Subsequent fourth-iterate investigations need
only 525 certified class representatives plus three explicit oversized
exceptions, instead of all 629 originals. No negative search over later
iterates is claimed.

## Next research use

Run fourth-iterate reconstruction and targeted retractions on one
representative of each **proved** `P_3` class, starting with the
smallest `P_3` orders and tracking any exceptional large iterates
separately. Only a complete positive divergence witness on a
representative should result in removal of its entire class from a
future versioned indeterminate list.
