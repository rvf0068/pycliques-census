"""Certified ordinary retractions for all 2,403 unresolved stiff ten-cores.

Exhaustively compare every deletion of one vertex in each source against
all six previously proved divergent nine-vertex cores. Check full graph
retractions (adjacent OR equal), exact induced sections and the historic
two connected coaffine-suspension divergence certificates. A new v5
working list excludes only newly proved cases. All v4 data are immutable.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from io import StringIO
import json
from pathlib import Path

import networkx as nx

import current_indeterminate_v4 as previous

ROOT = Path(__file__).resolve().parents[1]
CORE_TABLE = "reports/order10_core_index_v1/classes.tsv"
OLD_LIST = "indeterminate_order_10_v4.txt"
NEW_LIST = "indeterminate_order_10_v5.txt"
OUT = "research/order10_direct_divergent_ninecore_retracts_v1"
CORE_SHA256 = "5a9b08c548aa5671f9c1403cf1badd0044211f7ef75129c83980462efa6f16eb"
V4_GIT_SHA1 = "60594c7e071c3a6a201980b26729f67ab754db10"
V4_SCRIPT_GIT_SHA1 = "03730bfb393ba215d2cb02f2cc775768ddd99d16"
TARGETS = {
    6938923: "HEht}pl",
    6939350: "HEht~bl",
    7454135: "HEnb~jl",
    9678187: "HQyuzpt",
    10768817: "HUZ~v~}",
    11363569: "HUzrv~}",
}
COAFFINE = {
    10768817: ((5, 6), (0, 1, 2, 3, 4, 7, 8), (1, 2, 3, 4, 0, 8, 7)),
    11363569: ((7, 8), (0, 1, 2, 3, 4, 5, 6), (1, 2, 3, 4, 5, 6, 0)),
}
EXPECTED_IDS = (
    10768894, 11363661, 11372238, 11475102, 11519660,
    11541397, 11655985, 11660877, 11716425,
)
EXPECTED_BY_TARGET = {10768817: 4, 11363569: 5}
EXPECTED_INDUCED_SECTIONS = 31


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode() + b"\0" + raw
    ).hexdigest()


def decode(encoded: str) -> nx.Graph:
    return nx.convert_node_labels_to_integers(
        nx.from_graph6_bytes(encoded.encode("ascii")), ordering="sorted"
    )


def read_tsv(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(StringIO(data.decode()), delimiter="\t"))


def certify_divergent_suspension(i: int) -> None:
    """Independently check the old connected 2-coaffine-suspension witness."""
    graph = decode(TARGETS[i])
    poles, base, images = COAFFINE[i]
    if (
        len(graph) != 9 or len(poles) != 2 or len(set(poles)) != 2
        or len(set(base)) != 7 or set(base) | set(poles) != set(graph)
        or set(base) & set(poles) or graph.has_edge(*poles)
        or set(images) != set(base)
        or any(not graph.has_edge(p, v) for p in poles for v in base)
    ):
        raise ValueError("Invalid 2-coaffine suspension")
    sub = graph.subgraph(base)
    if not nx.is_connected(sub):
        raise ValueError("2-coaffination base is disconnected")
    perm = dict(zip(base, images))
    if any(perm[v] == v or sub.has_edge(v, perm[v]) for v in base):
        raise ValueError("Proposed automorphism is not a 2-coaffination")
    if any(
        sub.has_edge(u, v) != sub.has_edge(perm[u], perm[v])
        for u in base for v in base if u < v
    ):
        raise ValueError("Proposed coaffination fails to preserve adjacency")


def frozen_inputs(root: Path = ROOT) -> tuple[list[dict], list[str]]:
    raw_classes = (root / CORE_TABLE).read_bytes()
    if sha256(raw_classes) != CORE_SHA256:
        raise ValueError("The 2,439-class frozen index has changed")
    if git_blob((root / OLD_LIST).read_bytes()) != V4_GIT_SHA1:
        raise ValueError("The 8,233-case frozen v4 index has changed")
    if git_blob((root / "scripts/current_indeterminate_v4.py").read_bytes()) != V4_SCRIPT_GIT_SHA1:
        raise ValueError("The original v4 certificate verifier has changed")
    previous.check(root)
    for i, g6 in TARGETS.items():
        if previous.PROOFS.get(i, (None,))[0] != g6:
            raise ValueError("Divergent historical nine-core model mismatch")
    for i in COAFFINE:
        certify_divergent_suspension(i)

    classes = read_tsv(raw_classes)
    stiff = sorted(
        (r for r in classes if r["core_order"] == "10"),
        key=lambda r: int(r["core_id"]),
    )
    if len(classes) != 2439 or len(stiff) != 2403:
        raise ValueError("The original stiff ten-core population has changed")
    lines = (root / OLD_LIST).read_text(encoding="utf-8").splitlines()
    entries = {}
    for line in lines:
        if line and not line.startswith("#"):
            fields = line.split()
            if len(fields) != 6 or int(fields[0]) in entries:
                raise ValueError("The frozen v4 record is invalid")
            entries[int(fields[0])] = fields
    if len(entries) != 8233:
        raise ValueError("The frozen unresolved population has changed")
    ids = set()
    for row in stiff:
        i = int(row["core_id"])
        if (
            row["members"] != "1"
            or row["member_indices"] != str(i)
            or i not in entries
            or entries[i][1] != "10"
            or entries[i][2] != row["core_graph6"]
            or i in ids
        ):
            raise ValueError("The original stiff graph index has a changed member")
        ids.add(i)
    if ids != {i for i, fields in entries.items() if fields[1] == "10"}:
        raise ValueError("The v4 stiff ten-vertex partition is incomplete")
    return stiff, lines


def certify_retraction(
    G: nx.Graph, H: nx.Graph, projection: list[int], section: list[int]
) -> None:
    if (
        len(projection) != 10 or len(section) != 9
        or set(projection) != set(H)
        or len(set(section)) != 9
        or any(projection[section[q]] != q for q in H)
    ):
        raise ValueError("The maps are not a total split retraction")
    if any(
        H.has_edge(q, r) != G.has_edge(section[q], section[r])
        for q in H for r in H if q < r
    ):
        raise ValueError("The nine-vertex section is not an induced isomorphism")
    if any(
        projection[u] != projection[v]
        and not H.has_edge(projection[u], projection[v])
        for u, v in G.edges()
    ):
        raise ValueError("The retraction fails adjacency OR equality")


def scan_one(G: nx.Graph, H: nx.Graph, target_id: int) -> tuple[int, list[dict]]:
    """Exhaust all ten induced sections and every graph-isomorphism labeling."""
    degrees = sorted(dict(H.degree()).values())
    n_induced = 0
    witnesses = []
    for removed in sorted(G):
        retained = [v for v in G if v != removed]
        sub = G.subgraph(retained)
        if sorted(dict(sub.degree()).values()) != degrees:
            continue
        maps = list(nx.algorithms.isomorphism.GraphMatcher(
            sub, H
        ).isomorphisms_iter())
        if not maps:
            continue
        n_induced += 1
        for iso in maps:
            section = [0] * 9
            for v, q in iso.items():
                section[q] = v
            for image in H:
                projection = [iso[v] if v != removed else image for v in G]
                if any(
                    projection[u] != projection[v]
                    and not H.has_edge(projection[u], projection[v])
                    for u, v in G.edges()
                ):
                    continue
                certify_retraction(G, H, projection, section)
                witnesses.append({
                    "target_id": target_id,
                    "target_graph6": TARGETS[target_id],
                    "deleted_vertex": removed,
                    "projection": projection,
                    "section": section,
                })
    witnesses.sort(key=lambda w: (
        w["target_id"], w["deleted_vertex"],
        tuple(w["projection"]), tuple(w["section"])
    ))
    return n_induced, witnesses


def audit(root: Path = ROOT) -> tuple[list[dict], dict]:
    stiff, _ = frozen_inputs(root)
    targets = {i: decode(g6) for i, g6 in TARGETS.items()}
    positives = []
    induced_copies = 0
    by_target = {i: 0 for i in TARGETS}
    for row in stiff:
        index, encoded = int(row["core_id"]), row["core_graph6"]
        G = decode(encoded)
        if len(G) != 10 or not nx.is_connected(G):
            raise ValueError("Invalid exact source graph")
        if any(
            v != u and (set(G[v]) | {v}) <= (set(G[u]) | {u})
            for v in G for u in G
        ):
            raise ValueError("A supposed stiff source has a dominated vertex")
        found = []
        for target_id, H in targets.items():
            copies, matches = scan_one(G, H, target_id)
            induced_copies += copies
            found.extend(matches)
        if found:
            witness = min(
                found, key=lambda w: (
                    w["target_id"], w["deleted_vertex"],
                    tuple(w["projection"]), tuple(w["section"])
                )
            )
            by_target[witness["target_id"]] += 1
            positives.append({
                "original_index": index,
                "original_graph6": encoded,
                "status": "CERTIFIED_DIVERGENT",
                **witness,
            })
    if (
        tuple(x["original_index"] for x in positives) != EXPECTED_IDS
        or {i: n for i, n in by_target.items() if n} != EXPECTED_BY_TARGET
        or induced_copies != EXPECTED_INDUCED_SECTIONS
    ):
        raise ValueError(
            "Independent six-target exhaustive screen changed: "
            f"{[x['original_index'] for x in positives]}, "
            f"{by_target}, induced={induced_copies}"
        )
    counts = {
        "stiff_ten_sources_tested": 2403,
        "proved_divergent_ninecore_target_models": len(TARGETS),
        "induced_target_copies": induced_copies,
        "new_certified_stiff_ten_divergences": len(positives),
        "target_positive_counts": {str(i): n for i, n in by_target.items()},
        "previous_v4_unresolved": 8233,
        "current_v5_unresolved": 8224,
        "stiff_ten_remaining": 2394,
        "ninecore_originals_remaining": 3738,
        "snub_eightcore_originals_remaining": 2092,
    }
    return positives, counts


def generated(root: Path = ROOT) -> dict[str, bytes]:
    positives, counts = audit(root)
    excluded = {x["original_index"] for x in positives}
    old = (root / OLD_LIST).read_text(encoding="utf-8").splitlines()
    records = [line for line in old if line and not line.startswith("#")]
    kept = [
        line for line in records if int(line.split()[0]) not in excluded
    ]
    if len(records) != 8233 or len(kept) != 8224 or len(excluded) != 9:
        raise ValueError("The new and old versioned census populations disagree")
    v5 = "\n".join([
        "# Current order-10 unresolved after v4 and nine direct divergent stiff-core retractions",
        "# Remaining=8224 previous_v4=8233 new_certified_divergent=9",
        "# All historical data are immutable; finite negative target screens never imply convergence.",
        "# Format: original_index pared_order pared_graph6 certificate_rule certificate_target_status certificate_target_label",
        *kept, "",
    ]).encode()

    index = [
        "original_index\toriginal_graph6\ttarget_id\ttarget_graph6"
        "\tdeleted_vertex\tprojection\tsection"
    ]
    for w in positives:
        index.append("\t".join([
            str(w["original_index"]), w["original_graph6"],
            str(w["target_id"]), w["target_graph6"],
            str(w["deleted_vertex"]),
            ",".join(map(str, w["projection"])),
            ",".join(map(str, w["section"])),
        ]))
    cert = {
        "schema": 1,
        "source_scope": "all 2403 stiff ten-originals, all six proven divergent ninecore targets",
        "divergent_target_models": TARGETS,
        "independent_2009_expansive_graph_certificates": COAFFINE,
        "uses_Neumann_Lara_retraction_theorem": True,
        "negative_screen_does_not_imply_convergence": True,
        "counts": counts,
        "certified_positive_retractions": positives,
    }
    report = [
        "# Nine newly certified K-divergent stiff ten-vertex graphs",
        "",
        "These are nine NEW positive graph-retraction certificates; none",
        "has a dominated vertex. All nine were in the frozen v4 list.",
        "",
        "Their targets are two independently verified connected",
        "2-coaffine suspensions: core 10768817 (HUZ~v~}) and",
        "core 11363569 (HUzrv~}). They are K-divergent by",
        "Larrion--Neumann-Lara--Pizana (2009), On expansive graphs,",
        "Theorem 4.6. Neumann-Lara's Retraction Theorem implies",
        "that a graph retracting onto a K-divergent graph is",
        "also K-divergent (see Edge contraction and edge removal",
        "on iterated clique graphs, 2013).",
        "",
        "All 2,403 frozen stiff ten-vertex sources were independently",
        "screened against all SIX previously proved divergent",
        "nine-vertex cores, allowing deletion of any one source vertex",
        "and checking every exact induced isomorphism and all",
        "possible weak-morphism images of the removed vertex.",
        "Edges may map to edges OR equal vertices. The search found",
        "31 induced target copies but only NINE distinct graphs",
        "admitting a retract. Their complete ten-to-nine projection",
        "and nine-to-ten induced section maps are stored in",
        "certificates.json and new_divergent.tsv.",
        "",
        "| Original McKay index | Graph6 | Divergent nine-core target |",
        "|---:|---|---:|",
        *(
            f"| {w['original_index']} | {w['original_graph6']} | {w['target_id']} |"
            for w in positives
        ),
        "",
        "**Nine new graphs are proved K-divergent.** Negative searches",
        "against these six models are NOT proofs of K-convergence.",
        "",
        "| Remaining core order | Indeterminate originals (v5) |",
        "|---|---:|",
        "| 8 (snub disphenoid) | 2,092 |",
        "| 9 (29 stiff classes) | 3,738 |",
        "| 10 (stiff original) | 2,394 |",
        "| TOTAL | 8,224 |",
        "",
        "The old v4 index and all earlier run/report data remain intact.",
        "The new v5 index differs only by removal of these nine",
        "exact original indices, retaining all 8,224 other records.",
        "",
        "Reproduce with Python and NetworkX 3.6.1:",
        "",
        "    python scripts/direct_divergent_ninecore_retracts_v1.py verify",
        "    python -m unittest discover -s tests -p test_direct_divergent_ninecore_retracts_v1.py -v",
        "",
        "The verifier checks frozen source hashes and rebuilds the",
        "complete v4 index, then regenerates all positive and negative",
        "finite-family checks and every committed byte of v5.",
        "",
    ]
    outputs = {
        "certificates.json": (json.dumps(cert, sort_keys=True, indent=2) + "\n").encode(),
        "new_divergent.tsv": ("\n".join(index) + "\n").encode(),
        "summary.md": ("\n".join(report)).encode(),
    }
    manifest = {
        "schema": 1,
        "stage": "order10_direct_divergent_ninecore_retracts_v1",
        "new_proved_divergences": 9,
        "input_sha256": {
            CORE_TABLE: sha256((root / CORE_TABLE).read_bytes()),
            OLD_LIST: sha256((root / OLD_LIST).read_bytes()),
        },
        "outputs_sha256": {name: sha256(data) for name, data in sorted(outputs.items())},
        "v5_sha256": sha256(v5),
    }
    outputs["manifest.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    artifacts = {str(Path(OUT) / name): value for name, value in outputs.items()}
    artifacts[NEW_LIST] = v5
    return artifacts


def verify(root: Path = ROOT) -> None:
    for name, data in generated(root).items():
        path = root / name
        if not path.is_file() or path.read_bytes() != data:
            raise ValueError(f"Missing or modified direct-retraction certificate: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "build", "verify"))
    args = parser.parse_args()
    payload = generated()
    if args.action == "build":
        for name, data in payload.items():
            path = ROOT / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and path.read_bytes() != data:
                raise ValueError(f"Refusing to overwrite changed proof file: {name}")
            path.write_bytes(data)
    elif args.action == "plan":
        print("9 new proved divergent stiff ten-cores; 8233 -> 8224 indeterminate")
        return
    verify()
    print("VERIFIED nine ordinary retracts; 2,403 stiff sources tested; v5=8,224")


if __name__ == "__main__":
    main()
