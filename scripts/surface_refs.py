"""Load experimentally conjectured surface references into the classifier registry."""

from pathlib import Path

import networkx as nx
from pycliques.small import ReferenceStatus, register_reference_graph
from pycliques.surfaces import is_surface

ROOT = Path(__file__).resolve().parents[1]
SURFACE_FILE = ROOT / "config" / "conjectured_surfaces_order9.tsv"


def load_surface_references() -> int:
    if not SURFACE_FILE.is_file():
        raise ValueError("Order-9 surface registry is absent: finish stage 9 bound60 first")
    count = 0
    indices: set[int] = set()
    for line in SURFACE_FILE.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 2 or not parts[0].isdigit():
            raise ValueError(f"Malformed surface reference entry: {line!r}")
        index = int(parts[0])
        if index in indices:
            raise ValueError(f"Duplicate surface source index: {index}")
        indices.add(index)
        graph6 = parts[1]
        graph = nx.from_graph6_bytes(graph6.encode("ascii"))
        if len(graph) != 9 or not nx.is_connected(graph) or not is_surface(graph):
            raise ValueError(f"Non-surface graph in registered reference entry {index}")
        register_reference_graph(graph, status=ReferenceStatus.CONJECTURED, label=graph6)
        count += 1
    return count
