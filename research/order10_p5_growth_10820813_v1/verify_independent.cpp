// Independent C++20 certification of the fifth clique iterate of
// McKay 10820813 from a SHA-pinned complement of its 70-vertex P4.
//
// Completely independent of the Python fifth-stage maximal clique,
// fold, and octahedral witness implementations.
//
// Input: n m followed by sorted edges of the P4 complement (n=70,m=585).
// Output: fixed-width little-endian adjacency arrays of raw K(P4)
// (1977 rows) and its stiff 1896-vertex complete paring.
// SHA-256 of these binary arrays is pinned in certificates.json.
//
// No conclusion about divergence or higher iterates is asserted.
#include <algorithm>
#include <array>
#include <bit>
#include <bitset>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {
constexpr int P4_N = 70;
using Facet = std::bitset<P4_N>;
std::array<Facet, P4_N> source_adj;
std::vector<Facet> facets;

void bk(Facet r, Facet p, Facet x) {
    if (p.none() && x.none()) {
        facets.push_back(r);
        if (facets.size() > 10000)
            throw std::runtime_error("P4 fifth-stage facet limit");
        return;
    }
    Facet choices = p | x;
    int pivot = -1;
    std::size_t max_neighbors = 0;
    for (int u = 0; u < P4_N; ++u)
        if (choices.test(u)) {
            std::size_t current = (p & source_adj[u]).count();
            if (pivot < 0 || current > max_neighbors) {
                pivot = u;
                max_neighbors = current;
            }
        }
    Facet branches = pivot < 0 ? p : p & ~source_adj[pivot];
    for (int u = 0; u < P4_N; ++u)
        if (branches.test(u)) {
            Facet child = r;
            child.set(u);
            bk(child, p & source_adj[u], x & source_adj[u]);
            p.reset(u);
            x.set(u);
        }
}

using BitRows = std::vector<std::vector<std::uint64_t>>;

void put(BitRows &matrix, int u, int v) {
    matrix[u][v / 64] |= (std::uint64_t{1} << (v % 64));
}
bool has(BitRows const& matrix, int u, int v) {
    return (matrix[u][v / 64] >> (v % 64)) & std::uint64_t{1};
}
std::size_t degree(BitRows const& matrix, int u) {
    std::size_t result = 0;
    for (auto word : matrix[u])
        result += std::popcount(word);
    return result;
}
std::size_t num_edges(BitRows const& matrix) {
    std::size_t total = 0;
    for (int u = 0; u < static_cast<int>(matrix.size()); ++u)
        total += degree(matrix,u);
    if (total % 2 != 0)
        throw std::logic_error("Nonintegral graph edge count");
    return total / 2;
}
bool subset(std::vector<std::uint64_t> const& small,
            std::vector<std::uint64_t> const& big) {
    if (small.size() != big.size())
        throw std::logic_error("Mismatched bitset widths");
    for (std::size_t i=0; i<small.size(); ++i)
        if (small[i] & ~big[i])
            return false;
    return true;
}
std::vector<std::uint64_t> make_mask(int n) {
    std::vector<std::uint64_t> masks((n + 63) / 64, ~std::uint64_t{0});
    if (n % 64 != 0)
        masks.back() = (std::uint64_t{1} << (n % 64)) - 1;
    return masks;
}
void write_rows(std::string const& path, BitRows const& matrix) {
    const int n = static_cast<int>(matrix.size());
    std::ofstream out(path, std::ios::binary);
    if (!out)
        throw std::runtime_error("Cannot open output adjacency bytes: " + path);
    for (int u=0; u<n; ++u)
        for (int offset=0; offset<(n+7)/8; ++offset) {
            unsigned char next = 0;
            for (int bit=0; bit<8; ++bit) {
                int v = 8*offset+bit;
                if (v<n && has(matrix,u,v))
                    next |= static_cast<unsigned char>(1u << bit);
            }
            out.put(static_cast<char>(next));
        }
    if (!out)
        throw std::runtime_error("Failed to write canonical adjacency bytes");
}

