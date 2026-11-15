#!/usr/bin/env bash
# Install a separate uv environment for the v3 census; never change historical .venv.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$ROOT/.deps/pycliques-project-v3"
PIN="$(tr -d '[:space:]' < "$ROOT/config/pycliques_commit_v3.txt")"
[[ "$PIN" =~ ^[0-9a-f]{40}$ ]] || { echo "Invalid v3 upstream pin" >&2; exit 2; }
export PATH="$HOME/.local/bin:$PATH"
command -v uv >/dev/null || { echo "Install uv first" >&2; exit 2; }
if [[ ! -d "$SOURCE/.git" ]]; then
  mkdir -p "$(dirname "$SOURCE")"
  git clone --filter=blob:none https://github.com/rvf0068/pycliques-project.git "$SOURCE"
fi
[[ -z "$(git -C "$SOURCE" status --porcelain)" ]] || {
  echo "Refusing to change a dirty v3 dependency checkout" >&2; exit 2;
}
if [[ "$(git -C "$SOURCE" rev-parse HEAD)" != "$PIN" ]]; then
  git -C "$SOURCE" fetch --no-tags origin "$PIN"
  git -C "$SOURCE" checkout --detach "$PIN"
fi
[[ "$(git -C "$SOURCE" rev-parse HEAD)" == "$PIN" ]] || exit 3
(cd "$SOURCE" && uv sync --frozen --no-dev --python 3.11)
if [[ ! -e "$ROOT/.venv-v3" ]]; then
  ln -s ".deps/pycliques-project-v3/.venv" "$ROOT/.venv-v3"
elif [[ ! -L "$ROOT/.venv-v3" ]]; then
  echo "Not replacing an existing real .venv-v3 directory" >&2
  exit 2
fi
"$ROOT/.venv-v3/bin/python" - <<'PY'
from pycliques import retractions
import pycombtop, pyg6data
assert hasattr(retractions, "verify_special_octahedron_witness")
print("Separate v3 environment ready (historical .venv unchanged).")
PY
