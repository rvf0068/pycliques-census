#!/usr/bin/env bash
# Deliberately upgrade pycliques-project to the latest origin/main (or an
# explicit Git revision), then reinstall and pin that exact revision.
# Existing result manifests remain pinned to their previous revision.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$ROOT/.deps/pycliques-project"
PIN_FILE="$ROOT/config/pycliques_commit.txt"
export PATH="$HOME/.local/bin:$PATH"
if [[ ! -d "$SOURCE/.git" ]]; then
  bash "$ROOT/scripts/bootstrap.sh"
fi
if [[ -n "$(git -C "$SOURCE" status --porcelain)" ]]; then
  echo "Upstream source checkout has uncommitted modifications; refusing update" >&2
  exit 2
fi
OLD_PIN="$(tr -d '[:space:]' < "$PIN_FILE")"
git -C "$SOURCE" fetch --no-tags origin main
TARGET="${1:-origin/main}"
NEW_PIN="$(git -C "$SOURCE" rev-parse --verify "$TARGET^{commit}")"
if [[ "$NEW_PIN" == "$OLD_PIN" ]]; then
  echo "Already pinned to $NEW_PIN"
  exit 0
fi
# Atomic pin update and safe rollback on installation failure.
restore() {
  trap - ERR
  echo "Update failed; restoring pinned revision $OLD_PIN" >&2
  printf '%s\n' "$OLD_PIN" > "$PIN_FILE"
  git -C "$SOURCE" checkout --detach "$OLD_PIN" || true
  bash "$ROOT/scripts/bootstrap.sh" || true
}
trap restore ERR
git -C "$SOURCE" checkout --detach "$NEW_PIN"
printf '%s\n' "$NEW_PIN" > "$PIN_FILE"
bash "$ROOT/scripts/bootstrap.sh"
trap - ERR
printf '\nUpdated pycliques-project: %s -> %s\n' "$OLD_PIN" "$NEW_PIN"
printf 'Commit the updated config/pycliques_commit.txt.\n'
printf 'A new post-stage may use this revision while completed stages retain their original pins.\n'
printf 'Never change revisions mid-stage or rerun an old stage in place after an upgrade.\n'
printf 'The initial census still requires a NEW RUN_DIR if its parameters or revision change.\n'
