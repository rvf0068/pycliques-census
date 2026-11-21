# Positive bounded equivalence certificates for pared third clique iterates

**Scope:** full original-McKay coverage, but **not** a claim to have found
all globally maximal isomorphism classes or classified their clique behavior.

This stage authenticates the immutable v10 original-index list of **1,043
fully unclassified stiff ten-vertex graphs**. Eight independent shards reconstruct
and completely pare the first three clique iterates. Each original source has
an eight-second wall-clock limit and a cap of 250 maximal cliques per stage;
any unresolved enumeration is recorded as an explicit skip.

On the certified CI run, **1,024 originals were reconstructed**, while
**19 were skipped**. The shard-local exact isomorphism checks certify
**70 nontrivial within-shard groups containing 229 original graphs**.
These groups are positive equivalence witnesses, **not** globally maximal
classes: different shards may contain more representatives of the same
isomorphism class. In particular, the independently merged 33-member family
represented by McKay **7002338** (PR #56) can be spread among shards.

Each nontrivial group stores all original McKay indices and graph6 strings,
four stages of explicit dominated-vertex folds, the pared third-iterate graph6,
and a complete source-to-representative bijection. The builder uses a
Weisfeiler–Lehman signature only to prefilter; it validates exact graph
isomorphisms edge by edge. The separate verifier **does not call the builder's
fold function**: it checks every saved fold by the actual closed-neighborhood
inclusion before deleting a vertex, checks complete paring and intervening
clique graphs, and verifies the saved bijection on all vertex pairs.

The CI aggregator rechecks every within-shard bijection, confirms all
1,043 original indices appear **exactly once** across the eight shard
artifacts, checks source graph6 identity and reports all 19 explicit skips.
It deliberately makes **no negative global isomorphism claim**.

All classification files and past positive retraction archives remain
unchanged. No Betti-number computation or new K-divergence verdict is involved.

## Reproduction

With `networkx==3.6.1` from the repository root:

```bash
for i in {0..7}; do
  python research/order10_pared_k3_equivalence_v1/classes.py \
    --shard "$i" --shards 8 --output "/tmp/shard-$i.json"
  python research/order10_pared_k3_equivalence_v1/classes.py \
    --shard "$i" --shards 8 --verify "/tmp/shard-$i.json"
done
python research/order10_pared_k3_equivalence_v1/audit.py \
  /tmp/shard-{0..7}.json --output /tmp/verified-mckay-batch-audit.json
```

The time-intensive optional global exact matching experiment was retained
separately on the `research/order10-pared-k3-global-followup-v1` branch;
it is **not** part of this certified contribution.
