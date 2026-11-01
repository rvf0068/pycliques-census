"""One-pass, resumable connected census for large orders 9 and 10.

This calls the same pycliques fast classifier as the small-behavior CLI, but
never re-scans the gzip source once for *each* chunk. It streams the source
once per invocation and skips already committed chunks in constant work per
graph. Each chunk's verdict and pared-unresolved sidecar are written before
an atomic completion marker. Partial runs can be resumed without mixing data.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import os
from pathlib import Path

import networkx as nx
from pycliques.small import Verdict, classify_clique_behavior

from graph_sources import EXPECTED_COUNTS, connected_graphs, graph6


def _write_gzip(path: Path, data: bytes) -> None:
    """Produce deterministic gzip bytes (no timestamp or embedded filename)."""
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as stream:
            stream.write(data)


def _chunk_paths(folder: Path, start: int, end: int) -> tuple[Path, Path, Path]:
    name = f"{start:08d}-{end:08d}"
    return (
        folder / "chunks" / (name + ".tsv.gz"),
        folder / "unresolved_chunks" / (name + ".tsv.gz"),
        folder / "completed" / (name + ".done"),
    )


def write_unresolved_cohort(folder: Path, n: int, total: int, batch_size: int) -> None:
    """Rebuild the human-readable unresolved list from committed chunk sidecars."""
    target = folder / f"indeterminate_order_{n}.txt"
    temp = target.with_suffix(".partial")
    with temp.open("w", encoding="utf-8") as handle:
        handle.write(f"# Indeterminate clique behavior - connected graphs of order {n}\n")
        handle.write("# Format: original_index pared_order graph6 certificate_rule certificate_target_status certificate_target_label\n")
        for start in range(0, total, batch_size):
            end = min(total - 1, start + batch_size - 1)
            verdict, unresolved, done = _chunk_paths(folder, start, end)
            if not (verdict.is_file() and unresolved.is_file() and done.is_file()):
                raise RuntimeError(f"missing completed chunk for {n}: {start}-{end}")
            with gzip.open(unresolved, "rt", encoding="utf-8") as stream:
                for line in stream:
                    if line.strip():
                        handle.write(line)
    os.replace(temp, target)


def classify_order(n: int, folder: Path, batch_size: int, bound: int) -> None:
    if n not in (9, 10):
        raise ValueError("stream_connected is intended for orders 9 and 10")
    for name in ("chunks", "unresolved_chunks", "completed", "logs"):
        (folder / name).mkdir(parents=True, exist_ok=True)
    total = EXPECTED_COUNTS[n]
    current_start = -1
    rows: list[tuple[int, str, str]] = []
    unresolved_rows: list[str] = []
    skipped = False
    observed = 0

    def finish_chunk(start: int, end: int) -> None:
        if skipped:
            return
        if len(rows) != end - start + 1:
            raise RuntimeError(f"chunk {start}-{end} is incomplete")
        verdict, unresolved, done = _chunk_paths(folder, start, end)
        # Do not trust partial/crashed chunks without an explicit .done marker.
        if done.exists():
            raise RuntimeError("completed chunk unexpectedly modified")
        verdict_tmp = verdict.with_suffix(".partial")
        unresolved_tmp = unresolved.with_suffix(".partial")
        buf = io.StringIO(newline="")
        writer = csv.writer(buf, delimiter="\t", lineterminator="\n")
        buf.write("# index\tverdict\treason\n")
        writer.writerows(rows)
        _write_gzip(verdict_tmp, buf.getvalue().encode("utf-8"))
        _write_gzip(unresolved_tmp, "".join(unresolved_rows).encode("utf-8"))
        os.replace(verdict_tmp, verdict)
        os.replace(unresolved_tmp, unresolved)
        done_tmp = done.with_suffix(".partial")
        done_tmp.write_text(f"{start}\t{end}\n", encoding="ascii")
        os.replace(done_tmp, done)
        log = folder / "logs" / (done.stem + ".log")
        log.write_text(
            f"order={n} indices={start}-{end} classified={len(rows)} "
            f"indeterminate={len(unresolved_rows)} bound={bound}\n",
            encoding="utf-8",
        )
        print(f"n={n} indices={start}-{end} completed; unresolved={len(unresolved_rows)}", flush=True)

    for index, graph in enumerate(connected_graphs(n)):
        observed += 1
        start = (index // batch_size) * batch_size
        end = min(total - 1, start + batch_size - 1)
        if start != current_start:
            if current_start >= 0:
                previous_end = min(total - 1, current_start + batch_size - 1)
                finish_chunk(current_start, previous_end)
            current_start = start
            rows = []
            unresolved_rows = []
            verdict, unresolved, done = _chunk_paths(folder, start, end)
            skipped = done.exists()
            if skipped:
                if not verdict.is_file() or not unresolved.is_file():
                    raise RuntimeError(f"corrupt completion marker at {start}-{end}")
            else:
                # Discard incomplete files before replaying that chunk.
                verdict.unlink(missing_ok=True)
                unresolved.unlink(missing_ok=True)
                print(f"n={n}: classifying connected indices {start}-{end} / {total}", flush=True)
        if skipped:
            continue
        result = classify_clique_behavior(graph, bound=bound)
        rows.append((index, result.verdict.name, result.reason))
        if result.verdict is Verdict.INDETERMINATE:
            pared = nx.convert_node_labels_to_integers(result.pared_graph)
            cert = result.certificate
            rule = cert.rule if cert is not None else "-"
            status = (cert.target_status or "-") if cert is not None else "-"
            label = (cert.target_label or "-") if cert is not None else "-"
            unresolved_rows.append(
                f"{index} {pared.order()} {graph6(pared)} {rule} {status} {label}\n"
            )
    if observed != total:
        raise RuntimeError(f"order {n}: expected {total} graphs, found {observed}")
    if current_start >= 0:
        finish_chunk(current_start, total - 1)
    write_unresolved_cohort(folder, n, total, batch_size)
    print(f"Order {n} completely recorded with {total} connected graphs", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--order", type=int, required=True, choices=(9, 10))
    ap.add_argument("--folder", type=Path, required=True)
    ap.add_argument("--batch-size", type=int, required=True)
    ap.add_argument("--bound", type=int, required=True)
    args = ap.parse_args()
    if args.batch_size <= 0 or args.bound <= 0:
        ap.error("batch size and bound must be positive")
    classify_order(args.order, args.folder, args.batch_size, args.bound)


if __name__ == "__main__":
    main()
