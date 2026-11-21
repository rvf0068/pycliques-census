# A 33-member equivalence class of completely pared third clique iterates

**Proved structural result, not a clique-divergence/convergence classification.**
For each of the **33** original ten-vertex, stiff, currently fully unclassified
McKay indices listed in `verify.py`, the completely dominated-vertex-pared
third clique iterate is isomorphic to that of McKay **7002338**. Each has
**37 vertices and 503 edges** at the third pared level.

The self-contained verifier authenticates the exact original v10 census
Git blob, checks all 33 original numerical McKay indices and their graph6
strings, independently reconstructs the iterated clique graphs with two
different maximal-clique algorithms (NetworkX and bitset Bron–Kerbosch),
replays every dominated-vertex fold, and calculates full graph-isomorphism
bijections. Every vertex pair is checked for preservation of both edges
and nonedges; an adversarially altered map is rejected. The complete
explicit isomorphism maps are emitted as a reproducible JSON artifact.

This is **not 33 new divergence classifications**. The known invariance of
clique behavior under dominated-vertex dismantling, together with
isomorphism and taking iterates, shows all 33 graphs have identical
eventual K-convergence/divergence behavior. One future proof on the
representative settles every original McKay index in this class.

The earlier uniform bounded octahedral search found no positive
certificate, so all 33 remain listed as indeterminate. No Betti-number
calculation is involved.

## Reproduce

With `networkx==3.6.1` from repository root:

```bash
python research/order10_pared_k3_33class_v1/verify.py --write /tmp/pare-k3-33.json --self-test
python research/order10_pared_k3_33class_v1/verify.py --verify /tmp/pare-k3-33.json
```