void read_source(std::string const& path) {
    std::ifstream stream(path);
    int n = -1, m = -1;
    if (!(stream >> n >> m) || n != 70 || m != 585)
        throw std::runtime_error("Wrong frozen P4 complement dimensions");
    std::array<Facet,P4_N> nonadj;
    int previous_u=-1, previous_v=-1;
    for (int i=0; i<m; ++i) {
        int u=-1,v=-1;
        if (!(stream >> u >> v) || u<0 || v>=n || u>=v ||
            (previous_u>u || (previous_u==u && previous_v>=v)) ||
            nonadj[u].test(v))
            throw std::runtime_error("Unsorted or invalid complement edge");
        nonadj[u].set(v);
        nonadj[v].set(u);
        previous_u=u;previous_v=v;
    }
    int extra=0;
    if (stream >> extra)
        throw std::runtime_error("Trailing unexpected source data");
    for (int u=0;u<n;++u)
        for (int v=0;v<n;++v)
            if (u!=v && !nonadj[u].test(v))
                source_adj[u].set(v);
}

void check_o20(BitRows const& pared) {
    constexpr std::array<std::pair<int,int>,20> pairs {{
        {784,1374},{817,1401},{1406,451},{449,1014},
        {1400,471},{1016,1042},{763,1463},{1586,401},
        {759,1465},{1464,355},{1871,354},{1763,251},
        {0,1878},{1498,129},{604,1744},{1397,857},
        {425,1232},{1009,415},{518,1071},{564,1544}
    }};
    constexpr int n = 1896;
    std::vector<int> is_target(n,0);
    for (int i=0;i<20;++i) {
        auto [a,b] = pairs[i];
        if (a==b || a<0 || a>=n || b<0 || b>=n ||
            is_target[a] || is_target[b] || has(pared,a,b))
            throw std::logic_error("Not distinct antipodal nonedges");
        is_target[a]=is_target[b]=1;
        for (int j=0;j<i;++j) {
            auto [c,d] = pairs[j];
            if (!has(pared,a,c) || !has(pared,a,d) ||
                !has(pared,b,c) || !has(pared,b,d))
                throw std::logic_error("Not an induced O20: cross adjacency");
        }
    }
    std::vector<int> unique_forced(n,-1);
    int count_forced=0;
    for (int x=0;x<n;++x) {
        if (is_target[x])
            continue;
        int options=0,last=-1;
        for (auto [a,b]:pairs) {
            if (!has(pared,x,a)) {
                ++options;
                last=b;
            }
            if (!has(pared,x,b)) {
                ++options;
                last=a;
            }
        }
        if (options==0)
            throw std::logic_error("O20 does not dominate complement");
        if (options==1) {
            ++count_forced;
            unique_forced[x]=last;
        }
    }
    if (count_forced!=210 || !has(pared,87,458) ||
        unique_forced[87]!=857 || unique_forced[458]!=1397)
        throw std::logic_error("Incorrect forced antipodal retraction conflict");
    std::cout << "PASS: independent O20 induced-target and full"
                 " complement-domination check; 210 outside singleton"
                 " domains; edge 87-458 forced to antipodes 857-1397."
              << std::endl;
}

