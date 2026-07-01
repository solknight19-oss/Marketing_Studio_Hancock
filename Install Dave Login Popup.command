#!/bin/bash
# Double-click to make Dave open automatically when you log into this Mac.

set -e
cd "$(dirname "$0")"

LABEL="com.ryanknight.dave"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LAUNCHER="$PWD/Open Dave.command"

mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/open</string>
    <string>$LAUNCHER</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$PWD/app_data/dave_login_popup.log</string>
  <key>StandardErrorPath</key>
  <string>$PWD/app_data/dave_login_popup.err</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$UID" "$PLIST" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$UID" "$PLIST"
launchctl enable "gui/$UID/$LABEL"

open "$LAUNCHER"

echo ""
echo "Dave is installed as a login popup."
echo "He will open automatically when you log into this Mac."
echo ""
echo "Installed:"
echo "$PLIST"
echo ""
read -r -p "Press Enter to close..."
