#!/usr/bin/env bash
# One isolated pinned environment for the general targeted-retraction postpass.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PATH="$HOME/.local/bin:$PATH"
command -v uv >/dev/null || { echo "uv is required" >&2; exit 2; }
PIN="$(tr -d '[:space:]' < config/pycliques_commit_targeted_v3.txt)"
[[ "$PIN" =~ ^[0-9a-f]{40}$ ]] || { echo "Invalid targeted pin" >&2; exit 2; }
SRC="$ROOT/.deps/pycliques-project-targeted-v3"
LINK="$ROOT/.venv-targeted-v3"
if [[ ! -d "$SRC/.git" ]]; then
  mkdir -p "$(dirname "$SRC")"
  git clone --filter=blob:none https://github.com/rvf0068/pycliques-project.git "$SRC"
fi
[[ -z "$(git -C "$SRC" status --porcelain)" ]] || {
  echo "Targeted dependency checkout is dirty" >&2; exit 2;
}
if [[ "$(git -C "$SRC" rev-parse HEAD)" != "$PIN" ]]; then
  git -C "$SRC" fetch --no-tags origin "$PIN"
  git -C "$SRC" checkout --detach "$PIN"
fi
[[ "$(git -C "$SRC" rev-parse HEAD)" == "$PIN" ]] || exit 3
(cd "$SRC" && uv sync --frozen --no-dev --python 3.11)
if [[ ! -e "$LINK" ]]; then
  ln -s ".deps/pycliques-project-targeted-v3/.venv" "$LINK"
elif [[ ! -L "$LINK" || "$(readlink "$LINK")" != ".deps/pycliques-project-targeted-v3/.venv" ]]; then
  echo "Refusing to overwrite a foreign environment" >&2; exit 2
fi
"$LINK/bin/python" - <<'PY'
from pycliques import search_targeted_retractions
from pycombtop.bounded_betti import bounded_reduced_betti_mod2
assert callable(search_targeted_retractions)
assert callable(bounded_reduced_betti_mod2)
print("Targeted retraction environment ready.")
PY
