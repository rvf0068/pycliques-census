#!/usr/bin/env bash
# Isolated, pinned environment for the exploratory three-core targeted stage.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PATH="$HOME/.local/bin:$PATH"
command -v uv >/dev/null || { echo "uv is required" >&2; exit 2; }
PIN="$(tr -d '[:space:]' < config/pycliques_commit_core9_three_target_v1.txt)"
[[ "$PIN" =~ ^[0-9a-f]{40}$ ]] || { echo "Invalid core9 target pin" >&2; exit 2; }
SRC="$ROOT/.deps/pycliques-project-core9-three-v1"
LINK="$ROOT/.venv-core9-three-v1"
if [[ ! -d "$SRC/.git" ]]; then
  mkdir -p "$(dirname "$SRC")"
  git clone --filter=blob:none https://github.com/rvf0068/pycliques-project.git "$SRC"
fi
[[ -z "$(git -C "$SRC" status --porcelain)" ]] || {
  echo "Refusing to alter dirty dependency checkout" >&2; exit 2;
}
if [[ "$(git -C "$SRC" rev-parse HEAD)" != "$PIN" ]]; then
  git -C "$SRC" fetch --no-tags origin "$PIN"
  git -C "$SRC" checkout --detach "$PIN"
fi
[[ "$(git -C "$SRC" rev-parse HEAD)" == "$PIN" ]] || exit 3
(cd "$SRC" && uv sync --frozen --no-dev --python 3.11)
if [[ ! -e "$LINK" ]]; then
  ln -s ".deps/pycliques-project-core9-three-v1/.venv" "$LINK"
elif [[ ! -L "$LINK" || "$(readlink "$LINK")" != ".deps/pycliques-project-core9-three-v1/.venv" ]]; then
  echo "Refusing to replace an existing foreign environment" >&2; exit 2
fi
"$LINK/bin/python" - <<'PY'
from pycliques.small import CliqueSequence
from pycliques.targeted_retractions import search_targeted_retractions
from pycliques.retractions import find_special_octahedron_witness
from pycombtop.covering_divergence_search import search_covering_divergence
assert all(callable(x) for x in
           (search_targeted_retractions, find_special_octahedron_witness,
            search_covering_divergence))
print("Separate optimized core9 three-target environment ready")
PY
