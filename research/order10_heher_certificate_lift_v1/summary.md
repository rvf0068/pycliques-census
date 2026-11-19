# Independent certification of 99 ten-vertex graphs by a divergent nine-sphere

**Previous working census**: 8,223 unresolved original connected ten-vertex graphs.
**New working census**: **8,124** unresolved, including **4,509** conditionally
divergent cases. No still-unproved condition is promoted.

The new theorem in the separate O4-retraction PR proves that the nine-vertex
graph `HEher^{` (order-nine index 248687) is **K-divergent**: its full third
clique iterate retracts onto induced \(O_4\).

The frozen historical order-10 v6 list contains exactly 99 previously
conditional records whose reference label is that graph. Here are the
independently replayed mechanisms:

| Certified rule | Original ten-vertex graphs |
|---|---:|
| Pared graph isomorphic to proven divergent reference | 63 |
| Explicit ordinary retraction from pared graph to reference | 28 |
| Delete one edge in no triangle, then dominated-vertex fold | 6 |
| Admissible inverse local-cutpoint extension followed by deletion of a non-triangular local bridge, then dominated-vertex folds | 2 |
| **Total newly proved K-divergent** | **99** |

## Certification

The self-contained `scripts/heher_divergence_class_lift_v1.py` independently:

1. Authenticates the SHA of the frozen `indeterminate_order_10_v6.txt`.
2. Reconstructs the proven \(K^3(\texttt{HEher^{})\to O_4\) retraction
   and checks every source edge.
3. For every one of the **63** reference cases, constructs an explicit
   graph isomorphism to the proved nine-vertex target.
4. For every one of the **28** retraction cases, finds an induced copy
   of the exact target on nine vertices and a complete ten-to-nine
   graph retraction, fixing the induced target and mapping every edge
   to an edge or equality.
5. For each of the **6** edge-deletion cases, exhibits an edge with
   no triangle, removes it, then independently checks every
   dominated-vertex fold and terminal target isomorphism.
   This is the hypothesis of FANP13, Theorem 6.2.
6. For each of the **2** inverse-cutpoint cases, constructs the
   admissible local-cutpoint split, verifies that its joining edge is
   a local bridge (endpoints separated by distance at least four
   after removal), removes it, checks each fold, and verifies the
   target. These are the hypotheses of FANP13, Theorems 6.1 and 6.2.
7. Produces every complete, explicit witness as a JSON artifact and
   byte-checks both the versioned v7 list and current root against
   the 99 certified exclusions. Earlier stage records and lists
   remain unchanged.

The original ten-vertex-to-pared graph reductions are certified by
the existing immutable census stage and core-index provenance. This
lift independently verifies the *previously conjectural final
dependency* on the nine-vertex target.

Reproduction (from a checkout containing the O4 theorem, with
NetworkX 3.6.1):

```bash
python scripts/heher_divergence_class_lift_v1.py verify
python scripts/heher_divergence_class_lift_v1.py certificates \
  --output /tmp/heher-class-certificates.json
```

The current root `indeterminate_order_10.txt` and new
`indeterminate_order_10_v7.txt` are byte-identical. The independent
regression test now protects v7 and the immutable pre-v3 original
8,648-case snapshot. **The first nine-vertex graph `HCZTf\}`
remains K-behavior indeterminate**, along with its 120 historical
conditional ten-vertex cases.

This classification is valid once the new script passes independent
CI replay, and the positive nine-vertex O4 theorem is merged.
