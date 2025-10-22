#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

# Activate venv if present
if [ -d ".venv" ]; then
  echo "[INFO] Activating venv..."
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

# Load .env.local if present
if [ -f ".env.local" ]; then
  echo "[INFO] Loading .env.local"
  export $(grep -v '^\s*#' .env.local | xargs) || true
fi

MODE="${1:-}"
if [ -z "${MODE}" ]; then
  echo "Usage: bash kucoin-bot-run.sh --smoke | --once | --loop"
  exit 1
fi

echo "[INFO] Python: $(python --version)"
echo "[INFO] ENV=${ENV:-paper}"
echo "[INFO] Telegram token: $([ -n "${TELEGRAM_BOT_TOKEN:-}" ] && echo set || echo missing)"
echo "[INFO] Telegram chat:  $([ -n "${TELEGRAM_CHAT_ID:-}" ] && echo set || echo missing)"

case "${MODE}" in
  --smoke)
    echo "[INFO] Running SMOKE..."
    python -m src.main --smoke
    ;;
  --once)
    echo "[INFO] Running ONCE..."
    python -m src.main --once
    ;;
  --loop)
    echo "[INFO] Running LOOP (paper if ENV=paper)..."
    python -m src.main
    ;;
  *)
    echo "Unknown mode: ${MODE}"
    exit 1
    ;;
esac
