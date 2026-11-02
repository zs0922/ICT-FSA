#!/usr/bin/env bash
set -euo pipefail
source /home/zhangsi/tmp/FSA-m1/nm37-apb100-20261101/A150/environment.sh
mkdir -p "$XDG_RUNTIME_DIR" "$XDG_CACHE_HOME"
cd /home/zhangsi/tmp/FSA-m1/nm37-apb100-20261101/A150/src
finish() {
  result=$?
  trap - EXIT
  printf '%s\n' "$result" > /home/zhangsi/tmp/FSA-m1/nm37-apb100-20261101/A150/build01.exit
  date -u '+%FT%TZ'
  exit "$result"
}
trap finish EXIT
for phase in prepare units formal hbm-startup 'sim 4' 'sim 8' 'sim 16' elaborate implement; do
  date -u '+%FT%TZ'
  echo "START $phase"
  printf '%s\n' "$phase" > /home/zhangsi/tmp/FSA-m1/nm37-apb100-20261101/A150/current-phase.txt
  read -ra phase_args <<< "$phase"
  if /home/zhangsi/tmp/FSA-m1/nm37-apb100-20261101/A150/src/scripts/nm37-a150/run.sh "${phase_args[@]}"; then
    echo "PASS $phase"
  else
    rc=$?
    # A failed Vivado run must remain a failure; still collect a machine-readable
    # audit of its reports if the final routed checkpoint exists.
    if [[ "$phase" == implement ]]; then
      python3 /home/zhangsi/tmp/FSA-m1/nm37-apb100-20261101/A150/src/scripts/nm37-a150/check.py physical > /home/zhangsi/tmp/FSA-m1/nm37-apb100-20261101/A150/physical-followup.log 2>&1 || true
    fi
    exit "$rc"
  fi
done
