#!/usr/bin/env bash
# Install an independent, immutable pycliques revision for new order-9 research.
# Intentionally DO NOT modify config/pycliques_commit.txt or the original .venv.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="$ROOT/.deps/pycliques-project-order9"
REV=d6753ac445b57740d90997008aa96830d4fc117c
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null; then
  python3 -m pip install --user 'uv==0.9.26'
fi
if [[ ! -d "$TARGET/.git" ]]; then
  mkdir -p "$(dirname "$TARGET")"
  git clone --filter=blob:none https://github.com/rvf0068/pycliques-project.git "$TARGET"
fi
if [[ -n "$(git -C "$TARGET" status --porcelain)" ]]; then
  echo "Refusing dirty order-9 dependency checkout" >&2
  exit 2
fi
git -C "$TARGET" fetch --no-tags origin "$REV"
git -C "$TARGET" checkout --detach "$REV"
if [[ "$(git -C "$TARGET" rev-parse HEAD)" != "$REV" ]]; then
  echo "Incorrect independent order-9 dependency revision" >&2
  exit 2
fi
(cd "$TARGET" && uv sync --frozen --python 3.11 --no-dev)
"$TARGET/.venv/bin/python" - <<'PY'
import pycliques, pycombtop, pyg6data, networkx
print("Isolated order-9 environment:", pycliques.__file__)
print("NetworkX:", networkx.__version__)
PY
