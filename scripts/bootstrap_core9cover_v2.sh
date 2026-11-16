#!/usr/bin/env bash
# Separate uv dependency checkout for the post-PR14 nine-core covering stage.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIN="$(tr -d '[:space:]' < "$ROOT/config/pycliques_commit_core9cover_v2.txt")"
SRC="$ROOT/.deps/pycliques-project-core9cover-v2"
LINK="$ROOT/.venv-core9cover-v2"
[[ "$PIN" =~ ^[0-9a-f]{40}$ ]] || { echo "Invalid v2 pin" >&2; exit 2; }
export PATH="$HOME/.local/bin:$PATH"
command -v uv >/dev/null || { echo "uv is required" >&2; exit 2; }
if [[ ! -d "$SRC/.git" ]]; then
  mkdir -p "$(dirname "$SRC")"
  git clone --filter=blob:none https://github.com/rvf0068/pycliques-project.git "$SRC"
fi
[[ -z "$(git -C "$SRC" status --porcelain)" ]] || {
  echo "Refusing to alter a dirty core9cover dependency checkout" >&2; exit 2;
}
if [[ "$(git -C "$SRC" rev-parse HEAD)" != "$PIN" ]]; then
  git -C "$SRC" fetch --no-tags origin "$PIN"
  git -C "$SRC" checkout --detach "$PIN"
fi
[[ "$(git -C "$SRC" rev-parse HEAD)" == "$PIN" ]] || exit 3
(cd "$SRC" && uv sync --frozen --no-dev --python 3.11)
if [[ ! -e "$LINK" ]]; then
  ln -s ".deps/pycliques-project-core9cover-v2/.venv" "$LINK"
elif [[ ! -L "$LINK" || "$(readlink "$LINK")" != ".deps/pycliques-project-core9cover-v2/.venv" ]]; then
  echo "Refusing to replace an unrelated virtual environment" >&2
  exit 2
fi
"$LINK/bin/python" - <<'PY'
from pycombtop.covering_divergence_search import _bounded_pair_morphism
from pycliques.clockwork_pairs import clockwork_coaffine_pair
assert callable(_bounded_pair_morphism)
assert clockwork_coaffine_pair(3, 0).graph.number_of_nodes() == 18
print("Independent post-PR14 core9 covering environment ready.")
PY
