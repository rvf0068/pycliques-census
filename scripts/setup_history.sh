#!/usr/bin/env bash
# Make interactive Bash command history persistent, visible, and committable.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$ROOT/history"
touch "$ROOT/history/bash_history"
MARKER="# BEGIN PYCLIQUES_CENSUS_PERSISTENT_HISTORY"
if ! grep -Fqx "$MARKER" "$HOME/.bashrc" 2>/dev/null; then
  # Write with absolute workspace path, shell-escaped for spaces.
  printf -v ESCAPED_HISTORY '%q' "$ROOT/history/bash_history"
  cat >> "$HOME/.bashrc" <<EOF
$MARKER
export HISTFILE=$ESCAPED_HISTORY
export HISTSIZE=200000
export HISTFILESIZE=200000
shopt -s histappend
# Persist each interactive command rather than waiting for terminal exit.
case "\$-" in *i*) PROMPT_COMMAND="history -a\${PROMPT_COMMAND:+; \$PROMPT_COMMAND}" ;; esac
# END PYCLIQUES_CENSUS_PERSISTENT_HISTORY
EOF
fi
printf 'Bash history configured at %s\n' "$ROOT/history/bash_history"
