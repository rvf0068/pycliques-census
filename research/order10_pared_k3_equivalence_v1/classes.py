"""Exact isomorphism classes of completely pared K^3 for unresolved stiff McKay-10 graphs.

No use of Betti numbers. Exact source index and every witness is preserved.
No K-behavior verdict is changed: this only groups equivalent K-iterates.
"""
from __future__ import annotations
from collections import defaultdict
import argparse
import hashlib
import json
from pathlib import Path
import networkx as nx

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"indeterminate_order_10_v10.txt"
SOURCE_BLOB="35acbd4efbe6fd6816ff0b5c749b8b20b4455d1e"

def cases():
    raw=SOURCE.read_bytes()
    if hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()!=SOURCE_BLOB:
        raise ValueError("Frozen v10 McKay source changed")
    rows=[s.split() for s in raw.decode().splitlines() if s and not s.startswith("#")]
    data=[(int(f[0]),f[2]) for f in rows if len(f)==6 and f[1]=="10"
          and f[3:]==["-","-","-"]]
    if len(data)!=1043 or len({i for i,_ in data})!=1043:
        raise ValueError("Expected 1043 distinct unclassified McKay ten-cores")
    return data

def fold(G):
    H=G.copy();witness=[]
    while True:
        N={v:set(H[v])|{v} for v in H}
        found=next(((u,v) for u in sorted(H) for v in sorted(H)
                    if u!=v and N[u]<=N[v]),None)
        if found is None:break
        witness.append(list(found));H.remove_node(found[0])
    retained=sorted(H)
    return nx.convert_node_labels_to_integers(H,ordering="sorted"),witness,retained

def clique_graph(G,max_cliques=250):
    facets=[]
    for q in nx.find_cliques(G):
        facets.append(sum(1<<v for v in q))
        if len(facets)>max_cliques:return None
    facets.sort()
    H=nx.Graph();H.add_nodes_from(range(len(facets)))
    H.add_edges_from((i,j) for i in range(len(facets)) for j in range(i+1,len(facets))
                     if facets[i]&facets[j])
    return H

def reconstruct(g6):
    G=nx.from_graph6_bytes(g6.encode("ascii"))
    if len(G)!=10 or not nx.is_connected(G):raise ValueError("Bad source graph")
    stages=[]
    for lev in range(4):
        before=[len(G),G.number_of_edges()]
        G,folds,retained=fold(G)
        if lev==0 and folds:raise ValueError("Source core was not stiff")
        stages.append({"level":lev,"raw":before,
                       "pared":[len(G),G.number_of_edges()],
                       "folds":folds,"retained":retained})
        if lev<3:
            G=clique_graph(G)
            if G is None:return None,stages
    return G,stages

def key(G):
    return (len(G),G.number_of_edges(),
            tuple(sorted(d for _,d in G.degree())),
            nx.weisfeiler_lehman_graph_hash(G,iterations=5))

def complete_map(G,H):
    matcher=nx.algorithms.isomorphism.GraphMatcher(G,H)
    mapping=next(matcher.isomorphisms_iter(),None)
    if mapping is None:return None
    images=[int(mapping[v]) for v in range(len(G))]
    if (sorted(images)!=list(range(len(H))) or
        any(G.has_edge(u,v)!=H.has_edge(images[u],images[v])
            for u in G for v in G if u<v)):
        raise ValueError("Invalid explicit graph isomorphism")
    return images

def build():
    groups=defaultdict(list);skips=[]
    count=0
    for idx,g6 in cases():
        G,stages=reconstruct(g6)
        if G is None:
            skips.append({"index":idx,"graph6":g6,"stages":stages,
                          "reason":"clique graph exceeds 250 vertices"})
            continue
        bucket=groups[key(G)]
        winner=None
        for entry in bucket:
            mapping=complete_map(G,entry["graph"])
            if mapping is not None:
                winner=(entry,mapping);break
        if winner is None:
            entry={"representative":idx,"graph":G,"members":[]}
            bucket.append(entry)
            winner=(entry,list(range(len(G))))
        entry,mapping=winner
        entry["members"].append({"index":idx,"graph6":g6,"stages":stages,
                                 "to_representative":mapping})
        count+=1
        if count%100==0:print("PROGRESS",count,flush=True)
    classes=[]
    for group in groups.values():
        for entry in group:
            classes.append({"representative":entry["representative"],
                            "members":entry["members"]})
    classes.sort(key=lambda c:c["representative"])
    skips.sort(key=lambda s:s["index"])
    summary={"sources":1043,"processed":count,"skipped":len(skips),
             "isomorphism_classes":len(classes),
             "nontrivial_classes":sum(len(c["members"])>1 for c in classes),
             "members_in_nontrivial":sum(len(c["members"]) for c in classes if len(c["members"])>1)}
    if count+len(skips)!=1043:raise ValueError("Incomplete source partition")
    family=next((c for c in classes if c["representative"]==7002338),None)
    if family is None or len(family["members"])!=33:
        raise AssertionError("Expected 33-member McKay family not recovered")
    return {"schema":1,"source":"indeterminate_order_10_v10.txt",
            "summary":summary,"classes":classes,"skipped":skips}

def verify(data):
    expected=build()
    if data!=expected:raise ValueError("Saved isomorphism classes differ from complete replay")
    # Independently reconstruct all positive maps against full graphs,
    # rather than trusting just a WL hash or the search result.
    for c in data["classes"]:
        if len(c["members"])<2:continue
        G,_=reconstruct(c["members"][0]["graph6"])
        for member in c["members"]:
            H,stages=reconstruct(member["graph6"])
            pi=member["to_representative"]
            if (G is None or H is None or len(pi)!=len(H)
                or sorted(pi)!=list(range(len(G)))
                or any(H.has_edge(u,v)!=G.has_edge(pi[u],pi[v])
                       for u in H for v in H if u<v)):
                raise ValueError("Tampered explicit isomorphism")
            if stages!=member["stages"]:
                raise ValueError("Fold provenance mismatch")
    return data["summary"]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path)
    p.add_argument("--verify",type=Path)
    args=p.parse_args()
    if args.verify:
        data=json.loads(args.verify.read_text())
        print("VERIFIED_JSON "+json.dumps(verify(data),sort_keys=True))
    else:
        d=build()
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n")
        print("SUMMARY_JSON "+json.dumps(d["summary"],sort_keys=True))
        for c in d["classes"]:
            if len(c["members"])>=3:
                print("CLASS_JSON "+json.dumps({
                    "representative":c["representative"],
                    "members":[m["index"] for m in c["members"]]
                },sort_keys=True),flush=True)

if __name__=="__main__":main()
