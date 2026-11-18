# Exhaustive snub retractions of all 29 unresolved nine-vertex cores

This is an exact finite investigation of **graph retractions**
and second completely pared clique-iterate isomorphisms.
**It is not a new clique-divergence classification.**
Divergence of the snub disphenoid remains a conjecture.

The snub S has graph6 `GQyuzw`. A retraction onto S inside a
nine-vertex graph must delete one vertex v, identify it with
one of eight remaining vertices u, and fix the rest.
The checker tests all 9*8 possibilities, first verifying the
induced eight-vertex graph is isomorphic to S, then every source edge
under adjacency **or equality**. Negative local obstructions
are recorded for each impossible image.

| Core ID | Nine-vertex index | Original ten-graph members | Retraction v to u | Pared K² matches snub? |
|---:|---:|---:|---|---|
| 2317843 | 180593 | 70 | 2 to 1 | no |
| 3148541 | 220642 | 114 | 2 to 1 | no |
| 3505942 | 220895 | 133 | 2 to 5 | no |
| 4929602 | 232592 | 82 | 2 to 1 | YES |
| 4952669 | 233406 | 86 | 2 to 1 | no |
| 4953338 | 232908 | 196 | 2 to 1 | no |
| 4972358 | 233586 | 223 | 2 to 1 | YES |
| 5601875 | 251445 | 111 | 2 to 1 | no |
| 5645085 | 244584 | 207 | 2 to 1 | YES |

**Nine snub-retracting cores represent 1,222 original ten-vertex graphs.**
The six newly identified classes contribute **710** originals;
the previous three contribute **512**.

Six more cores (representing **811** originals)
contain an induced snub but have **no graph retraction** to it.
The other 14 cores contain **no induced snub**. These negative
statements are exhaustive within the 29 nine-vertex core classes.

## Stronger dynamical relationship for three cores

For cores 4929602, 4972358, and 5645085, the checker
independently constructs the full second completely pared
clique iterates and explicit graph isomorphisms to the second
completely pared clique iterate of S (20 vertices, 136 edges).
By the dominated-vertex dismantling theorem, the K-convergence
versus K-divergence behavior of **each of these three cores**
is the same as that of S. The same conclusion applies to the
**512 original ten-vertex graphs** which dismantle to those cores.
This is an unconditional **equivalence of behavior**, not a
proof of divergence for either side.

For the other six snub-retracting cores, the retraction gives
only the implication: **if S is K-divergent, so is the core**.
There is no converse implied by an arbitrary graph retraction.

References: Frías-Armenta--Neumann-Lara--Pizaña (2004),
*Dismantlings and iterated clique graphs*; and the standard
retraction/divergence theorem in clique-graph dynamics.

## Reproduction

After preparing an environment with NetworkX from the existing
pinned monorepo checkout:

```bash
.venv-special-k3-v5/bin/python scripts/core9_snub_retractions_v2.py verify
.venv-special-k3-v5/bin/python -m unittest discover -s tests -p 'test_core9_snub_retractions_v2.py' -v
```

The verifier recomputes every positive and negative finite search,
each explicit isomorphism, all three second-iterate isomorphisms,
and exactly reproduces all committed files. All past census and
previous three-graph certificate files remain untouched.
