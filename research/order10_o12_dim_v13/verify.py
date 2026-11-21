"""Independent, positive-only O12 proof and v12 -> v13 census audit.

No finder, integer-programming solver, or pycliques module is imported.
Every maximal clique is built independently by NetworkX, and each
dominated vertex is deleted sequentially with its closed-neighborhood
containment checked. The archived graph6 is matched by exact isomorphism.
"""
import hashlib
import json
from pathlib import Path
import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
CERT = Path(__file__).with_name("certificate.json")
BEFORE = ROOT / "indeterminate_order_10_v12.txt"
AFTER = ROOT / "indeterminate_order_10_v13.txt"
CURRENT = ROOT / "indeterminate_order_10.txt"
BEFORE_BLOB = "5130910bbc7994210d33d3ade857b5c0807a65d8"


def check(ok, message):
    if not ok:
        raise AssertionError(message)


def slow_pare(graph):
    graph = graph.copy()
    while True:
        vertices = list(graph)
        closed = {v: set(graph[v]) | {v} for v in vertices}
        dominated = next(
            (v for v in vertices if any(v != w and closed[v] <= closed[w]
                                       for w in vertices)), None
        )
        if dominated is None:
            break
        graph.remove_node(dominated)
    return nx.convert_node_labels_to_integers(graph)


def independent_clique_graph(graph):
    # Deliberately use all-pairs intersections instead of the finder's
    # inverted incidence lists.
    cliques = [frozenset(q) for q in nx.find_cliques(graph)]
    result = nx.Graph()
    result.add_nodes_from(range(len(cliques)))
    for i, q in enumerate(cliques):
        for j in range(i + 1, len(cliques)):
            if q.intersection(cliques[j]):
                result.add_edge(i, j)
    return result


def rows(raw):
    data = {}
    for line in raw.decode("utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        pieces = line.split()
        check(len(pieces) == 6, "Unexpected index row width")
        idx = int(pieces[0])
        check(idx not in data, "Duplicate McKay index")
        data[idx] = pieces
    check(list(data) == sorted(data), "Index is unsorted")
    return data


def verify():
    cert = json.loads(CERT.read_text())
    check(cert["index"] == 10510367, "Wrong McKay index")
    prior_bytes = BEFORE.read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(prior_bytes)).encode()
                        + b"\0" + prior_bytes).hexdigest()
    check(blob == BEFORE_BLOB, "Historical v12 blob was modified")
    after_bytes = AFTER.read_bytes()
    check(CURRENT.read_bytes() == after_bytes, "Current root must be v13")
    old, new = rows(prior_bytes), rows(after_bytes)
    check(len(old) == 2788 and len(new) == 2787, "Wrong census size")
    check(set(old) - set(new) == {10510367}, "Wrong deletion cohort")
    check(all(row == old[index] for index, row in new.items()),
          "A retained census row was modified")
    check(old[10510367][2] == cert["source_pared_g6"]
          and old[10510367][1] == "10"
          and old[10510367][3:] == ["-", "-", "-"],
          "The removed row was not the expected unconditional stiff graph")
    check(sum(r[4] == "conjectured_divergent" for r in new.values()) == 120,
          "The 120 conditional entries were modified")

    source = nx.from_graph6_bytes(cert["source_pared_g6"].encode())
    orders = []
    for i in range(5):
        source = slow_pare(source)
        orders.append([len(source), source.number_of_edges()])
        if i < 4:
            source = independent_clique_graph(source)
    check(orders == cert["p_sizes"], "Independent P0,...,P4 sizes differ")

    host = nx.from_graph6_bytes(cert["p4_g6"].encode())
    check(len(host) == 64 and host.number_of_edges() == 1844,
          "Saved host order or size differs")
    pairs = cert["target_pairs"]
    endpoints = [v for pair in pairs for v in pair]
    check(len(pairs) == 12 and len(set(endpoints)) == 24,
          "Target is not twelve disjoint opposite pairs")
    for i, u in enumerate(endpoints):
        for j in range(i + 1, len(endpoints)):
            v = endpoints[j]
            check(host.has_edge(u, v) == (j != (i ^ 1)),
                  "Target is not an induced O12")
    labels = cert["image_indices"]
    check(len(labels) == len(host) and
          all(isinstance(i, int) and 0 <= i < 24 for i in labels),
          "Projection label list is incomplete")
    projection = [endpoints[i] for i in labels]
    check(all(projection[t] == t for t in endpoints),
          "The target is not fixed pointwise")
    check(all(projection[u] == projection[v] or
              host.has_edge(projection[u], projection[v])
              for u, v in host.edges),
          "Projection fails a host-edge morphism check")

    iso = nx.algorithms.isomorphism.GraphMatcher(
        nx.complement(source), nx.complement(host)
    )
    check(iso.is_isomorphic(), "The independent P4 is not the saved host")
    f = iso.mapping  # independent source vertex -> saved host vertex
    finv = {v: k for k, v in f.items()}
    transported = {x: finv[projection[f[x]]] for x in source}
    check(all(transported[finv[t]] == finv[t] for t in endpoints),
          "Transported target not fixed")
    check(all(transported[u] == transported[v] or
              source.has_edge(transported[u], transported[v])
              for u, v in source.edges),
          "Transported map fails on a source edge")
    print("CERTIFIED_ORDER10_V13 prior=2788 removed=[10510367] remaining=2787")
    print("CERTIFIED_RETRACTION P4(10510367) -> O12 |V|=64 |E|=1844")
    print("INDEPENDENT_INTERMEDIATE_SIZES", orders)


if __name__ == "__main__":
    verify()
