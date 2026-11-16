"""Resumable homology-cache postpass on unresolved pared census graphs.

General algorithms live in pycliques-project. This driver only chooses
inputs, caches exact pycombtop Betti data, isolates expensive workers,
records scoped search results, and replays positive retraction witnesses.
It NEVER upgrades a historical clique-behavior verdict automatically.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys

import networkx as nx

from pycliques import (
    TargetRetractionResult,
    TargetSearchStatus,
    search_targeted_retractions,
    verify_targeted_retraction,
)
from pycliques.small import CliqueSequence
from pycombtop.bounded_betti import bounded_reduced_betti_mod2

ROOT = Path(__file__).resolve().parents[1]
PIN_FILE = ROOT / "config/pycliques_commit_targeted_v1.txt"
SCRIPT = ROOT / "scripts/targeted_retractions_v1.py"
SOURCE_PATTERN = "indeterminate_order_{order}.txt"
OUT_PATTERN = "runs/order{order}/targeted-retractions-v1"
MAX_CLIQUE_BOUND = 120
ITERATES = 3
MAX_HOST_VERTICES = 80
MAX_BETTI_FACES = 150_000
MAX_BETTI_PARTIAL_DEGREE = 3
MAX_TARGET_ORDER = 16
MAX_PATTERNS = 20_000
MAX_STATES = 100_000
MAX_ASSIGNMENTS = 250_000
TIMEOUT_SECONDS = 120
MEMORY_MIB = 2048
BATCH_SIZE = 5
SCHEMA = 1


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".partial")
    try:
        temp.write_text(json.dumps(payload,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        os.replace(temp,path)
    finally:
        temp.unlink(missing_ok=True)


def input_rows(order: int) -> dict[int,str]:
    path=ROOT/SOURCE_PATTERN.format(order=order)
    lines=path.read_text(encoding="utf-8").splitlines()
    rows={}
    for line in lines:
        if not line or line.startswith("#"):
            continue
        fields=line.split()
        if len(fields)!=6:
            raise ValueError("Malformed frozen indeterminate input row")
        index=int(fields[0])
        if index in rows:
            raise ValueError("Duplicate indeterminate index")
        graph=nx.from_graph6_bytes(fields[2].encode("ascii"))
        if not nx.is_connected(graph):
            raise ValueError("Indeterminate graph is disconnected")
        rows[index]=fields[2]
    return rows


def root_dir(order: int) -> Path:
    return ROOT/OUT_PATTERN.format(order=order)


def manifest(order: int) -> dict:
    path=ROOT/SOURCE_PATTERN.format(order=order)
    return {
        "schema":SCHEMA,"order":order,
        "source_sha256":digest(path.read_bytes()),
        "code_sha256":digest(SCRIPT.read_bytes()),
        "dependency_pin":PIN_FILE.read_text(encoding="utf-8").strip(),
        "settings":{
            "clique_bound":MAX_CLIQUE_BOUND,"iterates":ITERATES,
            "max_host_vertices":MAX_HOST_VERTICES,
            "max_betti_faces":MAX_BETTI_FACES,
            "max_partial_degree":MAX_BETTI_PARTIAL_DEGREE,
            "max_target_order":MAX_TARGET_ORDER,
            "max_patterns":MAX_PATTERNS,"max_states":MAX_STATES,
            "max_assignments":MAX_ASSIGNMENTS,
            "timeout_seconds":TIMEOUT_SECONDS,"memory_mib":MEMORY_MIB,
        },
        "scope":"pared input and verified pared iterates only",
    }


def require_manifest(order: int) -> Path:
    directory=root_dir(order)
    current=manifest(order)
    frozen=directory/"manifest.json"
    if frozen.exists():
        if read_json(frozen)!=current:
            raise ValueError("Frozen targeted postpass sources/parameters changed")
    else:
        # Never adopt old records or cache files under a newly generated
        # manifest. Their source, pin, and limits are unverified.
        if directory.exists() and any(directory.iterdir()):
            raise ValueError(
                "Targeted stage has artifacts without manifest.json; "
                "archive/remove them before starting a new frozen stage"
            )
        atomic(frozen,current)
    return directory


def graph6(graph: nx.Graph) -> str:
    numbered=nx.convert_node_labels_to_integers(graph)
    return nx.to_graph6_bytes(numbered,header=False).decode("ascii").strip()


def cache_homology(graph: nx.Graph, directory: Path) -> tuple[dict[int,int]|None,str]:
    """Return one persisted exact profile for this exact labeled encoding."""
    encoded=graph6(graph)
    key=digest(encoded.encode("ascii"))
    cache_path=directory/"homology_cache"/(key+".json")
    if cache_path.exists():
        saved=read_json(cache_path)
        if saved.get("schema")!=SCHEMA or saved.get("graph6")!=encoded:
            raise ValueError("Homology cache key/provenance mismatch")
        data=saved["betti_numbers"]
        known=None if data is None else {int(d):int(v) for d,v in data.items()}
        if known is not None and any(d<0 or v<0 for d,v in known.items()):
            raise ValueError("Invalid cached reduced Betti profile")
        return known,key
    known=bounded_reduced_betti_mod2(graph,max_faces=MAX_BETTI_FACES)
    mode="full"
    if known is None:
        known=bounded_reduced_betti_mod2(
            graph,max_faces=MAX_BETTI_FACES,max_degree=MAX_BETTI_PARTIAL_DEGREE,
        )
        mode="partial" if known is not None else "face_limit"
    atomic(cache_path,{
        "schema":SCHEMA,"graph6":encoded,"mode":mode,
        "max_faces":MAX_BETTI_FACES,
        "max_partial_degree":MAX_BETTI_PARTIAL_DEGREE,
        "algorithm":"pycombtop.bounded_betti.bounded_reduced_betti_mod2",
        "betti_numbers":None if known is None else {
            str(d):int(v) for d,v in known.items()
        },
    })
    return known,key


def serialize_family(graph: nx.Graph,result: TargetRetractionResult) -> dict:
    row={
        "status":result.status.name,"patterns":result.patterns_checked,
        "induced_targets":result.induced_targets_checked,
        "states":result.states_explored,"assignments":result.assignments_tried,
        "reason":result.reason,
    }
    if result.status is TargetSearchStatus.FOUND:
        if not verify_targeted_retraction(graph,result):
            raise ValueError("Positive result cannot be independently replayed")
        vertices=list(graph)
        lookup={v:i for i,v in enumerate(vertices)}
        row.update({
            "kind":result.target_kind,
            "target_indices":[lookup[v] for v in result.target_vertices],
            "projection_indices":[lookup[result.projection[v]] for v in vertices],
            "status_scope":"structural_retraction_only",
        })
    return row


def analyze(index: int, input_g6: str, directory: Path) -> dict:
    graph=nx.from_graph6_bytes(input_g6.encode("ascii"))
    sequence=CliqueSequence(graph,bound=MAX_CLIQUE_BOUND)
    levels=[]
    for level in range(ITERATES):
        current=sequence[level]
        if current is None:
            levels.append({"level":level,"status":"CLIQUE_BOUND_EXCEEDED"})
            break
        encoded=graph6(current)
        if len(current)>MAX_HOST_VERTICES:
            levels.append({
                "level":level,"graph6":encoded,
                "status":"HOST_ORDER_LIMIT",
            })
            break
        known,key=cache_homology(current,directory)
        families=search_targeted_retractions(
            current,betti_numbers=known,
            max_target_order=MAX_TARGET_ORDER,max_patterns=MAX_PATTERNS,
            max_states=MAX_STATES,max_assignments=MAX_ASSIGNMENTS,
        )
        levels.append({
            "level":level,"graph6":encoded,"order":len(current),
            "edges":current.number_of_edges(),"status":"COMPLETED",
            "homology_cache_key":key,
            "betti_known":None if known is None else {
                str(d):v for d,v in known.items()
            },
            "families":{
                family:serialize_family(current,result)
                for family,result in families.items()
            },
        })
    return {
        "schema":SCHEMA,"index":index,"input_graph6":input_g6,
        "scope":"pared_input_and_pared_iterates_only",
        "no_automatic_behavior_verdict":True,
        "analysis_complete":True,
        "status":"COMPLETED",
        "levels":levels,
    }


def worker(order:int,index:int) -> None:
    rows=input_rows(order)
    directory=require_manifest(order)
    if index not in rows:
        raise ValueError("Index not among current unresolved inputs")
    record=analyze(index,rows[index],directory)
    atomic(directory/"records"/f"{index:08d}.json",record)


def resource_limit() -> None:
    maximum=MEMORY_MIB*1024*1024
    resource.setrlimit(resource.RLIMIT_AS,(maximum,maximum))


def run_one(order:int,index:int) -> None:
    directory=require_manifest(order)
    path=directory/"records"/f"{index:08d}.json"
    if path.exists():
        return
    cmd=[sys.executable,str(SCRIPT),"worker","--order",str(order),
         "--index",str(index)]
    try:
        process=subprocess.run(cmd,capture_output=True,text=True,
            timeout=TIMEOUT_SECONDS,preexec_fn=resource_limit,check=False)
        if process.returncode:
            atomic(path,{
                "schema":SCHEMA,"index":index,"status":"ERROR",
                "error":process.stderr[-2000:],
                "no_automatic_behavior_verdict":True,
            })
    except subprocess.TimeoutExpired:
        atomic(path,{
            "schema":SCHEMA,"index":index,"status":"TIMEOUT",
            "no_automatic_behavior_verdict":True,
        })


def verify_record(
    record: dict, graph6_input: str, directory: Path, *, index: int | None = None
) -> None:
    """Replay the complete pared-iterate chain and every positive witness.

    We deliberately do not rerun the possibly expensive negative searches.
    Their finite scope is retained as a record, not a negative theorem.
    """
    if (
        record.get("schema") != SCHEMA
        or record.get("status") != "COMPLETED"
        or record.get("analysis_complete") is not True
        or record.get("input_graph6") != graph6_input
        or record.get("scope") != "pared_input_and_pared_iterates_only"
        or record.get("no_automatic_behavior_verdict") is not True
        or type(record.get("index")) is not int
        or (index is not None and record["index"] != index)
    ):
        raise ValueError("Incomplete or incorrectly scoped targeted record")

    levels = record.get("levels")
    if not isinstance(levels, list) or not levels or len(levels) > ITERATES:
        raise ValueError("Missing/truncated targeted iterate data")

    source = nx.from_graph6_bytes(graph6_input.encode("ascii"))
    sequence = CliqueSequence(source, bound=MAX_CLIQUE_BOUND)
    expected_families = {"octahedra", "suspensions", "cycle_complements"}
    terminal = {"CLIQUE_BOUND_EXCEEDED", "HOST_ORDER_LIMIT"}

    for position, level in enumerate(levels):
        if not isinstance(level, dict) or level.get("level") != position:
            raise ValueError("Noncontiguous or malformed iterate record")
        current = sequence[position]
        status = level.get("status")
        if status in terminal:
            if position != len(levels) - 1:
                raise ValueError("Terminal iterate cannot have later results")
            if status == "CLIQUE_BOUND_EXCEEDED" and current is not None:
                raise ValueError("False clique-bound termination")
            if status == "HOST_ORDER_LIMIT" and (
                current is None or len(current) <= MAX_HOST_VERTICES
                or level.get("graph6") != graph6(current)
            ):
                raise ValueError("False host-order-limit termination")
            continue

        if (
            status != "COMPLETED"
            or current is None
            or len(current) > MAX_HOST_VERTICES
        ):
            raise ValueError("Invalid completed-iterate status")
        expected_encoding = graph6(current)
        if level.get("graph6") != expected_encoding:
            raise ValueError("Stored graph is not the actual pared clique iterate")
        graph = nx.from_graph6_bytes(expected_encoding.encode("ascii"))
        if (
            len(graph) != level.get("order")
            or graph.number_of_edges() != level.get("edges")
        ):
            raise ValueError("Wrong stored iterate order or edge count")

        key = digest(expected_encoding.encode("ascii"))
        if level.get("homology_cache_key") != key:
            raise ValueError("Incorrect cached graph key")
        cache = read_json(directory/"homology_cache"/(key+".json"))
        if (
            cache.get("schema") != SCHEMA
            or cache.get("graph6") != expected_encoding
            or cache.get("algorithm") !=
            "pycombtop.bounded_betti.bounded_reduced_betti_mod2"
            or cache.get("max_faces") != MAX_BETTI_FACES
            or cache.get("max_partial_degree") != MAX_BETTI_PARTIAL_DEGREE
            or cache.get("mode") not in {"full", "partial", "face_limit"}
            or cache.get("betti_numbers") != level.get("betti_known")
        ):
            raise ValueError("Cached Betti data/provenance does not match iterate")
        ranks = cache["betti_numbers"]
        if ranks is not None:
            if (
                not isinstance(ranks, dict)
                or any(
                    not isinstance(d, str) or not d.isdigit()
                    or type(v) is not int or v < 0
                    for d, v in ranks.items()
                )
            ):
                raise ValueError("Invalid exact Betti data")
            if cache["mode"] == "partial" and (
                set(ranks) != {str(d) for d in range(MAX_BETTI_PARTIAL_DEGREE+1)}
            ):
                raise ValueError("Partial ranks do not cover the declared degrees")
        elif cache["mode"] != "face_limit":
            raise ValueError("Unknown Betti data must have face-limit status")

        families = level.get("families")
        if not isinstance(families, dict) or set(families) != expected_families:
            raise ValueError("One or more target-family results are missing")
        for family, data in families.items():
            if not isinstance(data, dict) or data.get("status") not in {
                "FOUND", "EXHAUSTED", "LIMIT_REACHED", "HOMOLOGY_EXCLUDED",
            }:
                raise ValueError("Invalid target-family result")
            if any(
                type(data.get(field)) is not int or data[field] < 0
                for field in ("patterns", "induced_targets",
                              "states", "assignments")
            ):
                raise ValueError("Malformed search counters")
            if data["status"] != "FOUND":
                if any(k in data for k in (
                    "target_indices", "projection_indices", "kind",
                )):
                    raise ValueError("A negative/limited result contains a witness")
                continue
            target_indices = data.get("target_indices")
            projection_indices = data.get("projection_indices")
            if (
                not isinstance(target_indices, list)
                or not isinstance(projection_indices, list)
                or not target_indices
                or len(projection_indices) != len(graph)
                or len(target_indices) != len(set(target_indices))
                or any(type(v) is not int or v not in graph
                       for v in target_indices+projection_indices)
            ):
                raise ValueError("Malformed graph-retraction witness arrays")
            test = TargetRetractionResult(
                family=family, status=TargetSearchStatus.FOUND,
                target_kind=data.get("kind"),
                target_vertices=tuple(target_indices),
                projection={v: projection_indices[v] for v in graph},
            )
            if not verify_targeted_retraction(graph, test):
                raise ValueError("Positive retraction failed independent replay")
    if levels[-1]["status"] == "COMPLETED" and len(levels) != ITERATES:
        raise ValueError("Successful record ends before requested iterate count")


def verify_all(order:int) -> dict:
    directory=require_manifest(order)
    rows=input_rows(order)
    counts={"COMPLETED":0,"TIMEOUT":0,"ERROR":0,"MISSING":0,"FOUND":0}
    for index,g6 in rows.items():
        path=directory/"records"/f"{index:08d}.json"
        if not path.exists():
            counts["MISSING"]+=1
            continue
        record=read_json(path)
        if record.get("status") in ("TIMEOUT","ERROR"):
            if (
                record.get("schema") != SCHEMA
                or record.get("index") != index
                or record.get("no_automatic_behavior_verdict") is not True
            ):
                raise ValueError("Malformed terminal worker record")
            counts[record["status"]]+=1
            continue
        verify_record(record,g6,directory,index=index)
        counts["COMPLETED"]+=1
        counts["FOUND"]+=sum(
            result["status"]=="FOUND"
            for level in record["levels"]
            if level["status"]=="COMPLETED"
            for result in level["families"].values()
        )
    return counts


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("plan","next","all","verify","worker"))
    parser.add_argument("--order",type=int,choices=(9,10),default=9)
    parser.add_argument("--index",type=int)
    parser.add_argument("--batch-size",type=int,default=BATCH_SIZE)
    parser.add_argument("--limit",type=int)
    args=parser.parse_args()
    if args.action=="worker":
        if args.index is None:
            parser.error("--index is mandatory for worker")
        worker(args.order,args.index)
        return
    directory=require_manifest(args.order)
    rows=input_rows(args.order)
    if args.action=="verify":
        print(json.dumps(verify_all(args.order),sort_keys=True))
        return
    pending=[
        index for index in rows
        if not (directory/"records"/f"{index:08d}.json").exists()
    ]
    if args.action=="plan":
        print(json.dumps({
            "order":args.order,"inputs":len(rows),
            "distinct_graph6":len(set(rows.values())),
            "pending":len(pending),
            "homology_cache_files":len(list(
                (directory/"homology_cache").glob("*.json")
            )),
        },sort_keys=True))
        return
    if args.batch_size<1 or args.limit is not None and args.limit<1:
        parser.error("Batch size and optional limit must be positive")
    todo=pending if args.action=="all" else pending[:args.batch_size]
    if args.limit is not None:
        todo=todo[:args.limit]
    for index in todo:
        run_one(args.order,index)
    print(json.dumps(verify_all(args.order),sort_keys=True))


if __name__=="__main__":
    main()
