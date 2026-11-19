"""New K-divergence certificate by a retraction K(G) -> O3.

Exhaustively screen the 2424 still unresolved stiff-core classes (the
8-, 9-, and 10-vertex pared class representatives in v5), including
all induced O3 vertex sets in the FIRST clique graph. A positive weak
graph retraction (edges map to adjacent or equal vertices) proves
K-divergence by Neumann-Lara's Retraction Theorem and the octahedron
divergence theorem. No negative result establishes convergence.

Old v5 list and its proof scripts are byte-pinned and unchanged.
New deterministic certificate and v6 list are versioned separately.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from collections import Counter
from itertools import combinations
from pathlib import Path
import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
CLASSES = "reports/order10_core_index_v1/classes.tsv"
OLD = "indeterminate_order_10_v5.txt"
PRIOR_SCRIPT = "scripts/direct_divergent_ninecore_retracts_v1.py"
DIR = "research/order10_k1_octahedron_retract_v1"
NEW = "indeterminate_order_10_v6.txt"
CLASSES_SHA = "5a9b08c548aa5671f9c1403cf1badd0044211f7ef75129c83980462efa6f16eb"
OLD_BLOB = "52d71a90a60b0f714bdbb4bc2aef4fdb857f49e2"
PRIOR_BLOB = "5abeb042f66668b59858ca28aeae14447abb5349"
EXPECTED_ID = 11634099
EXPECTED_G6 = "IEjer^{lo"
REFERENCE_SECTION = [1,15,5,10,9,14]
REFERENCE_PROJECTION = [5,0,2,1,5,2,0,3,0,4,3,3,4,3,5,1,5]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def first_clique_graph(g6: str) -> tuple[nx.Graph,list[int]]:
    original = nx.from_graph6_bytes(g6.encode("ascii"))
    facets = sorted(sum(1 << v for v in q) for q in nx.find_cliques(original))
    h = nx.Graph()
    h.add_nodes_from(range(len(facets)))
    h.add_edges_from((i,j) for i,j in combinations(h,2)
                     if facets[i] & facets[j])
    return h,facets


def O3() -> nx.Graph:
    h = nx.Graph()
    h.add_nodes_from(range(6))
    h.add_edges_from((i,j) for i,j in combinations(range(6),2)
                     if i//2 != j//2)
    return h


def verify_map(h: nx.Graph, section: list[int], projection: list[int]) -> None:
    target = O3()
    if (len(projection) != len(h) or len(section) != 6
        or len(set(section)) != 6 or not set(section) <= set(h)
        or any(t not in target for t in projection)
        or any(projection[section[i]] != i for i in target)):
        raise ValueError("Invalid retraction or section map")
    for i,j in combinations(target,2):
        if h.has_edge(section[i],section[j]) != target.has_edge(i,j):
            raise ValueError("The six section vertices do not induce O3")
    for u,v in h.edges():
        a,b = projection[u],projection[v]
        if a != b and not target.has_edge(a,b):
            raise ValueError("Graph morphism maps an edge to a forbidden nonedge")


def sections(h: nx.Graph):
    """All induced O3 six-sets, as triples of complement matching edges."""
    non = {v:set(h)-{v}-set(h[v]) for v in h}
    edges = [(a,b) for a,b in combinations(h,2) if b in non[a]]
    for p,(a,b) in enumerate(edges):
        for q in range(p+1,len(edges)):
            c,d = edges[q]
            if len({a,b,c,d}) < 4 or any(
                v in non[u] for u in (a,b) for v in (c,d)
            ):
                continue
            for r in range(q+1,len(edges)):
                e,f = edges[r]
                if len({a,b,c,d,e,f}) != 6 or any(
                    v in non[u] for u in (a,b,c,d) for v in (e,f)
                ):
                    continue
                yield [a,b,c,d,e,f]


def search_projection(h: nx.Graph, section: list[int]) -> list[int]|None:
    model=O3()
    p=[-1]*len(h)
    for i,v in enumerate(section):
        p[v]=i
    rest=[]
    for v in h:
        if p[v]>=0:
            continue
        domain=[i for i in range(6)
                if all(not h.has_edge(v,section[j]) or i==j
                       or model.has_edge(i,j) for j in range(6))]
        if not domain:
            return None
        rest.append((v,domain))
    rest.sort(key=lambda x:(len(x[1]),x[0]))
    def visit(k):
        if k==len(rest):
            return True
        v,domain=rest[k]
        for t in domain:
            if any(h.has_edge(v,u) and t!=p[u] and not model.has_edge(t,p[u])
                   for u,_ in rest[:k]):
                continue
            p[v]=t
            if visit(k+1):
                return True
            p[v]=-1
        return False
    if visit(0):
        verify_map(h,section,p)
        return p
    return None


def old_data(root:Path=ROOT):
    if sha((root/CLASSES).read_bytes()) != CLASSES_SHA:
        raise ValueError("Frozen core-class source changed")
    if blob((root/OLD).read_bytes()) != OLD_BLOB:
        raise ValueError("Frozen v5 unresolved source changed")
    if blob((root/PRIOR_SCRIPT).read_bytes()) != PRIOR_BLOB:
        raise ValueError("Historical v5 divergent proof script changed")
    lines=(root/OLD).read_text().splitlines()
    active={}
    for line in lines:
        if line and not line.startswith("#"):
            fields=line.split()
            if len(fields)!=6 or int(fields[0]) in active:
                raise ValueError("Malformed or duplicated v5 original")
            active[int(fields[0])]=fields
    if len(active)!=8224 or EXPECTED_ID not in active:
        raise ValueError("Wrong v5 original population")
    rows=[]
    population=set()
    for line in (root/CLASSES).read_text().splitlines()[1:]:
        idx,order,g6,n,_conj,members=line.split("\t")
        ids=[int(x) for x in members.split(",")]
        if len(ids)!=int(n) or len(set(ids))!=len(ids):
            raise ValueError("Corrupt class-index membership")
        if population.intersection(ids):
            raise ValueError("Overlapping source classes")
        population.update(ids)
        representative=int(idx)
        if representative not in active:
            if any(i in active for i in ids):
                raise ValueError("Partially resolved core class")
            continue
        if set(ids)-set(active) or active[representative][1:3]!=[order,g6]:
            raise ValueError("Active class is not identical to original index")
        rows.append((representative,int(order),g6,ids))
    if len(rows)!=2424 or dict(Counter(r[1] for r in rows))!={8:1,9:29,10:2394}:
        raise ValueError("Unexpected 2424-core unresolved population")
    if {x for _,_,_,members in rows for x in members} != set(active):
        raise ValueError("Core-class partition does not cover active v5 originals")
    return rows,lines


def audit(root:Path=ROOT):
    rows,_=old_data(root)
    positives=[]
    candidate_hosts=0
    copies=0
    for index,order,g6,members in rows:
        h,facets=first_clique_graph(g6)
        has_candidate=False
        witness=None
        for S in sections(h):
            copies+=1
            has_candidate=True
            if witness is None:
                p=search_projection(h,S)
                if p is not None:
                    witness=(S,p)
        if has_candidate:
            candidate_hosts+=1
        if witness is not None:
            positives.append({
                "index":index,"graph6":g6,"core_order":order,
                "original_members":members,"K_order":len(h),
                "K_edges":h.number_of_edges(),
                "maximal_clique_masks":facets,
                "section":witness[0],"projection":witness[1],
                "proof":"K(G) retracts to O3, hence G is K-divergent",
            })
    if candidate_hosts!=40 or copies!=3972:
        raise ValueError(f"Wrong complete induced-O3 screen: {candidate_hosts}, {copies}")
    if ([r["index"] for r in positives]!=[EXPECTED_ID]
        or positives[0]["original_members"]!=[EXPECTED_ID]
        or positives[0]["graph6"]!=EXPECTED_G6):
        raise ValueError("Exhaustive audit did not produce precisely the expected positive")
    ref_h,_=first_clique_graph(EXPECTED_G6)
    if (len(ref_h),ref_h.number_of_edges())!=(17,87):
        raise ValueError("Reference 17-vertex K(G) fingerprint changed")
    verify_map(ref_h,REFERENCE_SECTION,REFERENCE_PROJECTION)
    return positives,{"active_classes":2424,"candidate_hosts":candidate_hosts,
                      "all_induced_sections":copies,"positive_classes":1,
                      "v5_originals":8224,"v6_originals":8223}


def generate(root:Path=ROOT):
    positives,stats=audit(root)
    _,lines=old_data(root)
    remaining=[line for line in lines if line and not line.startswith("#")
               and int(line.split()[0])!=EXPECTED_ID]
    if len(remaining)!=8223:
        raise ValueError("New unresolved index has incorrect population")
    v6="\n".join([
        "# Order-10 unresolved after v5 and one K(G)-to-O3 divergent retraction",
        "# Remaining=8223 previous_v5=8224 additional_certified_divergent=1",
        "# Previous source lists and all historical proofs preserved.",
        "# Format: original_index pared_order pared_graph6 certificate_rule certificate_target_status certificate_target_label",
        *remaining,""
    ]).encode()
    cert={"schema":1,"target":"O3 = complement of 3 disjoint K2",
          "theorem":"Neumann-Lara Retraction Theorem",
          "no_convergence_inferred_from_negative_cases":True,
          "screen_statistics":stats,
          "positive_certificates":positives,
          "independent_reference":{"section":REFERENCE_SECTION,
                                   "projection":REFERENCE_PROJECTION}}
    explanation="\n".join([
        "# A new divergent stiff ten-vertex graph from its first clique graph",
        "",
        "Index **11634099**, graph6 IEjer^{lo, is K-divergent.",
        "Its first clique graph has 17 vertices and 87 edges.",
        "The vertices [1,15,5,10,9,14] induce O3, with antipodal",
        "pairs (1,15), (5,10), (9,14). The explicit projection is",
        "",
        "    [5,0,2,1,5,2,0,3,0,4,3,3,4,3,5,1,5]",
        "",
        "Every edge maps to an edge or equality and the projection",
        "fixes the six-vertex induced copy. Hence O3 is a retract of",
        "K(G). Since O3 is K-divergent (Neumann-Lara), the Retraction",
        "Theorem proves that K(G), hence G, is K-divergent.",
        "",
        "The exhaustive first-iterate screen covers all 2424 active",
        "core classes (1 eight-core, 29 nine-cores, 2394 ten-cores).",
        "40 first clique graphs contain an induced O3, producing",
        "3972 induced target vertex sets; exhaustive retraction tests",
        "produce precisely this one positive. All other finite-family",
        "negatives are inconclusive for K-convergence.",
        "",
        "Versioned v6 excludes just original index 11634099:",
        "8224 - 1 = **8223** indeterminate ten-vertex graphs.",
        "All prior census files, verdicts, and certificates are unchanged.",
        "",
    ]).encode()
    base={
        DIR+"/certificates.json":(json.dumps(cert,indent=2,sort_keys=True)+"\n").encode(),
        DIR+"/summary.md":explanation,
        NEW:v6,
    }
    manifest={"schema":1,"input_sha256":{CLASSES:sha((root/CLASSES).read_bytes()),
                                          OLD:sha((root/OLD).read_bytes())},
              "output_sha256":{path:sha(data) for path,data in sorted(base.items())}}
    base[DIR+"/manifest.json"]=(json.dumps(manifest,indent=2,sort_keys=True)+"\n").encode()
    return base


def verify(root:Path=ROOT):
    for rel,raw in generate(root).items():
        if not (root/rel).is_file() or (root/rel).read_bytes()!=raw:
            raise ValueError(f"Missing or altered v6 proof artifact: {rel}")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=["plan","build","verify"])
    args=parser.parse_args()
    payload=generate()
    if args.mode=="build":
        for rel,raw in payload.items():
            path=ROOT/rel
            path.parent.mkdir(parents=True,exist_ok=True)
            if path.exists() and path.read_bytes()!=raw:
                raise ValueError(f"Refusing to overwrite different certificate: {rel}")
            path.write_bytes(raw)
    if args.mode!="plan":
        verify()
    print("Certified K(G) -> O3 divergence at index 11634099; unresolved 8224 -> 8223")


if __name__=="__main__":
    main()
