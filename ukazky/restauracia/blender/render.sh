#!/usr/bin/env bash
# Spustí Blender so zámkom (na stroji smie bežať len jeden Blender naraz).
# Použitie: bash render.sh --view main --res 1600 --samples 160 --out render/main.png --json ../assets/stoly.json
BLENDER="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
HERE="$(cd "$(dirname "$0")" && pwd)"
LOCK="$(cd "$HERE/../../.." && pwd)/.blender.lock"
until mkdir "$LOCK" 2>/dev/null; do
  echo "zámok je obsadený, čakám…"
  sleep 20
done
trap 'rmdir "$LOCK"' EXIT
cd "$HERE"
"$BLENDER" -b --factory-startup -P scena.py -- "$@" 2>&1 | grep -v -E "^Fra:|^$" | tail -n 40
