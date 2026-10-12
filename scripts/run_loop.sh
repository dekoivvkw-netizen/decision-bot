#!/usr/bin/env bash
# Loop continuo Decision Bot
# Uso:
#   ./scripts/run_loop.sh
#   ./scripts/run_loop.sh 15 --paper
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MIN=15
PAPER=0
for a in "$@"; do
  case "$a" in
    --paper) PAPER=1 ;;
    *) MIN="$a" ;;
  esac
done

if [[ -d .venv ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

if [[ "$PAPER" -eq 1 ]]; then
  exec python -m revolutx_bot decide --paper --loop "$MIN"
else
  exec python -m revolutx_bot decide --loop "$MIN"
fi
