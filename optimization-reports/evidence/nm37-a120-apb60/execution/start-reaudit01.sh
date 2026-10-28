#!/usr/bin/env bash
set -euo pipefail
base=/home/zhangsi/tmp/FSA-m1/nm37-a120-20261023
[[ ! -e "$base/reaudit01" && ! -e "$base/reaudit01.pid" && ! -e "$base/reaudit01-driver.log" ]]
nohup setsid "$base/run-reaudit01.sh" > "$base/reaudit01-driver.log" 2>&1 < /dev/null &
pid=$!
printf '%s\n' "$pid" > "$base/reaudit01.pid"
printf 'Started read-only A120 acceptance PID %s\n' "$pid"
