"""Positive-only O3-O8 retract screen in pared K2-K4 of unclassified stiff McKay-10 cores."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import networkx as nx

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"indeterminate_order_10_v10.txt"
BLOB="35acbd4efbe6fd6816ff0b4455d1e"
sys.path.insert(0,str(ROOT/"research/order10_third_iterate_oct_sweep_v1"))
from sweep import Search,clique_graph,verify_positive

def cases():
    raw=SOURCE.read_bytes()
    sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    if sha!=BLOB:raise ValueError("Changed version-ten index")
    lines=[line.split() for line in raw.decode().splitlines()
           if line and not line.startswith("#")]
    if any(len(f)!=6 for f in lines):raise ValueError("Bad index row")
    data=[(int(f[0]),f[2]) for f in lines if f[1]=="10" and f[3:]==["-","-","-"]]
    if len(data)!=1043 or len({i for i,_ in data})!=1043:
        raise ValueError("Expected 1043 original McKay indices")
    return data

def pare(G):
    H=G.copy();folds=[]
    while True:
        N={u:set(H[u])|{u} for u in H}
        pair=next(((u,v) for u in sorted(H) for v in sorted(H)
                   if u!=v and N[u]<=N[v]),None)
        if pair is None:break
        folds.append(list(pair));H.remove_node(pair[0])
    labels=sorted(H)
    return nx.convert_node_labels_to_integers(H,ordering="sorted"),folds,labels

def run_one(idx,g6,seconds,cap):
    G=nx.from_graph6_bytes(g6.encode("ascii"))
    if len(G)!=10 or not nx.is_connected(G):
        raise ValueError("Bad ten-vertex connected source")
    stages=[];bounded=False;proof=None
    for depth in range(5):
        raw=[len(G),G.number_of_edges()]
        H,folds,labels=pare(G)
        if depth==0 and folds:raise ValueError("Original is not stiff")
        stages.append({"level":depth,"raw":raw,"pared":[len(H),H.number_of_edges()],
                       "folds":folds,"retained":labels})
        if depth>=2:
            for d in (8,7,6,5,4,3):
                if 2*d>len(H):continue
                search=Search(H,d,max_patterns=120000,seconds=seconds)
                out=search.run();bounded|=search.limit_hit
                if out is not None:
                    verify_positive(H,[tuple(p) for p in out["opposite_pairs"]],out["projection"])
                    proof={"mckay_index":idx,"graph6":g6,"level":depth,"dimension":d,
                           "stages":stages,"opposite_pairs":out["opposite_pairs"],
                           "projection":out["projection"]}
                    break
            if proof:break
        if depth==4 or len(H)>cap:break
        try:G=clique_graph(H,max_facets=cap,max_seconds=8.)
        except (OverflowError,TimeoutError):break
    return proof,bounded,stages[-1]["level"]==4

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--batch",type=int,required=True)
    p.add_argument("--batches",type=int,default=8)
    p.add_argument("--seconds",type=float,default=.55)
    p.add_argument("--max-facets",type=int,default=140)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.batches<1 or not 0<=a.batch<a.batches or a.seconds<=0:
        p.error("Invalid batch or time limit")
    chosen=cases()[a.batch::a.batches];positives=[]
    count={"batch":a.batch,"batches":a.batches,"total":len(chosen),
           "examined":0,"positive":0,"bounded":0,"K4_screened":0,"errors":0}
    for idx,g6 in chosen:
        count["examined"]+=1
        try:
            proof,limit,k4=run_one(idx,g6,a.seconds,a.max_facets)
            count["bounded"]+=bool(limit)
            count["K4_screened"]+=bool(k4)
            if proof:
                positives.append(proof);count["positive"]+=1
                print("PROOF_JSON "+json.dumps(proof,separators=(",",":"),sort_keys=True),
                      flush=True)
        except Exception as ex:
            count["errors"]+=1
            print("ERROR_JSON "+json.dumps({"index":idx,"error":repr(ex)}),flush=True)
        if count["examined"]%20==0:
            print("PROGRESS_JSON "+json.dumps(count,sort_keys=True),flush=True)
    if count["examined"]!=len(chosen):raise ValueError("Missed index")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps({"summary":count,"proofs":positives},indent=2)+"\n")
    print("SUMMARY_JSON "+json.dumps(count,sort_keys=True),flush=True)
    if count["errors"]:raise SystemExit("Unexplained graph errors")

if __name__=="__main__":main()
