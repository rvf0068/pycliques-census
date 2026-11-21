# Twelve new positive \(K^2\to O_3\) certificates for ten-vertex stiff cores

**Status:** 12 **proved \(K\)-divergences**, each with a complete ordinary
graph retraction, independently replayable from its graph6 string.
Historical census indices are zero-based McKay connected-order-ten indices.

## Positive theorem and proof

Let \(O_d=\overline{dK_2}\), so \(O_3\) is the 6-vertex octahedron.
Every maximal clique of \(O_d\) chooses exactly one endpoint of each
of the \(d\) independent nonedges, and two maximal cliques are
disjoint exactly when their choices are complementary. Therefore
\[
K(O_d)\cong O_{2^{d-1}}.
\]
It follows that \(O_3\) is \(K\)-divergent.

For every graph in the table, the accompanying `certificates.json`
gives an induced six-vertex \(O_3\subseteq K^2(G)\) and **all**
coordinates of a projection \(r:V(K^2(G))\to V(O_3)\). The standalone
`verify.py` independently reconstructs the two unpared clique graphs,
checks the six fixed target vertices, verifies exactly three disjoint
nonedges on the target, and checks that **every edge** of \(K^2(G)\)
has adjacent or equal projected endpoints. Thus \(r\) is an ordinary
graph retraction. Neumann-Lara's Retraction Theorem implies
\(K^2(G)\) is \(K\)-divergent, and therefore \(G\) is \(K\)-divergent.
In particular, no conjectural snub-disphenoid assertion is used.

| McKay index | Graph6 | \(|K(G)|\) | \(|E(K(G))|\) | \(|K^2(G)|\) | \(|E(K^2(G))|\) |
|---:|---|---:|---:|---:|---:|
| 10298587 | `ICZJbu}v_` | 16 | 73 | 24 | 169 |
| 10582171 | `ICZejv{nO` | 17 | 83 | 25 | 192 |
| 10592280 | `ICZenXynG` | 16 | 72 | 24 | 171 |
| 11031164 | `ICpderm^o` | 15 | 63 | 24 | 163 |
| 11031734 | `ICpder}^o` | 14 | 56 | 22 | 142 |
| 11106678 | `ICpduzm\o` | 14 | 54 | 22 | 144 |
| 11551444 | `IEhetp}^O` | 14 | 54 | 22 | 144 |
| 11566611 | `IEhffZmvO` | 15 | 65 | 22 | 148 |
| 11585214 | `IEhuVf{z_` | 15 | 62 | 22 | 145 |
| 11599630 | `IEhvEv{z_` | 17 | 83 | 24 | 176 |
| 11602159 | `IEhvFf{z_` | 17 | 84 | 25 | 190 |
| 11624876 | `IEjbvN{}_` | 16 | 76 | 23 | 169 |

All twelve appear in the **frozen v8** list with pared order 10 and
the three original classification fields `- - -`. No graph with a
conditional reference is promoted to a theorem.

## Data and independent replay

The `certificates.json` array uses the **canonical integer-mask order**
on the maximal cliques of each iterate. All projection arrays have
length \(|V(K^2(G))|\) and are indexed by the canonical source vertex.
The target vertex set is an increasing six-element list; the map fixes
it pointwise. This avoids dependence on a library's arbitrary
maximal-clique enumeration order.

The verifier deliberately implements a second maximal-clique enumerator
using **bitset Bron--Kerbosch**, independently of NetworkX's
`find_cliques`. Both sets of maximal cliques must agree at both
levels. It authenticates the frozen v8 input by its Git blob hash, checks
all twelve graph6 encodings and their previously unclassified statuses,
and rejects adversarial mutation of the section, graph edge count and
source graph6 encoding. No omitted negative result or timeout counts
as evidence of divergence.

Reproduce from the census repository root:

```bash
python -m pip install networkx==3.6.1
python research/order10_second_clique_o3_retracts_v1/verify.py --self-test
```

The proof stage **does not itself change** any historical working index.
A separate, explicitly versioned index advancement may remove these
twelve proved cases from the current 7,932-case list, yielding 7,920.
The old v8 evidence must remain unchanged.

## Search provenance and limitations

The discovery screened raw \(K^2(G)\) for ordinary retractions onto
induced \(O_3\), after first testing structurally simpler targets.
Among the 2,357 stiff ten-vertex cores in the v8 working list,
2,354 had \(|K^2(G)|\le36\). These were screened with an induced-matching
enumeration in the complement plus local-domain constraints and
arc-consistency/backtracking; 57 successful maps belonged to exactly
12 source graphs. The three larger second clique graphs (42, 62, 288
vertices) were deliberately deferred. The **positive certificates**
are independently replayed here. The exploratory negative-search counts
are *not* supplied as a full, independently archived exhaustion proof
and must not be used to classify any other graph.

Relevant prior results and sources: Neumann-Lara's graph Retraction
Theorem as used by the census's earlier octahedral certificates
(`research/order10_first_clique_octahedron_retract_v1`);
the previous \(O_4\) lift
(`research/order10_four_o4_lift_v1`).
