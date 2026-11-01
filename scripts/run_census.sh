#!/usr/bin/env bash
# Connected unlabeled graphs ONLY. Initial verification: orders 1--8.
# Later: MIN_ORDER=9 MAX_ORDER=9 RUN_DIR=runs/order9-bound30 bash scripts/run_census.sh
# Later: MIN_ORDER=10 MAX_ORDER=10 BATCH_SIZE=5000 RUN_DIR=runs/order10-bound30 bash scripts/run_census.sh
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MIN_ORDER="${MIN_ORDER:-1}"
MAX_ORDER="${MAX_ORDER:-8}"
BATCH_SIZE="${BATCH_SIZE:-500}"
CLIQUE_BOUND="${CLIQUE_BOUND:-30}"
RUN_DIR="${RUN_DIR:-$ROOT/runs/baseline-through8-bound30}"
if ! [[ "$MIN_ORDER" =~ ^([1-9]|10)$ && "$MAX_ORDER" =~ ^([1-9]|10)$ \
     && "$BATCH_SIZE" =~ ^[1-9][0-9]*$ && "$CLIQUE_BOUND" =~ ^[1-9][0-9]*$ ]]; then
  echo "MIN_ORDER and MAX_ORDER must be 1..10; BATCH_SIZE and CLIQUE_BOUND must be positive" >&2
  exit 2
fi
if (( MIN_ORDER > MAX_ORDER )); then
  echo "MIN_ORDER cannot exceed MAX_ORDER" >&2
  exit 2
fi
RUN_DIR="$(mkdir -p "$RUN_DIR" && cd "$RUN_DIR" && pwd)"
export PATH="$HOME/.local/bin:$PATH"
# Bootstrap is safe to repeat; it installs the exact pinned upstream version.
bash "$ROOT/scripts/bootstrap.sh"
SOURCE="$ROOT/.deps/pycliques-project"
PYTHON="$SOURCE/.venv/bin/python"
CLASSIFY="$SOURCE/.venv/bin/small-behavior"
"$PYTHON" "$ROOT/scripts/provenance.py" --root "$ROOT" --run-dir "$RUN_DIR" \
  --min-order "$MIN_ORDER" --max-order "$MAX_ORDER" --batch-size "$BATCH_SIZE" \
  --bound "$CLIQUE_BOUND"

# This history contains only research commands and settings (not arbitrary secrets).
mkdir -p "$ROOT/history"
if [[ ! -e "$ROOT/history/experiment_commands.tsv" ]]; then
  printf 'utc_timestamp\tcommand\tmin_order\tmax_order\tbatch_size\tclique_bound\trun_dir\tupstream_sha\n' \
    > "$ROOT/history/experiment_commands.tsv"
fi
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
  "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
  'bash scripts/run_census.sh' "$MIN_ORDER" "$MAX_ORDER" "$BATCH_SIZE" "$CLIQUE_BOUND" \
  "$RUN_DIR" "$(git -C "$SOURCE" rev-parse HEAD)" >> "$ROOT/history/experiment_commands.tsv"

for (( n=MIN_ORDER; n<=MAX_ORDER; n++ )); do
  ORDER_DIR="$RUN_DIR/order$n"
  mkdir -p "$ORDER_DIR/chunks" "$ORDER_DIR/logs"
  # Index inventories are useful and inexpensive through 8. For 9--10 the
  # hashed original graph6 dataset and streamed validation avoid an enormous,
  # redundant index file in Git.
  if (( n <= 8 )) && [[ ! -f "$ORDER_DIR/graph_index.tsv" ]]; then
    "$PYTHON" "$ROOT/scripts/index_graphs.py" --order "$n" --output "$ORDER_DIR/graph_index.tsv"
  fi
  if (( n <= 5 )); then
    if [[ ! -f "$ORDER_DIR/verdicts.tsv" ]]; then
      echo "Order $n: classifying connected small graph types"
      "$PYTHON" "$ROOT/scripts/run_small.py" --order "$n" --bound "$CLIQUE_BOUND" \
        --output "$ORDER_DIR/verdicts.tsv" > "$ORDER_DIR/logs/classify.log" 2>&1
    fi
    continue
  fi
  if (( n >= 9 )); then
    # One traversal of the entire compressed source per invocation, rather
    # than the quadratic rescan cost of repeated CLI --start/--end calls.
    "$PYTHON" "$ROOT/scripts/stream_connected.py" --order "$n" \
      --folder "$ORDER_DIR" --batch-size "$BATCH_SIZE" --bound "$CLIQUE_BOUND"
    continue
  fi
  case "$n" in
    6) TOTAL=112 ;;
    7) TOTAL=853 ;;
    8) TOTAL=11117 ;;
  esac
  for (( start=0; start<TOTAL; start+=BATCH_SIZE )); do
    end=$((start+BATCH_SIZE-1))
    if (( end >= TOTAL )); then end=$((TOTAL-1)); fi
    printf -v CHUNK '%08d-%08d' "$start" "$end"
    OUTPUT="$ORDER_DIR/chunks/$CHUNK.tsv.gz"
    if [[ -f "$OUTPUT" ]]; then
      echo "Order $n, indices $start-$end already completed; skipping"
      continue
    fi
    echo "Order $n: classifying connected graphs $start-$end of $TOTAL"
    TEMP="$ORDER_DIR/chunks/$CHUNK.tsv.partial"
    GZ_TEMP="$OUTPUT.partial"
    rm -f "$TEMP" "$GZ_TEMP"
    # The current small-behavior program updates only the processed index range
    # in the saved unresolved cohort; --no-lookup prevents historical influence.
    "$CLASSIFY" "$n" --bound "$CLIQUE_BOUND" --start "$start" --end "$end" \
      --no-lookup --no-skip-dominated --data-dir "$ORDER_DIR" \
      --output-file "$TEMP" > "$ORDER_DIR/logs/$CHUNK.log" 2>&1
    # -n omits timestamps and file names for stable, commit-friendly gzip bytes.
    gzip -n -c "$TEMP" > "$GZ_TEMP"
    mv "$GZ_TEMP" "$OUTPUT"
    rm -f "$TEMP"
  done
done
"$PYTHON" "$ROOT/scripts/validate.py" --run-dir "$RUN_DIR"
echo "Connected census validated. Commit $RUN_DIR and history/ if desired."
