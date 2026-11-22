"""Independent unseeded coaffine cross-check using merged pycliques PR #36.

This does NOT enumerate octahedral targets. It searches all coaffine weak
endomorphisms via the native C++17 solver, whose completeness for ordinary
octahedral retractions follows from f = inclusion * antipode * retraction.
Only an EXHAUSTED status is accepted as a negative certificate.
"""
from __future__ import annotations

import pycliques as pc

from verify import SOURCES, clique_graph, completely_pared, source_p3


def exclude(graph, description: str) -> None:
    outcome = pc.find_octahedral_retraction_coaffine(
        graph,
        min_dimension=3,
        max_states=500_000,
        time_limit=60,
        backend="native",
    )
    if outcome.status is not pc.RetractionSearchStatus.EXHAUSTED:
        raise AssertionError(
            f"{description}: need EXHAUSTED, received {outcome.status.name}, "
            f"states={outcome.states_explored}"
        )
    print(
        f"PASS {description}: EXHAUSTED after {outcome.states_explored} states, "
        f"{outcome.arc_revisions} arc revisions",
        flush=True,
    )


def main() -> None:
    if not __debug__:
        raise RuntimeError("Optimized Python bypasses proof-critical assertions")

    from verify import check_frozen_v17

    check_frozen_v17()
    print(f"Built verified-native source at: {pc.build_coaffine_native()}", flush=True)

    for index in sorted(SOURCES):
        graph = source_p3(SOURCES[index])
        exclude(graph, f"McKay {index} P3")

    third = source_p3(SOURCES[10803453])
    fourth = completely_pared(clique_graph(third))
    if (len(fourth), fourth.number_of_edges()) != (60, 1339):
        raise AssertionError("Unexpected McKay 10803453 P4 structure")
    exclude(fourth, "McKay 10803453 P4")
    print("PASS: all seven independent native coaffine exclusions", flush=True)


if __name__ == "__main__":
    main()
