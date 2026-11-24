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
prefilters**. Every positive group is confirmed by full NetworkX
GraphMatcher isomorphism, with an explicit complete vertex bijection
saved in [certificates.json](certificates.json).

The independent verifier reconstructs each archived pair again,
checks the bijection on **every edge and nonedge**, and independently
rebuilds the global class partition to ensure no same-class matches
were silently missed. Tests deliberately corrupt a vertex mapping
and verify rejection.

## Initial screening results; subject to CI replay

An independent finite structural prefilter on the 629 stiff cores
completed 626 third pared iterates. It found **525 invariant candidate
classes**, of which **33** non-singleton buckets contained **134**
originals and 492 were singletons. The subsequent exact
isomorphism verification in this PR must confirm these counts
before the certificate is considered established.

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
python -m unittest research.order10_p3_global_v23_index.test_classes -v
```

The archived certificate is generated once using `build`, then
independently checked using `verify`. No negative search over later
iterates is claimed.

## Next research use

Run fourth-iterate reconstruction and targeted retractions on one
representative of each **proved** `P_3` class, starting with the
smallest `P_3` orders and tracking any exceptional large iterates
separately. Only a complete positive divergence witness on a
representative should result in removal of its entire class from a
future versioned indeterminate list.
