#!/usr/bin/env bash
# Isolated G1/G2 covering investigation; no historical census mutation.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[[ -x "$ROOT/.venv-core9cover-v2/bin/python" ]] || {
  echo "Run bash scripts/bootstrap_core9cover_v2.sh first" >&2
  exit 2
}
if (( $# > 1 )); then
  echo "Usage: bash scripts/core9iterate_v1.sh [plan|next|all|verify|replay|BATCH]" >&2
  exit 2
fi
exec "$ROOT/.venv-core9cover-v2/bin/python" "$ROOT/scripts/core9iterate_v1.py" "${1:-next}"
