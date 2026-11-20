# Exact homology-first investigation of the path-join sphere family

## Family

For \(3\le m\le n\), let \(F_{m,n}\) be the 1-skeleton of
\(\partial(P_m*P_n)\), with each path indexed by its number of vertices.
A cross edge joins \(a_i\) and \(b_j\) exactly when one of \(a_i,b_j\)
is an endpoint of its path.

The replay tests the independent graph identifications
\(F_{4,4}\cong\) snub disphenoid (graph6 \`GQyuzw\`) and
\(F_{4,5}\cong\) the nine-vertex sphere (graph6 \`HCZTf\\}\`,
McKay order-nine index 208409).

## Finite results, not a divergence theorem

For all **28 pairs** \(4\le m\le n\le10\), raw \(K^3(F_{m,n})\)
is reconstructed through intersection of maximal cliques.
Each host is simplified by deleting only vertices whose **open neighborhood**
admits a fully recorded sequence of ordinary dominated-vertex folds down
to one vertex. These are simplicial homotopy equivalences, **not**
ordinary graph retractions or K-behavior equivalences.

The full reduced mod-2 homology of the residual clique complex is
computed using exact bitset Gaussian elimination on finite GF(2)
boundary matrices, with a complete face budget and Euler cross-check.

| Pair(s) | Only nonzero reduced GF(2) Betti number |
|---|---|
| \(F_{4,4}\) | \(\widetilde\beta_5=5\) |
| \(F_{4,5}\) | \(\widetilde\beta_3=3\) |
| The other 26 pairs, \(4\le m\le n\le10\) | \(\widetilde\beta_2=1\) |

**Stronger conclusion for the other 26:** Each residual clique complex
admits a replayable sequence of elementary simplicial collapses to a
connected closed triangulated 2-manifold with Euler characteristic 2.
The checker verifies both manifold links and Euler characteristic.
Therefore for these 26 finite cases
\[
\Delta(K^3(F_{m,n}))\simeq S^2.
\]
This suggests, but does not prove, the same statement for all
\(m,n\ge4\), other than \((4,4)\) and \((4,5)\).

## Homological exclusion rule for target retractions

If a graph \(X\) retracts onto \(Y\), then every reduced homology group
of \(\Delta(Y)\) is a direct summand of the corresponding group of
\(\Delta(X)\). Since \(\Delta(O_d)\cong S^{d-1}\):

- For \(K^3(F_{4,4})\), \(O_3,O_4\) are homologically impossible;
  \(O_6\) is not excluded by homology. In a separate target screen
  the third iterate contains no induced \(O_6\).
- For \(K^3(F_{4,5})\), \(O_3\) is excluded, \(O_4\) survives homology.
  Its absence as a graph retract was separately certified in
  \`scripts/core9_o4_divergence_v1.py\`.
- For the other 26, \(O_4\) is excluded; \(O_3\) is not excluded by
  homology alone.

The current experiment does **not** assert divergence of any member
of the family with both parameters at least four.

## Reproduction

From the census repository root, with NetworkX 3.6.1:

\`\`\`bash
python scripts/fmn_homology_first_v1.py build --max-n 10 \
  --output /tmp/fmn-homology-v1.json
python scripts/fmn_homology_first_v1.py verify \
  --input /tmp/fmn-homology-v1.json
python -m unittest discover -s tests -p test_fmn_homology_first_v1.py -v
\`\`\`

The JSON artifact records **every** vertex deletion and every fold
in its open neighborhood, and for 26 cases every face-collapse pair.
The verifier reconstructs all raw clique iterates and recomputes
the full GF(2) ranks before accepting a certificate.
Adversarial tests check rejection of invalid folds, false Betti numbers
and non-free face removals. No historical census data are modified.
