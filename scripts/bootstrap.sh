#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$ROOT/.deps/pycliques-project"
PIN="$(tr -d '[:space:]' < "$ROOT/config/pycliques_commit.txt")"
if [[ ! "$PIN" =~ ^[0-9a-f]{40}$ ]]; then
  echo "Expected a 40-digit Git SHA in config/pycliques_commit.txt" >&2
  exit 2
fi
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null || [[ "$(uv --version)" != 'uv 0.9.26' ]]; then
  python3 -m pip install --user --upgrade 'uv==0.9.26'
fi
if [[ ! -d "$SOURCE/.git" ]]; then
  mkdir -p "$(dirname "$SOURCE")"
  git clone --filter=blob:none https://github.com/rvf0068/pycliques-project.git "$SOURCE"
fi
if [[ -n "$(git -C "$SOURCE" status --porcelain)" ]]; then
  echo "Refusing to modify a dirty dependency checkout at $SOURCE" >&2
  exit 2
fi
if [[ "$(git -C "$SOURCE" rev-parse HEAD)" != "$PIN" ]]; then
  git -C "$SOURCE" fetch --no-tags origin "$PIN"
  git -C "$SOURCE" checkout --detach "$PIN"
fi
if [[ "$(git -C "$SOURCE" rev-parse HEAD)" != "$PIN" ]]; then
  echo "Pinned dependency commit mismatch" >&2
  exit 3
fi
(
 cd "$SOURCE"
 uv sync --frozen --no-dev --python 3.11
)
"$SOURCE/.venv/bin/python" - <<'PY'
import networkx, pycliques, pyg6data
print('Environment ready: NetworkX', networkx.__version__)
print('Pycliques module:', pycliques.__file__)
print('Pyg6data module:', pyg6data.__file__)
PY

# Expose the installed packages and CLIs as the Codespace's default Python.
# The symlink is ignored by Git, while the dependency revision is tracked.
if [[ ! -e "$ROOT/.venv" ]]; then
  ln -s ".deps/pycliques-project/.venv" "$ROOT/.venv"
elif [[ ! -L "$ROOT/.venv" ]]; then
  echo "Refusing to replace an existing non-symlink $ROOT/.venv" >&2
  exit 2
fi
"$ROOT/.venv/bin/python" -c 'import pycombtop; print("pycombtop installed:", pycombtop.__file__)'
