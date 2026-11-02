#!/usr/bin/env bash
# Run the pinned C10 post-pass and refresh the root working list on every exit.
# The original postpass module is unchanged, preserving existing source hashes.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$ROOT/.venv/bin/python"
RUN_DIR="$ROOT/runs/order9-bound30-after-clockwork-fix"
OUTPUT_DIR=""
ARGS=("$@")

for ((i=0; i<${#ARGS[@]}; i++)); do
  case "${ARGS[$i]}" in
    --run-dir)
      (( i+1 < ${#ARGS[@]} )) || { echo "--run-dir requires a value" >&2; exit 2; }
      RUN_DIR="${ARGS[$((i+1))]}"
      i=$((i+1))
      ;;
    --output-dir)
      (( i+1 < ${#ARGS[@]} )) || { echo "--output-dir requires a value" >&2; exit 2; }
      OUTPUT_DIR="${ARGS[$((i+1))]}"
      i=$((i+1))
      ;;
  esac
done

if (( ${#ARGS[@]} == 0 )); then
  ARGS=(--run-dir "$RUN_DIR")
fi

refresh() {
  local code=$?
  trap - EXIT
  echo "Refreshing root indeterminate_order_9.txt from saved post-pass records..."
  if [[ -n "$OUTPUT_DIR" ]]; then
    "$PYTHON" "$ROOT/postpasses/refresh_indeterminate_order9.py" \
      --run-dir "$RUN_DIR" --postpass-dir "$OUTPUT_DIR" || {
        echo "Root unresolved list could not be refreshed" >&2
        if (( code == 0 )); then code=1; fi
      }
  else
    "$PYTHON" "$ROOT/postpasses/refresh_indeterminate_order9.py" \
      --run-dir "$RUN_DIR" || {
        echo "Root unresolved list could not be refreshed" >&2
        if (( code == 0 )); then code=1; fi
      }
  fi
  exit "$code"
}
trap refresh EXIT

"$PYTHON" "$ROOT/postpasses/clique_retract_comp_c10.py" "${ARGS[@]}"
