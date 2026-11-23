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
        if (argc != 4)
            throw std::runtime_error(
                "Usage: enumerate.cpp host.edgelist size time_limit_seconds"
            );
        target_size = std::stoi(argv[2]);
        time_limit = std::stod(argv[3]);
        if (time_limit <= 0.0)
            throw std::runtime_error("invalid time limit");

        std::FILE* file = std::fopen(argv[1], "r");
        if (!file) throw std::runtime_error("missing graph file");
        int edge_count = 0;
        if (std::fscanf(file, "%d %d", &n, &edge_count) != 2
                || n < 1 || n > 63 || edge_count < 0
                || target_size < 1 || target_size > n)
            throw std::runtime_error("invalid graph header");

        const Bits all = (Bits(1) << n) - 1;
        full = all;
        Bits graph_open[64]{};
        for (int i = 0; i < edge_count; ++i) {
            int u, v;
            if (std::fscanf(file, "%d %d", &u, &v) != 2
                    || u < 0 || v < 0 || u >= n || v >= n || u == v)
                throw std::runtime_error("invalid source edge");
            graph_open[u] |= Bits(1) << v;
            graph_open[v] |= Bits(1) << u;
        }
        std::fclose(file);

        for (int x = 0; x < n; ++x)
            complement_open[x] =
                all & ~(graph_open[x] | (Bits(1) << x));

        begin = std::chrono::steady_clock::now();
        search(0, 0);
        std::cout
            << "EXHAUSTIVE size=" << target_size
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
