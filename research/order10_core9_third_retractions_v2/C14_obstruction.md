# A short obstruction to the unique C14-complement retraction

This independent, human-checkable proof uses the frozen graph6 labeling
from `runs/order10/core9-structure-v1/records/06962151.json`,
`iterates[3]["graph6"]`. Let X be that 40-vertex third
**completely pared** clique iterate of stiff nine-core `HEhvfzm`.

The complement of X has exactly one induced 14-cycle. Its cyclic
vertex order is

`15, 0, 38, 12, 31, 13, 30, 16, 1, 26, 8, 25, 7, 22`.

Let T denote these 14 vertices. The induced graph X[T] is C14^c.
For any graph retraction r:X -> X[T], with the convention that a
graph morphism sends adjacent vertices to adjacent *or equal* vertices,
an outside vertex x has to map into

D_x = { t in T : N_X(x) intersect T is contained in N_{X[T]}[t] }.

The exact domain calculations from the stored graph6 are

- D_4 = {1,7,8};
- D_27 = {26};
- D_33 = {22}.

Both edges 4~27 and 4~33 occur in X. Since r(27)=26, the first
forces r(4)=7: 7 is the **only** member of D_4 adjacent or equal to
26. But r(33)=22 and 7,22 are distinct nonadjacent vertices in
X[T], because they are consecutive in the complement 14-cycle.
This contradicts edge 4~33.

**Thus no graph retraction X -> X[T] exists.** Since the induced
C14-complement is unique, X retracts onto no C14-complement.

## Minimal reproducibility check

Execute this from the repository root using any NetworkX environment:

```python
import json
from pathlib import Path
import networkx as nx

data = json.loads(Path(
    "runs/order10/core9-structure-v1/records/06962151.json"
).read_text())
X = nx.from_graph6_bytes(data["iterates"][3]["graph6"].encode("ascii"))
cycle = [15, 0, 38, 12, 31, 13, 30, 16, 1, 26, 8, 25, 7, 22]
T = set(cycle)
H = X.subgraph(T)
assert len(X) == 40 and X.number_of_edges() == 601
cycles = [
    c for c in nx.chordless_cycles(nx.complement(X), length_bound=40)
    if len(c) == 14
]
assert len(cycles) == 1 and set(cycles[0]) == T

def domain(x):
    fixed_neighbors = set(X[x]) & T
    return {t for t in T if fixed_neighbors <= (set(H[t]) | {t})}

assert domain(4) == {1, 7, 8}
assert domain(27) == {26}
assert domain(33) == {22}
assert X.has_edge(4, 27) and X.has_edge(4, 33)
assert {t for t in domain(4) if t == 26 or H.has_edge(t, 26)} == {7}
assert not H.has_edge(7, 22) and 7 != 22
print("No retraction onto the unique C14 complement")
```

This local obstruction strengthens the independently replayed bounded
CSP search. Neither result claims K-convergence: other kinds of
K-divergent retracts, and other divergence mechanisms, remain open.
