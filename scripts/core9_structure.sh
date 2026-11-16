#!/usr/bin/env bash
# Dedicated read-only structural investigation of the 29 unresolved core9 graphs.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[[ -x "$ROOT/.venv-v3/bin/python" ]] || {
  echo "Run bash scripts/bootstrap_v3.sh to prepare the pinned v3 environment" >&2
  exit 2
}
if (( $# > 1 )); then
  echo "Usage: bash scripts/core9_structure.sh [plan|next|all|verify|BATCH_INDEX]" >&2
  exit 2
fi
exec "$ROOT/.venv-v3/bin/python" "$ROOT/scripts/core9_structure.py" "${1:-next}"
