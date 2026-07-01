#!/bin/bash
# Starts Dave Desktop as an Electron app.

cd "$(dirname "$0")"

NODE_BIN="/Users/rknight/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin"
export PATH="$NODE_BIN:$PATH"

export PORT="${PORT:-8772}"
export HOST="${HOST:-127.0.0.1}"
export APP_DATA_DIR="${APP_DATA_DIR:-$PWD/app_data}"
export DAVE_LOCAL_AUTO_LOGIN=1
export DAVE_ELEVENLABS_VOICE_NAME="${DAVE_ELEVENLABS_VOICE_NAME:-Jarvis 1.1 Voice}"
export DAVE_ELEVENLABS_FALLBACK_VOICE_ID="${DAVE_ELEVENLABS_FALLBACK_VOICE_ID:-6Lopt6P83rUsEz3TeM5C}"
export DAVE_ELEVENLABS_FALLBACK_VOICE_NAME="${DAVE_ELEVENLABS_FALLBACK_VOICE_NAME:-Jarvis}"

if [ -z "$ELEVENLABS_API_KEY" ] && [ -s "../Hancock_CoPilot/elevenlabs_key.txt" ]; then
  export ELEVENLABS_API_KEY="$(cat ../Hancock_CoPilot/elevenlabs_key.txt)"
fi
if [ -z "$ANTHROPIC_API_KEY" ] && [ -s "../Hancock_CoPilot/anthropic_key.txt" ]; then
  export ANTHROPIC_API_KEY="$(cat ../Hancock_CoPilot/anthropic_key.txt)"
fi
if [ -z "$OPENAI_API_KEY" ] && [ -s "../Hancock_CoPilot/openai_key.txt" ]; then
  export OPENAI_API_KEY="$(cat ../Hancock_CoPilot/openai_key.txt)"
fi

if [ ! -x "node_modules/.bin/electron" ]; then
  echo "Dave Electron is not installed yet."
  echo "Run: Install Dave Electron.command"
  exit 1
fi

health_current() {
  curl -fsS --max-time 2 "http://127.0.0.1:${PORT}/healthz" 2>/dev/null | grep -q 'dave_stt_fallback_v10'
}

health_any() {
  curl -fsS --max-time 2 "http://127.0.0.1:${PORT}/healthz" >/dev/null 2>&1
}

mkdir -p "$APP_DATA_DIR"

if ! health_current; then
  if health_any; then
    stale_pids="$(lsof -tiTCP:${PORT} -sTCP:LISTEN 2>/dev/null || true)"
    if [ -n "$stale_pids" ]; then
      echo "Stopping older Dave service..."
      kill $stale_pids 2>/dev/null || true
      sleep 1
    fi
  fi
  echo "Starting Dave background service..."
  nohup python3 -u server.py >> "$APP_DATA_DIR/dave_server.log" 2>&1 &
  echo "$!" > "$APP_DATA_DIR/dave_server.pid"
  for _ in 1 2 3 4 5 6 7 8 9 10 11 12; do
    if health_current; then
      break
    fi
    sleep 1
  done
fi

./node_modules/.bin/electron .
