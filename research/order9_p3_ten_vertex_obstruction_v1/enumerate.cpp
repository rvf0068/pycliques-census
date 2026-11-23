// Independent C++17 finite proof for all exact-size open 2-dominating
// sets in the complement of an input simple graph X, plus a necessary
// unary fixed-target retraction test.
//
// Every row x requires at least two selected nonneighbors in X,
// INCLUDING selected target vertices. This is necessary for an
// induced target T with Delta(T) <= |T|-3 to be a retract of X.
// 0. A well-formed finite input must have n <= 63.
// 1. DPLL forces all still-available neighbors of a deficient row
//    when their number equals its remaining deficit.
// 2. Optimistic total-demand bound safely prunes impossible subtrees.
// 3. Every binary branch (selected/excluded) is visited.
// 4. When a smaller open double cover appears, enumerate ALL its
//    exact-size supersets rather than discarding them.
// 5. Each candidate S is checked against ALL complement rows, then
//    for every outside x, require a y in S with
//    N_H(y) intersect S subset N_H(x) intersect S.
// 6. A timeout is INCONCLUSIVE and returns nonzero; only an exhaustive
//    successful run produces an exact zero-survivor certificate.
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <iostream>
#include <stdexcept>
#include <unordered_set>
#include <vector>

#include "native_p3.hpp"

using Bits = std::uint64_t;
static int n = 0, target_size = 0;
static Bits complement_open[64]{}, full = 0;
static std::uint64_t nodes = 0, solutions = 0, unary_survivors = 0;
static std::uint64_t forced = 0, bound_prunes = 0;
static std::unordered_set<Bits> distinct;
static std::chrono::steady_clock::time_point begin;
static double time_limit = 0.0;

static inline int count(Bits value) { return __builtin_popcountll(value); }
static inline int low(Bits value) { return __builtin_ctzll(value); }

static double elapsed() {
    return std::chrono::duration<double>(
        std::chrono::steady_clock::now() - begin
    ).count();
}

static void verify_candidate(Bits selected) {
    if (count(selected) != target_size)
        throw std::runtime_error("wrong exact target cardinality");
    for (int x = 0; x < n; ++x) {
        if (count(complement_open[x] & selected) < 2)
            throw std::runtime_error("invalid open double-cover candidate");
    }
    if (!distinct.insert(selected).second) return;
    ++solutions;

    bool possible = true;
    for (int x = 0; x < n; ++x) {
        if (selected & (Bits(1) << x)) continue;
        const Bits nonneighbors_x = complement_open[x] & selected;
        Bits options = selected;
        bool image_exists = false;
        while (options) {
            const int y = low(options);
            options &= options - 1;
            if (((complement_open[y] & selected) & ~nonneighbors_x) == 0) {
                image_exists = true;
                break;
            }
        }
        if (!image_exists) {
            possible = false;
            break;
        }
    }
    if (possible) {
        ++unary_survivors;
        std::cout << "UNARY_SURVIVOR vertices=";
        for (int v = 0; v < n; ++v)
            if (selected & (Bits(1) << v)) std::cout << v << ',';
        std::cout << '\n';
    }
}

static void enumerate_extensions(Bits selected, Bits undecided, int missing) {
    if (missing == 0) {
        verify_candidate(selected);
        return;
    }
    if (count(undecided) < missing) return;
    while (undecided) {
        const Bits bit = undecided & -undecided;
        undecided -= bit;
        enumerate_extensions(selected | bit, undecided, missing - 1);
    }
}

static void search(Bits selected, Bits excluded) {
    ++nodes;
    if ((nodes & 0x1FFFFULL) == 0 && elapsed() > time_limit)
        throw std::runtime_error("TIME_LIMIT_INCONCLUSIVE");
    if (count(selected) > target_size) return;

    Bits undecided = 0, unmet = 0;
    int total_deficit = 0;
    while (true) {
        undecided = full & ~(selected | excluded);
        unmet = 0;
        total_deficit = 0;
        bool changed = false;
        for (int x = 0; x < n; ++x) {
            const int deficit =
                2 - count(complement_open[x] & selected);
            if (deficit <= 0) continue;
            const Bits available = complement_open[x] & undecided;
            const int capacity = count(available);
            if (capacity < deficit) return;
            if (capacity == deficit) {
                selected |= available;
                forced += capacity;
                changed = true;
                break;
            }
            unmet |= Bits(1) << x;
            total_deficit += deficit;
        }
        if (count(selected) > target_size) return;
        if (!changed) break;
    }
    if (!unmet) {
        enumerate_extensions(
            selected, full & ~(selected | excluded),
            target_size - count(selected)
        );
        return;
    }

    const int available_slots = target_size - count(selected);
    if (available_slots <= 0 || !undecided) return;

    struct Candidate {
        int gain, vertex;
    };
    std::vector<Candidate> candidates;
    Bits choices = undecided;
    while (choices) {
        const int vertex = low(choices);
        choices &= choices - 1;
        const int gain = count(complement_open[vertex] & unmet);
        candidates.push_back({gain, vertex});
    }
    std::sort(
        candidates.begin(), candidates.end(),
        [](const Candidate& a, const Candidate& b) {
            return a.gain > b.gain
                || (a.gain == b.gain && a.vertex < b.vertex);
        }
    );
    int optimistic_gain = 0;
    for (int i = 0; i < available_slots
            && i < static_cast<int>(candidates.size()); ++i)
        optimistic_gain += candidates[i].gain;
    if (optimistic_gain < total_deficit) {
        ++bound_prunes;
        return;
    }
    const Bits pivot = Bits(1) << candidates.front().vertex;
    search(selected | pivot, excluded);
    search(selected, excluded | pivot);
}

int main(int argc, char** argv) {
    try {
        if (argc != 5)
            throw std::runtime_error(
                "Usage: enumerate.cpp McKay_index original_graph6 size time_limit_seconds"
            );
        const int index = std::stoi(argv[1]);
        target_size = std::stoi(argv[3]);
        time_limit = std::stod(argv[4]);
        if (time_limit <= 0.0)
            throw std::runtime_error("invalid time limit");

        // Independently reconstruct every P0-P3 stage in native C++.
        // No graph/edgelist is created by Python for this verification.
        const auto graph = native_p3::build(index, argv[2]);
        const auto graph_open = native_p3::bitmasks(graph);
        n = graph.size();
        if (n < 1 || n > 63 || target_size < 1 || target_size > n)
            throw std::runtime_error("invalid reconstructed P3 dimension");
        full = (Bits(1) << n) - 1;
        for (int x = 0; x < n; ++x)
            complement_open[x] = full & ~(graph_open[x] | (Bits(1) << x));

        begin = std::chrono::steady_clock::now();
        search(0, 0);
        std::cout
            << "EXHAUSTIVE native_P3=" << n << "/" << graph.edge_count()
            << " size=" << target_size
            << " open_double_covers=" << solutions
            << " unary_survivors=" << unary_survivors
            << " search_nodes=" << nodes
            << " forced=" << forced
            << " bound_prunes=" << bound_prunes
            << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "INCONCLUSIVE " << error.what() << '\n';
        return 2;
    }
}
