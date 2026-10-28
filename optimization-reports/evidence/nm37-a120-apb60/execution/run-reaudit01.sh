#!/usr/bin/env bash
set -euo pipefail
base=/home/zhangsi/tmp/FSA-m1/nm37-a120-20261023
source "$base/environment-build02.sh"
export A120_REAUDIT_OUT="$base/reaudit01"
cd "$FSA_A120_WORK"
finish() {
  result=$?
  trap - EXIT
  printf '%s\n' "$result" > "$base/reaudit01.exit"
  date -u '+%FT%TZ'
  exit "$result"
}
trap finish EXIT
date -u '+%FT%TZ'
"$FSA_A120_WORK/scripts/nm37-a120/run.sh" reaudit
