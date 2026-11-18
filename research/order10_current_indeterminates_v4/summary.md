# Current order-10 indeterminate population, certificate lift v4

This is a **certified accounting update**, not a new divergence theorem.
The original and v3 census results and all historical proof files remain
unchanged. The previous v3 list contained 8,533 graphs; six distinct
nine-vertex stiff-core classes with independently replayable divergence
certificates cover 300 of those original connected ten-vertex graphs.

| Core representative | Graph6 | Original members | Certified mechanism |
|---:|---|---:|---|
| 6938923 | `HEht}pl` | 23 | special_O4_core_lift_v1 |
| 6939350 | `HEht~bl` | 110 | special_O4_core_lift_v1 |
| 7454135 | `HEnb~jl` | 61 | historical_raw_K3_special_O7 |
| 9678187 | `HQyuzpt` | 37 | historical_raw_K3_special_O4 |
| 10768817 | `HUZ~v~}` | 33 | historical_coaffine_suspension |
| 11363569 | `HUzrv~}` | 36 | historical_coaffine_suspension |

**Total newly excluded from the stale v3 working list: 300**
(133 special-O4-core-lift originals plus 167 disjoint historical
nine-core-lift originals). Every index was still in v3.

**Remaining indeterminate: 8,233 original connected order-ten graphs.**
These comprise 2,092 representatives with an eight-vertex pared core
(the conjectural snub-disphenoid class), 3,738 original members
distributed among 29 still unresolved nine-vertex cores, and
2,403 original graphs with a ten-vertex stiff core.
The 4,608 entries annotated conjectured_divergent retain their
unproved status; **no conjectural cases are promoted to proofs**.

This stage uses the original zero-based McKay census indices.
Its certified_divergent.tsv records every excluded index, its
exact nine-core class and the source of its existing proof.

## Mathematical provenance

- For cores 6938923 and 6939350, replay the saved independent
  special-O4 K^3 witnesses and 133 original dominated-fold/isomorphism
  certificates via scripts/special_octahedron_class_lift_v1.py verify.
- For the other four core classes, scripts/historical_ninecore_lift_v1.py
  independently verifies 167 complete original fold and isomorphism
  certificates, special O7/O4 witnesses in raw K^3, or an explicit
  suspension coaffination. These cores are proved K-divergent.
- The theorem of Frías-Armenta--Neumann-Lara--Pizaña (2004) preserves
  clique convergence/divergence under dominated-vertex deletions.
  The suspension certificates use Larrión--Neumann-Lara--Pizaña
  (2009), Theorem 4.6.

Neither failure of a bounded retraction search nor conditional
snub-disphenoid evidence is used to discard any further graph.

## Reproduction

From the census repository with the pinned historical environment:

```bash
bash scripts/bootstrap_special_k3_v5.sh
.venv-special-k3-v5/bin/python scripts/special_octahedron_class_lift_v1.py verify
.venv-special-k3-v5/bin/python scripts/historical_ninecore_lift_v1.py --output /tmp/historical-ninecore-lift-167.json
.venv-special-k3-v5/bin/python scripts/historical_ninecore_lift_v1.py --verify /tmp/historical-ninecore-lift-167.json
.venv-special-k3-v5/bin/python scripts/current_indeterminate_v4.py verify
```

The v4 verification command independently rebuilds all three
committed v4 artifacts in memory and compares their bytes. Its
build command refuses to overwrite different existing results.
