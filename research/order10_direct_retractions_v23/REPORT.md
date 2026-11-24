# Certified ten-v23: 149 stiff ten-vertex cores retract onto divergent nine-vertex graphs

## The new result

**149 previously indeterminate connected ten-vertex McKay originals are
\(K\)-divergent.** Each is stiff (no dominated vertex), but admits a
*complete ordinary graph retraction* onto an induced copy of one of six
previously proved \(K\)-divergent nine-vertex graphs.

The full source graph6, the vertex deleted to obtain the nine-vertex
induced target, the image of that vertex, and a nine-point bijection to
the certified nine-vertex reference are saved for **each of the 149
graphs** in [certificates.json](certificates.json).

For every witness, the independent verifier reconstructs both graphs
from graph6 and checks **all source edges** (adjacent *or equal* after
projection), **all target edges and nonedges** under the bijection,
pointwise fixation of the induced target, and absence of any dominated
vertex in the original ten-vertex source.

Neumann-Lara's Retraction Theorem gives the implication
\(H\) \(K\)-divergent and \(H\) a retract of \(G\)
\(\implies G\) \(K\)-divergent. A convenient statement is Theorem 3.1 of
F. Larrión, M. A. Pizaña and R. Villarroel-Flores,
*Iterated clique graphs and bordered compact surfaces*
(https://xamanek.izt.uam.mx/map/papers/mangas08x.pdf).
The prior nine-vertex divergent sources carry complete archived
octahedral retractions that the new verifier **replays**.

## Exact source families

| Proved nine-vertex reference | Graph6 | Ten-originals newly certified |
|---:|---|---:|
| 249436 | `HEhff^{` | **39** |
| 249574 | `HEhfvx}` | **20** |
| 250814 | `HEhuvzm` | **26** |
| 251759 | `HEhvtzm` | **26** |
| 251902 | `HEhvvzm` | **23** |
| 254369 | `HEjfvx}` | **15** |
| **Total** | | **149** |

The initial deterministic target screen compared all 778 stiff ten-vertex
cores surviving ten-v22 with each of the **nine** proved divergent
nine-vertex originals in frozen nine-v4 but absent from nine-v9. Six
reference families yielded the 149 positive retractions. This is
a *finite target screen only*: failure against this target family is
not evidence of convergence.

## Example

McKay **5808448** (graph6 `I?bbU^un_`) retracts onto the induced
nine-vertex subgraph obtained by deleting vertex 3, via the map
\(r(3)=0\), \(r(v)=v\) for every \(v\ne 3\).
The fixed subgraph is isomorphic to proved divergent McKay **249436**
(graph6 `HEhff^{`). The vertex-level target bijection is archived.

Crucially, **stiffness does not preclude retractions**. Here vertex
3 is not adjacent to its projection image 0. The map respects all
source edges, but the closed-neighborhood domination test cannot delete
vertex 3. This is why searching only for dominated vertices did not
recover this family.

## Exact census transition

| Class of still-unresolved connected ten-vertex originals | ten-v22 | ten-v23 |
|---|---:|---:|
| Pared to the three unresolved nine-vertex cores | 430 | **430** |
| Stiff ten-vertex pared cores | 778 | **629** |
| **All unresolved original graphs** | **1,208** | **1,059** |

The immutable [ten-v22](../../indeterminate_order_10_v22.txt) snapshot
has Git blob SHA-1 `b066bf5b32d0c77448a0a23e10d33715aca19fc0`.
The new immutable [ten-v23](../../indeterminate_order_10_v23.txt)
and current [working root](../../indeterminate_order_10.txt) agree
byte-for-byte. Exactly the 149 source indices in
[certificates.json](certificates.json) are removed; all 1,059 retained
six-field records are preserved without modification.

Nine-v9 remains exactly three indeterminate graphs, McKay 249576,
251628 and 260040; none is promoted by this work.

## Reproduce the positive certificates

From the repository root with Python 3.12 and NetworkX 3.6.1:

```sh
python -m research.order10_direct_retractions_v23.verify
python -m research.order10_direct_retractions_v23.scan
python -m unittest research.order10_direct_retractions_v23.test_verify -v
python -m unittest discover -s tests -p test_current_root_index.py -v
python -m research.order10_direct_retractions_v23.replay_v22
```

The independent scanner reconstructs the finite search over all 778 stiff sources and nine certified nine-vertex targets and checks that it recovers exactly the 149 archived positives.
The new verifier checks all 149 direct retractions, independently
replays each of the six source nine-vertex divergence proofs,
authenticates frozen v22 and verifies the exact 149-index deletion.
Historical ten-v22 proofs can be replayed against the frozen v22
working root, with no modifications to their actual proof logic.
The dedicated CI workflow rejects `python -O` to guard against
suppression of proof-critical assertions.

**Next:** Continue searching the remaining 629 stiff ten-core
originals with deeper pared-iterate equivalences and genuinely new
positive octahedral/source retractions. No resource-limited negative
search can resolve their \(K\)-behavior.
