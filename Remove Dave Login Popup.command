#!/bin/bash
# Double-click to stop Dave from opening automatically at login.

set -e

LABEL="com.ryanknight.dave"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

launchctl bootout "gui/$UID" "$PLIST" >/dev/null 2>&1 || true
rm -f "$PLIST"

echo ""
echo "Dave login popup removed."
echo "You can still open Dave manually with Open Dave.command."
echo ""
read -r -p "Press Enter to close..."
