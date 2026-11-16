#!/usr/bin/env bash
# Separate post-PR14 nine-core cover searches; never alter historical census.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[[ -x "$ROOT/.venv-core9cover-v2/bin/python" ]] || {
  echo "First run: bash scripts/bootstrap_core9cover_v2.sh" >&2
  exit 2
}
if (( $# > 1 )); then
  echo "Usage: bash scripts/core9cover_v2.sh [plan|next|all|verify|replay|BATCH]" >&2
  exit 2
fi
exec "$ROOT/.venv-core9cover-v2/bin/python" "$ROOT/scripts/core9cover_v2.py" "${1:-next}"
