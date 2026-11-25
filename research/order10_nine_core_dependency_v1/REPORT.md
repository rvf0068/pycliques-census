# Exact links from unresolved nine-vertex cores to stiff ten-vertex families

## Theorem (conditional clique-behavior equivalences)

Write \(P_0(G)\) for complete dominated-vertex paring and
\(P_{j+1}(G)=P(K(P_j(G)))\), with \(K\) the maximal-clique intersection
graph. The dismantling theorem of Frías-Armenta, Neumann-Lara and
Pizaña preserves eventual clique behavior under paring.

**Theorem.** The following *exact* graph isomorphisms hold:

\[
\begin{aligned}
 P_3(G_{249576}^{(9)})&\cong P_3(G_{7044680}^{(10)}),\\
 P_3(G_{251628}^{(9)})&\cong P_3(G_{7070392}^{(10)}),\\
 P_3(G_{260040}^{(9)})&\cong P_3(G_{7479384}^{(10)}).
\end{aligned}
\]

Superscripts specify the original connected-graph order, not an
iteration exponent. McKay indices refer to the exact original
connected-graph enumeration within that order.

| Unresolved nine-original | Its \(P_3\) vertices/edges | Certified stiff ten \(P_3\)-class representative | Exact ten-original members |
|---:|---:|---:|---:|
| **249576** | 53 / 1,044 | **7044680** | 17 |
| **251628** | 55 / 1,156 | **7070392** | 23 |
| **260040** | 58 / 1,289 | **7479384** | 25 |
| **Total** | | | **65** |

The [certificate archive](certificates.json) gives all 53, 55 and 58
coordinates of the three complete nine-to-ten bijections. The
[verifier](verify.py) reconstructs both sides from their original
graph6 strings using the already independently certified NetworkX
and bitset Bron--Kerbosch reconstruction, then checks **every
ordered pair** of vertices under the archived maps. It also
independently reconstructs **each of the 65 stiff ten-vertex
originals** and checks all 65 previously archived complete P3
member-to-representative bijections against the immutable
[global P3 archive](../order10_p3_global_v23_index/certificates.json).

These are positive isomorphism theorems, not merely matching
graph dimensions, hashes or failed retraction searches.

## Additional fourth-iterate bridge

The already merged, independently verified
[ten-v24 P4 cap-recovery theorem](../order10_p4_cap_rescue_v24/REPORT.md)
gives an exact 685-coordinate isomorphism

\[
 P_4(G_{7044680}^{(10)})\cong P_4(G_{11614797}^{(10)}).
\]

McKay 11614797 was a **singleton** in the historical global P3
index, so it is not among the 65 originals above.

Combining this historical fourth-iterate bridge with
\(P_3(G_{249576}^{(9)})\cong P_3(G_{7044680}^{(10)})\)
proves that McKay 11614797 has the same **eventual K-behavior**
as the still-indeterminate nine-original 249576. The new verifier
reconstructs both fourth iterates, checks the old pinned
685-coordinate bijection against every edge and nonedge, and pins
the exact original positive certificate blob.

## Correct decomposition of the unresolved ten-v25 cohort

The frozen nine-v9 and ten-v25 sources contain **430** ten-originals
whose completely pared original has nine vertices isomorphic to one
of the unresolved nine-originals. The verifier independently checks
each of these 430 nine-vertex graph isomorphisms, rather than
merely trusting their graph6 encodings.

These are *disjoint* from the newly proved stiff equivalences:

| Unresolved nine-original | Pared-nine dependents | Stiff \(P_3\) dependents | Extra stiff \(P_4\) dependent | Total |
|---:|---:|---:|---:|---:|
| 249576 | 141 | 17 | 1 | **159** |
| 251628 | 147 | 23 | 0 | **170** |
| 260040 | 142 | 25 | 0 | **167** |
| **Total** | **430** | **65** | **1** | **496** |

Therefore **496 of the 1,052 currently unresolved original
ten-vertex graphs** have the same eventual K-behavior as one of
the three still-indeterminate nine-originals. The remaining
**556 stiff ten-vertex originals** have *not yet been linked*
to these three nine-originals by the certified equivalences here;
this does **not** assert that no such relation exists.

The number of unresolved ten-vertex originals is still **1,052**,
and the number of unresolved nine-vertex originals is still **3**.
**There is no census promotion, no removal, and no assertion of
convergence or divergence.**

## Proof and reproducibility

The archive pins Git blob identities for both authoritative frozen
indices and for the previous global P3 and P4 certificate archives.
It checks both mutable working roots against their current frozen
indices, preserves all historical data, and independently derives
the disjoint population counts.

Run from the census root with Python 3.12 and NetworkX 3.6.1:

```sh
python -m research.order10_nine_core_dependency_v1.verify
python -m unittest research.order10_nine_core_dependency_v1.test_verify -v
```

The dedicated GitHub Actions workflow also rejects optimized Python
(which could disable older proof-critical assertions).

## Consequences for research priorities

A proof of the eventual clique behavior of **any one** of the
three remaining nine-originals now determines that behavior for
**159, 170, or 167** unresolved ten-originals, respectively. This
makes the three nine-originals even more important than the original
430-pared-core count suggested.

The third pared iterates of the unresolved nine-originals have 53,
55 and 58 vertices. Previous complete negative searches ruled out
certain low-degree retracts on at most ten vertices at this stage;
those are genuine *restricted retraction obstructions*, not
convergence theorems. The new equivalences suggest reusing exact
nine-core witnesses across their larger stiff ten-vertex families
instead of running duplicate searches.
