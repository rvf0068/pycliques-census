# Certified ten-v25: four additional ten-vertex K-divergences

## Theorem

Let \(P_0(G)=P(G)\) denote complete closed-neighborhood paring,
and let \(P_{j+1}(G)=P(K(P_j(G)))\).

**Theorem.** Each of the four original connected ten-vertex
McKay graphs with indices **11551790, 11552072, 11555600,
11707526** is \(K\)-divergent.

For every graph \(G\) on this list we construct a complete
132-vertex isomorphism

\[
\varphi_G:P_4(G)\ \cong\ P_3(H),
\qquad H=G_{260910},
\]

where the nine-vertex graph \(H\) (graph6
`HUZvvzu`) already has a certified **ordinary
retraction** \(r:P_3(H)\to O_{15}\), and
\(O_d=\overline{dK_2}\).

**Proof.** Transport the complete retraction using
\(\varphi_G^{-1}\circ r\circ\varphi_G\).
This is an ordinary pointwise-fixed graph retraction of
\(P_4(G)\) onto an induced \(O_{15}\), as independently
checked on every source edge by the new verifier.
Since \(K(O_d)\cong O_{2^{d-1}}\), the target is
\(K\)-divergent. The ordinary retraction theorem and
the dismantling theorem for clique iterations imply
that the original \(G\) is \(K\)-divergent. \(\square\)

This is a **cross-depth** equivalence: the original
ten-vertex graphs need four pared clique iterations
to reach the third pared clique iterate of the proven
divergent nine-vertex reference. There is no need
for the two iteration depths to coincide.

## Full positive certificates

| Original McKay | Original graph6 | \(P_0\) edges | \(P_1\) vertices | \(P_2\) vertices | \(P_3\) vertices | \(P_4\) vertices |
|---:|---|---:|---:|---:|---:|---:|
| **11551790** | `IEhetr}|o` | 28 | 9 | 12 | 21 | **132** |
| **11552072** | `IEhetvm~O` | 28 | 9 | 12 | 21 | **132** |
| **11555600** | `IEhevi~~_` | 29 | 9 | 12 | 21 | **132** |
| **11707526** | `IQyurzUuo` | 28 | 9 | 12 | 21 | **132** |

The edge counts at stages \(P_1,\ldots,P_4\) are
**26, 52, 176, 7,880**, for every source.

The [positive certificate archive](certificates.json)
stores each original graph6, all five stage dimensions,
complete canonical P4 graph6 SHA-256, and a **full
132-coordinate vertex bijection** (132 Base64-encoded
bytes with a separately pinned SHA-256 digest).
Each saved bijection is checked on **all 132 squared
ordered vertex pairs**, not just positive edges,
graph invariants, or WL hashes.

The historical complete ordinary retraction is
in [order9_260910_o15_v1](../order9_260910_o15_v1/certificate.json),
Git blob:

`8d97a9e8278cf67aa2c431fb2551b47547bf19f5`.

The historical reference P3 has exactly 132 vertices,
7,880 edges, and labeled graph6 SHA-256:

`248ab6dc4e6bb9317ba2b271bb3e551bbdecae1e8111cf07beb8858a227513a6`.

The independent verifier reconstructs this historical
reference and checks its entire projection: the 15
antipodal nonedges, all octahedral cross-pair edges,
all 132 source image assignments, fixation of all 30
target vertices, and preservation of all 7,880 edges.

Then it independently reconstructs **each** of the
four ten-vertex graphs from original graph6 using
deterministic paring and complete sorted maximal
clique lists. At every stage the enumerator is
crosschecked against independent pivoted bitset
Bron--Kerbosch. Another independent P4 reconstruction
from the previously merged exact P3 index and PR #92
paring code crosschecks the result without relying
on matching labels.

After the saved full isomorphism is checked,
the verifier explicitly constructs all 132 coordinates
of the transported O15 retraction and checks that it
fixes the induced target pointwise and maps every
source edge to an edge or an equal vertex. A
label-constrained GraphMatcher on the sparse
complement graphs independently validates the
specific archived bijection.

Every source is independently proved divergent; the
former four-original P3 equivalence class is only
an additional check.

## Exact ten-v24 to ten-v25 census promotion

The old snapshot is pinned to the immutable Git blob

`cf0ba2b44519b51565808fbe0b24d3c76c061666`.

The new immutable ten-v25 snapshot and current working
indeterminate-order-ten root have exactly the four
original indices above removed, and **all 1,052
retained six-column records are unchanged**.

| Unresolved ten-original partition | ten-v24 | ten-v25 |
|---|---:|---:|
| Pared to one of three unresolved nine-vertex graphs | 430 | **430** |
| Stiff ten-vertex original cores | 626 | **622** |
| **All unresolved originals** | **1,056** | **1,052** |

The nine-v9 census is unaffected: three nine-vertex
originals remain unresolved, along with their
430 dependent ten-vertex originals.

In the frozen global P3 index the four promoted
sources formed one exact class, represented by
11551790. Consequently the 622 surviving stiff
originals comprise **619** with fully reconstructed
P3 in **521 classes**, plus the same three
resource-limited P3 cases. All old P3 and P4
proof archives remain unchanged.

## Reproduce

From the census repository root with Python 3.12
and NetworkX 3.6.1:

```sh
python -m research.order10_p4_crossdepth_o15_v25.verify
python -m unittest research.order10_p4_crossdepth_o15_v25.test_verify -v
python -m unittest discover -s tests -p test_current_root_index.py -v
```

The dedicated CI workflow also replays the historical
ten-v24 proof with only a read-only in-memory alias
for the formerly mutable root, so historical
certificates remain valid when ten-v25 becomes current.

## Research direction

These four new divergences resulted from comparing
**iterates at different depths**. The next search
should index the pared clique iterates of every
proved divergent nine-vertex reference and compare
them against the small P3/P4 iterates of the 521
remaining reconstructible stiff ten-vertex classes.
Only complete positive isomorphisms and retraction
certificates should be used to advance the index.
