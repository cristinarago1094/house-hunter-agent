#!/bin/zsh
set -e

PROJECT_DIR="/Users/crago/Library/CloudStorage/OneDrive-Microsoft/Documents/House Hunter Agent"
cd "$PROJECT_DIR"

if [ -f ".env" ]; then
  set -a
  source ".env"
  set +a
fi

/usr/bin/python3 main.py >> data/daily.log 2>&1
