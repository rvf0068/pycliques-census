# Exact P2-isomorphism certificates: 27 new order-ten divergences (v15)

**Result.** The frozen order-ten v14 unresolved index contains 2,568 original
McKay entries. Exactly **27 unconditional, stiff ten-vertex entries** have now
been proved **K-divergent** by exact isomorphism of their second completely
pared clique iterates to already certified divergent reference graphs.
The new current root is v15 with **2,541** unresolved originals; all **120**
previously conditional cases are retained verbatim. The order-nine v4 root
(12 unresolved) is unchanged.

## The exact theorem and positive reference proofs

Let `P` denote complete sequential closed-neighborhood dominated-vertex
paring, with `P_0(G)=P(G)` and `P_{j+1}(G)=P(K(P_j(G)))`.
The dismantling theorem of Frías-Armenta–Neumann-Lara–Pizaña,
*Dismantlings and iterated clique graphs*, Discrete Mathematics **282**
(2004), 263–265, shows that each dominated-vertex deletion preserves
eventual clique behavior. Thus if `P_j(G) ≅ P_j(H)` as graphs and
`H` is K-divergent, then `G` is K-divergent.

The 27 new references are:

- **26** have `P_2(G) ≅ P_2(S)`, where `S` is the eight-vertex
  snub disphenoid `GQyuzw`. Both second pared iterates have
  **20 vertices / 136 edges**. The prior complete
  `K^4(S) → O_24` retraction and its independent verification are
  documented in
  [pycliques-project](https://github.com/rvf0068/pycliques-project/blob/main/docs/snub_o24_retraction.md).
  That proved positive underlies the frozen v3 nine-vertex
  snub promotions and v11 ten-vertex promotion.
- **1** (original McKay **11612099**, pared graph6 `IEhvvZ~~o`) has
  `P_2(G) ≅ P_2(T)`, with **51 vertices / 1,176 edges**, where
  `T` is nine-vertex original McKay **11363569** (`HUzrv~}`).
  It is the suspension of `C_7^c`: its two poles are nonadjacent
  and adjacent to all seven base vertices. The cyclic permutation
  `i ↦ i+1 (mod 7)` is a coaffination of the base. The previously
  archived divergence proof is by the expansive-suspension theorem
  of Larrión–Neumann-Lara–Pizaña, *On expansive graphs* (2009),
  Theorem 4.6, and is independently recorded in
  `scripts/historical_ninecore_lift_v1.py` and its CI proof replay.

Consequently **all 27 are proved**, not conjectured or inferred from
Betti numbers, WL hash equality, or a failed bounded search.

## Original McKay indices

The 26 new snub-P2 matches:

```text
 9696790   9784367  10030716  10374306  10375764  10494971
10496278  10585242  10625349  11267123  11267623  11268005
11292105  11411161  11416793  11495314  11496350  11497535
11599615  11606773  11608187  11608188  11609491  11634539
11638625  11698302
```

The further suspension-P2 match is **11612099**. The versioned
[certificate.json](certificate.json) stores **every original pared graph6**
and a **complete explicit 20- or 51-vertex isomorphism bijection**.
The mappings use a deterministic independent NetworkX labeling, not
the potentially different labels of the public pycliques implementation.

## How this was found

The initial full screen on all 2,568 frozen v14 records used public
`pycliques.completely_pared_graph`, `pycliques.clique_graph`, and
NetworkX exact `GraphMatcher` on the complemented graphs. The 49
reference instances comprised 36 previously snub-certified nine-vertex
sources (25 distinct pared graph6 encodings), the new O12-positive
nine-core 248936, six historically proved divergent nine-vertex cores,
and six O6/O12-positive ten-vertex cores.

The method constructs completely pared K2 for each source. It applies
graph-order, edge-count, degree-sequence and WL-hash invariants only
as **necessary prefilters**. A reported positive is accepted solely if
a full graph isomorphism was found and *every* ordered vertex pair
passes the edge/nonedge-preservation test. All eight P2 shards passed;
**0 distinct source graph6 strings were excluded by the K2 bound**.

The complementary P3 screen reproduced the same 26 snub positives.
The suspension reference exceeded that P3 pilot's clique bound;
four distinct source graph6 inputs also exceeded the P3 bound.
**No negative claim is made** about those third iterates or any other
unexamined divergent reference.

## Independent replay and census audit

`verify.py` is a positive-only independent proof that:

1. Authenticates the immutable **v14** input's Git blob;
2. Independently constructs all 27 second pared iterates using NetworkX
   maximal-clique enumeration and sequential dominated-vertex removal;
3. Checks each archived explicit bijection against **all** vertex pairs,
   using both edges and nonedges, and validates both reference sources;
4. Independently checks the suspension's cyclic coaffination and poles;
5. Confirms the 27 deleted original records are precisely the certified
   stiff, unconditional set, with every retained row unchanged, and all
   120 conditional rows preserved;
6. With `--public`, reconstructs every positive using the pinned public
   `pycliques` package and compares exact graph isomorphism;
7. With `--full`, re-runs the **entire 2,568-case P2 search**, requiring
   exactly the saved 27 positives and no skipped source graph6 inputs.

The exhaustive no-cutoff replay is also available as **eight independent
CI shards**, grouped by original McKay index modulo 8. Each job recomputes
every source in its partition with public `pycliques`, refuses skipped
cores or exceptions, verifies its exact source count, and compares its
positive index set with the corresponding saved 27-certificate subset.
The eight partitions are disjoint and cover all 2,568 original indices.
This replaces the earlier sequential eight-shard CI job, which reached
its 25-minute runner time limit; no mathematical assertion or negative
search interpretation was changed.

The historical v4/v14 verifier is retained byte-for-byte and invoked
through `replay_v14.py`, which changes *read access* to its former
current-root path only during the historical proof replay. All earlier
versioned indexes and historical research files are unchanged.

### Reproduction from the census repository

Install NetworkX 3.6.1 and `pycliques` from monorepo commit
`782deb653b8748e1b5759389cdd2134beac69351` (PR #32 merged).

```sh
python -m research.order10_reference_lifts_pilot.verify
PYTHONHASHSEED=0 python -m research.order10_reference_lifts_pilot.verify --public
# Optional: reproduce one of the eight exhaustive CI partitions.
PYTHONHASHSEED=0 python -m research.order10_reference_lifts_pilot.verify --full --shard 0 --shards 8
# Or omit --shard to check all eight partitions sequentially on one machine.
PYTHONHASHSEED=0 python -m research.order10_reference_lifts_pilot.verify --full
PYTHONHASHSEED=0 python -m research.order10_reference_lifts_pilot.replay_v14
python -m unittest discover -s tests -p test_current_root_index.py -v
```

An additional candidate graph from the search may be considered only
when the independent isomorphism or retraction proof is complete; no
timeout, heuristic similarity, or isolated induced octahedron is promoted.
