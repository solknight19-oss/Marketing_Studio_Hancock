#!/bin/zsh
cd "$(dirname "$0")"
python3 scan_chad_updates.py "$@"
echo
echo "Done. If this needs a specific local database, run with --db /path/to/studio.db."
echo "If this needs the live site, run with STUDIO_PASSWORD set for Ryan's account."
read -k 1 "?Press any key to close..."
