#!/usr/bin/env bash
# Single entry point for each reproducible census stage.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PATH="$HOME/.local/bin:$PATH"

if [[ "${1:-}" == baseline && $# -eq 1 ]]; then
  .venv/bin/python -c 'import sys; sys.path.insert(0, "scripts"); from staged import check_baseline; check_baseline()'
  exit 0
fi

if (( $# != 2 )) || [[ ! "${1:-}" =~ ^(9|10)$ ]]; then
  echo "Usage: bash scripts/stage.sh baseline | {9|10} {initial|c10|bound60|homotopy|bound70}" >&2
  exit 2
fi

ORDER="$1"
STAGE="$2"
case "$ORDER/$STAGE" in
  9/initial|9/c10|9/bound60|10/initial|10/c10|10/homotopy|10/bound70) ;;
  *) echo "Unsupported stage $ORDER/$STAGE" >&2; exit 2 ;;
esac

if [[ "$STAGE" == initial ]]; then
  .venv/bin/python -c 'import sys; sys.path.insert(0, "scripts"); from staged import check_baseline; check_baseline()'
  if [[ "$ORDER" == 10 ]]; then
    [[ -f config/conjectured_surfaces_order9.tsv && -f runs/order9/bound60/summary.json ]] || {
      echo "Finish order 9 through bound60 (including surface registry) before order 10." >&2
      exit 1
    }
  fi
  BATCH=10000
  if [[ "$ORDER" == 10 ]]; then BATCH=5000; fi
  MIN_ORDER="$ORDER" MAX_ORDER="$ORDER" BATCH_SIZE="$BATCH" CLIQUE_BOUND=30 \
    RUN_DIR="$ROOT/runs/order$ORDER/initial" bash scripts/run_census.sh
  .venv/bin/python scripts/staged.py "$ORDER" refresh
  exit 0
fi

set +e
.venv/bin/python scripts/staged.py "$ORDER" "$STAGE"
status=$?
set -e
# Preserve the working cohort even when interrupted after completed records.
.venv/bin/python scripts/staged.py "$ORDER" refresh
exit "$status"
