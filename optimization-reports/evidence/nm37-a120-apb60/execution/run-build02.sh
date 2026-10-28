#!/usr/bin/env bash
set -euo pipefail
base=/home/zhangsi/tmp/FSA-m1/nm37-a120-20261023
source "$base/environment-build02.sh"
mkdir -p "$XDG_RUNTIME_DIR" "$XDG_CACHE_HOME"
cd "$FSA_A120_WORK"
finish() {
  result=$?
  trap - EXIT
  printf '%s\n' "$result" > "$base/c0-build02.exit"
  date -u '+%FT%TZ'
  exit "$result"
}
trap finish EXIT
for phase in prepare units formal hbm-startup 'sim 4' 'sim 8' 'sim 16' elaborate implement; do
  date -u '+%FT%TZ'
  echo "START $phase"
  read -ra phase_args <<< "$phase"
  "$FSA_A120_WORK/scripts/nm37-a120/run.sh" "${phase_args[@]}"
  echo "PASS $phase"
done