void run(int argc, char** argv) {
    if (argc!=4)
        throw std::runtime_error("Usage: verifier P4_complement raw_bytes P5_bytes");
    read_source(argv[1]);
    bk(Facet{}, Facet{}.set(), Facet{});
    // Facet{}.set() sets all 70 bits; no graph labels are reused from Python.
    std::sort(facets.begin(),facets.end(),[](Facet const& a,Facet const& b) {
        for (int i=P4_N-1;i>=0;--i)
            if (a.test(i)!=b.test(i))
                return !a.test(i) && b.test(i);
        return false;
    });
    if (facets.size()!=1977 ||
        std::adjacent_find(facets.begin(),facets.end())!=facets.end())
        throw std::logic_error("Independent BK disagrees on 1977 maximal cliques");

    const int n=static_cast<int>(facets.size());
    const int words=(n+63)/64;
    BitRows raw(n,std::vector<std::uint64_t>(words));
    for (int u=0;u<n;++u)
        for (int v=u+1;v<n;++v)
            if ((facets[u] & facets[v]).any()) {
                put(raw,u,v);
                put(raw,v,u);
            }
    if (num_edges(raw)!=1742560)
        throw std::logic_error("Unexpected K(P4) adjacency size");
    write_rows(argv[2], raw);

    auto mask=make_mask(n);
    BitRows complement=raw;
    std::vector<int> cdeg(n);
    for (int u=0;u<n;++u) {
        for (int word=0; word<words;++word)
            complement[u][word]=(~raw[u][word]) & mask[word];
        complement[u][u/64] &= ~(std::uint64_t{1}<<(u%64));
        cdeg[u]=static_cast<int>(degree(complement,u));
    }
    std::vector<int> order(n);
    std::iota(order.begin(),order.end(),0);
    std::sort(order.begin(),order.end(),[&](int u,int v) {
        return std::pair(cdeg[u],u) < std::pair(cdeg[v],v);
    });
    std::vector<int> dominator(n,-1);
    int removed=0;
    for (int u=0;u<n;++u) {
        for (int v:order) {
            if (cdeg[v]>cdeg[u] ||
                (cdeg[v]==cdeg[u] && v>=u))
                break;
            if (subset(complement[v],complement[u])) {
                dominator[u]=v;
                ++removed;
                break;
            }
        }
    }
    if (removed!=81)
        throw std::logic_error("Expected exactly 81 dominated K5 vertices");
    std::vector<int> kept;
    for (int u=0;u<n;++u)
        if (dominator[u]<0)
            kept.push_back(u);
    if (kept.size()!=1896)
        throw std::logic_error("Unexpected stiff P5 order");

    for (int u=0;u<n;++u) if (dominator[u]>=0) {
        int v=u;
        while (dominator[v]>=0)
            v=dominator[v];
        if (!subset(complement[v],complement[u]))
            throw std::logic_error("Deleted vertex lacks surviving dominator");
    }

    std::vector<std::uint64_t> alive(words,0);
    for (int u:kept)
        alive[u/64] |= std::uint64_t{1}<<(u%64);
    for (int u:kept)
        for (int v:kept)
            if (u!=v) {
                bool contained=true;
                for (int word=0;word<words;++word)
                    if ((complement[v][word]&alive[word]) &
                        ~(complement[u][word]&alive[word])) {
                        contained=false;break;
                    }
                if (contained)
                    throw std::logic_error("P5 not stiff: remaining domination");
            }

    const int pared_n=static_cast<int>(kept.size());
    BitRows pared(pared_n,
        std::vector<std::uint64_t>((pared_n+63)/64));
    for (int i=0;i<pared_n;++i)
        for (int j=i+1;j<pared_n;++j)
            if (has(raw,kept[i],kept[j])) {
                put(pared,i,j);
                put(pared,j,i);
            }
    if (num_edges(pared)!=1601683)
        throw std::logic_error("Wrong number of fifth pared edges");
    write_rows(argv[3],pared);
    check_o20(pared);
    std::cout << "PASS: independent C++20 Bron--Kerbosch K(P4) = "
              << n << " vertices / " << num_edges(raw) << " edges;"
              << " 81 simultaneous valid domination folds;"
              << " completely pared, stiff P5 = "
              << pared_n << " vertices / "
              << num_edges(pared) << " edges." << std::endl;
}
}

int main(int argc,char** argv) {
    try {
        run(argc,argv);
        return 0;
    } catch (std::exception const& err) {
        std::cerr << "FAIL: " << err.what() << '\n';
        return 1;
    }
}
