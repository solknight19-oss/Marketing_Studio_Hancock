#!/bin/bash
# Opens Dave in a browser that can support voice capture better than the Codex in-app browser.

cd "$(dirname "$0")"

PORT="${PORT:-8772}"
HOST="${HOST:-127.0.0.1}"
APP_DATA_DIR="${APP_DATA_DIR:-$PWD/app_data}"
export HOST PORT APP_DATA_DIR
export DAVE_LOCAL_AUTO_LOGIN=1
export DAVE_ELEVENLABS_VOICE_ID="${DAVE_ELEVENLABS_VOICE_ID:-}"
export DAVE_ELEVENLABS_VOICE_NAME="${DAVE_ELEVENLABS_VOICE_NAME:-Jarvis 1.1 Voice}"
export DAVE_ELEVENLABS_FALLBACK_VOICE_ID="${DAVE_ELEVENLABS_FALLBACK_VOICE_ID:-6Lopt6P83rUsEz3TeM5C}"
export DAVE_ELEVENLABS_FALLBACK_VOICE_NAME="${DAVE_ELEVENLABS_FALLBACK_VOICE_NAME:-Jarvis}"
if [ -z "$ELEVENLABS_API_KEY" ] && [ -s "../Hancock_CoPilot/elevenlabs_key.txt" ]; then
  export ELEVENLABS_API_KEY="$(cat ../Hancock_CoPilot/elevenlabs_key.txt)"
fi
if [ -z "$OPENAI_API_KEY" ] && [ -s "../Hancock_CoPilot/openai_key.txt" ]; then
  export OPENAI_API_KEY="$(cat ../Hancock_CoPilot/openai_key.txt)"
fi

LOG_FILE="$APP_DATA_DIR/dave_server.log"
URL="http://127.0.0.1:${PORT}/dave-local"
HEALTH_URL="http://127.0.0.1:${PORT}/healthz"

mkdir -p "$APP_DATA_DIR"

open_voice_browser() {
  open -a "Google Chrome" "$1" 2>/dev/null || open -a "Safari" "$1" 2>/dev/null || open "$1"
}

dave_ready() {
  python3 - "$HEALTH_URL" <<'PY' >/dev/null 2>&1
import json, sys, urllib.request
with urllib.request.urlopen(sys.argv[1], timeout=2) as response:
    data = json.loads(response.read().decode("utf-8"))
dave = data.get("dave") or {}
raise SystemExit(0 if dave.get("interaction_version") == "dave_elevenlabs_stt_v8" else 1)
PY
}

stop_stale_port() {
  PIDS="$(lsof -tiTCP:${PORT} -sTCP:LISTEN 2>/dev/null || true)"
  if [ -n "$PIDS" ]; then
    echo "Restarting Dave on port $PORT."
    kill $PIDS 2>/dev/null || true
    sleep 2
  fi
}

echo "Opening Dave Voice Mode..."
echo "URL: $URL"
echo "Log: $LOG_FILE"

if curl -s "$HEALTH_URL" >/dev/null 2>&1; then
  if dave_ready; then
    open_voice_browser "$URL"
    exit 0
  fi
  stop_stale_port
fi

nohup python3 -u server.py >> "$LOG_FILE" 2>&1 &

for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  if curl -s "$HEALTH_URL" >/dev/null 2>&1; then
    open_voice_browser "$URL"
    echo "Dave Voice Mode is online."
    exit 0
  fi
  sleep 1
done

echo "Dave did not come online. Recent log:"
tail -40 "$LOG_FILE"
exit 1
