#!/usr/bin/env bash
# Dedicated witness-capable core9 benchmark (historical stages unchanged).
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[[ -x "$ROOT/.venv-v3/bin/python" ]] || {
  echo "Run bash scripts/bootstrap_v3.sh first (separate pinned v3 environment)" >&2
  exit 2
}
if (( $# > 1 )); then
  echo "Usage: bash scripts/core9.sh [plan|next|all|verify|BATCH_INDEX]" >&2
  exit 2
fi
exec "$ROOT/.venv-v3/bin/python" "$ROOT/scripts/core9_benchmark.py" "${1:-next}"
