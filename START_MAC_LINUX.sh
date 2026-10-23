#!/usr/bin/env bash
# WhatIf launcher — Swayam Shakya
set -e
cd -- "$(dirname -- "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python 3.10 or newer is required. Install it, then run this launcher again.'
  exit 1
fi
exec python3 run.py "$@"
