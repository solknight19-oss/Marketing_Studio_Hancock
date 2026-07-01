#!/bin/bash
# Start the Hancock service locally and open Dave's command briefing.

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
TOKEN_FILE="$APP_DATA_DIR/.dave_desktop_token"
if [ ! -s "$TOKEN_FILE" ]; then
  python3 - <<'PY' "$TOKEN_FILE"
import pathlib, secrets, sys
path = pathlib.Path(sys.argv[1])
path.write_text(secrets.token_urlsafe(36), encoding="utf-8")
path.chmod(0o600)
PY
fi
DAVE_TOKEN="$(cat "$TOKEN_FILE")"
URL="http://127.0.0.1:${PORT}/dave-local"
HEALTH_URL="http://127.0.0.1:${PORT}/healthz"

mkdir -p "$APP_DATA_DIR"

open_url() {
  open -a "Google Chrome" "$1" 2>/dev/null || open -a "Safari" "$1" 2>/dev/null || open "$1" 2>/dev/null || python3 -m webbrowser "$1"
}

dave_ready() {
  python3 - "$HEALTH_URL" <<'PY' >/dev/null 2>&1
import json, sys, urllib.request
with urllib.request.urlopen(sys.argv[1], timeout=2) as response:
    data = json.loads(response.read().decode("utf-8"))
dave_voice = data.get("dave_voice") or {}
dave = data.get("dave") or {}
ready = (
    dave_voice.get("configured")
    and dave_voice.get("preferred_voice") == "Jarvis 1.1 Voice"
    and dave.get("ui_version") == "cockpit_v2"
    and dave.get("interaction_version") == "dave_elevenlabs_stt_v8"
)
raise SystemExit(0 if ready else 1)
PY
}

stop_stale_port() {
  PIDS="$(lsof -tiTCP:${PORT} -sTCP:LISTEN 2>/dev/null || true)"
  if [ -n "$PIDS" ]; then
    echo "Restarting stale Dave service on port $PORT."
    kill $PIDS 2>/dev/null || true
    sleep 2
  fi
}

echo "Starting Dave command briefing..."
echo "URL: $URL"
echo "Log: $LOG_FILE"
echo "If Dave asks you to sign in, local first-run credentials are in: $APP_DATA_DIR/INITIAL_LOGINS.md"
{
  echo ""
  echo "==== Dave launcher $(date '+%Y-%m-%d %H:%M:%S') ===="
  echo "URL: $URL"
  echo "APP_DATA_DIR: $APP_DATA_DIR"
  echo "TOKEN_PREFIX: ${DAVE_TOKEN:0:8}"
} >> "$LOG_FILE"

if curl -s "$HEALTH_URL" >/dev/null 2>&1; then
  if dave_ready; then
    echo "Hancock service is already running. Opening Dave."
    open_url "$URL"
    exit 0
  fi
  stop_stale_port
fi

echo "Starting Dave in the background. Log: $LOG_FILE"
nohup python3 -u server.py >> "$LOG_FILE" 2>&1 &
SERVER_PID=$!
echo "Dave process: $SERVER_PID"

for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  if curl -s "$HEALTH_URL" >/dev/null 2>&1; then
    open_url "$URL"
    echo "Dave is online at $URL"
    exit 0
  fi
  sleep 1
done

echo "Dave did not come online. Recent log:"
tail -40 "$LOG_FILE"
exit 1
