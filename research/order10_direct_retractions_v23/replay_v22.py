"""Replay immutable ten-v22 positive proofs after ten-v23 promotion.

Redirect only the historical verifier's mutable root path to frozen v22.
All graph6, bijections, archived source certificates and old counts unchanged.
"""
from __future__ import annotations

from research.order10_p3_reference_lifts_v22 import verify as v22


def main() -> None:
    v22.CURRENT = v22.V22
    v22.verify_archive()


if __name__ == "__main__":
    main()
