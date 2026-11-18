"""Discover certified K-divergent retraction targets from historical census.

Read ONLY completed, frozen, *proved DIVERGENT* classifications at orders
6..9, including order-nine positive post-stages. For each original graph H,
construct H, K(H), K^2(H) without paring, then record independent closed-
neighborhood domination folds to a stiff graph S. Each derived S is
K-divergent by the published invariance of clique behavior under folding.

If a host X retracts to any of these original/iterated targets T, X also
retracts to S, since S is an induced retract of T. Thus searching the
stiff representatives is lossless FOR THESE HISTORICAL TARGETS; the search
does not claim to enumerate all K-divergent graphs in general.

Deduplicate stiff graphs by WL-bucket followed by exact isomorphism.
Screen their homology (0..5) against the two frozen third pared iterates
under necessary induced embedding constraints. Do not call an uncomputed
Betti number zero, and never promote absence of targets to convergence.

Worker and verifier are separately time/memory bounded. The historical
census and all previous experiment results remain immutable.
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
import signal
import subprocess
import sys
import tempfile
import time

import networkx as nx
from pycombtop.bounded_betti import bounded_reduced_betti_mod2

from graph_sources import connected_graphs, EXPECTED_COUNTS
from validate import iter_chunks, iter_verdicts
import core9_clique_targets_v1 as prior

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research/order10_historical_divergent_targets_v1"
BASE = ROOT / "runs/baseline-through8-bound30"
NINE = ROOT / "runs/order9"
SCHEMA = 1
HOST_IDS = (6914104, 6962151)
HIST_COUNTS = {6: 1, 7: 9, 8: 222, 9: 9864}
ADDITIONAL_NINE = {"c10": 4, "bound60": 1, "bound70": 3}
LEVELS = 2
MAX_TARGET_ORDER = 40
MAX_FACES = 150000
TIMEOUT_SECONDS = 260
MEMORY_MIB = 2800
ISOMORPHISM_SECONDS = 0.05


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def graph6(graph: nx.Graph) -> str:
    return nx.to_graph6_bytes(
        nx.convert_node_labels_to_integers(graph, ordering="sorted"),
        header=False
    ).decode("ascii").strip()


def graph_from_g6(string: str) -> nx.Graph:
    return nx.from_graph6_bytes(string.encode("ascii"))


def candidate_isomorphic_key(graph: nx.Graph) -> tuple:
    return (len(graph), graph.number_of_edges(),
            nx.weisfeiler_lehman_graph_hash(graph, iterations=5))


def bounded_isomorphic(a: nx.Graph, b: nx.Graph, diagnostics: Counter) -> bool:
    """Never allow one hard Graph Isomorphism case to stall the whole census.

    An unverified comparison is treated as *distinct*, never merged.
    Thus this affects the efficiency of deduplication but cannot
    falsify a mathematical result or lose a candidate.
    """
    if a.number_of_nodes() <= 12:
        return nx.is_isomorphic(a,b)
    if graph6(a) == graph6(b):
        return True
    previous_handler=signal.getsignal(signal.SIGALRM)
    def expired(*_):
        raise TimeoutError("Only the candidate graph isomorphism test exceeded budget")
    signal.signal(signal.SIGALRM,expired)
    signal.setitimer(signal.ITIMER_REAL,ISOMORPHISM_SECONDS)
    try:
        return nx.is_isomorphic(a,b)
    except TimeoutError:
        diagnostics["isomorphism_timeouts"]+=1
        return False
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous_handler)


def stiff_fold(graph: nx.Graph) -> tuple[nx.Graph, list[list[int]]]:
    """Full deterministic dominated-vertex deletion, with explicit witnesses."""
    h = graph.copy()
    steps = []
    while True:
        closed = {v: set(h[v]) | {v} for v in h}
        selected = next(
            ((v,u) for v in sorted(h) for u in sorted(h)
             if v != u and closed[v] <= closed[u]),
            None,
        )
        if selected is None:
            break
        v,u = selected
        if not h.has_edge(v,u):
            raise AssertionError("Closed-neighborhood domination implies adjacency")
        steps.append([int(v),int(u)])
        h.remove_node(v)
    for v in h:
        if any(
            v != u and set(h[v]) | {v} <= set(h[u]) | {u}
            for u in h
        ):
            raise AssertionError("Final graph is not stiff")
    return nx.convert_node_labels_to_integers(h, ordering="sorted"), steps


def raw_clique_graph_bounded(graph: nx.Graph) -> nx.Graph | None:
    """Raw K(G), with maximum number of vertices bounded BEFORE construction."""
    maximal = list(islice(nx.find_cliques(graph), MAX_TARGET_ORDER+1))
    if len(maximal) > MAX_TARGET_ORDER:
        return None
    facets = sorted(tuple(sorted(q)) for q in maximal)
    graph_sets = [set(q) for q in facets]
    h = nx.Graph()
    h.add_nodes_from(range(len(facets)))
    h.add_edges_from(
        (i,j) for i in range(len(facets))
        for j in range(i+1,len(facets))
        if graph_sets[i] & graph_sets[j]
    )
    return h


def staged_proven_positive_indices() -> dict[int, dict]:
    """Only frozen positive records; nothing conjectural or merely limited."""
    evidence = {}
    for stage, expected in ADDITIONAL_NINE.items():
        folder = NINE / stage
        summary = json.loads((folder / "summary.json").read_text())
        manifest = json.loads((folder / "manifest.json").read_text())
        if summary["manifest"] != manifest or manifest.get("stage") != stage:
            raise ValueError(f"Wrong frozen order-nine {stage} provenance")
        positives = []
        for p in sorted((folder / "records").glob("*.json")):
            row = json.loads(p.read_text())
            idx = row.get("index")
            if not isinstance(idx,int) or p.name != f"{idx:08d}.json":
                raise ValueError("Malformed staged index")
            if stage == "c10":
                good = (row.get("status") == "RETRACTION_FOUND"
                        and isinstance(row.get("witness"),dict))
                reason = "verified C10-complement K-retraction"
            else:
                good = row.get("verdict") == "DIVERGENT"
                reason = row.get("reason", "")
            if good:
                if idx in evidence:
                    raise ValueError(f"Duplicate later nine-vertex proof for {idx}")
                if any(word in reason.lower() for word in ("conjectur","conditional")):
                    raise ValueError(f"Conditional divergence falsely used at {idx}")
                evidence[idx] = {
                    "stage":stage, "graph6":row["graph6"],
                    "reason":reason, "record_sha256":sha(p),
                }
                positives.append(idx)
        if len(positives) != expected:
            raise ValueError(f"Unexpected historical positive {stage}: {positives}")
    return evidence


def historic_inputs():
    """Stream all stable original graphs paired with archived verdicts."""
    extras = staged_proven_positive_indices()
    observed = Counter()
    totals = Counter()
    for n in range(6,10):
        directory = (
            BASE / f"order{n}" if n <= 8
            else NINE / "initial" / "order9"
        )
        batch = 500 if n <= 8 else 10000
        verdicts = iter_chunks(directory,n,batch)
        for idx,graph in enumerate(connected_graphs(n)):
            try:
                v_idx,status,reason = next(verdicts)
            except StopIteration as exc:
                raise ValueError(f"Truncated original historical order {n}") from exc
            if v_idx != idx:
                raise ValueError(f"Historical verdict misindexed at n={n},i={idx}")
            totals[n] += 1
            if status == "DIVERGENT":
                observed[n] += 1
                if any(word in reason.lower() for word in ("conjectur","conditional")):
                    raise ValueError("Conditional historical verdict falsely marked divergent")
                yield {
                    "order":n,"index":idx,"graph6":graph6(graph),
                    "stage":"initial","historical_reason":reason
                },graph
            if n == 9 and idx in extras:
                if status != "INDETERMINATE":
                    raise ValueError(f"Later positive was not initially unresolved: {idx}")
                reference = extras[idx]
                if graph6(graph) != reference["graph6"]:
                    raise ValueError(f"Staged positive graph6 differs at {idx}")
                yield {
                    "order":9,"index":idx,"graph6":graph6(graph),
                    "stage":reference["stage"],
                    "historical_reason":reference["reason"],
                    "record_sha256":reference["record_sha256"],
                },graph
        if next(verdicts,None) is not None or totals[n] != EXPECTED_COUNTS[n]:
            raise ValueError(f"Unexpected extra archived historical rows for order {n}")
        if observed[n] != HIST_COUNTS[n]:
            raise ValueError(f"Historical divergence count changed for order {n}: {observed[n]}")


def known_target_models() -> list[tuple[str,nx.Graph]]:
    """Avoid repeated searches of families already checked in PRs 22-24."""
    models = []
    def add(name,g):
        if len(g)<=MAX_TARGET_ORDER:
            models.append((name,g))
    for d in range(3,MAX_TARGET_ORDER//2+1):
        add("O_d",nx.complement(nx.disjoint_union_all(
            [nx.path_graph(2) for _ in range(d)])))
    for n in range(4,21):
        add("susp(C_n)",prior.suspension_cycle(n))
        add("K(susp(C_n))",prior.raw_clique_graph(prior.suspension_cycle(n)))
    for n in range(8,15):
        base=prior.complement_cycle(n)
        add("C_n^c",base)
        if n<=13:
            add("K(C_n^c)",prior.raw_clique_graph(base))
    # Additional rank-one coaffine joins are included in the still-open
    # PR24; tag them separately, not as certified exclusions here.
    for n,r in [(5,2),(7,2),(8,1),(10,1),
                (5,3),(7,3),(8,2),(10,2),(11,1),(13,1)]:
        g=nx.complement(nx.disjoint_union_all(
            [nx.cycle_graph(n)]+[nx.path_graph(2) for _ in range(r)]))
        add("PR24_coaffine_join",g)
    ico=nx.icosahedral_graph()
    for r in (1,2):
        g=nx.complement(nx.disjoint_union_all(
            [nx.complement(ico)]+[nx.path_graph(2) for _ in range(r)]))
        add("PR24_icosahedron_suspension",g)
    return models


def structural_necessary(target:nx.Graph,host:nx.Graph) -> str | None:
    """Only monotone *necessary* induced-embedding constraints."""
    if len(target)>len(host):
        return "ORDER"
    if target.number_of_edges()>host.number_of_edges():
        return "EDGES"
    d1=sorted((d for _,d in target.degree()),reverse=True)
    d2=sorted((d for _,d in host.degree()),reverse=True)
    if any(a>b for a,b in zip(d1,d2)):
        return "DEGREES"
    comp_target=nx.complement(target)
    comp_host=nx.complement(host)
    cd1=sorted((d for _,d in comp_target.degree()),reverse=True)
    cd2=sorted((d for _,d in comp_host.degree()),reverse=True)
    if any(a>b for a,b in zip(cd1,cd2)):
        return "COMPLEMENT_DEGREES"
    omitted=len(host)-len(target)
    lower=comp_host.number_of_edges()-sum(cd2[:omitted])
    if lower>comp_target.number_of_edges():
        return "COMPLEMENT_EDGE_BOUND"
    return None


def make_catalog() -> dict:
    hosts={i:prior.host(i)[0] for i in HOST_IDS}
    host_betti={i:prior.host(i)[1] for i in HOST_IDS}
    hist_counts=Counter()
    started=time.monotonic()
    source_examples=[]
    classes=[]
    buckets=defaultdict(list)
    counters=Counter()
    for source,original in historic_inputs():
        hist_counts[source["stage"]]+=1
        if len(source_examples)<5:
            source_examples.append(source)
        current=original
        for level in range(LEVELS+1):
            if level:
                if current is None:
                    break
                current=raw_clique_graph_bounded(current)
                if current is None:
                    counters[f"iterate_limit_K{level}"]+=1
                    break
            pared,folds=stiff_fold(current)
            if not nx.is_connected(pared):
                raise AssertionError("A connected source must remain connected after folds")
            identity=candidate_isomorphic_key(pared)
            existing=next((
                i for i in buckets[identity]
                if bounded_isomorphic(classes[i]["graph"],pared,counters)
            ),None)
            if existing is not None:
                classes[existing]["occurrences"]+=1
                classes[existing]["by_level"][str(level)]+=1
                continue
            i=len(classes)
            classes.append({
                "graph":pared,"graph6":graph6(pared),
                "occurrences":1,"by_level":Counter({str(level):1}),
                "provenance":{
                    "historical_graph":source,
                    "iterate_level":level,
                    "raw_iterate_graph6":graph6(current),
                    "dominated_deletions":folds,
                },
            })
            buckets[identity].append(i)
        counters["historical_input_graphs"]+=1
        if counters["historical_input_graphs"]%1000==0:
            print(f"PROGRESS historical={counters['historical_input_graphs']} "
                  f"stiff_classes={len(classes)} "
                  f"elapsed={time.monotonic()-started:.1f}s",
                  file=sys.stderr,flush=True)
    print(f"PHASE screened-source inventory built: "
          f"classes={len(classes)} "
          f"elapsed={time.monotonic()-started:.1f}s",
          file=sys.stderr,flush=True)
    if counters["historical_input_graphs"]!=10104 or (
        hist_counts!=Counter({"initial":10096,"c10":4,"bound60":1,"bound70":3})
    ):
        raise ValueError("Full historical graph source counts do not match frozen summaries")
    models=known_target_models()
    eligible_by_host=Counter()
    eliminations=Counter()
    candidates=[]
    for class_index,record in enumerate(classes):
        if class_index%100==0:
            print(f"PROGRESS target_betti={class_index}/{len(classes)} "
                  f"elapsed={time.monotonic()-started:.1f}s",
                  file=sys.stderr,flush=True)
        graph=record["graph"]
        raw_struct={i:structural_necessary(graph,hosts[i]) for i in HOST_IDS}
        if all(v is not None for v in raw_struct.values()):
            counters["candidate_structurally_excluded"]+=1
            continue
        # A limit is not a negative result. Flag it for later study.
        betti=bounded_reduced_betti_mod2(
            graph,max_faces=MAX_FACES,max_degree=5)
        homology_status="EXACT_THROUGH_5" if betti is not None else "RESOURCE_LIMIT"
        if betti is None:
            counters["homology_incomplete"]+=1
        known=next(
            (name for name,ref in models
             if (len(ref)==len(graph)
                 and ref.number_of_edges()==graph.number_of_edges()
                 and nx.is_isomorphic(graph,ref))),None
        )
        keep=[]
        reasons={}
        for core_id in HOST_IDS:
            reason=raw_struct[core_id]
            if reason is None and betti is not None:
                if any(betti.get(k,0)>host_betti[core_id][k] for k in range(6)):
                    reason="HOMOLOGY"
            if reason is None:
                keep.append(core_id)
                eligible_by_host[core_id]+=1
            else:
                eliminations[reason]+=1
            reasons[str(core_id)]=reason or "PASSED_NECESSARY_TESTS"
        if not keep:
            continue
        candidates.append({
            "graph6":record["graph6"],
            "order":len(graph),"edges":graph.number_of_edges(),
            "occurrences":record["occurrences"],
            "origins_by_iterate":dict(record["by_level"]),
            "representative_provenance":record["provenance"],
            "known_previously_searched_family":known,
            "target_betti_mod2_degrees_0_to_5":(
                {str(k):v for k,v in betti.items()} if betti is not None else None
            ),
            "homology_status":homology_status,
            "eligible_hosts":keep,
            "host_filters":reasons,
        })
    candidates.sort(key=lambda c:(
        c["known_previously_searched_family"] is not None,
        not any(c["target_betti_mod2_degrees_0_to_5"] and
                c["target_betti_mod2_degrees_0_to_5"].get(str(
                    3 if h==6914104 else 4),0)==1
                for h in c["eligible_hosts"]),
        c["order"],c["edges"],-c["occurrences"],c["graph6"]
    ))
    if len({(c["order"],c["edges"],c["graph6"]) for c in candidates})!=len(candidates):
        raise AssertionError("Duplicate candidate graph label")
    return {
        "schema":SCHEMA,"status":"COMPLETED",
        "historical_original_graph_count":counters["historical_input_graphs"],
        "historical_positive_stages":dict(hist_counts),
        "all_unique_stiff_target_isomorphism_classes":len(classes),
        "max_raw_clique_iterate":LEVELS,
        "skipped_expansions_exceeding_40":{
            k:v for k,v in counters.items() if k.startswith("iterate_limit_")
        },
        "classes_excluded_by_cheap_structure":counters["candidate_structurally_excluded"],
        "homology_resource_limits":counters["homology_incomplete"],
        "exact_iso_comparison_timeouts_kept_distinct":counters["isomorphism_timeouts"],
        "remaining_candidate_classes":len(candidates),
        "remaining_by_host":{str(k):eligible_by_host[k] for k in HOST_IDS},
        "candidate_classes_with_no_old_family_match":sum(
            c["known_previously_searched_family"] is None for c in candidates),
        "elimination_counts":dict(eliminations),
        "candidate_targets":candidates,
        "interpretation":(
            "Each derived target has an explicitly recorded historical "
            "positive and dominated-fold provenance; these are ONLY "
            "necessary homological/structural screens, not retraction proofs"
        ),
    }


def manifest() -> dict:
    paths=[
        Path(__file__),
        ROOT/"scripts/core9_clique_targets_v1.py",
        ROOT/"scripts/core9_third_retractions_v2.py",
        ROOT/"scripts/validate.py",
        ROOT/"scripts/graph_sources.py",
        ROOT/"config/pycliques_commit_core9_three_target_v1.txt",
        BASE/"summary.json",BASE/"manifest.json",
        NINE/"initial"/"summary.json",NINE/"initial"/"manifest.json",
    ]
    for stage in ADDITIONAL_NINE:
        paths.extend([NINE/stage/"manifest.json",NINE/stage/"summary.json"])
    # Every original verdict chunk is authenticated through its own SHA.
    chunk_paths=[]
    for n in range(6,10):
        folder=(BASE/f"order{n}" if n<=8 else NINE/"initial"/"order9")/"chunks"
        chunk_paths+=sorted(folder.glob("*.tsv.gz"))
    if len(chunk_paths)!=sum(
        (EXPECTED_COUNTS[n]+(500 if n<=8 else 10000)-1)//
        (500 if n<=8 else 10000)
        for n in range(6,10)
    ):
        raise ValueError("Historical verdict chunk count is incomplete")
    # Later positive reports: include all files because their proofs are
    # independently selected in staged_proven_positive_indices().
    record_paths=[
        p for stage in ADDITIONAL_NINE
        for p in sorted((NINE/stage/"records").glob("*.json"))
    ]
    full=paths+chunk_paths+record_paths
    return {
        "schema":SCHEMA, "stage":"historical_divergent_targets_v1",
        "orders":[6,7,8,9], "expected_positive":10104,
        "levels":[0,1,2], "max_target_order":MAX_TARGET_ORDER,
        "homology_through_degree":5,"max_faces":MAX_FACES,
        "hosts":list(HOST_IDS),"timeout_seconds":TIMEOUT_SECONDS,
        "memory_mib":MEMORY_MIB,
        "isomorphism_comparison_max_seconds":ISOMORPHISM_SECONDS,
        "uncompleted_isomorphism_comparisons_kept_as_separate_candidates":True,
        "source_sha256":{
            str(p.relative_to(ROOT)):sha(p) for p in full
        },
        "scope":"historically PROVED divergent graphs; no snub or conditional sources",
    }


def save(path:Path, data:dict) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",encoding="utf-8",dir=path.parent,prefix=".historical-",
        suffix=".tmp",delete=False,
    ) as tmp:
        partial=Path(tmp.name)
        json.dump(data,tmp,sort_keys=True,indent=2)
        tmp.write("\n")
    try: os.replace(partial,path)
    finally: partial.unlink(missing_ok=True)


def limit() -> None:
    mem=MEMORY_MIB*1024**2
    resource.setrlimit(resource.RLIMIT_AS,(mem,mem))


def subprocess_bounded(action:str,path:Path) -> None:
    args=[sys.executable,str(Path(__file__)),action,"--output",str(path)]
    try:
        p=subprocess.run(args,timeout=TIMEOUT_SECONDS,preexec_fn=limit,
                         text=True,capture_output=True)
    except subprocess.TimeoutExpired as exc:
        captured=exc.stderr or b""
        if isinstance(captured,bytes):
            captured=captured.decode("utf-8",errors="replace")
        print(f"Bounded {action} timed out. Latest worker diagnostics:\n"
              f"{captured[-7000:]}",file=sys.stderr,flush=True)
        raise TimeoutError(f"Historical target {action} exceeded {TIMEOUT_SECONDS}s") from exc
    if p.returncode:
        raise RuntimeError(f"Historical target {action} failed:\n{p.stderr[-4500:]}")


def authenticate(path:Path) -> None:
    actual=json.loads(path.read_text())
    if actual.get("status")=="TIMEOUT":
        if actual!={"schema":SCHEMA,"status":"TIMEOUT",
                    "phase":"worker","limit_seconds":TIMEOUT_SECONDS}:
            raise ValueError("Forged timeout or unsupported negative evidence")
        return
    if actual!=make_catalog():
        raise ValueError("Historical catalog differs from a fresh full replay")


def run(directory:Path) -> None:
    meta=manifest()
    directory.mkdir(parents=True,exist_ok=True)
    header=directory/"manifest.json"
    if header.exists():
        if json.loads(header.read_text())!=meta:
            raise ValueError("Existing historical catalog has different provenance")
    else:
        if any(directory.iterdir()):
            raise ValueError("Refusing preexisting unversioned outputs")
        save(header,meta)
    record=directory/"catalog.json"
    if not record.exists():
        with tempfile.TemporaryDirectory() as td:
            candidate=Path(td)/"candidate.json"
            try:
                subprocess_bounded("worker",candidate)
            except TimeoutError:
                save(record,{"schema":SCHEMA,"status":"TIMEOUT",
                             "phase":"worker","limit_seconds":TIMEOUT_SECONDS})
            else:
                # All positive and nonpositive observations were freshly
                # regenerated inside a separate bounded verifier before
                # any record is accepted. A second immediate full replay
                # would be redundant and disproportionately expensive.
                subprocess_bounded("check",candidate)
                save(record,json.loads(candidate.read_text()))
    if json.loads(header.read_text())!=meta:
        raise ValueError("Historical catalog manifest changed while running")


def verify(directory:Path) -> None:
    if json.loads((directory/"manifest.json").read_text())!=manifest():
        raise ValueError("Historical input or script hash changed")
    subprocess_bounded("check",directory/"catalog.json")
    print("Historical divergent target catalog fully independently replayed")


def report(directory:Path) -> None:
    verify(directory)
    data=json.loads((directory/"catalog.json").read_text())
    if data["status"]=="TIMEOUT":
        print(json.dumps({"status":"INCONCLUSIVE_TIMEOUT"}))
        return
    summary={k:v for k,v in data.items() if k!="candidate_targets"}
    print(json.dumps(summary,indent=2,sort_keys=True))
    for h in HOST_IDS:
        subset=[c for c in data["candidate_targets"]
                if h in c["eligible_hosts"] and
                c["known_previously_searched_family"] is None]
        print(f"HOST {h}: {len(subset)} not-previously-targeted candidates")
        for c in subset[:30]:
            origin=c["representative_provenance"]["historical_graph"]
            print(f"  order={c['order']} edges={c['edges']} "
                  f"g6={c['graph6']} first_origin={origin['order']}:{origin['index']} "
                  f"stage={origin['stage']} Klevel={c['representative_provenance']['iterate_level']} "
                  f"betti={c['target_betti_mod2_degrees_0_to_5']}")


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=["run","worker","check","verify","report","plan"])
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    if args.action=="plan":
        print(json.dumps(manifest(),indent=2,sort_keys=True));return
    if args.action in ("worker","check"):
        if args.output is None:
            p.error("Worker/check needs --output file")
        if args.action=="worker":save(args.output,make_catalog())
        else:authenticate(args.output)
        return
    directory=args.output or OUTPUT
    if args.action=="run":run(directory)
    elif args.action=="verify":verify(directory)
    else:report(directory)


if __name__=="__main__":
    main()
