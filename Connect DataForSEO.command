#!/bin/bash
# Connect DataForSEO to the Hancock Marketing Studio.
# Double-click this after creating the account at https://app.dataforseo.com/register
# Your API credentials are on the dashboard under API Access (an API login + API password —
# these are separate from the password you use to sign in to their website).
set -e
KEY_FILE="$HOME/Desktop/Knight/Hancock_CoPilot/dataforseo_key.txt"

echo "=================================================="
echo "  Connect DataForSEO to the Marketing Studio"
echo "=================================================="
echo
echo "You need the API LOGIN and API PASSWORD from"
echo "https://app.dataforseo.com  ->  API Access."
echo
printf "API login (usually your email): "
read DFS_LOGIN
printf "API password (typing is hidden): "
read -s DFS_PASSWORD
echo
echo

if [ -z "$DFS_LOGIN" ] || [ -z "$DFS_PASSWORD" ]; then
  echo "Nothing saved — both fields are required. Run this again when you have them."
  exit 1
fi

mkdir -p "$(dirname "$KEY_FILE")"
printf '%s:%s' "$DFS_LOGIN" "$DFS_PASSWORD" > "$KEY_FILE"
chmod 600 "$KEY_FILE"
unset DFS_PASSWORD

echo "Testing the connection against DataForSEO..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -u "$(cat "$KEY_FILE")" \
  -H "Content-Type: application/json" \
  -d '[{"keywords":["roof inspection"],"location_code":2840,"language_code":"en"}]' \
  https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live)

if [ "$HTTP_CODE" = "200" ]; then
  echo
  echo "✅ Connected. The key is saved (gitignored, never committed)."
  echo "   Restart the local Studio server and the 'Pull Real Keyword Data'"
  echo "   buttons in the Content tab will return live numbers."
  echo
  echo "   For the LIVE site: add an environment variable named DATAFORSEO_AUTH"
  echo "   with the same login:password value in the Render dashboard"
  echo "   (hancock-live-marketing-studio service -> Environment)."
else
  echo
  echo "⚠️  DataForSEO answered with HTTP $HTTP_CODE — the credentials may be wrong,"
  echo "   or the account has no balance yet. The key was saved; fix the account"
  echo "   and run this again to re-test. Nothing is broken."
fi
echo
read -p "Press Return to close."
