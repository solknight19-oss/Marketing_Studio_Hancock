#!/bin/bash
# Installs the Electron runtime used by Dave Desktop.

cd "$(dirname "$0")"

PNPM="/Users/rknight/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm"
NODE_BIN="/Users/rknight/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin"
export PATH="$NODE_BIN:$PATH"

echo "Installing Dave Desktop dependencies..."
mkdir -p "$PWD/app_data/electron-cache"
export electron_config_cache="$PWD/app_data/electron-cache"
if command -v npm >/dev/null 2>&1; then
  npm install --ignore-scripts
elif [ -x "$PNPM" ]; then
  "$PNPM" install --ignore-scripts
else
  echo "npm was not found, and bundled pnpm was not available."
  echo "Install Node.js first, then run this again."
  exit 1
fi

if [ -f "node_modules/electron/install.js" ]; then
  "$NODE_BIN/node" "node_modules/electron/install.js"
fi

echo ""
echo "Dave Electron is installed."
echo "Start it with: Start Dave Electron.command"
