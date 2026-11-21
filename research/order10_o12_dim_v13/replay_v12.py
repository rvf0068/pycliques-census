"""Read-only compatibility replay for archived v12 proof after v13 became current.

Only redirects historical reads of the former current-root pathname;
never modifies working files or immutable snapshots.
"""
from pathlib import Path
from unittest.mock import patch
from research.order10_fourth_oct_v1 import verify_v12

ORIGINAL = Path.read_bytes


def historical_read_bytes(path):
    if path == verify_v12.CURRENT:
        return ORIGINAL(verify_v12.AFTER)
    return ORIGINAL(path)


if __name__ == "__main__":
    with patch.object(Path, "read_bytes", historical_read_bytes):
        verify_v12.main()
