// Independent native reconstruction of the third completely pared clique
// iterate from an ORIGINAL order-nine graph6 string. No Python edge-list
// input, NetworkX graph, or precomputed P3 adjacency is used.
//
// Small intermediate graphs are represented by a dynamic adjacency matrix:
// the unpared clique graph may have more than 63 vertices. Only the final
// verified P3 host is converted to 64-bit masks for exhaustive enumeration.
#ifndef ORDER9_P3_NATIVE_RECONSTRUCTION_HPP
#define ORDER9_P3_NATIVE_RECONSTRUCTION_HPP

#include <algorithm>
#include <cstdint>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

namespace native_p3 {

using Bits = std::uint64_t;

struct Graph {
    std::vector<std::vector<unsigned char>> edge;
    explicit Graph(int n = 0)
        : edge(n, std::vector<unsigned char>(n, 0)) {}
    int size() const { return static_cast<int>(edge.size()); }
    void add(int a, int b) {
        if (a != b) edge[a][b] = edge[b][a] = 1;
    }
    int edge_count() const {
        int count = 0;
        for (int b = 0; b < size(); ++b)
            for (int a = 0; a < b; ++a)
                count += edge[a][b];
        return count;
    }
};

inline Graph decode_graph6(const std::string& source) {
    if (source.empty()) throw std::runtime_error("empty original graph6");
    const int n = static_cast<unsigned char>(source[0]) - 63;
    if (n != 9 || source.size() != 7)
        throw std::runtime_error("expected one nine-vertex graph6");
    for (unsigned char c : source)
        if (c < 63 || c > 126)
            throw std::runtime_error("invalid graph6 character");
    Graph graph(n);
    int bit = 0;
    for (int j = 1; j < n; ++j) {
        for (int i = 0; i < j; ++i, ++bit) {
            const unsigned char encoded = source[1 + bit / 6] - 63;
            if ((encoded >> (5 - bit % 6)) & 1)
                graph.add(i, j);
        }
    }
    return graph;
}

inline bool is_dominated(const Graph& graph, int vertex, int other) {
    // Closed neighborhoods: N[vertex] is contained in N[other].
    for (int z = 0; z < graph.size(); ++z) {
        if ((z == vertex || graph.edge[vertex][z])
            && !(z == other || graph.edge[other][z]))
            return false;
    }
    return true;
}

inline Graph pare(Graph graph) {
    // Remove the first dominated vertex and repeat to a stiff core.
    // Reindexing preserves the remaining order; it need not agree with
    // NetworkX's particular labeling, since all counts are isomorphism
    // invariant and every result is independently checked below.
    while (true) {
        int victim = -1;
        for (int v = 0; v < graph.size() && victim == -1; ++v)
            for (int w = 0; w < graph.size(); ++w)
                if (v != w && is_dominated(graph, v, w)) {
                    victim = v;
                    break;
                }
        if (victim == -1) return graph;
        graph.edge.erase(graph.edge.begin() + victim);
        for (auto& row : graph.edge) row.erase(row.begin() + victim);
    }
}

inline void bron_kerbosch(
    const Graph& graph,
    std::vector<int>& current,
    std::vector<int> possible,
    std::vector<int> excluded,
    std::vector<std::vector<int>>& maximal
) {
    if (possible.empty() && excluded.empty()) {
        maximal.push_back(current);
        return;
    }
    // Pivot minimizing the number of recursive subproblems.
    int pivot = -1, best = -1;
    for (int u : possible) {
        int score = 0;
        for (int v : possible) score += graph.edge[u][v];
        if (score > best) { best = score; pivot = u; }
    }
    for (int u : excluded) {
        int score = 0;
        for (int v : possible) score += graph.edge[u][v];
        if (score > best) { best = score; pivot = u; }
    }
    const auto choices = possible;
    for (int v : choices) {
        if (pivot >= 0 && graph.edge[pivot][v]) continue;
        current.push_back(v);
        std::vector<int> next_possible, next_excluded;
        for (int u : possible)
            if (graph.edge[v][u]) next_possible.push_back(u);
        for (int u : excluded)
            if (graph.edge[v][u]) next_excluded.push_back(u);
        bron_kerbosch(
            graph, current, std::move(next_possible),
            std::move(next_excluded), maximal
        );
        current.pop_back();
        possible.erase(std::find(possible.begin(), possible.end(), v));
        excluded.push_back(v);
    }
}

inline Graph clique_graph(const Graph& source) {
    std::vector<int> current;
    std::vector<int> possible(source.size());
    std::iota(possible.begin(), possible.end(), 0);
    std::vector<std::vector<int>> maximal;
    bron_kerbosch(source, current, possible, {}, maximal);
    Graph result(static_cast<int>(maximal.size()));
    // A clique-intersection graph: two maximal cliques are adjacent
    // exactly when they intersect. Explicit comparisons are small here.
    for (int q = 0; q < static_cast<int>(maximal.size()); ++q) {
        for (int p = 0; p < q; ++p) {
            bool intersects = false;
            for (int v : maximal[q])
                if (std::find(maximal[p].begin(), maximal[p].end(), v)
                    != maximal[p].end()) {
                    intersects = true;
                    break;
                }
            if (intersects) result.add(q, p);
        }
    }
    return result;
}

inline int triangle_count(const Graph& graph) {
    int count = 0;
    for (int a = 0; a < graph.size(); ++a)
        for (int b = a + 1; b < graph.size(); ++b)
            if (graph.edge[a][b])
                for (int c = b + 1; c < graph.size(); ++c)
                    if (graph.edge[a][c] && graph.edge[b][c])
                        ++count;
    return count;
}

struct Case {
    int index;
    const char* graph6;
    int orders[4];
    int edges[4];
    int triangles;
};

inline Graph build(int index, const std::string& original) {
    constexpr Case cases[] = {
        {249576, "HEhfvzu", {9, 13, 22, 53}, {23, 53, 159, 1044}, 10453},
        {251628, "HEhvVn{", {9, 13, 20, 55}, {23, 54, 137, 1156}, 12507},
        {260040, "HQyvex}", {9, 13, 21, 58}, {23, 53, 151, 1289}, 14776},
    };
    const Case* expected = nullptr;
    for (const Case& candidate : cases)
        if (candidate.index == index) expected = &candidate;
    if (!expected || original != expected->graph6)
        throw std::runtime_error("original McKay identity/graph6 mismatch");
    Graph graph = pare(decode_graph6(original));
    for (int level = 0; level < 4; ++level) {
        if (graph.size() != expected->orders[level]
            || graph.edge_count() != expected->edges[level])
            throw std::runtime_error(
                "independent native P" + std::to_string(level)
                + " stage vertex/edge mismatch"
            );
        if (level < 3) graph = pare(clique_graph(graph));
    }
    if (triangle_count(graph) != expected->triangles)
        throw std::runtime_error("independent P3 triangle count mismatch");
    return graph;
}

inline std::vector<Bits> bitmasks(const Graph& graph) {
    if (graph.size() > 63) throw std::runtime_error("P3 is too large");
    std::vector<Bits> masks(graph.size(), 0);
    for (int x = 0; x < graph.size(); ++x)
        for (int y = 0; y < graph.size(); ++y)
            if (graph.edge[x][y]) masks[x] |= Bits(1) << y;
    return masks;
}

}  // namespace native_p3
#endif
