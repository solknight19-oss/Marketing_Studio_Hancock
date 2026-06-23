#!/bin/bash
cd "$(dirname "$0")"
echo "Starting Hancock deploy preview..."
python3 server.py &
PID=$!
sleep 2
open "http://127.0.0.1:8765"
echo "Preview running at http://127.0.0.1:8765"
echo "Close this window to stop it."
wait $PID
