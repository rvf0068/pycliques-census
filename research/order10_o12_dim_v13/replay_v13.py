"""Replay the historical order-ten v12 -> v13 O12 certificate under v14.

Only the obsolete assertion that the *current* working root equals v13 is
redirected to the immutable v13 snapshot. All historical hashes, census
rows, graph reconstructions, target checks and full retraction checks
remain those of the original, unchanged v13 verifier.
"""
from pathlib import Path
from unittest.mock import patch

from research.order10_o12_dim_v13 import verify as historical

ORIGINAL = Path.read_bytes


def historical_read(path: Path) -> bytes:
    if path.resolve() == historical.CURRENT.resolve():
        return ORIGINAL(historical.AFTER)
    return ORIGINAL(path)


def main() -> None:
    with patch.object(Path, "read_bytes", historical_read):
        historical.verify()


if __name__ == "__main__":
    main()
