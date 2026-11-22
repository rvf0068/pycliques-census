// Independent C++17 bitset proof replay of induced snub retraction obstructions.
// Input: n m followed by all u v edges, with vertices numbered 0,...,n-1.
// Enumerates every induced copy of graph6 GQyuzw and does not use time limits.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <unordered_set>
#include <vector>

using Mask = std::uint64_t;
constexpr int PATTERN_SIZE = 8;
// Neighborhoods in the snub graph6 GQyuzw, indexed by pattern vertex.
constexpr std::array<Mask, 8> PATTERN = {116, 216, 177, 226, 199, 205, 59, 62};
int n = 0, m = 0;
Mask full = 0;
std::vector<Mask> adj;
std::array<int, 8> order = {}, assigned = {};
std::unordered_set<Mask> targets;
std::uint64_t embedded = 0, blocked = 0, possible = 0;

void verify_target(Mask target) {
    if (!targets.insert(target).second) return;
    for (int v = 0; v < n; ++v) {
        if ((target >> v) & 1ULL) continue;
        // Any fixed-target retraction image r(v) must be adjacent or
        // equal to every target neighbor of v. Check all eight images.
        const Mask target_neighbors = adj[v] & target;
        bool has_image = false;
        Mask choices = target;
        while (choices) {
            const int t = __builtin_ctzll(choices);
            choices &= choices - 1;
            if ((target_neighbors & ~(adj[t] | (1ULL << t))) == 0) {
                has_image = true;
                break;
            }
        }
        if (!has_image) {
            ++blocked;
            return;
        }
    }
    ++possible;
}

void enumerate(int depth, Mask used) {
    if (depth == PATTERN_SIZE) {
        ++embedded;
        verify_target(used);
        return;
    }
    const int v = order[depth];
    Mask available = full & ~used;
    // Enforce both the edges and the nonedges of the snub graph.
    for (int j = 0; j < depth; ++j) {
        const int earlier = order[j];
        const int image = assigned[earlier];
        if ((PATTERN[v] >> earlier) & 1ULL) {
            available &= adj[image];
        } else {
            available &= full & ~adj[image];
        }
    }
    while (available) {
        const int image = __builtin_ctzll(available);
        available &= available - 1;
        assigned[v] = image;
        enumerate(depth + 1, used | (1ULL << image));
    }
}

int main(int argc, char** argv) {
    try {
        if (argc != 2) {
            throw std::runtime_error("usage: snub_native graph.edgelist");
        }
        std::ifstream in(argv[1]);
        if (!(in >> n >> m) || n < 8 || n > 63 || m < 0 || m > n * (n - 1) / 2) {
            throw std::runtime_error("invalid graph header");
        }
        full = (1ULL << n) - 1;
        adj.assign(n, 0);
        for (int i = 0; i < m; ++i) {
            int u, v;
            if (!(in >> u >> v) || u < 0 || v < 0 || u >= n || v >= n || u == v) {
                throw std::runtime_error("invalid input edge");
            }
            if ((adj[u] >> v) & 1ULL) {
                throw std::runtime_error("duplicate input edge");
            }
            adj[u] |= 1ULL << v;
            adj[v] |= 1ULL << u;
        }
        for (int i = 0; i < 8; ++i) order[i] = i;
        std::stable_sort(order.begin(), order.end(), [](int a, int b) {
            return __builtin_popcountll(PATTERN[a])
                > __builtin_popcountll(PATTERN[b]);
        });
        enumerate(0, 0);
        std::cout << "EXHAUSTED " << targets.size() << ' ' << embedded
                  << ' ' << blocked << ' ' << possible << '\n';
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "snub_native verifier: " << e.what() << '\n';
        return 2;
    }
}
