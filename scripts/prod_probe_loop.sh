#!/usr/bin/env bash
# Runs scripts/prod_probe.py every 30s, forever, until killed. Night
# mission #3, Tache 1: background probe for the whole session, the raw
# data behind the Cloudflare support ticket. Launch detached (nohup ... &
# disown) so it survives independently of any single tool call.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
while true; do
  python3 scripts/prod_probe.py
  sleep 30
done
