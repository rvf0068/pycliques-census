// Independent C++17 cross-check of all eight-element external double covers.
// Input: n m followed by undirected edges u v; target graph is NOT supplied.
// Full integer DFS: selecting v satisfies its own row; an unselected x
// requires at least two selected complement-neighbors.
// The upper bound on remaining total deficit uses the largest per-variable
// possible contributions, IGNORING overlap, hence is a safe pruning rule.
// A time limit NEVER produces a negative certificate.
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <functional>
#include <iostream>
#include <stdexcept>
#include <unordered_set>

using Bits = std::uint64_t;
static int n, target_size;
static Bits nonedges[64], edges[64], full;
static std::uint64_t calls = 0, forced = 0, pruned_bound = 0;
static std::uint64_t solutions = 0, degree_candidates = 0;
static std::unordered_set<Bits> distinct;
static std::chrono::steady_clock::time_point began;
static double time_limit;

static inline int count(Bits b) { return __builtin_popcountll(b); }
static inline int low(Bits b) { return __builtin_ctzll(b); }
static double seconds() {
    return std::chrono::duration<double>(
        std::chrono::steady_clock::now() - began).count();
}

// Return false only when the whole subtree has been exhausted.
// Unknown / invalid configuration throws and leaves the proof incomplete.
static void exhaustive(Bits chosen, Bits excluded) {
    if ((++calls & 65535ULL) == 0 && seconds() > time_limit)
        throw std::runtime_error("resource limit: inconclusive");
    if (count(chosen) > target_size) return;
    Bits undecided = 0, needed = 0, needed_two = 0;
    int total_deficit = 0;
    while (true) {
        undecided = full & ~(chosen | excluded);
        needed = needed_two = 0;
        total_deficit = 0;
        bool changed = false;
        for (int x = 0; x < n; ++x) {
            const Bits bit = Bits(1) << x;
            if (chosen & bit) continue;
            const int already = count(nonedges[x] & chosen);
            if (already >= 2) continue;
            const int demand = 2 - already;
            const Bits possible = nonedges[x] & undecided;
            const int capacity = count(possible);
            if (excluded & bit) {
                if (capacity < demand) return;
                if (capacity == demand) {
                    chosen |= possible;
                    forced += capacity;
                    changed = true;
                    break;
                }
            } else if (capacity < demand) {
                chosen |= bit;
                ++forced;
                changed = true;
                break;
            }
            needed |= bit;
            total_deficit += demand;
            if (demand == 2) needed_two |= bit;
        }
        if (count(chosen) > target_size) return;
        if (!changed) break;
    }

    if (needed == 0) {
        if (count(chosen) != target_size)
            throw std::runtime_error(
                "smaller cover found: certify minimum size first");
        if (!distinct.insert(chosen).second) return;
        ++solutions;
        int four = 0, five = 0;
        for (int x = 0; x < n; ++x) {
            if (!(chosen & (Bits(1) << x))) continue;
            int d = count(edges[x] & chosen);
            four += (d == 4);
            five += (d == 5);
        }
        if (four == 4 && five == 4) ++degree_candidates;
        return;
    }

    int slots = target_size - count(chosen);
    if (slots <= 0 || !undecided) return;

    int gains[64];
    int size = 0, best_priority = -1, pivot = -1;
    Bits pending = undecided;
    while (pending) {
        int v = low(pending);
        pending &= pending - 1;
        const int gain = count(
            (nonedges[v] | (Bits(1) << v)) & needed)
            + int(bool(needed_two & (Bits(1) << v)));
        gains[size++] = gain;
        int priority = gain * 128 + count(nonedges[v] & needed);
        if (priority > best_priority) {
            best_priority = priority;
            pivot = v;
        }
    }
    std::sort(gains, gains + size, std::greater<int>());
    int optimistic = 0;
    for (int j = 0; j < slots && j < size; ++j)
        optimistic += gains[j];
    if (optimistic < total_deficit) {
        ++pruned_bound;
        return;
    }

    if (pivot < 0) throw std::runtime_error("unbranched search state");
    Bits bit = Bits(1) << pivot;
    exhaustive(chosen | bit, excluded);
    exhaustive(chosen, excluded | bit);
}

int main(int argc, char** argv) {
    try {
        if (argc != 4) throw std::runtime_error(
            "Usage: enumerate.cpp graph.edgelist size time_limit_seconds");
        target_size = std::stoi(argv[2]);
        time_limit = std::stod(argv[3]);
        if (time_limit <= 0) throw std::runtime_error("invalid timeout");
        std::FILE* f = std::fopen(argv[1], "r");
        if (!f) throw std::runtime_error("missing host graph");
        int m = -1;
        if (std::fscanf(f, "%d %d", &n, &m) != 2
                || n < 1 || n > 63 || m < 0
                || target_size < 1 || target_size > n)
            throw std::runtime_error("invalid graph header");
        full = (Bits(1) << n) - 1;
        for (int i = 0; i < m; ++i) {
            int a, b;
            if (std::fscanf(f, "%d %d", &a, &b) != 2
                    || a < 0 || b < 0 || a >= n || b >= n || a == b)
                throw std::runtime_error("invalid graph edge");
            edges[a] |= Bits(1) << b;
            edges[b] |= Bits(1) << a;
        }
        std::fclose(f);
        for (int v = 0; v < n; ++v)
            nonedges[v] = full & ~(edges[v] | (Bits(1) << v));
        began = std::chrono::steady_clock::now();
        exhaustive(0, 0);
        std::cout << "EXHAUSTED size=" << target_size
                  << " coverings=" << solutions
                  << " degree_4_5_candidates=" << degree_candidates
                  << " states=" << calls
                  << " forced=" << forced
                  << " integer_bound_prunes=" << pruned_bound
                  << "\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "INCONCLUSIVE: " << e.what() << "\n";
        return 2;
    }
}
