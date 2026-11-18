"""Build a certified K-divergent target catalog from historical census verdicts.

Unlike conjectural/divergence-by-growth candidates, every input is a
historically saved DIVERGENT verdict on a connected graph of order 6..9,
or one of the six independently replayed historical divergent nine-core
entries. Conjectured snub-disphenoid divergence is NEVER included.

Completely pare each source, retain its original index/verdict provenance,
and deduplicate isomorphic primitive roots. Completely pare K(root) and
K^2(root), again deduplicating isomorphic targets. Every such target is
certified K-divergent under the established dominated-fold and K-iterate
transfer theorems.

Screen candidate graph retracts of two frozen 37- and 40-vertex third
pared clique iterates using safe necessary combinatorial bounds and
exact reduced mod-2 homology in dimensions 0..5. Report a shortlist:
this phase does NOT claim any positive retraction or global absence.

The saved census records are read-only, and all record generation and
full deterministic verification occur in separately bounded subprocesses.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
from itertools import islice
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile

import networkx as nx
from pycliques.dominated import completely_pared_graph
from pycombtop.bounded_betti import bounded_reduced_betti_mod2

from graph_sources import EXPECTED_COUNTS, connected_graphs
import core9_third_retractions_v2 as previous

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research/historical_divergent_target_library_v1"
BASE = ROOT / "runs/baseline-through8-bound30"
NINE = ROOT / "runs/order9/initial"
NINE_CROSSREF = ROOT / "reports/order10_core9_crossref_v1/matches.tsv"
HOSTS = (6914104, 6962151)
SCHEMA = 1
MAX_ITERATE = 2
MAX_CLIQUES_PER_ITERATE = 160
MAX_TARGET_ORDER = 40
MAX_FACES = 180_000
MAX_HOMOLOGY_DEGREE = 5
WORKER_SECONDS = 480
MEMORY_MIB = 3072
HISTORICAL_DIVERGENT_COUNTS = {6: 1, 7: 9, 8: 222, 9: 9864}
EXTRA_NINE_CLASSES = 6
TOP_PER_HOST = 40


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encoded(graph: nx.Graph) -> str:
    return nx.to_graph6_bytes(nx.convert_node_labels_to_integers(
        graph, ordering="sorted"), header=False).decode("ascii").strip()


def decode(text: str) -> nx.Graph:
    return nx.from_graph6_bytes(text.encode("ascii"))


def normalize(graph: nx.Graph) -> nx.Graph:
    return nx.convert_node_labels_to_integers(graph, ordering="sorted")


def core(graph: nx.Graph) -> nx.Graph:
    result = normalize(completely_pared_graph(graph))
    if any(
        set(result[v]) | {v} <= set(result[u]) | {u}
        for v in result for u in result if u != v and result.has_edge(u,v)
    ):
        raise ValueError("Source has not been completely pared")
    return result


def raw_k(graph: nx.Graph) -> tuple[nx.Graph | None, int]:
    facets = sorted(
        tuple(sorted(f)) for f in islice(
            nx.find_cliques(graph), MAX_CLIQUES_PER_ITERATE + 1
        )
    )
    if len(facets) > MAX_CLIQUES_PER_ITERATE:
        return None, len(facets)
    facets_as_sets = tuple(map(set, facets))
    result = nx.Graph()
    result.add_nodes_from(range(len(facets)))
    result.add_edges_from(
        (i,j) for i in range(len(facets))
        for j in range(i+1,len(facets))
        if facets_as_sets[i] & facets_as_sets[j]
    )
    return result, len(facets)


def verdict_files(n: int) -> list[Path]:
    folder = (
        BASE / f"order{n}" / "chunks"
        if n <= 8 else NINE / "order9" / "chunks"
    )
    files = sorted(folder.glob("*.tsv.gz"))
    if not files:
        raise ValueError(f"Historical verdict chunks are missing for order {n}")
    return files


def saved_divergent_verdicts() -> dict[int, dict[int, str]]:
    """Only historically certified DIVERGENT; all indices must be accounted for."""
    expected = {
        int(row["order"]): row for row in json.loads(
            (BASE / "summary.json").read_text()
        )["orders"]
    }
    nine = json.loads((NINE / "summary.json").read_text())["orders"][0]
    expected[9] = nine
    result = {}
    for n in range(6,10):
        counts = Counter()
        next_index = 0
        positives = {}
        for filename in verdict_files(n):
            with gzip.open(filename, "rt", encoding="utf-8") as file:
                for line in file:
                    if not line.strip() or line.startswith("#"):
                        continue
                    index, status, reason = line.rstrip("\n").split("\t", 2)
                    i = int(index)
                    if i != next_index:
                        raise ValueError(f"Historical index missing or reordered in {filename}")
                    next_index += 1
                    counts[status] += 1
                    if status == "DIVERGENT":
                        if not reason.strip():
                            raise ValueError("Positive source lacks original reason")
                        positives[i] = reason
                    elif status not in {"CONVERGENT", "INDETERMINATE"}:
                        raise ValueError(f"Unsupported historical verdict {status}")
        if next_index != EXPECTED_COUNTS[n]:
            raise ValueError(f"Historical order-{n} source incomplete")
        if (
            len(positives) != HISTORICAL_DIVERGENT_COUNTS[n]
            or counts["DIVERGENT"] != expected[n]["divergent"]
            or counts["CONVERGENT"] != expected[n]["convergent"]
            or counts["INDETERMINATE"] != expected[n]["indeterminate"]
        ):
            raise ValueError(f"Stored verdict counts differ at order {n}: {counts}")
        result[n] = positives
    return result


def extra_nine_proofs() -> dict[int, dict]:
    """Six independently certified historical core divergences.

    The nine-vertex original index and graph6 are frozen by the core9
    crossreference. These positive results are not inferred from the
    snub disphenoid or from an unbounded iteration limit.
    """
    with NINE_CROSSREF.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    positives = {}
    for row in rows:
        if row["historical_verdict"] != "DIVERGENT":
            continue
        if not row["first_positive_stage"] or row["first_positive_stage"] == "-":
            raise ValueError("Unproven historical nine-core classification")
        i = int(row["order9_index"])
        if i in positives:
            raise ValueError("Duplicate historical positive core index")
        positives[i] = {
            "graph6": row["order9_graph6"],
            "core_graph6": row["core_graph6"],
            "reason": row["positive_rule"] + ": " + row["positive_reason"],
            "stage": row["first_positive_stage"],
        }
    if len(positives) != EXTRA_NINE_CLASSES:
        raise ValueError("Unexpected later historical divergent core count")
    return positives


class IsoIndex:
    """Exact graph-isomorphism deduplication with a WL-hash prefilter."""
    def __init__(self):
        self.graphs: list[nx.Graph] = []
        self.buckets: dict[tuple[int,int,str],list[int]] = defaultdict(list)

    def add(self, graph: nx.Graph) -> tuple[int, bool]:
        graph = normalize(graph)
        key = (
            len(graph), graph.number_of_edges(),
            nx.weisfeiler_lehman_graph_hash(graph),
        )
        for i in self.buckets[key]:
            if nx.is_isomorphic(graph, self.graphs[i]):
                return i, False
        i = len(self.graphs)
        self.graphs.append(graph)
        self.buckets[key].append(i)
        return i, True


def generate() -> dict:
    """Reconstruct ONLY verified divergent sources and their small K iterates."""
    verdicts = saved_divergent_verdicts()
    extras = extra_nine_proofs()
    for i,x in extras.items():
        if i in verdicts[9] and not verdicts[9][i]:
            raise ValueError("Contradictory historical nine-core proof")
    root_index = IsoIndex()
    roots: list[dict] = []
    seen_extra = set()
    selected_counts = Counter()
    for n in range(6,10):
        indices = set(verdicts[n])
        if n == 9:
            indices.update(extras)
        for index, graph in enumerate(connected_graphs(n)):
            if index not in indices:
                continue
            selected_counts[n] += 1
            g6 = encoded(graph)
            label = "initial_divergent"
            reason = verdicts[n].get(index)
            if n == 9 and index in extras:
                if g6 != extras[index]["graph6"]:
                    raise ValueError(f"Saved historical positive graph6 differs: {index}")
                seen_extra.add(index)
                if reason is None:
                    label = "historical_extra_certified"
                    reason = extras[index]["reason"]
            if reason is None:
                raise AssertionError("A selected graph has no positive proof")
            root = core(graph)
            cid, created = root_index.add(root)
            if created:
                roots.append({
                    "id": cid, "pared_graph6": encoded(root),
                    "pared_order": len(root),
                    "pared_edges": root.number_of_edges(),
                    "first_original": {
                        "order": n, "index": index, "graph6": g6,
                        "verdict_origin": label, "positive_reason": reason,
                    },
                    "member_counts_by_order": {},
                    "example_originals": [],
                })
            record = roots[cid]
            key = str(n)
            record["member_counts_by_order"][key] = record["member_counts_by_order"].get(key,0)+1
            if len(record["example_originals"]) < 4:
                record["example_originals"].append({
                    "order":n, "index":index, "graph6":g6, "origin":label,
                })
    if set(seen_extra) != set(extras):
        raise ValueError("A certified nine-core source was not traversed")
    for n, count in HISTORICAL_DIVERGENT_COUNTS.items():
        if selected_counts[n] != count + (
            sum(i not in verdicts[9] for i in extras) if n==9 else 0
        ):
            raise ValueError(f"Missing or miscounted certified sources order {n}")
    # All roots and K-iterates inherit certified divergence; if a finite
    # bound is exceeded it means the target was NOT generated, not that
    # it is K-convergent.
    target_index = IsoIndex()
    targets: list[dict] = []
    limited = []
    for root in roots:
        g = decode(root["pared_graph6"])
        for level in range(MAX_ITERATE + 1):
            if len(g) > MAX_TARGET_ORDER:
                limited.append({"root_id":root["id"],"level":level,
                                "reason":"TARGET_ORDER_LIMIT","order":len(g)})
                break
            tid, created = target_index.add(g)
            if created:
                targets.append({
                    "id":tid,"graph6":encoded(g),"order":len(g),
                    "edges":g.number_of_edges(),
                    "source_certificates":[],
                })
            targets[tid]["source_certificates"].append({
                "root_id":root["id"],"level":level,
            })
            if level == MAX_ITERATE:
                break
            raw, facets = raw_k(g)
            if raw is None:
                limited.append({
                    "root_id":root["id"],"level":level+1,
                    "reason":"RAW_MAXIMAL_CLIQUE_BOUND","at_least":facets,
                })
                break
            g = core(raw)
    return {
        "schema":SCHEMA, "status":"COMPLETE_WITH_BOUNDED_ITERATES",
        "source_verdict_counts":{str(n):len(verdicts[n]) for n in range(6,10)},
        "historical_extra_count":len(extras),
        "selected_original_counts":{str(n):selected_counts[n] for n in range(6,10)},
        "primitive_root_count":len(roots),
        "unique_iterated_target_count":len(targets),
        "roots":roots,
        "targets":targets,
        "omitted_iterates":limited,
        "limitations":(
            "Only historically proven positive verdicts; target levels 0..2 "
            "completely pared, maximal-clique construction bound 160, "
            "target size limit 40. All omissions are explicit."
        ),
    }


def necessary_induced_bounds(host: nx.Graph, candidate: nx.Graph) -> tuple[bool,str]:
    """Cheap necessary (not sufficient) bounds for induced copies."""
    n,k=len(host),len(candidate)
    if k>n:
        return False,"ORDER"
    if candidate.number_of_edges()>host.number_of_edges():
        return False,"EDGE_COUNT"
    host_degrees=sorted((d for _,d in host.degree()),reverse=True)
    target_degrees=sorted((d for _,d in candidate.degree()),reverse=True)
    if any(target_degrees[i]>host_degrees[i] for i in range(k)):
        return False,"DEGREE_MAJORANT"
    ch=nx.complement(host)
    ct=nx.complement(candidate)
    target_complement=ct.number_of_edges()
    omit=n-k
    degree_sum=sum(sorted((d for _,d in ch.degree()),reverse=True)[:omit])
    if ch.number_of_edges()-degree_sum>target_complement:
        return False,"COMPLEMENT_EDGE_LOWER_BOUND"
    comp_host_degrees=sorted((d for _,d in ch.degree()),reverse=True)
    comp_target_degrees=sorted((d for _,d in ct.degree()),reverse=True)
    if any(comp_target_degrees[i]>comp_host_degrees[i] for i in range(k)):
        return False,"COMPLEMENT_DEGREE_MAJORANT"
    return True,"PASSES_ELEMENTARY_BOUNDS"


def screen(library: dict) -> dict:
    """Sound homology and induced-embedding necessary conditions, not a retraction proof."""
    if library["schema"]!=SCHEMA or library["status"]!="COMPLETE_WITH_BOUNDED_ITERATES":
        raise ValueError("Unexpected catalog")
    output={}
    for core_id in HOSTS:
        host, host_hom = (
            previous.third_iterate(core_id),
            previous.exact_low_betti(previous.third_iterate(core_id)),
        )
        counts=Counter()
        candidates=[]
        for target in library["targets"]:
            tid=target["id"]
            graph=decode(target["graph6"])
            valid,reason=necessary_induced_bounds(host,graph)
            counts[reason]+=1
            if not valid:
                continue
            hom=bounded_reduced_betti_mod2(
                graph,max_degree=MAX_HOMOLOGY_DEGREE,max_faces=MAX_FACES,
            )
            if hom is None:
                counts["HOMOLOGY_INCOMPLETE"]+=1
                entry={"target_id":tid,"order":len(graph),
                       "homology_status":"INCOMPLETE","obstruction":None}
            else:
                failing=[i for i in range(MAX_HOMOLOGY_DEGREE+1)
                         if hom[i]>host_hom[i]]
                if failing:
                    counts["HOMOLOGY_OBSTRUCTED"]+=1
                    continue
                counts["HOMOLOGY_PASSES"]+=1
                entry={"target_id":tid,"order":len(graph),
                       "homology_status":"PASSES_THROUGH_DEGREE_5",
                       "betti":{str(i):hom[i] for i in range(MAX_HOMOLOGY_DEGREE+1)}}
                entry["matched_homology_rank"]=hom[3 if core_id==6914104 else 4]
            entry["original_witnesses"]=target["source_certificates"][:4]
            candidates.append(entry)
        candidates.sort(key=lambda x:(
            x.get("homology_status")=="INCOMPLETE",
            -x.get("matched_homology_rank",0),
            x["order"],x["target_id"],
        ))
        output[str(core_id)]={
            "host_order":len(host),
            "host_graph6":encoded(host),
            "host_exact_mod2_betti_0_5":{
                str(i):host_hom[i] for i in range(MAX_HOMOLOGY_DEGREE+1)
            },
            "filter_counts":dict(sorted(counts.items())),
            "homology_admissible_or_incomplete_count":len(candidates),
            "priority_shortlist":candidates[:TOP_PER_HOST],
            "unlisted_candidate_count":max(0,len(candidates)-TOP_PER_HOST),
            "status":"SCREEN_ONLY_NO_RETRACTION_CLAIMS",
        }
    return {
        "schema":SCHEMA,
        "target_count":library["unique_iterated_target_count"],
        "roots":library["primitive_root_count"],
        "hosts":output,
        "conclusion":"Only necessary induced-embedding and mod-2 homology checks; "
                     "a positive screen is not a retraction, and omitted candidates "
                     "are never claimed K-convergent.",
    }


def manifest() -> dict:
    dependencies=[
        Path(__file__),ROOT/"scripts/graph_sources.py",
        ROOT/"scripts/core9_third_retractions_v2.py",
        ROOT/"scripts/core9_three_target_v1.py",
        ROOT/"scripts/bootstrap_core9_three_target_v1.sh",
        BASE/"summary.json",NINE/"summary.json",NINE_CROSSREF,
        ROOT/"config/pycliques_commit_core9_three_target_v1.txt",
    ]
    dependencies.extend(
        p for n in range(6,10) for p in verdict_files(n)
    )
    return {
        "schema":SCHEMA,"stage":"historical_divergent_target_library_v1",
        "historical_orders":[6,7,8,9],
        "historical_divergent_counts":HISTORICAL_DIVERGENT_COUNTS,
        "certified_extra_nine_cases":EXTRA_NINE_CLASSES,
        "max_pared_clique_iterate":MAX_ITERATE,
        "max_raw_cliques_per_iterate":MAX_CLIQUES_PER_ITERATE,
        "max_target_order":MAX_TARGET_ORDER,
        "homology_max_degree":MAX_HOMOLOGY_DEGREE,
        "homology_max_faces":MAX_FACES,
        "shortlist_entries_per_host":TOP_PER_HOST,
        "source_sha256":{str(p.relative_to(ROOT)):sha(p) for p in dependencies},
        "scope":"certified historical DIVERGENT + independently proven extras only; "
                "no predictions from conjectural or bounded-only verdicts",
    }


def atomic_json(path:Path,payload:dict) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",encoding="utf-8",dir=path.parent,
        prefix=".divergent-target-",suffix=".partial",delete=False,
    ) as f:
        tmp=Path(f.name)
        json.dump(payload,f,sort_keys=True,indent=2)
        f.write("\n")
    try:
        os.replace(tmp,path)
    finally:
        tmp.unlink(missing_ok=True)


def limit_resources():
    maximum=MEMORY_MIB*1024**2
    resource.setrlimit(resource.RLIMIT_AS,(maximum,maximum))


def bounded(action:str,path:Path) -> None:
    args=[sys.executable,str(Path(__file__)),action,"--output",str(path)]
    try:
        result=subprocess.run(
            args,timeout=WORKER_SECONDS,capture_output=True,
            text=True,preexec_fn=limit_resources,
        )
    except subprocess.TimeoutExpired as e:
        raise TimeoutError("Historical catalog worker/replay exceeded time cap") from e
    if result.returncode:
        raise RuntimeError(f"Historical catalog {action} failed:\n{result.stderr[-5000:]}")


def verify_payload(path:Path) -> None:
    saved=json.loads(path.read_text())
    expected=generate()
    if saved!=expected:
        raise ValueError("Saved historical source verdict, deduplication or iterate differs")


def verify_screen(path:Path,library:Path) -> None:
    saved=json.loads(path.read_text())
    catalog=json.loads(library.read_text())
    if saved!=screen(catalog):
        raise ValueError("Saved homology/induced screening differs from independent replay")


def run(destination:Path) -> None:
    metadata=manifest()
    destination.mkdir(parents=True,exist_ok=True)
    m=destination/"manifest.json"
    if m.exists():
        if json.loads(m.read_text())!=metadata:
            raise ValueError("Immutable historical catalog provenance differs")
    else:
        if any(destination.iterdir()):
            raise ValueError("Cannot append into directory without matching manifest")
        atomic_json(m,metadata)
    catalog=destination/"certified_targets.json"
    screened=destination/"homology_screen.json"
    if not catalog.exists():
        with tempfile.TemporaryDirectory() as temp:
            result=Path(temp)/"result.json"
            bounded("worker-catalog",result)
            bounded("check-catalog",result)
            atomic_json(catalog,json.loads(result.read_text()))
    else:
        bounded("check-catalog",catalog)
    if not screened.exists():
        with tempfile.TemporaryDirectory() as temp:
            result=Path(temp)/"result.json"
            # Independent bounded worker recomputes the saved catalog by
            # provenance on validation; it never trusts a bare graph6 list.
            subprocess_args=[sys.executable,str(Path(__file__)),
                             "worker-screen","--output",str(result),
                             "--catalog",str(catalog)]
            try:
                subprocess.run(
                    subprocess_args,timeout=WORKER_SECONDS,
                    check=True,preexec_fn=limit_resources,
                )
            except subprocess.TimeoutExpired as e:
                raise TimeoutError("Screening did not complete") from e
            atomic_json(screened,json.loads(result.read_text()))
    bounded("check-catalog",catalog)
    args=[sys.executable,str(Path(__file__)),"check-screen",
          "--output",str(screened),"--catalog",str(catalog)]
    subprocess.run(args,timeout=WORKER_SECONDS,check=True,
                   preexec_fn=limit_resources)
    print("Historical certified target catalog and homology screen verified")


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=("plan","run","worker-catalog","check-catalog",
                                    "worker-screen","check-screen","report"))
    p.add_argument("--output",type=Path)
    p.add_argument("--catalog",type=Path)
    a=p.parse_args()
    if a.action=="plan":
        print(json.dumps(manifest(),indent=2,sort_keys=True))
        return
    if a.action in ("worker-catalog","check-catalog","worker-screen","check-screen"):
        if a.output is None:
            p.error("Worker/check require --output")
        if a.action=="worker-catalog":
            atomic_json(a.output,generate())
        elif a.action=="check-catalog":
            verify_payload(a.output)
        elif a.action=="worker-screen":
            if a.catalog is None:
                p.error("worker-screen requires --catalog")
            atomic_json(a.output,screen(json.loads(a.catalog.read_text())))
        else:
            if a.catalog is None:
                p.error("check-screen requires --catalog")
            verify_screen(a.output,a.catalog)
        return
    directory=a.output or OUTPUT
    if a.action=="run":
        run(directory)
    else:
        print(json.dumps({
            "catalog":json.loads((directory/"certified_targets.json").read_text())["unique_iterated_target_count"],
            "screen":json.loads((directory/"homology_screen.json").read_text()),
        },indent=2,sort_keys=True))


if __name__=="__main__":
    main()
