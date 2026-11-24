// Independent C++20 check of all octahedral targets in the original P4.
// Reads ONLY the 70-vertex complement edge list generated from the
// independently pinned Python P4 graph6. It does NOT call Python's
// matching enumerator, target screen, or negative-certificate archive.
//
// If there were a retraction onto an induced O_d, d >= 3, the target
// would be a complement-dominating induced matching. The only forbidden
// images of a source edge are opposite endpoints in that matching.
// Any singleton-domain contradiction proves impossibility.
//
// Complete enumeration ends at dimension eight; if O8 does not occur,
// larger induced octahedra cannot occur either.
#include <array>
#include <bit>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <utility>
#include <vector>

namespace {
constexpr int N = 70;
constexpr int MAX_PAIRS = 600;
constexpr int WORDS = (MAX_PAIRS + 63) / 64;

struct Bits {
    std::array<std::uint64_t, WORDS> words{};
    void set(int v) { words.at(v / 64) |= std::uint64_t{1} << (v % 64); }
    void clear(int v) { words.at(v / 64) &= ~(std::uint64_t{1} << (v % 64)); }
    Bits operator&(Bits const& b) const {
        Bits result;
        for (int i = 0; i < WORDS; ++i)
            result.words[i] = words[i] & b.words[i];
        return result;
    }
    Bits operator|(Bits const& b) const {
        Bits result;
        for (int i = 0; i < WORDS; ++i)
            result.words[i] = words[i] | b.words[i];
        return result;
    }
    bool operator==(Bits const& b) const { return words == b.words; }
};

bool nonedge[N][N] = {};
std::vector<std::pair<int, int>> pairs;
std::vector<Bits> compat;
std::vector<Bits> covered_by_pair;
Bits complete_vertices;
std::array<long long, 9> induced{};
std::array<long long, 9> dominating{};
std::array<std::array<long long, 4>, 9> screens{};

int obstruction(int d, const std::array<int, 9>& chosen) {
    std::array<int, N> location;
    location.fill(-1);
    std::array<int, 16> ends{};
    for (int i = 0; i < d; ++i) {
        auto [a, b] = pairs[chosen[i]];
        ends[2*i] = a;
        ends[2*i+1] = b;
        location[a] = 2*i;
        location[b] = 2*i+1;
    }

    std::array<std::uint16_t, N> dom{};
    for (int x = 0; x < N; ++x) {
        if (location[x] >= 0) {
            dom[x] = static_cast<std::uint16_t>(1u << location[x]);
        } else {
            unsigned int options = 0;
            for (int i = 0; i < d; ++i) {
                if (nonedge[x][ends[2*i+1]])
                    options |= 1u << (2*i);
                if (nonedge[x][ends[2*i]])
                    options |= 1u << (2*i+1);
            }
            if (options == 0)
                return 0;  // no target image compatible with fixed endpoints
            dom[x] = static_cast<std::uint16_t>(options);
        }
    }
    // Separate first-round direct antipodal forced-image conflicts.
    for (int x = 0; x < N; ++x) {
        if (std::popcount(static_cast<unsigned>(dom[x])) != 1)
            continue;
        const int antipode = 1 << (std::countr_zero(static_cast<unsigned>(dom[x])) ^ 1);
        for (int y = x+1; y < N; ++y) {
            if (!nonedge[x][y] && dom[y] == antipode)
                return 1;
        }
    }
    // Complete singleton-domain arc consistency: a forced image u
    // forbids only its antipode on every neighbor in the host graph.
    std::array<int, N> queue{};
    int head = 0, tail = 0;
    for (int x = 0; x < N; ++x)
        if (std::popcount(static_cast<unsigned>(dom[x])) == 1)
            queue[tail++] = x;
    while (head < tail) {
        const int x = queue[head++];
        const unsigned int forbidden =
            1u << (std::countr_zero(static_cast<unsigned>(dom[x])) ^ 1);
        for (int y = 0; y < N; ++y) {
            if (x == y || nonedge[x][y] || !(dom[y] & forbidden))
                continue;
            dom[y] &= static_cast<std::uint16_t>(~forbidden);
            if (!dom[y])
                return 2;
            if (std::popcount(static_cast<unsigned>(dom[y])) == 1) {
                if (tail >= N)
                    throw std::logic_error("A vertex became singleton twice");
                queue[tail++] = y;
            }
        }
    }
    return 3; // inconclusive: do NOT claim that a retraction is impossible
}

void search(int depth, Bits available, Bits covered, std::array<int, 9>& chosen) {
    ++induced[depth];
    if (depth >= 3 && covered == complete_vertices) {
        ++dominating[depth];
        const int result = obstruction(depth, chosen);
        ++screens[depth][result];
        if (result == 3)
            throw std::logic_error("Unrefuted induced octahedron: no negative proof");
    }
    if (depth == 8)
        return;
    for (int word = 0; word < WORDS; ++word) {
        std::uint64_t candidates = available.words[word];
        while (candidates) {
            const int bit = std::countr_zero(candidates);
            const int i = word * 64 + bit;
            candidates &= candidates - 1;
            available.clear(i);
            chosen[depth] = i;
            search(depth+1, available & compat[i],
                   covered | covered_by_pair[i], chosen);
        }
    }
}

void run() {
    int n = 0, m = 0;
    if (!(std::cin >> n >> m) || n != N || m != 585)
        throw std::runtime_error("Wrong complement graph order/edge count");
    int previous_a = -1, previous_b = -1;
    for (int i = 0; i < m; ++i) {
        int a = -1, b = -1;
        if (!(std::cin >> a >> b) || a < 0 || a >= b || b >= N ||
            nonedge[a][b] ||
            (previous_a >= a && (previous_a > a || previous_b >= b)))
            throw std::runtime_error("Complement edge list must be sorted, unique");
        nonedge[a][b] = nonedge[b][a] = true;
        previous_a = a;
        previous_b = b;
    }
    int trailing = 0;
    if (std::cin >> trailing)
        throw std::runtime_error("Additional unexpected graph data");
    for (int a = 0; a < N; ++a)
        for (int b = a + 1; b < N; ++b)
            if (nonedge[a][b])
                pairs.emplace_back(a, b);
    if (pairs.size() != 585)
        throw std::runtime_error("Missing or repeated complement edges");
    compat.resize(pairs.size());
    covered_by_pair.resize(pairs.size());
    for (int i = 0; i < N; ++i)
        complete_vertices.set(i);
    for (std::size_t i = 0; i < pairs.size(); ++i) {
        auto [a, b] = pairs[i];
        for (int x = 0; x < N; ++x)
            if (x == a || x == b || nonedge[x][a] || nonedge[x][b])
                covered_by_pair[i].set(x);
    }
    for (std::size_t i = 0; i < pairs.size(); ++i) {
        auto [a, b] = pairs[i];
        for (std::size_t j = i + 1; j < pairs.size(); ++j) {
            auto [c, d] = pairs[j];
            if (!nonedge[a][c] && !nonedge[a][d] &&
                !nonedge[b][c] && !nonedge[b][d])
                compat[i].set(static_cast<int>(j));
        }
    }
    Bits all;
    for (int i = 0; i < 585; ++i) all.set(i);
    std::array<int, 9> chosen{};
    search(0, all, Bits{}, chosen);

    const std::array<long long, 9> expected_induced{
        1, 585, 41878, 387428, 472762, 14304, 491, 2, 0
    };
    const std::array<long long, 9> expected_dominating{
        0, 0, 0, 22, 205024, 144, 0, 0, 0
    };
    const std::array<long long, 9> expected_direct{
        0, 0, 0, 22, 166199, 140, 0, 0, 0
    };
    const std::array<long long, 9> expected_propagated{
        0, 0, 0, 0, 38825, 4, 0, 0, 0
    };
    if (induced != expected_induced ||
        dominating != expected_dominating)
        throw std::logic_error("Enumerated octahedron dimensions disagree");
    for (int d = 3; d <= 8; ++d) {
        if (screens[d][0] != 0 ||
            screens[d][1] != expected_direct[d] ||
            screens[d][2] != expected_propagated[d] ||
            screens[d][3] != 0)
            throw std::logic_error("Inconclusive target or failed propagation counts");
        std::cout << "O" << d << ": induced=" << induced[d]
                  << " dominating=" << dominating[d]
                  << " direct=" << screens[d][1]
                  << " propagated=" << screens[d][2]
                  << " unrefuted=" << screens[d][3] << '\n';
    }
    std::cout << "PASS: independent C++20 total enumeration:"
                 " no O_d retraction from P4(10820813), d >= 3.\n";
}
} // namespace

int main() {
    try {
        run();
        return 0;
    } catch (std::exception const& exc) {
        std::cerr << "FAIL: " << exc.what() << '\n';
        return 1;
    }
}
