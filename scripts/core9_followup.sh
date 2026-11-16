#!/usr/bin/env bash
# Resumable, pinned nine-core covering/bound/isomorphism follow-ups.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[[ -x "$ROOT/.venv-v3/bin/python" ]] || {
  echo "Prepare pinned witness-capable environment: bash scripts/bootstrap_v3.sh" >&2
  exit 2
}
if (( $# > 1 )); then
  echo "Usage: bash scripts/core9_followup.sh [plan|iso|next|all|verify|BATCH_INDEX]" >&2
  exit 2
fi
exec "$ROOT/.venv-v3/bin/python" "$ROOT/scripts/core9_followup.py" "${1:-next}"
