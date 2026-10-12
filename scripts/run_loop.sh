#!/usr/bin/env bash
# Loop continuo Decision Bot (paper opzionale)
# Uso: ./scripts/run_loop.sh [minuti] [--paper]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
MIN="${1:-15}"
EXTRA=()
if [[ "${2:-}" == "--paper" ]] || [[ "${1:-}" == "--paper" ]]; then
  EXTRA+=(--paper)
  [[ "${1:-}" == "--paper" ]] && MIN=15
fi
if [[ -d .venv ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi
exec python -m revolutx_bot decide --loop "$MIN" "${EXTRA[@]}"
