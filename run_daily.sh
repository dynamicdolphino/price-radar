#!/bin/zsh
# Daily pipeline: scrape all active matches, then regenerate the dashboard.
set -e
cd "$(dirname "$0")"
/usr/bin/python3 src/scrape.py >> scrape.log 2>&1
/usr/bin/python3 src/dashboard.py >> scrape.log 2>&1
echo "run finished $(date '+%Y-%m-%d %H:%M')" >> scrape.log
