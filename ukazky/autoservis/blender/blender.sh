#!/bin/sh
# Spustí Blender so zámkom (na počítači smie bežať len jeden Blender naraz).
#   sh blender.sh <skript.py> [argumenty skriptu]
LOCK="$(cd "$(dirname "$0")/../../.." && pwd)/.blender.lock"
n=0
until mkdir "$LOCK" 2>/dev/null; do
  n=$((n + 1)); [ $((n % 6)) -eq 1 ] && echo "čakám na zámok Blendera…"
  sleep 10
done
trap 'rmdir "$LOCK" 2>/dev/null' EXIT INT TERM
script="$1"; shift
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup -P "$script" -- "$@" 2>&1 \
  | grep -vE "^(Fra:|Blender |Read |Saved|Time:|$| *$)" | grep -vE "Sample [0-9]+/|Rendering|Remaining|Mem:"
echo "blender hotový"
