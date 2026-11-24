"""Pin all five P4 reference graphs to historical *complete* O6/O12 proofs.

These immutable Git blob checks and original graph6 provenance prevent
a self-consistent but unproved change to the reference dictionaries.
Both old archives carry complete map images and labeled host digests.
The historical O6/O12 proof-replay workflow separately reconstructs
and validates the complete source-to-octahedron retractions.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT / "indeterminate_order_10_v11.txt"
O6 = ROOT / "research/order10_fourth_oct_v1/o6_certificates.json"
O12 = ROOT / "research/order10_fourth_oct_v1/o12_certificates.json"

PINNED_BLOBS = {
    ORIGINAL: "34023e9323945c4a6e5e1249c37ba955ba62473f",
    O6: "ea336204cf97c5f86b29afd802daac50fa20d3cc",
    O12: "b94f89ad8061b310dc615331867c8b6d91a75fd5",
}

# (source graph6, pared-fourth vertices, edges, historical labeled
#  host graph6 SHA-256, induced octahedral dimension).
# Digests refer to *historical certificate labeling*, which need not
# coincide with the independent sorted-facet labeling used in this pilot.
PINNED_REFERENCES = {
    10223405: (
        "ICXnRi^uo", 182, 14298,
        "737598a59fabfa22ab95c05581290a2ded7b5f5a0d3ea15422b14f522f55f68b",
        12,
    ),
    10775850: (
        "ICpVUjx|_", 188, 15083,
        "1d22f6ffb2bb8b1fbe0b7578ce20c1bc086b78b445fec0f17757a27cf92ca000",
        12,
    ),
    10223467: (
        "ICXnRjZmo", 151, 8413,
        "86d0ce1e43a522f23971a2c3d42d316160cfa4412ed684475cade8c2cef0e4af",
        6,
    ),
    11104269: (
        "ICpdupvZo", 160, 9258,
        "b8fd6aa3c03c5961da44f83274961c846205348f7acec21caef6fd61236c160d",
        6,
    ),
    11563706: (
        "IEhfe^{zO", 159, 9276,
        "2f62ea23b2522f0e03e1c893785eaa799011741cee86ff2a8f8ee101d88f7be4",
        6,
    ),
}

REFERENCE_G6 = {index: item[0] for index, item in PINNED_REFERENCES.items()}
REFERENCE_DIMENSIONS = {
    index: (item[1], item[2])
    for index, item in PINNED_REFERENCES.items()
}


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError(reason)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def check_reference_provenance() -> None:
    """Match every search reference to a frozen published O6/O12 full map."""
    for path, expected in PINNED_BLOBS.items():
        require(path.is_file() and git_blob(path.read_bytes()) == expected,
                f"Historical reference proof/source Git blob changed: {path.name}")

    originals = {}
    for line in ORIGINAL.read_text(encoding="ascii").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        require(len(parts) == 6, "Malformed historical original row")
        originals[int(parts[0])] = parts

    o6 = json.loads(O6.read_text(encoding="utf-8"))
    o12 = json.loads(O12.read_text(encoding="utf-8"))
    require(o6["schema"] == o12["schema"] == 1 and
            o6["source"] == o12["source"] == ORIGINAL.name,
            "Historical certificate schema or source has changed")
    require(len(o6["proofs"]) == 3 and len(o12["proofs"]) == 2,
            "Wrong number of historical positive retraction certificates")

    all_proofs = {}
    for dimension, data in ((6, o6), (12, o12)):
        for cert in data["proofs"]:
            index = cert["index"]
            require(index not in all_proofs,
                    "Repeated historical divergent reference index")
            all_proofs[index] = (dimension, cert)
    require(set(all_proofs) == set(PINNED_REFERENCES) ==
            set(REFERENCE_G6) == set(REFERENCE_DIMENSIONS),
            "The five search references differ from the complete proof set")

    for index, (graph6, order, edges, host_sha, dimension) in (
        PINNED_REFERENCES.items()
    ):
        require(REFERENCE_G6[index] == graph6 and
                REFERENCE_DIMENSIONS[index] == (order, edges),
                f"Uncertified reference graph6/dimensions substituted: {index}")
        require(originals.get(index) ==
                [str(index), "10", graph6, "-", "-", "-"],
                f"Reference {index} is not the frozen original McKay source")
        historical_dimension, cert = all_proofs[index]
        require(historical_dimension == dimension and
                cert["source_graph6"] == graph6 and
                cert["host_sha256"] == host_sha,
                f"Reference {index} differs from certified historical host digest")
        if dimension == 6:
            require(cert["K4_pared"] == [order, edges],
                    f"Historical O6 source {index} dimensions changed")
        else:
            require((cert["k4_order"], cert["k4_edges"], cert["depth"])
                    == (order, edges, 4),
                    f"Historical O12 source {index} dimensions changed")
        pairs = cert["pairs"]
        endpoints = [v for pair in pairs for v in pair]
        require(len(pairs) == dimension and
                len(endpoints) == len(set(endpoints)) == 2 * dimension and
                all(isinstance(v, int) and 0 <= v < order for v in endpoints),
                f"Malformed historic O{dimension} target for {index}")
        images = list(base64.b64decode(cert["images_b64"], validate=True))
        require(len(images) == order and
                set(images) == set(endpoints) and
                all(images[v] == v for v in endpoints),
                f"Historical reference {index} lacks a full target-fixed retraction")

    print("PASS: all five reference McKay graph6 strings, O6/O12"
          " target dimensions, complete image lists and original host SHA-256"
          " digests are pinned to three immutable historical Git blobs.",
          flush=True)


if __name__ == "__main__":
    check_reference_provenance()
